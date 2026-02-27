from utils.db import supabase

try:
    response = supabase.table("kalkulationen").select("*").limit(1).execute()
    print("Erfolgreich verbunden:", response.data)
except Exception as e:
    print("Fehler beim Laden der Daten:", e)
