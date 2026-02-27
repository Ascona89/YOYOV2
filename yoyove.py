import streamlit as st
from utils.db import supabase

# -----------------------------
# Benutzer & Rollen (Beispiel)
# -----------------------------
USERS = {
    "user1": {"password": "pass1", "role": "USER"},
    "silent1": {"password": "pass2", "role": "SILENT"},
    "admin1": {"password": "pass3", "role": "ADMIN"}
}

# -----------------------------
# Login-Funktion
# -----------------------------
def login():
    st.title("YOYO App Login")
    username = st.text_input("Benutzername")
    password = st.text_input("Passwort", type="password")
    if st.button("Login"):
        user = USERS.get(username)
        if user and user["password"] == password:
            st.session_state.logged_in = True
            st.session_state.user_role = user["role"]
            st.session_state.username = username
        else:
            st.error("Ungültiger Benutzername oder Passwort")

# -----------------------------
# Länder-Auswahl nach Login
# -----------------------------
def select_country():
    st.header(f"Willkommen {st.session_state.username} ({st.session_state.user_role})")
    countries = [
        "Deutschland", "Österreich", "Schweiz", "Belgien", "Luxemburg", "Niederlande",
        "England", "Irland", "Schottland", "Finnland", "Schweden", "Dänemark",
        "Norwegen", "Polen", "Tschechien"
    ]
    selected_country = st.selectbox("Wähle dein Land:", countries)
    
    if st.button("Daten laden"):
        try:
            response = supabase.table("kalkulationen").select("*") \
                .eq("country_code", selected_country).execute()
            data = response.data
            st.write("Daten für", selected_country)
            st.json(data)
        except Exception as e:
            st.error(f"Fehler beim Laden der Daten: {e}")

# -----------------------------
# Main App
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login()
else:
    select_country()
