# -*- coding: utf-8 -*-
"""
Created on Sat Jan 30 2026
@author: dioue
"""
# pinnacle.py
import requests
import pandas as pd
from datetime import datetime
import pytz

def scrape_pinnacle(Id_sport=None) -> pd.DataFrame:
    """
    Scrape Pinnacle (moneyline markets) - Version simplifiée
    
    Id_sport : liste des IDs de sports que tu veux scraper, ex: ["10", "45"]
               Si None, utilise la liste par défaut.
    """
    paris_tz = pytz.timezone("Europe/Paris")
    rows = []
    
    # Valeur par défaut si rien n'est passé
    if Id_sport is None:
        Id_sport = ["10", "45", "40", "42"]  # Tennis, Cycling, Ski alpin, Ski jumping
    
    BASE_URL = "https://guest.api.arcadia.pinnacle.com/0.1"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/129.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.pinnacle.com",
        "Referer": "https://www.pinnacle.com/",
    }
    
    # Boucle sur chaque sport
    for sport_id in Id_sport:
        print(f"🔍 Scraping sport ID: {sport_id}")
        
        # Récupérer tous les matchups du sport (contient déjà les infos de base)
        url_matchups = f"{BASE_URL}/sports/{sport_id}/matchups?withSpecials=false&brandId=0"
        
        try:
            resp = requests.get(url_matchups, headers=HEADERS)
            resp.raise_for_status()
            matchups = resp.json()
            print(f"   ✅ {len(matchups)} matchups trouvés")
        except Exception as e:
            print(f"   ⚠️ Erreur sport {sport_id}: {e}")
            continue
        
        matchups_added = 0
        
        for m in matchups:
            participants = m.get("participants", [])
            
            # Ne garder que les face-à-face (2 participants)
            if len(participants) != 2:
                continue
            
            # Vérifier qu'il y a des periods avec moneyline
            periods = m.get("periods", [])
            if not periods or not periods[0].get("hasMoneyline"):
                continue
            
            period = periods[0]
            
            # Vérifier que le statut est "open"
            if period.get("status") != "open":
                continue
            
            # Récupérer cutoff
            cut_off_str = period.get("cutoffAt")
            cutoff = None
            if cut_off_str:
                dt_utc = datetime.fromisoformat(cut_off_str.replace("Z", "+00:00"))
                cutoff = dt_utc.astimezone(paris_tz)
            
            # Exclure si cutoff déjà passé
            if cutoff and cutoff < datetime.now(paris_tz):
                continue
            
            # Récupérer les infos
            league = m.get("league", {})
            league_name = league.get("name")
            
            participant_1 = participants[0].get("name")
            participant_2 = participants[1].get("name")
            event_name = f"{participant_1} vs {participant_2}"
            
            # ⚠️ LIMITATION : On ne peut pas récupérer les cotes exactes sans l'API markets
            # On crée quand même les lignes pour indiquer que le match existe
            # Tu devras peut-être utiliser un autre endpoint ou scraper le site web
            
            rows.append({
                "Bookmaker": "Pinnacle",
                "Competition": league_name,
                "Evenement": event_name,
                "Competiteur": participant_1,
                "Cote": None,  # ⚠️ Non disponible sans API markets
                "Cutoff": cutoff,
            })
            
            rows.append({
                "Bookmaker": "Pinnacle",
                "Competition": league_name,
                "Evenement": event_name,
                "Competiteur": participant_2,
                "Cote": None,  # ⚠️ Non disponible sans API markets
                "Cutoff": cutoff,
            })
            
            matchups_added += 1
        
        print(f"   ✅ {matchups_added} matchups ajoutés (cotes non disponibles)")
    
    # Créer le DataFrame
    df = pd.DataFrame(rows)
    df["Extraction"] = datetime.now(paris_tz)
    
    return df[
        [
            "Bookmaker",
            "Competition",
            "Extraction",
            "Cutoff",
            "Evenement",
            "Competiteur",
            "Cote"
        ]
    ]


df = scrape_pinnacle(["42"])