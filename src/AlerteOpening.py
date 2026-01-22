# -*- coding: utf-8 -*-
import os
import json
from pathlib import Path
import pandas as pd
import requests

# Import des scrapers
from Scrap_Sportaza import scrape_sportaza
from Scrap_Betify import scrape_betify
from Scrap_Greenluck import scrape_greenluck

# --- CONFIGURATION --- #
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR.parent / "data.json"

# Proxy local GitHub Actions
PROXY_HOST = os.environ.get("PROXY_HOST", "127.0.0.1")
PROXY_PORT = os.environ.get("PROXY_PORT", "8888")
PROXIES = {
    "http": f"http://{PROXY_HOST}:{PROXY_PORT}",
    "https": f"http://{PROXY_HOST}:{PROXY_PORT}"
}

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
        response = requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, proxies=PROXIES)
        print(f"✅ Message Telegram envoyé : {response.status_code}")
    except Exception as e:
        print(f"⚠️ Erreur Telegram : {e}")

def safe_scrape(scrape_func, sports):
    """Scrape en mode sécurisé avec proxy et fallback sur DataFrame vide"""
    try:
        df = scrape_func(Id_sport=sports, proxies=PROXIES)
        if df is None or df.empty:
            return pd.DataFrame(columns=["Bookmaker","Competition","Extraction","Cutoff","Evenement","Competiteur","Cote"])
        return df
    except Exception as e:
        print(f"⚠️ Erreur lors du scrape {scrape_func.__name__} : {e}")
        return pd.DataFrame(columns=["Bookmaker","Competition","Extraction","Cutoff","Evenement","Competiteur","Cote"])

# --- MAIN --- #
def main():
    print("🚀 Début du script d'alerte...")

    # 1️⃣ Charger les anciennes compétitions
    old_data = load_data()
    old_comp = set(old_data.get("competitions", []))
    print(f"📂 Anciennes compétitions ({len(old_comp)}) : {old_comp}")

    # 2️⃣ Scraper tous les bookmakers
    print("🔍 Scraping en cours...")
    df_betify    = safe_scrape(scrape_betify,    SPORTS_BETIFY)
    df_sportaza  = safe_scrape(scrape_sportaza,  SPORTS_SPORTAZA)
    df_greenluck = safe_scrape(scrape_greenluck, SPORTS_GREENLUCK)

    # 3️⃣ Fusionner tous les résultats
    df_all = pd.concat([df_sportaza, df_betify, df_greenluck], ignore_index=True)
    print(f"📊 Total de lignes scrapées : {len(df_all)}")

    # 4️⃣ Créer un SET unique de "Bookmaker | Competition"
    if df_all.empty:
        current_comp = set()
    else:
        current_comp = set(
            f"{row['Bookmaker']} | {row['Competition']}"
            for _, row in df_all.iterrows()
        )
    print(f"🎯 Compétitions actuelles ({len(current_comp)}) : {current_comp}")

    # 5️⃣ Identifier les nouvelles compétitions
    new_comp = current_comp - old_comp
    print(f"🆕 Nouvelles compétitions ({len(new_comp)}) : {new_comp}")

    # 6️⃣ Envoyer les alertes pour chaque nouvelle compétition
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
        print(f"📤 Envoi d'alerte : {comp}")
        send_telegram_message(msg)

    if new_comp:
        print(f"✅ {len(new_comp)} nouvelle(s) compétition(s) détectée(s) et alertée(s).")
    else:
        print("ℹ️ Aucune nouvelle compétition détectée.")

    # 7️⃣ Sauvegarder toutes les compétitions actuelles
    save_data({"competitions": sorted(list(current_comp))})
    print(f"💾 Sauvegarde de {len(current_comp)} compétitions dans data.json")
    print("✅ Script terminé.")

if __name__ == "__main__":
    main()
