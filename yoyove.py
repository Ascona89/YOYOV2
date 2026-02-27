import streamlit as st
from utils.db import supabase
import pandas as pd

# ------------------------------
# Login & Rollen
# ------------------------------
st.title("YOYO Cloud App")

role = st.radio("Login als:", ["User", "Silent", "Admin"])

# ------------------------------
# Länder-Auswahl
# ------------------------------
countries = [
    "Deutschland", "Österreich", "Schweiz", "Belgien", "Luxemburg",
    "Niederlande", "England", "Irland", "Schottland",
    "Finnland", "Schweden", "Dänemark", "Norwegen",
    "Polen", "Tschechien"
]

# Admin kann Länder ausblenden
if role == "Admin":
    hidden_countries = st.multiselect("Länder ausblenden (für schrittweisen Launch):", countries)
else:
    hidden_countries = []

# User wählt nur sichtbare Länder
available_countries = [c for c in countries if c not in hidden_countries]
selected_country = st.selectbox("Aktives Land auswählen:", available_countries)

st.write(f"Angemeldet als **{role}** in **{selected_country}**")

# ------------------------------
# Beispiel: Daten aus Supabase laden
# ------------------------------
if st.button("Daten laden"):
    response = supabase.table("kalkulationen").select("*").eq("land", selected_country).execute()
    if response.data:
        df = pd.DataFrame(response.data)
        st.dataframe(df)
    else:
        st.info("Keine Daten gefunden")
