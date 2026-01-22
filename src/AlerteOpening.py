# -*- coding: utf-8 -*-
import os
import json
from pathlib import Path
import pandas as pd
import requests

# --- Scrapers ---
from Scrap_Sportaza import scrape_sportaza
from Scrap_Betify import scrape_betify
from Scrap_Greenluck import scrape_greenluck

# --- CONFIGURATION ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR.parent / "data.json"

# --- CONFIGURATION PROXY (Simple & Direct) ---
# On utilise l'IP que tu as fournie : 212.114.194.76
# Si le port est 80, on utilise http://IP:80
PROXY_URL = "http://212.114.194.76:80" 

PROXIES_BETIFY = {
    "http": PROXY_URL,
    "https": PROXY_URL
}

# Sports par défaut
SPORTS_SPORTAZA  = ["1359","923","924","1380","1405","1406","904","1411","1412","672","893"]
SPORTS_BETIFY    = ["17","22","43","44","45","46","48"]
SPORTS_GREENLUCK = ["14","15","16","17","27","28","31","32"]

# --- HELPERS ---
def load_data():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"competitions": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def send_telegram_message(msg):
    if not TOKEN or not CHAT_ID:
        print("⚠️ TELEGRAM_TOKEN ou CHAT_ID non défini !")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        response = requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
        print(f"✅ Message Telegram envoyé")
    except Exception as e:
        print(f"⚠️ Erreur Telegram : {e}")

def safe_scrape(scrape_func, sports, use_proxy=False):
    """Scrape en mode sécurisé, proxy uniquement pour Betify"""
    try:
        if scrape_func.__name__ == "scrape_betify" and use_proxy:
            print(f"🌐 Scraping {scrape_func.__name__} via PROXY ({PROXY_URL})...")
            # On passe les proxies direct sans SOCKS5 complexe
            df = scrape_func(Id_sport=sports, proxies=PROXIES_BETIFY)
        else:
            print(f"🚀 Scraping {scrape_func.__name__} en DIRECT (IP GitHub)...")
            df = scrape_func(Id_sport=sports)
            
        if df is None or df.empty:
            return pd.DataFrame(columns=["Bookmaker","Competition","Extraction","Cutoff","Evenement","Competiteur","Cote"])
        return df
    except Exception as e:
        print(f"⚠️ Erreur lors du scrape {scrape_func.__name__} : {e}")
        return pd.DataFrame(columns=["Bookmaker","Competition","Extraction","Cutoff","Evenement","Competiteur","Cote"])

# --- MAIN ---
def main():
    print("🚀 Début du script d'alerte...")

    # 1️⃣ Anciennes compétitions
    old_data = load_data()
    old_comp = set(old_data.get("competitions", []))

    # 2️⃣ Scraping (Betify est le seul avec use_proxy=True)
    df_betify    = safe_scrape(scrape_betify,    SPORTS_BETIFY, use_proxy=True)
    df_sportaza  = safe_scrape(scrape_sportaza,  SPORTS_SPORTAZA)
    df_greenluck = safe_scrape(scrape_greenluck, SPORTS_GREENLUCK)

    # 3️⃣ Fusionner
    df_all = pd.concat([df_sportaza, df_betify, df_greenluck], ignore_index=True)
    print(f"📊 Total de lignes scrapées : {len(df_all)}")

    if df_all.empty:
        print("❌ Aucune donnée trouvée.")
        return

    # 4️⃣ SET unique Bookmaker | Competition
    current_comp = set(f"{row['Bookmaker']} | {row['Competition']}" for _, row in df_all.iterrows())
    new_comp = current_comp - old_comp

    # 5️⃣ Envoi alertes
    for comp in new_comp:
        bookmaker, competition = comp.split(" | ", 1)
        df_comp = df_all[(df_all["Bookmaker"] == bookmaker) & (df_all["Competition"] == competition)]
        
        # Extraction du cutoff propre
        try:
            cutoff_list = df_comp["Cutoff"].dropna().unique()
            cutoff_str = cutoff_list[0].strftime("%Y-%m-%d %H:%M") if len(cutoff_list) > 0 else "N/A"
        except:
            cutoff_str = "N/A"

        msg = (
            f"⚡ Nouvelle compétition !\n"
            f"🎰 Bookmaker : {bookmaker}\n"
            f"🏆 Compétition : {competition}\n"
            f"⏰ Cutoff : {cutoff_str}"
        )
        send_telegram_message(msg)

    # 6️⃣ Sauvegarder
    save_data({"competitions": sorted(list(current_comp))})
    print(f"💾 Sauvegarde terminée.")

if __name__ == "__main__":
    main()