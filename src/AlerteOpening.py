# -*- coding: utf-8 -*-
import os
import json
from pathlib import Path
import pandas as pd
from Scrap_Sportaza import scrape_sportaza
from Scrap_Betify import scrape_betify
from Scrap_Greenluck import scrape_greenluck
import requests

# --- CONFIGURATION --- #
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR.parent / "data.json"

# Sports par défaut par bookmaker
SPORTS_SPORTAZA = ["1359","923","924","1380","1405","1406","904","1411","1412","672", "893"]
SPORTS_BETIFY   = ["43","44","46"]
SPORTS_GREENLUCK= ["16","27","28"]

# --- HELPERS --- #
def load_data():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"competitions": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def send_telegram_message(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# --- MAIN --- #
def main():
    old_data = load_data()
    old_comp = old_data.get("competitions", [])

    # 1️⃣ Scraper tous les bookmakers
    df_sportaza = scrape_sportaza(SPORTS_SPORTAZA)
    df_betify   = scrape_betify(SPORTS_BETIFY)
    df_greenluck= scrape_greenluck(SPORTS_GREENLUCK)

    # 2️⃣ Fusionner tous les résultats
    df_all = pd.concat([df_sportaza, df_betify, df_greenluck], ignore_index=True)

    # Liste des compétitions actuelles
    current_comp = df_all["Competition"].dropna().unique().tolist()

    # 3️⃣ Identifier les nouvelles compétitions
    new_comp = [c for c in current_comp if c not in old_comp]

    # 4️⃣ Envoyer les alertes
    if new_comp:
        for comp in new_comp:
            # Filtrer toutes les lignes pour cette compétition
            df_comp = df_all[df_all["Competition"] == comp]

            # Regrouper par bookmaker
            for bookmaker in df_comp["Bookmaker"].unique():
                df_book = df_comp[df_comp["Bookmaker"] == bookmaker]

                cutoff_list = df_book["Cutoff"].dropna().unique()
                cutoff_str = cutoff_list[0].strftime("%Y-%m-%d %H:%M") if len(cutoff_list) > 0 else "N/A"
                nb_cotes = len(df_book)

                msg = (
                    f"⚡ Nouvelle compétition détectée !\n"
                    f"🎰 Bookmaker : {bookmaker}\n"
                    f"🏆 Compétition : {comp}\n"
                    f"⏰ Cutoff : {cutoff_str}\n"
                    f"📊 Nombre de cotes : {nb_cotes}"
                )
                send_telegram_message(msg)
    else:
        send_telegram_message("ℹ️ Test : aucune nouvelle compétition détectée pour le moment.")

    # 5️⃣ Sauvegarder les compétitions actuelles
    save_data({"competitions": current_comp})
    print(f"{len(new_comp)} nouvelles compétitions détectées.")

if __name__ == "__main__":
    main()
