import streamlit as st
from utils.db import supabase

# -----------------------------
# Einfaches Passwort
# -----------------------------
APP_PASSWORD = "passwort"  # hier dein Passwort eintragen

# -----------------------------
# Länder
# -----------------------------
COUNTRIES = [
    "Deutschland", "Österreich", "Schweiz", "Belgien", "Luxemburg", "Niederlande",
    "England", "Irland", "Schottland", "Finnland", "Schweden", "Dänemark",
    "Norwegen", "Polen", "Tschechien"
]

# -----------------------------
# Main App
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("YOYO App Login")
    password = st.text_input("Passwort", type="password")
    if st.button("Login"):
        if password == APP_PASSWORD:
            st.session_state.logged_in = True
        else:
            st.error("Falsches Passwort!")
else:
    st.header("Länderauswahl")
    selected_country = st.selectbox("Wähle dein Land:", COUNTRIES)
    
    if st.button("Daten laden"):
        try:
            response = supabase.table("kalkulationen").select("*") \
                .eq("country_code", selected_country).execute()
            data = response.data
            st.write("Daten für", selected_country)
            st.json(data)
        except Exception as e:
            st.error(f"Fehler beim Laden der Daten: {e}")
