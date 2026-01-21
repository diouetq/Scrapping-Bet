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
DATA_FILE = BASE_DIR.parent / "data.json"  # GitHub Actions va le mettre ici

# Sports par défaut par bookmaker
SPORTS_SPORTAZA  = ["1359","923","924","1380","1405","1406","904","1411","1412","672", "893"]
SPORTS_BETIFY    = ["17","22","43","44","45","46","48"]
SPORTS_GREENLUCK = ["14","15","16","17","27","28","31","32"]

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
    """Envoie un message sur Telegram"""
    if not TOKEN or not CHAT_ID:
        print("⚠️ TELEGRAM_TOKEN ou CHAT_ID non défini !")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except Exception as e:
        print(f"⚠️ Erreur Telegram : {e}")

def safe_scrape(scrape_func, sports):
    """Appel sécurisé d’un scraper, retourne toujours un DataFrame"""
    try:
        df = scrape_func(sports)
        if df is None or df.empty:
            return pd.DataFrame(columns=["Bookmaker","Competition","Extraction","Cutoff","Evenement","Competiteur","Cote"])
        return df
    except Exception as e:
        print(f"⚠️ Erreur lors du scrape {scrape_func.__name__} : {e}")
        return pd.DataFrame(columns=["Bookmaker","Competition","Extraction","Cutoff","Evenement","Competiteur","Cote"])

# --- MAIN --- #
def main():
    old_data = load_data()
    old_comp = old_data.get("competitions", [])

    # 1️⃣ Scraper tous les bookmakers
    df_sportaza  = safe_scrape(scrape_sportaza,  SPORTS_SPORTAZA)
    df_betify    = safe_scrape(scrape_betify,    SPORTS_BETIFY)
    df_greenluck = safe_scrape(scrape_greenluck, SPORTS_GREENLUCK)

    # 2️⃣ Fusionner tous les résultats
    df_all = pd.concat([df_sportaza, df_betify, df_greenluck], ignore_index=True)

    # 3️⃣ Créer liste de "Bookmaker | Competition" sans set, pour garder toutes les combinaisons
    current_comp = [f"{row['Bookmaker']} | {row['Competition']}" for _, row in df_all.iterrows()]
    current_comp = list(dict.fromkeys(current_comp))  # supprime uniquement les doublons exacts dans le même bookmaker
    # 4️⃣ Identifier les nouvelles compétitions
    new_comp = [c for c in current_comp if c not in old_comp]

    # 5️⃣ Envoyer les alertes
    if new_comp:
        for comp in new_comp:
            bookmaker, competition = comp.split(" | ", 1)
            df_comp = df_all[(df_all["Bookmaker"] == bookmaker) & (df_all["Competition"] == competition)]

            cutoff_list = df_comp["Cutoff"].dropna().unique()
            cutoff_str = cutoff_list[0].strftime("%Y-%m-%d %H:%M") if len(cutoff_list) > 0 else "N/A"
            nb_cotes = len(df_comp)

            msg = (
                f"⚡ Nouvelle compétition détectée !\n"
                f"🎰 Bookmaker : {bookmaker}\n"
                f"🏆 Compétition : {competition}\n"
                f"⏰ Cutoff : {cutoff_str}\n"
                f"📊 Nombre de cotes : {nb_cotes}"
            )
            send_telegram_message(msg)
    else:
        # Envoi pour test si aucune nouvelle compétition
        send_telegram_message("ℹ️ Test : aucune nouvelle compétition détectée pour le moment.")

    # 6️⃣ Sauvegarder les compétitions actuelles dans data.json
    save_data({"competitions": current_comp})
    print(f"{len(new_comp)} nouvelles compétitions détectées.")

if __name__ == "__main__":
    main()
