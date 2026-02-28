def show_contractnumbers():
    st.header("📑 Contract Numbers")

    # ======================
    # Produkte
    # ======================
    df_sw = pd.DataFrame({
        "Produkt": ["Shop", "App", "POS", "Pay", "Connect", "TSE"],
        "List_OTF": [999, 49, 999, 49, 0, 0],
        "List_MRR": [119, 49, 89, 25, 13.72, 12],
        "Typ": ["Software"] * 6
    })

    df_hw = pd.DataFrame({
        "Produkt": ["Ordermanager", "POS inkl 1 Printer", "Cash Drawer", "Extra Printer", "Additional Display", "PAX"],
        "List_OTF": [299, 1699, 149, 199, 100, 299],
        "List_MRR": [0] * 6,
        "Typ": ["Hardware"] * 6
    })

    # ======================
    # Session State
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
        total_mrr = st.number_input("💶 Gesamt MRR (€)", min_value=0.0, step=50.0)
    with col2:
        total_otf = st.number_input("💶 Gesamt OTF (€)", min_value=0.0, step=100.0)

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
        ]
    )

    prozent_map = {
        "Keine": 0,
        "Gemischte Zahlung (25% + 12 Wochen) 10%": 0.10,
        "Online-Umsatz (100%) 10%": 0.10,
        "Monatliche Raten (12 Monate) 35%": 0.35,
        "Online-Umsatz (25% + 12 Wochen) 15%": 0.15
    }

    prozent = prozent_map[zahlung]
    otf_adjusted = total_otf * (1 - prozent)
    st.caption(f"Verwendete OTF für Kalkulation: **{round(otf_adjusted)} €**")

    # ======================
    # Mengen Software
    # ======================
    st.subheader("💻 Software")
    cols = st.columns(len(df_sw))
    for i, row in df_sw.iterrows():
        with cols[i]:
            st.session_state[f"qty_sw_{i}"] = st.number_input(
                row["Produkt"], min_value=0, step=1,
                value=st.session_state[f"qty_sw_{i}"]
            )

    # ======================
    # Mengen Hardware
    # ======================
    st.subheader("🖨️ Hardware")
    cols = st.columns(len(df_hw))
    for i, row in df_hw.iterrows():
        with cols[i]:
            st.session_state[f"qty_hw_{i}"] = st.number_input(
                row["Produkt"], min_value=0, step=1,
                value=st.session_state[f"qty_hw_{i}"]
            )

    df_sw["Menge"] = [st.session_state[f"qty_sw_{i}"] for i in range(len(df_sw))]
    df_hw["Menge"] = [st.session_state[f"qty_hw_{i}"] for i in range(len(df_hw))]

    # ======================
    # OTF Verteilung
    # ======================
    base = (
        (df_sw["Menge"] * df_sw["List_OTF"]).sum() +
        (df_hw["Menge"] * df_hw["List_OTF"]).sum()
    )

    factor = otf_adjusted / base if base > 0 else 0

    df_sw["OTF"] = (df_sw["Menge"] * df_sw["List_OTF"] * factor).round(0)
    df_hw["OTF"] = (df_hw["Menge"] * df_hw["List_OTF"] * factor).round(0)

    # ======================
    # 🔥 MRR Berechnung
    # ======================
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

    df_sw.loc[df_sw["Produkt"] == "Connect", "MRR_Monat"] = connect_total
    df_sw.loc[df_sw["Produkt"] == "Connect", "MRR_Woche"] = connect_qty * 3.43

    df_sw.loc[df_sw["Produkt"] == "TSE", "MRR_Monat"] = tse_total
    df_sw.loc[df_sw["Produkt"] == "TSE", "MRR_Woche"] = tse_qty * 3.00

    df_hw["MRR_Monat"] = 0.0
    df_hw["MRR_Woche"] = 0.0

    # =====================================================
    # 🧾 Ergebnisübersicht
    # =====================================================
    def get_row(df, produkt):
        row = df[df["Produkt"] == produkt]
        if not row.empty:
            return row.iloc[0]
        return None

    shop = get_row(df_sw, "Shop")
    app = get_row(df_sw, "App")
    pos = get_row(df_sw, "POS")
    pay = get_row(df_sw, "Pay")
    tse = get_row(df_sw, "TSE")

    order_manager = get_row(df_hw, "Ordermanager")
    pos_printer_bundle = get_row(df_hw, "POS inkl 1 Printer")
    cash_drawer = get_row(df_hw, "Cash Drawer")
    extra_printer = get_row(df_hw, "Extra Printer")
    display = get_row(df_hw, "Additional Display")
    pax = get_row(df_hw, "PAX")

    st.markdown("---")
    st.header("📊 Ergebnisübersicht")

    st.subheader("🛒 Preise Shop")
    st.write(f"Webshop WRR: {(shop['MRR_Woche'] if shop is not None else 0):.2f} €")
    st.write(f"Appshop WRR: {(app['MRR_Woche'] if app is not None else 0):.2f} €")
    st.write(f"Shop Anmeldegebühren: {((shop['OTF'] if shop is not None else 0) + (app['OTF'] if app is not None else 0)):.0f} €")

    st.subheader("🖥️ YOYO POS")
    st.write(f"YOYO POS Abonnementgebühr: {(pos['MRR_Woche'] if pos is not None else 0):.2f} €")
    st.write(f"YOYO POS Anmeldegebühr: {(pos['OTF'] if pos is not None else 0):.0f} €")
    st.write(f"TSE: {(tse['MRR_Woche'] if tse is not None else 0):.2f} €")

    st.subheader("💳 YOYOPAY")
    st.write(f"Tägliche Abonnement Festgebühr: {((pay['MRR_Woche']/7) if pay is not None else 0):.2f} €")
    st.write(f"Feste Anmeldegebühr: {(pay['OTF'] if pay is not None else 0):.0f} €")

    st.subheader("🖨️ Hardware Komponenten")

    def hw_display(row, label):
        if row is None or row["Menge"] == 0:
            return
        menge = int(row["Menge"])
        gesamt = int(row["OTF"])
        einzel = int(gesamt / menge) if menge > 0 else 0

        if menge == 1:
            st.write(f"{label}: {gesamt} €")
        else:
            st.write(f"{label}: {gesamt} € ({menge}x {einzel} €)")

    hw_display(pos_printer_bundle, "Sunmi D3 Pro")
    hw_display(display, "Kundendisplay")
    hw_display(cash_drawer, "Cash Drawer")
    hw_display(extra_printer, "POS Printer")
    hw_display(order_manager, "Ordermanager")
    hw_display(pax, "Kartenterminal")
