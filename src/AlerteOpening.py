# -*- coding: utf-8 -*-
import os
import json
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
from Scrap_Sportaza import scrape_sportaza
from Scrap_Betify import scrape_betify
from Scrap_Greenluck import scrape_greenluck
from Scrap_Pinnacle import scrape_pinnacle
import requests
import inspect


# --- CONFIGURATION --- #
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR.parent / "data.json"

# Sports par défaut par bookmaker
SPORTS_SPORTAZA  = ["1596","1359","1373","1393","1387", "904", "923", "924", "1405", "1406", "1415","2245", "1356", "1659", "893","2239"]
SPORTS_BETIFY    = ["17","43","44","45","46","48"]
SPORTS_GREENLUCK = ["14","15","16","17","27","28","31"]
SPORTS_PINNACLE  = ["40","41", "42","43","44", "45"] 

# 🗑️ DURÉE DE RÉTENTION : Compétitions plus vieilles que X jours seront supprimées
RETENTION_DAYS = 7  # Garde 7 jours d'historique

# --- HELPERS --- #
def load_data():
    """Charge le fichier JSON avec gestion des timestamps"""
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Rétrocompatibilité : si ancien format (liste simple), on le convertit
            if isinstance(data.get("competitions"), list) and data["competitions"]:
                if isinstance(data["competitions"][0], str):
                    # Ancien format : ["Bookmaker | Competition", ...]
                    # On le convertit avec timestamp actuel
                    now = datetime.now().isoformat()
                    data["competitions"] = {
                        comp: now for comp in data["competitions"]
                    }
            return data
    return {"competitions": {}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def clean_old_competitions(competitions_dict, retention_days):
    """Supprime les compétitions plus anciennes que retention_days"""
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    cleaned = {
        comp: timestamp 
        for comp, timestamp in competitions_dict.items()
        if datetime.fromisoformat(timestamp) > cutoff_date
    }
    removed_count = len(competitions_dict) - len(cleaned)
    if removed_count > 0:
        print(f"🗑️ Nettoyage : {removed_count} compétition(s) de plus de {retention_days} jours supprimée(s)")
    return cleaned

def send_telegram_message(msg):
    """Envoie un message sur Telegram"""
    if not TOKEN or not CHAT_ID:
        print("⚠️ TELEGRAM_TOKEN ou CHAT_ID non défini !")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        response = requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=30)        
        print(f"✅ Message Telegram envoyé : {response.status_code}")
    except Exception as e:
        print(f"⚠️ Erreur Telegram : {e}")


def safe_scrape(scrape_func, sports, use_tor=False):
    try:
        signature = inspect.signature(scrape_func)
        
        if 'use_tor' in signature.parameters:
            df = scrape_func(Id_sport=sports, use_tor=use_tor)
        else:
            print(f"ℹ️ {scrape_func.__name__} ne supporte pas encore Tor, appel direct.")
            df = scrape_func(Id_sport=sports)

        required_cols = ["Bookmaker", "Competition", "Extraction", "Cutoff", "Evenement", "Competiteur", "Cote"]

        if df is None or not isinstance(df, pd.DataFrame):
            print(f"⚠️ {scrape_func.__name__} a renvoyé None ou pas un DataFrame")
            return pd.DataFrame(columns=required_cols)
        
        if df.empty:
            print(f"ℹ️ {scrape_func.__name__} n'a trouvé aucune donnée")
            return pd.DataFrame(columns=required_cols)

        for col in required_cols:
            if col not in df.columns:
                df[col] = None
        
        print(f"✅ {scrape_func.__name__} : {len(df)} lignes trouvées")
        return df[required_cols]

    except Exception as e:
        print(f"⚠️ Erreur lors du scrape {scrape_func.__name__} : {e}")
        return pd.DataFrame(columns=["Bookmaker", "Competition", "Extraction", "Cutoff", "Evenement", "Competiteur", "Cote"])
    
    
    
# --- MAIN --- #
def main():
    print("🚀 Début du script d'alerte...")
    
    # 1️⃣ Charger et nettoyer l'historique
    old_data = load_data()
    old_comp_dict = old_data.get("competitions", {})
    
    # Nettoyage des anciennes compétitions
    old_comp_dict = clean_old_competitions(old_comp_dict, RETENTION_DAYS)
    
    old_comp = set(old_comp_dict.keys())
    print(f"📂 Compétitions en base ({len(old_comp)})")

    # 2️⃣ Scraper tous les bookmakers
    print("🔍 Scraping en cours...")
    df_betify    = safe_scrape(scrape_betify,    SPORTS_BETIFY, use_tor=True)
    df_sportaza  = safe_scrape(scrape_sportaza,  SPORTS_SPORTAZA)
    df_greenluck = safe_scrape(scrape_greenluck, SPORTS_GREENLUCK)
    df_pinnacle  = safe_scrape(scrape_pinnacle,  SPORTS_PINNACLE, use_tor=False)

    # 3️⃣ Fusionner tous les résultats
    df_all = pd.concat([df_sportaza, df_betify, df_greenluck, df_pinnacle], ignore_index=True)
    print(f"📊 Total de lignes scrapées : {len(df_all)}")

    # 4️⃣ Créer un SET unique de "Bookmaker | Competition"
    if df_all.empty:
        current_comp = set()
    else:
        current_comp = set(
            f"{row['Bookmaker']} | {row['Competition']}" 
            for _, row in df_all.iterrows()
        )
    
    print(f"🎯 Compétitions actuelles ({len(current_comp)})")

    # 5️⃣ Identifier les nouvelles compétitions
    new_comp = current_comp - old_comp
    print(f"🆕 Nouvelles compétitions ({len(new_comp)}) : {new_comp}")

    # 6️⃣ Envoyer les alertes
    if new_comp:
        for comp_key in new_comp:
            try:
                bookmaker, competition = comp_key.split(" | ", 1)
                df_comp = df_all[(df_all["Bookmaker"] == bookmaker) & (df_all["Competition"] == competition)].copy()
                
                # Calculs statistiques
                nb_cotes = len(df_comp)
                trj_list = []
                df_comp["Cote"] = pd.to_numeric(df_comp["Cote"], errors='coerce')
                
                for event, group in df_comp.groupby("Evenement"):
                    if len(group) == 2:
                        cotes = group["Cote"].values
                        if not pd.isna(cotes).any() and all(c >= 1.0 for c in cotes):
                            trj = (1 / ((1/cotes[0]) + (1/cotes[1]))) * 100
                            trj_list.append(trj)
                
                avg_trj_display = f"{sum(trj_list) / len(trj_list):.2f}%" if trj_list else "Non disponible"
                
                # Cutoff
                cutoff_list = df_comp["Cutoff"].dropna().unique()
                cutoff_str = "N/A"
                if len(cutoff_list) > 0 and cutoff_list[0] is not None:
                    try:
                        cutoff_str = pd.to_datetime(cutoff_list[0]).strftime("%d/%m %H:%M")
                    except:
                        cutoff_str = str(cutoff_list[0])

                # Message Telegram
                msg = (
                    f"⚡ Nouvelle compétition H2H détectée !\n"
                    f"🎰 Bookmaker : {bookmaker}\n"
                    f"🏆 Compétition : {competition}\n"
                    f"⏰ Cutoff : {cutoff_str}\n"
                    f"📊 Nombre de cotes : {nb_cotes}\n"
                    f"💰 TRJ Moyen : {avg_trj_display}\n"
                )
                
                print(f"📤 Envoi d'alerte : {comp_key} ({nb_cotes} cotes, {avg_trj_display})")
                send_telegram_message(msg)
                
            except Exception as e:
                print(f"⚠️ Erreur lors du calcul des stats pour {comp_key} : {e}")
        
        print(f"✅ {len(new_comp)} nouvelle(s) compétition(s) détectée(s) et alertée(s).")
    else:
        print("ℹ️ Aucune nouvelle compétition détectée.")

    # 7️⃣ Mise à jour du dictionnaire avec timestamps
    now = datetime.now().isoformat()
    for comp in new_comp:
        old_comp_dict[comp] = now
    
    save_data({"competitions": old_comp_dict})
    print(f"💾 Sauvegarde de {len(old_comp_dict)} compétitions dans data.json")
    print("✅ Script terminé.")

if __name__ == "__main__":
    main()