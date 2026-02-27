# yoyove.py
import streamlit as st
from utils.db import supabase

st.title("YOYO Kalkulationen")

# Länder auswählen
countries = ["DE","AT","CH","BE","LU","NL","GB","IE","SC","FI","SE","DK","NO","PL","CZ"]
selected_country = st.selectbox("Land auswählen", countries)

# Daten abfragen
try:
    response = supabase.table("kalkulationen").select("*").eq("country_code", selected_country).execute()
    data = response.data

    if data:
        st.write(data)
    else:
        st.warning("Keine Daten für dieses Land gefunden.")
except Exception as e:
    st.error(f"Fehler beim Laden der Daten: {e}")
