# -*- coding: utf-8 -*-
import os
import json
from pathlib import Path
from Scrap_Sportaza import scrape_sportaza
import requests

# --- CONFIGURATION --- #
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR.parent / "data.json"
DEFAULT_SPORTS = ["1359","923","924","1380","1405","1406","904","1411","1412","672", "893"]

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
    df = scrape_sportaza(DEFAULT_SPORTS)
    current_comp = df["Competition"].dropna().unique().tolist()

    new_comp = [c for c in current_comp if c not in old_comp]

    if new_comp:
        for c in new_comp:
            send_telegram_message(f"⚡ Nouvelle compétition détectée !\n🏆 {c}")
    else:
        send_telegram_message("ℹ️ Test : aucune nouvelle compétition détectée pour le moment.")

    save_data({"competitions": current_comp})
    print(f"{len(new_comp)} nouvelles compétitions détectées.")

if __name__ == "__main__":
    main()
