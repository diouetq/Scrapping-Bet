# -*- coding: utf-8 -*
import os
import json
from pathlib import Path
import pandas as pd
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
SPORTS_SPORTAZA  = ["1359","1393", "904", "923", "924", "1405", "1406", "1415","2245", "1356", "1659", "893","2239"]
SPORTS_BETIFY    = ["17","22","43","44","45","46","48"]
SPORTS_GREENLUCK = ["14","15","16","17","27","28","31","32"]
SPORTS_PINNACLE= ["42"]

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
        response = requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=30)        
        print(f"✅ Message Telegram envoyé : {response.status_code}")
    except Exception as e:
        print(f"⚠️ Erreur Telegram : {e}")


def safe_scrape(scrape_func, sports, use_tor=False):
    try:
        # On vérifie si la fonction (ex: scrape_sportaza) possède 'use_tor' dans ses arguments
        signature = inspect.signature(scrape_func)
        
        if 'use_tor' in signature.parameters:
            # Si elle accepte use_tor, on lui envoie
            df = scrape_func(Id_sport=sports, use_tor=use_tor)
        else:
            # Sinon, on l'appelle normalement (pour Sportaza et Greenluck)
            print(f"ℹ️ {scrape_func.__name__} ne supporte pas encore Tor, appel direct.")
            df = scrape_func(Id_sport=sports)

        # --- Le reste de ton code reste identique ---
        if df is None or not isinstance(df, pd.DataFrame):
            print(f"⚠️ {scrape_func.__name__} a renvoyé None ou pas un DataFrame")
            return pd.DataFrame(columns=["Bookmaker","Competition","Extraction","Cutoff","Evenement","Competiteur","Cote"])
        
        if df.empty:
            print(f"ℹ️ {scrape_func.__name__} n'a trouvé aucune donnée")
            return pd.DataFrame(columns=["Bookmaker","Competition","Extraction","Cutoff","Evenement","Competiteur","Cote"])        
        
        # ✅ IMPORTANT : Ne garde PAS uniquement required_cols ici 
        # car on a besoin de "Evenement" et "Cote" pour le calcul du TRJ plus tard !
        cols_to_keep = ["Bookmaker", "Competition", "Extraction", "Cutoff", "Evenement", "Competiteur", "Cote"]
        
        # On vérifie lesquelles sont présentes
        available_cols = [c for c in cols_to_keep if c in df.columns]
        
        print(f"✅ {scrape_func.__name__} : {len(df)} lignes trouvées")
        return df[available_cols]

    except Exception as e:
        print(f"⚠️ Erreur lors du scrape {scrape_func.__name__} : {e}")
        return pd.DataFrame(columns=["Bookmaker","Competition","Extraction","Cutoff","Evenement","Competiteur","Cote"])
    
    
# --- MAIN --- #
def main():
    print("🚀 Début du script d'alerte...")
    
    # 1️⃣ Charger les anciennes compétitions
    old_data = load_data()
    old_comp = set(old_data.get("competitions", []))  # ✅ Utiliser un SET pour comparaison rapide
    print(f"📂 Anciennes compétitions ({len(old_comp)}) : {old_comp}")

    # 2️⃣ Scraper tous les bookmakers en mode sécurisé
    print("🔍 Scraping en cours...")
    df_betify    = safe_scrape(scrape_betify,    SPORTS_BETIFY, use_tor=True)
    df_sportaza  = safe_scrape(scrape_sportaza,  SPORTS_SPORTAZA)
    df_greenluck = safe_scrape(scrape_greenluck, SPORTS_GREENLUCK)
    df_pinnacle = safe_scrape(scrape_pinnacle, SPORTS_PINNACLE, use_tor=True)

    # 3️⃣ Fusionner tous les résultats
    df_all = pd.concat([df_sportaza, df_betify, df_greenluck, df_pinnacle], ignore_index=True)
    print(f"📊 Total de lignes scrapées : {len(df_all)}")

    # 4️⃣ ✅ CORRECTION : Créer un SET unique de "Bookmaker | Competition"
    if df_all.empty:
        current_comp = set()
    else:
        current_comp = set(
            f"{row['Bookmaker']} | {row['Competition']}" 
            for _, row in df_all.iterrows()
        )
    
    print(f"🎯 Compétitions actuelles ({len(current_comp)}) : {current_comp}")

    # 5️⃣ Identifier les **nouvelles combinaisons** depuis le dernier run
    new_comp = current_comp - old_comp  # ✅ Différence entre sets
    print(f"🆕 Nouvelles compétitions ({len(new_comp)}) : {new_comp}")

# 6️⃣ Envoyer les alertes pour chaque nouvelle combinaison
    if new_comp:
        for comp_key in new_comp:
            try:
                bookmaker, competition = comp_key.split(" | ", 1)
                
                # On filtre toutes les lignes de cette compétition précise
                df_comp = df_all[(df_all["Bookmaker"] == bookmaker) & (df_all["Competition"] == competition)]
                
                # --- CALCULS STATISTIQUES ---
                # 1. Nombre de cotes (nombre total de lignes pour cette comp)
                nb_cotes = len(df_comp)
                
                # 2. Calcul du TRJ moyen
                # On regroupe par événement (match) pour calculer le TRJ de chaque match
                # On part du principe qu'il y a 2 compétiteurs par événement
                trj_list = []
                for event, group in df_comp.groupby("Evenement"):
                    if len(group) == 2:
                        cotes = group["Cote"].values
                        trj = (1 / ((1/cotes[0]) + (1/cotes[1]))) * 100
                        trj_list.append(trj)
                
                avg_trj = sum(trj_list) / len(trj_list) if trj_list else 0
                # ----------------------------

                # Récupération de la date de cutoff
                cutoff_list = df_comp["Cutoff"].dropna().unique()
                cutoff_str = pd.to_datetime(cutoff_list[0]).strftime("%d/%m %H:%M") if len(cutoff_list) > 0 else "N/A"

                msg = (
                    f"⚡ Nouvelle compétition H2H détectée !\n"
                    f"🎰 Bookmaker : {bookmaker}\n"
                    f"🏆 Compétition : {competition}\n"
                    f"⏰ Cutoff : {cutoff_str}\n"
                    f"📊 Nombre de cotes : {nb_cotes}\n"
                    f"💰 TRJ Moyen : {avg_trj:.2f}%\n"
 
                )
                
                print(f"📤 Envoi d'alerte : {comp_key} ({nb_cotes} cotes, {avg_trj:.2f}% TRJ)")
                send_telegram_message(msg)
                
            except Exception as e:
                print(f"⚠️ Erreur lors du calcul des stats pour {comp_key} : {e}")
        
        print(f"✅ {len(new_comp)} nouvelle(s) compétition(s) détectée(s) et alertée(s).")
    else:
        print("ℹ️ Aucune nouvelle compétition détectée.")
        # ❌ Ne pas envoyer de message "test" à chaque fois
        # send_telegram_message("ℹ️ Test : aucune nouvelle compétition détectée pour le moment.")

    # 7️⃣ Sauvegarder **toutes les combinaisons actuelles** dans data.json
    save_data({"competitions": sorted(list(current_comp))})  # ✅ Trier pour plus de clarté
    print(f"💾 Sauvegarde de {len(current_comp)} compétitions dans data.json")
    print("✅ Script terminé.")

if __name__ == "__main__":
    main()