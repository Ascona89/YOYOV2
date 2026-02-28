import streamlit as st
import pandas as pd
from datetime import datetime, date
from supabase import create_client
import math
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import json
import requests
import re
from datetime import datetime

# =====================================================
# 🔐 Passwörter
# =====================================================
USER_PASSWORD = "oyysouth"
SILENT_USER_PASSWORD = "silentlogin"
ADMIN_PASSWORD = "sebaforceo"
PIPELINE_PASSWORDS = ["south", "mids", "east", "north"]

# =====================================================
# 🧠 Supabase
# =====================================================
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

def log_login(role, success):
    supabase.table("login_events").insert({
        "role": role,
        "success": success,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

# =====================================================
# 🧠 Session State Initialisierung
# =====================================================
st.session_state.setdefault("logged_in", False)
st.session_state.setdefault("is_admin", False)
st.session_state.setdefault("USER_PASSWORD", USER_PASSWORD)
st.session_state.setdefault("show_map", False)

# =====================================================
# 🔐 Login Funktion
# =====================================================
def login(password):
    user_pw = st.session_state.get("USER_PASSWORD", USER_PASSWORD)
    if password == user_pw:
        st.session_state.logged_in = True
        st.session_state.is_admin = False
        log_login("User", True)
        st.rerun()
    elif password == SILENT_USER_PASSWORD:
        st.session_state.logged_in = True
        st.session_state.is_admin = False
        st.rerun()
    elif password == ADMIN_PASSWORD:
        st.session_state.logged_in = True
        st.session_state.is_admin = True
        log_login("Admin", True)
        st.rerun()
    else:
        log_login("Unknown", False)
        st.error("❌ Falsches Passwort")

# =====================================================
# 👑 Admin Dashboard
# =====================================================
if st.session_state.is_admin:
    st.header("👑 Admin Dashboard")
    data = supabase.table("login_events").select("*").order("created_at", desc=True).execute()
    df = pd.DataFrame(data.data)
    if not df.empty:
        df["Datum"] = pd.to_datetime(df["created_at"]).dt.date
        st.subheader("📄 Login-Historie")
        st.dataframe(df, use_container_width=True)
        st.subheader("📊 Logins pro Tag")
        logins_per_day = df[df["success"]==True].groupby("Datum").size().reset_index(name="Logins")
        st.dataframe(logins_per_day, use_container_width=True)
        st.bar_chart(logins_per_day.set_index("Datum"))
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("CSV Export", csv, "login_history.csv", "text/csv")
    else:
        st.info("Noch keine Login-Daten vorhanden.")

    st.subheader("🔑 User Passwort ändern")
    new_password = st.text_input("Neues User-Passwort", type="password")
    if st.button("Update User Passwort"):
        if new_password:
            st.session_state['USER_PASSWORD'] = new_password
            st.success("✅ Passwort erfolgreich geändert!")
        else:
            st.warning("Bitte ein gültiges Passwort eingeben.")
    st.stop()

# =====================================================
# 🔐 Login Abfrage
# =====================================================
if not st.session_state.get("logged_in", False):
    st.header("🔐 Login")
    pw = st.text_input("Passwort eingeben", type="password")
    if st.button("Login"):
        login(pw)
    st.stop()

# =====================================================
# 🔧 App Setup
# =====================================================
st.set_page_config(page_title="Kalkulations-App", layout="wide")
st.title("📊 Kalkulations-App")
page = st.sidebar.radio(
    "Wähle eine Kalkulation:",
    ["Platform", "Cardpayment", "Pricing", "Radien", "Contractnumbers", "Pipeline", "Restaurants"]
)

# ==========================
# Hilfsfunktionen für persistente Inputs
# ==========================
def persistent_number_input(label, key, value=0.0, **kwargs):
    st.session_state.setdefault(key, value)
    st.session_state[key] = st.number_input(label, value=st.session_state[key], key=f"ui_{key}", **kwargs)
    return st.session_state[key]

def persistent_text_input(label, key, value="", **kwargs):
    st.session_state.setdefault(key, value)
    st.session_state[key] = st.text_input(label, value=st.session_state[key], key=f"ui_{key}", **kwargs)
    return st.session_state[key]

def persistent_selectbox(label, key, options, index=0, **kwargs):
    st.session_state.setdefault(key, options[index])
    st.session_state[key] = st.selectbox(label, options, index=options.index(st.session_state[key]), **kwargs)
    return st.session_state[key]

# =====================================================
# 🏁 Platform
# =====================================================
def show_platform():
    st.header("🏁 Platform Kalkulation")
    col1, col2 = st.columns([2, 1.5])
    with col1:
        st.subheader("Eingaben")
        revenue = persistent_number_input("Revenue on platform (€)", "revenue", 0.0, step=250.0)
        commission_pct = persistent_number_input("Commission (%)", "commission_pct", 14.0, step=1.0)
        avg_order_value = persistent_number_input("Average order value (€)", "avg_order_value", 25.0, step=5.0)
        service_fee = persistent_number_input("Service Fee (€)", "service_fee", 0.69, step=0.1)
        toprank_per_order = persistent_number_input("TopRank per Order (€)", "toprank_per_order", 0.0, step=0.1)

    cost_platform = revenue * (commission_pct / 100) + (0.7 * revenue / avg_order_value if avg_order_value else 0) * service_fee
    sum_of_orders = revenue / avg_order_value if avg_order_value else 0
    toprank_cost = sum_of_orders * toprank_per_order
    total_cost = cost_platform + toprank_cost

    st.markdown("### 💶 Cost on Platform")
    st.markdown(f"<div style='color:red; font-size:28px;'>{total_cost:,.2f} €</div>", unsafe_allow_html=True)
    st.markdown("---")

    st.subheader("Vertragsdetails")
    OTF = persistent_number_input("One Time Fee (OTF) (€)", "OTF", 0.0, step=100.0)
    MRR = persistent_number_input("Monthly Recurring Revenue (MRR) (€)", "MRR", 0.0, step=10.0)
    contract_length = persistent_number_input("Contract length (Monate)", "contract_length", 24, step=12)

    transaction = 0.7 * revenue / 5 * 0.35
    cost_monthly = MRR + transaction
    saving_monthly = total_cost - cost_monthly
    saving_over_contract = saving_monthly * contract_length

    st.markdown("---")
    st.subheader("📊 Kennzahlen")
    col1, col2, col3, col4 = st.columns(4)
    col1.markdown(f"<div style='color:red; font-size:28px;'>💶 {total_cost:,.2f} €</div>", unsafe_allow_html=True)
    col1.caption("Total Platform Cost")
    col2.markdown(f"<div style='color:blue; font-size:28px;'>💳 {cost_monthly:,.2f} €</div>", unsafe_allow_html=True)
    col2.caption("Cost Monthly (MRR + Transaction)")
    col3.markdown(f"<div style='color:green; font-size:28px;'>💰 {saving_monthly:,.2f} €</div>", unsafe_allow_html=True)
    col3.caption("Saving Monthly")
    col4.markdown(f"<div style='color:orange; font-size:28px;'>💸 {saving_over_contract:,.2f} €</div>", unsafe_allow_html=True)
    col4.caption("Saving over Contract Length")

# =====================================================
# 💳 Cardpayment
# =====================================================
def show_cardpayment():
    st.header("💳 Cardpayment Vergleich")
    col_rev, col_sum = st.columns(2)
    with col_rev:
        revenue = persistent_number_input("Revenue (€)", "revenue", 0.0, step=250.0)
    with col_sum:
        sum_payments = persistent_number_input("Sum of payments", "sum_payments", 0.0, step=20.0)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Actual")
        mrr_a = persistent_number_input("Monthly Fee (€)", "mrr_a", 0.0, step=5.0)
        comm_a = persistent_number_input("Commission (%)", "comm_a", 1.39, step=0.01)
        auth_a = persistent_number_input("Authentification Fee (€)", "auth_a", 0.0)
    with col2:
        st.subheader("Offer")
        mrr_o = persistent_number_input("Monthly Fee (€)", "mrr_o", 0.0, step=5.0)
        comm_o = persistent_number_input("Commission (%)", "comm_o", 1.19, step=0.01)
        auth_o = persistent_number_input("Authentification Fee (€)", "auth_o", 0.06)

    total_actual = revenue * (comm_a/100) + sum_payments * auth_a + mrr_a
    total_offer = revenue * (comm_o/100) + sum_payments * auth_o + mrr_o
    saving = total_offer - total_actual
    saving_per_year = saving * 12

    st.markdown("---")
    col3, col4, col5, col6 = st.columns(4)
    col3.markdown(f"<div style='color:red; font-size:28px;'>💳 {total_actual:,.2f} €</div>", unsafe_allow_html=True)
    col3.caption("Total Actual")
    col4.markdown(f"<div style='color:blue; font-size:28px;'>💳 {total_offer:,.2f} €</div>", unsafe_allow_html=True)
    col4.caption("Total Offer")
    col5.markdown(f"<div style='color:green; font-size:28px;'>💰 {saving:,.2f} €</div>", unsafe_allow_html=True)
    col5.caption("Ersparnis (Offer - Actual)")
    col6.markdown(f"<div style='color:orange; font-size:28px;'>💸 {saving_per_year:,.2f} €</div>", unsafe_allow_html=True)
    col6.caption("Ersparnis pro Jahr")



# =====================================================
# 💳 Contract Numbers
# =====================================================
def show_contractnumbers():
    st.header("📑 Contract Numbers")

    # ======================
    # Produkte Software
    # ======================
    df_sw = pd.DataFrame({
        "Produkt": ["Shop", "App", "POS", "Pay", "Connect", "TSE", "Kiosk"],
        "List_OTF": [999, 49, 999, 49, 0, 0, 0],
        "List_MRR": [119, 49, 89, 25, 13.72, 12, 89],
        "Min_OTF": [365, 15, 365, 35, 0, 0, 0],
        "Min_MRR": [50, 15, 49, 5, 15, 12, 49],
        "Typ": ["Software"] * 7
    })

    # ======================
    # Produkte Hardware
    # ======================
    df_hw = pd.DataFrame({
        "Produkt": ["Ordermanager", "POS inkl 1 Printer", "Cash Drawer", "Extra Printer", "Additional Display", "PAX", "Kiosk"],
        "List_OTF": [299, 1699, 149, 199, 100, 299, 1699],
        "Min_OTF": [135, 350, 50, 99, 100, 225, 1441.02],
        "List_MRR": [0] * 7,
        "Min_MRR": [0] * 7,
        "Typ": ["Hardware"] * 7
    })

    # ======================
    # Session State Defaults
    # ======================
    for i in range(len(df_sw)):
        st.session_state.setdefault(f"qty_sw_{i}", 0)
    for i in range(len(df_hw)):
        st.session_state.setdefault(f"qty_hw_{i}", 0)

    # ======================
    # Eingaben Gesamt MRR / OTF
    # ======================
    col1, col2 = st.columns(2)
    with col1:
        total_mrr = st.number_input("💶 Gesamt MRR (€)", min_value=0.0, step=50.0, key="total_mrr_cn")
    with col2:
        total_otf = st.number_input("💶 Gesamt OTF (€)", min_value=0.0, step=100.0, key="total_otf_cn")

    # ======================
    # Zahlungsoption
    # ======================
    st.subheader("💳 Zahlungsoption (optional)")
    zahlung = st.selectbox(
        "Auswahl",
        [
            "Keine",
            "Gemischte Zahlung (25% + 12 Wochen) 10%",
            "Online-Umsatz (100%) 10%",
            "Monatliche Raten (12 Monate) 35%",
            "Online-Umsatz (25% + 12 Wochen) 15%"
        ],
        key="zahlung_cn"
    )

    if zahlung == "Gemischte Zahlung (25% + 12 Wochen) 10%":
        otf_adjusted = total_otf / 110 * 100
    elif zahlung == "Online-Umsatz (100%) 10%":
        otf_adjusted = total_otf / 110 * 100
    elif zahlung == "Monatliche Raten (12 Monate) 35%":
        otf_adjusted = total_otf / 135 * 100
    elif zahlung == "Online-Umsatz (25% + 12 Wochen) 15%":
        otf_adjusted = total_otf / 115 * 100
    else:
        otf_adjusted = total_otf

    st.caption(f"Verwendete OTF für Kalkulation: **{round(otf_adjusted)} €**")

    # ======================
    # Mengen Software
    # ======================
    st.subheader("💻 Software")
    cols = st.columns(len(df_sw))
    for i, row in df_sw.iterrows():
        with cols[i]:
            st.session_state[f"qty_sw_{i}"] = st.number_input(
                label=row["Produkt"],
                min_value=0,
                step=1,
                value=st.session_state[f"qty_sw_{i}"],
                key=f"qty_sw_input_{i}"
            )

    # ======================
    # Mengen Hardware
    # ======================
    st.subheader("🖨️ Hardware")
    cols = st.columns(len(df_hw))
    for i, row in df_hw.iterrows():
        with cols[i]:
            st.session_state[f"qty_hw_{i}"] = st.number_input(
                label=row["Produkt"],
                min_value=0,
                step=1,
                value=st.session_state[f"qty_hw_{i}"],
                key=f"qty_hw_input_{i}"
            )

    df_sw["Menge"] = [st.session_state[f"qty_sw_{i}"] for i in range(len(df_sw))]
    df_hw["Menge"] = [st.session_state[f"qty_hw_{i}"] for i in range(len(df_hw))]

    # ======================
    # Preislogik
    # ======================
    min_mrr_total = (df_sw["Menge"] * df_sw["Min_MRR"]).sum()
    list_mrr_total = (df_sw["Menge"] * df_sw["List_MRR"]).sum()
    min_otf_total = (
        (df_sw["Menge"] * df_sw["Min_OTF"]).sum() +
        (df_hw["Menge"] * df_hw["Min_OTF"]).sum()
    )
    list_otf_total = (
        (df_sw["Menge"] * df_sw["List_OTF"]).sum() +
        (df_hw["Menge"] * df_hw["List_OTF"]).sum()
    )

    # Warnlogik
    if total_mrr < min_mrr_total or otf_adjusted < min_otf_total:
        st.error("🔴 Preis zu gering (unter Mindestpreis)")
    elif total_mrr > list_mrr_total or otf_adjusted > list_otf_total:
        st.warning("🟡 Preis über Liste")

    # OTF Verteilung
    base = list_otf_total
    factor = otf_adjusted / base if base > 0 else 0
    df_sw["OTF"] = (df_sw["Menge"] * df_sw["List_OTF"] * factor).round(0)
    df_hw["OTF"] = (df_hw["Menge"] * df_hw["List_OTF"] * factor).round(0)

    # MRR Berechnung
    connect_qty = df_sw.loc[df_sw["Produkt"] == "Connect", "Menge"].values[0]
    tse_qty = df_sw.loc[df_sw["Produkt"] == "TSE", "Menge"].values[0]

    connect_total = connect_qty * 13.72
    tse_total = tse_qty * 12.00

    fixed_total = connect_total + tse_total
    remaining_mrr = max(total_mrr - fixed_total, 0)

    proportional_df = df_sw[~df_sw["Produkt"].isin(["Connect", "TSE"])]
    mrr_base = (proportional_df["Menge"] * proportional_df["List_MRR"]).sum()
    mrr_factor = remaining_mrr / mrr_base if mrr_base > 0 else 0

    df_sw["MRR_Monat"] = 0.0
    df_sw["MRR_Woche"] = 0.0

    for i, row in proportional_df.iterrows():
        monat = row["Menge"] * row["List_MRR"] * mrr_factor
        df_sw.loc[i, "MRR_Monat"] = round(monat, 2)
        df_sw.loc[i, "MRR_Woche"] = round(monat / 4, 2)

    # Connect & TSE
    df_sw.loc[df_sw["Produkt"] == "Connect", "MRR_Monat"] = connect_total
    df_sw.loc[df_sw["Produkt"] == "Connect", "MRR_Woche"] = connect_qty * 3.43
    df_sw.loc[df_sw["Produkt"] == "TSE", "MRR_Monat"] = tse_total
    df_sw.loc[df_sw["Produkt"] == "TSE", "MRR_Woche"] = tse_qty * 3.00

    # =====================================================
    # 📝 Vertrags-Textgenerator
    # =====================================================
    st.markdown("---")
    st.subheader("📝 Vertrags-Textgenerator")

    restaurant_name = st.text_input("Restaurant Name", value="RESTAURANTNAME", key="restaurant_name_cn")

    products_sw_dict = {row["Produkt"]: row for _, row in df_sw.iterrows()}
    products_hw_dict = {row["Produkt"]: row for _, row in df_hw.iterrows()}

    def check_mark(product):
        return "✅" if products_sw_dict.get(product, {}).get("Menge", 0) > 0 else "❌"

    def mrr_text(product):
        menge = products_sw_dict.get(product, {}).get("Menge", 0)
        if menge > 0:
            return f"{products_sw_dict[product]['MRR_Monat']:.2f} €"
        return ""

    # Hardware Mengen
    qty_pos = products_hw_dict.get("POS inkl 1 Printer", {}).get("Menge", 0)
    qty_pax = products_hw_dict.get("PAX", {}).get("Menge", 0)
    qty_order = products_hw_dict.get("Ordermanager", {}).get("Menge", 0)
    qty_cashdrawer = products_hw_dict.get("Cash Drawer", {}).get("Menge", 0)
    qty_printer = products_hw_dict.get("Extra Printer", {}).get("Menge", 0)
    qty_addscreen = products_hw_dict.get("Additional Display", {}).get("Menge", 0)
    qty_kiosk = products_hw_dict.get("Kiosk", {}).get("Menge", 0)

    # --- Standardtext ---
    pos_mrr_total = df_sw.loc[df_sw["Produkt"].isin(["POS", "TSE"]), "MRR_Monat"].sum()
    contract_text = f"""
Signed: {restaurant_name}

Web Shop (119€) {check_mark('Shop')} {mrr_text('Shop')}
App (49€) {check_mark('App')} {mrr_text('App')}
POS (89€) {check_mark('POS')} {pos_mrr_total:.2f} €
GAW (150€) ✅
Connect (15€) {check_mark('Connect')} {mrr_text('Connect')}
Kiosk (89€) {check_mark('Kiosk')} {mrr_text('Kiosk')}

Lead Quality:
Lead Gen:
GMB:
Discount:
MRR: {df_sw['MRR_Monat'].sum():.2f} €
SUF: {df_sw['OTF'].sum():.0f} €
Hardware: {df_hw['OTF'].sum():.0f} €
ZDS:
"""

    # --- PAY Block optional (dynamische Werte) ---
    pay_qty = products_sw_dict.get("Pay", {}).get("Menge", 0)
    if pay_qty > 0:
        pay_otf = df_sw.loc[df_sw["Produkt"] == "Pay", "OTF"].sum()
        pay_mrr = df_sw.loc[df_sw["Produkt"] == "Pay", "MRR_Monat"].sum()
        pay_hw = 0  # falls relevant, sonst 0

        contract_text += f"""
PAY:
Commission:
Trans:
Auth:
KYC:
Hardware: {pay_hw:.0f} €
SUF: {pay_otf:.0f} €
MRR: {pay_mrr:.2f} €
Merchant Statement:
"""

    # --- Hardware Block optional ---
    if qty_pos + qty_pax + qty_cashdrawer + qty_printer + qty_addscreen + qty_kiosk > 0:
        contract_text += f"""
Number of POS: {qty_pos}
Number of Printers: {qty_printer}
Additional Screen: {qty_addscreen}
Cash Drawer: {qty_cashdrawer}
Kiosk: {qty_kiosk}
"""

    st.text_area("📄 Generierter Vertrags-Text", contract_text, height=420)

# =====================================================
# 💰 Pricing
# =====================================================
def show_pricing():
    st.header("💰 Pricing Kalkulation")

    software_data = {
        "Produkt": ["Shop", "App", "POS", "Pay", "Connect", "Kiosk"],
        "Min_OTF": [365, 15, 365, 35, 0, 0],
        "List_OTF": [999, 49, 999, 49, 0, 0],
        "Min_MRR": [50, 15, 49, 5, 15, 49],
        "List_MRR": [119, 49, 89, 25, 15, 89]
    }

    hardware_data = {
        "Produkt": [
            "Ordermanager", "POS inkl 1 Printer", "Cash Drawer",
            "Extra Printer", "Additional Display", "PAX", "Kiosk"
        ],
        "Min_OTF": [135, 350, 50, 99, 100, 225, 1441.02],
        "List_OTF": [299, 1699, 149, 199, 100, 299, 1699],
        "Min_MRR": [0, 0, 0, 0, 0, 0, 49],
        "List_MRR": [0, 0, 0, 0, 0, 89, 89]
    }

    # Leasing Preise (monatlich)
    leasing_prices = {
        "Ordermanager": {"min": 9.00, "list": 19.93},
        "POS inkl 1 Printer": {"min": 23.33, "list": 113.27},
        "Cash Drawer": {"min": 3.33, "list": 9.93},
        "Extra Printer": {"min": 7.17, "list": 19.07},
        "Additional Display": {"min": 9.59, "list": 9.59},
        "PAX": {"min": 15.00, "list": 19.93},
        "Kiosk": {"min": 96.07, "list": 96.07}
    }

    df_sw = pd.DataFrame(software_data)
    df_hw = pd.DataFrame(hardware_data)

    # -------------------------------
    # Session Defaults
    # -------------------------------
    for i in range(len(df_sw)):
        st.session_state.setdefault(f"sw_{i}", 0)
    for i in range(len(df_hw)):
        st.session_state.setdefault(f"hw_{i}", 0)
        st.session_state.setdefault(f"lease_hw_{i}", 0)

    st.session_state.setdefault("pricing_discount", 0)

    # -------------------------------
    # Software Inputs
    # -------------------------------
    st.subheader("💻 Software")
    cols = st.columns(len(df_sw))
    for i, row in df_sw.iterrows():
        with cols[i]:
            st.number_input(row["Produkt"], min_value=0, step=1, key=f"sw_{i}")
    df_sw["Menge"] = [st.session_state[f"sw_{i}"] for i in range(len(df_sw))]

    # -------------------------------
    # Hardware Kauf Inputs
    # -------------------------------
    st.subheader("🖨️ Hardware Kauf")
    cols = st.columns(len(df_hw))
    for i, row in df_hw.iterrows():
        with cols[i]:
            st.number_input(row["Produkt"], min_value=0, step=1, key=f"hw_{i}")
    df_hw["Menge"] = [st.session_state[f"hw_{i}"] for i in range(len(df_hw))]

    # -------------------------------
    # Rabatt
    # -------------------------------
    discount = st.number_input("Rabatt (%)", min_value=0, max_value=100, step=1, key="pricing_discount")
    discount_factor = 1 - discount / 100

    # -------------------------------
    # Berechnungen Listpreise
    # -------------------------------
    otf_software_list = sum([
        qty * (row["List_OTF"] if row["Produkt"] != "Kiosk" else 0)
        for qty, (_, row) in zip(df_sw["Menge"], df_sw.iterrows())
    ]) * discount_factor
    mrr_list = (df_sw["Menge"] * df_sw["List_MRR"]).sum() * discount_factor
    otf_hardware_list = (df_hw["Menge"] * df_hw["List_OTF"]).sum() * discount_factor
    total_otf_list = otf_software_list + otf_hardware_list

    # Minimalpreise
    min_mrr_total = (df_sw["Menge"] * df_sw["Min_MRR"]).sum()
    min_otf_total = sum([
        qty * (row["Min_OTF"] if row["Produkt"] != "Kiosk" else 0)
        for qty, (_, row) in zip(df_sw["Menge"], df_sw.iterrows())
    ]) + (df_hw["Menge"] * df_hw["Min_OTF"]).sum()
    min_leasing_total = sum([
        st.session_state[f"lease_hw_{i}"] * leasing_prices[row["Produkt"]]["min"]
        for i, row in df_hw.iterrows()
    ])

    # -------------------------------
    # Anzeige Listpreise
    # -------------------------------
    st.subheader("📊 Übersicht Listpreise")
    col1, col2, col3, col4 = st.columns(4)
    col1.markdown(f"### 🧩 MRR LIST: {mrr_list:,.2f} €")
    col2.markdown(f"### 🖥️ OTF LIST: {total_otf_list:,.2f} €")
    col3.markdown(f"### 🖨️ OTF HARDWARE: {otf_hardware_list:,.2f} €")
    col4.markdown(f"### 💻 OTF SOFTWARE: {otf_software_list:,.2f} €")

    # -------------------------------
    # Neue Hardware Leasing Eingaben
    # -------------------------------
    st.markdown("---")
    st.subheader("Hardware Leasing")

    cols = st.columns(len(df_hw))
    leasing_hw_qty = []
    for i, row in df_hw.iterrows():
        with cols[i]:
            qty = st.number_input(
                row["Produkt"],
                min_value=0,
                step=1,
                key=f"lease_hw_{i}"
            )
            leasing_hw_qty.append(qty)

    # Berechnung Leasing monatlich mit festen Preisen
    leasing_monatlich = sum([
        qty * leasing_prices[row["Produkt"]]["list"] for qty, (_, row) in zip(leasing_hw_qty, df_hw.iterrows())
    ])

    # -------------------------------
    # Ergebnisanzeige MRR Software / Leasing / Gesamt
    # -------------------------------
    st.markdown("### 📊 Leasing Übersicht")
    col1, col2, col3 = st.columns(3)
    col1.metric("MRR Software", f"{mrr_list:,.2f} €")
    col2.metric("Leasing Hardware", f"{leasing_monatlich:,.2f} €")
    col3.metric("Gesamt", f"{(mrr_list + leasing_monatlich):,.2f} €")

    # -------------------------------
    # Minimalpreise nur über Dropdown (Erweitert)
    # -------------------------------
    with st.expander("🔻 Erweitert"):
        st.markdown(f"### MIN MRR Software: {min_mrr_total:,.2f} €")
        st.markdown(f"### MIN OTF Software+Hardware: {min_otf_total:,.2f} €")
        st.markdown(f"### MIN Leasing Hardware: {min_leasing_total:,.2f} €")

    # -------------------------------
    # Preistabelle
    # -------------------------------
    with st.expander("Preisdetails anzeigen"):
        df_show = pd.concat([df_sw, df_hw])[[
            "Produkt", "Min_OTF", "List_OTF", "Min_MRR", "List_MRR"
        ]]

        st.dataframe(
            df_show.style.format({
                "Min_OTF": "{:,.0f} €",
                "List_OTF": "{:,.0f} €",
                "Min_MRR": "{:,.0f} €",
                "List_MRR": "{:,.0f} €",
            }),
            hide_index=True,
            use_container_width=True
        )
# =====================================================
# 📍 Radien
# =====================================================
def show_radien():
    import math
    import folium
    import pandas as pd
    from streamlit_folium import st_folium
    import json
    import requests
    import streamlit as st

    st.header("🗺️ Radien oder PLZ-Flächen anzeigen")

    # =====================================================
    # Session State für PLZ-Flächen
    # =====================================================
    if "plz_blocks" not in st.session_state:
        st.session_state["plz_blocks"] = [
            {"plz": "", "min_order": 0.0, "delivery_cost": 0.0}
        ]

    # =====================================================
    # Eingabe & Modus
    # =====================================================
    col_input, col_mode = st.columns([3, 1])
    with col_input:
        user_input = st.text_input(
            "📍 Adresse, Stadt oder PLZ eingeben (nur für Radien)"
        )
    with col_mode:
        mode = st.selectbox("Anzeige-Modus", ["Radien", "PLZ-Flächen"])

    # =====================================================
    # Karte vorbereiten
    # =====================================================
    m = folium.Map(location=[51.1657, 10.4515], zoom_start=6)
    colors = [
        "blue", "green", "red", "orange", "purple",
        "darkred", "darkblue", "darkgreen", "cadetblue", "pink"
    ]

    # =====================================================
    # PLZ-FLÄCHEN
    # =====================================================
    if mode == "PLZ-Flächen":

        try:
            with open("plz-5stellig.geojson", "r", encoding="utf-8") as f:
                geojson_data = json.load(f)
        except Exception as e:
            st.error(f"GeoJSON konnte nicht geladen werden: {e}")
            return

        st.subheader("📦 Liefergebiete (PLZ-Flächen)")

        for idx, block in enumerate(st.session_state["plz_blocks"]):
            col_plz, col_min, col_del = st.columns([3, 1.5, 1.5])

            with col_plz:
                block["plz"] = st.text_input(
                    f"PLZ-Gruppe {idx+1} (Komma getrennt)",
                    value=block["plz"],
                    key=f"plz_{idx}"
                )

            with col_min:
                block["min_order"] = st.number_input(
                    "Mindestbestellwert (€)",
                    min_value=0.0,
                    step=1.0,
                    value=block["min_order"],
                    key=f"min_{idx}"
                )

            with col_del:
                block["delivery_cost"] = st.number_input(
                    "Lieferkosten (€)",
                    min_value=0.0,
                    step=0.5,
                    value=block["delivery_cost"],
                    key=f"del_{idx}"
                )

        if len(st.session_state["plz_blocks"]) < 10:
            if st.button("➕ Eingabefeld hinzufügen"):
                st.session_state["plz_blocks"].append(
                    {"plz": "", "min_order": 0.0, "delivery_cost": 0.0}
                )

        all_coords = []
        download_rows = []

        for block in st.session_state["plz_blocks"]:
            if not block["plz"].strip():
                continue

            plz_list = [p.strip() for p in block["plz"].split(",") if p.strip()]

            for feature in geojson_data.get("features", []):
                props = feature.get("properties", {})
                plz_val = props.get("plz") or props.get("POSTCODE")

                if plz_val in plz_list:
                    geom = feature["geometry"]
                    coords = geom["coordinates"]

                    if geom["type"] == "Polygon":
                        for ring in coords:
                            all_coords.extend([[lat, lon] for lon, lat in ring])
                    elif geom["type"] == "MultiPolygon":
                        for poly in coords:
                            for ring in poly:
                                all_coords.extend([[lat, lon] for lon, lat in ring])

                    folium.GeoJson(
                        feature,
                        style_function=lambda x, c=colors[st.session_state["plz_blocks"].index(block) % len(colors)]: {
                            "fillColor": c,
                            "color": "black",
                            "weight": 1,
                            "fillOpacity": 0.3
                        },
                        tooltip=f"""
                        PLZ: {plz_val}<br>
                        Mindestbestellwert: {block['min_order']} €<br>
                        Lieferkosten: {block['delivery_cost']} €
                        """
                    ).add_to(m)

                    download_rows.append({
                        "PLZ": plz_val,
                        "Mindestbestellwert": block["min_order"],
                        "Lieferkosten": block["delivery_cost"]
                    })

        if all_coords:
            m.fit_bounds(all_coords)

        st_folium(m, width=700, height=500)

        if download_rows:
            df_download = pd.DataFrame(download_rows)
            csv = df_download.to_csv(index=False).encode("utf-8")

            st.download_button(
                "📥 PLZ-Liefergebiete herunterladen",
                csv,
                "plz_liefergebiete.csv",
                "text/csv"
            )

    # =====================================================
    # RADIEN
    # =====================================================
    else:
        CSV_URL = "https://raw.githubusercontent.com/Ascona89/Kalkulationen.py/main/plz_geocoord.csv"

        @st.cache_data
        def load_plz_data():
            df = pd.read_csv(CSV_URL, dtype=str)
            df["lat"] = df["lat"].astype(float)
            df["lon"] = df["lon"].astype(float)
            return df

        df_plz = load_plz_data()

        if not user_input.strip():
            return

        headers = {"User-Agent": "kalkulations-app/1.0"}
        try:
            response = requests.get(
                "https://photon.komoot.io/api/",
                params={"q": user_input, "limit": 1, "lang": "de"},
                headers=headers,
                timeout=10
            )
            data = response.json()
            lon_c, lat_c = data["features"][0]["geometry"]["coordinates"]
        except Exception:
            st.error("🌍 Geocoding fehlgeschlagen.")
            return

        radien_input = st.text_input("📏 Radien eingeben (km, Komma getrennt)", value="5,10")

        radien = [float(r.strip()) for r in radien_input.split(",") if r.strip()]

        folium.Marker([lat_c, lon_c], tooltip=user_input, icon=folium.Icon(color="red")).add_to(m)

        all_coords = [[lat_c, lon_c]]

        for i, r in enumerate(radien):
            folium.Circle(
                [lat_c, lon_c],
                radius=r * 1000,
                color=colors[i % len(colors)],
                fill=True,
                fill_opacity=0.2,
                tooltip=f"{r} km"
            ).add_to(m)

            all_coords.append([lat_c + r / 110.574, lon_c + r / 110.574])
            all_coords.append([lat_c - r / 110.574, lon_c - r / 110.574])

        m.fit_bounds(all_coords)
        st_folium(m, width=700, height=500)

        def haversine(lat1, lon1, lat2, lon2):
            R = 6371
            phi1, phi2 = math.radians(lat1), math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlambda = math.radians(lon2 - lon1)
            a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
            return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        df_plz["distance_km"] = df_plz.apply(
            lambda r: haversine(lat_c, lon_c, r["lat"], r["lon"]),
            axis=1
        )

        df_result = df_plz[df_plz["distance_km"] <= max(radien)].sort_values("distance_km")

        st.subheader("📋 PLZ im Radius")
        st.dataframe(df_result[["plz", "lat", "lon", "distance_km"]], use_container_width=True)

# =====================================================
# 🚧 Pipeline
# =====================================================
def show_pipeline():
    st.header(" Pipeline")
    st.info("Only available for MIDS/ wrong Permission.")

# =====================================================
# 🏪 Restaurants
# =====================================================
def show_restaurants():
    st.header(" Restaurants")
    st.info("Only available for MIDS/ wrong Permission.")
# =====================================================
# ⚡ Seite auswählen
# =====================================================
if page == "Platform":
    show_platform()
elif page == "Cardpayment":
    show_cardpayment()
elif page == "Contractnumbers":
    show_contractnumbers()
elif page == "Pricing":
    show_pricing()
elif page == "Radien":
    show_radien()
elif page == "Pipeline":
    show_pipeline()
elif page == "Restaurants":
    show_restaurants() 
