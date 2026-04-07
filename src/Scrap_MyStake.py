# -*- coding: utf-8 -*-
"""
Created on Sat Dec 27 18:38:53 2025

@author: dioue
"""

# mystake.py

import requests
import json
import pandas as pd
from datetime import datetime
import pytz


def scrape_mystake(Id_sport=None) -> pd.DataFrame:
    """
    Scrape MyStake (Face-à-face / H2H)
    
    Id_sport : liste des IDs de sports que tu veux scraper, ex: ["16","2"]
               Si None, utilise ["16"] (Cyclisme) par défaut.
    """
    paris_tz = pytz.timezone("Europe/Paris")
    rows = []

    # Valeur par défaut (Cyclisme) si rien n'est passé
    if Id_sport is None:
        Id_sport = ["16","8"]

    url_header = "https://analytics-sp.googleserv.tech/api/sport/getheader/en"
    
    try:
        response = requests.get(url_header)
        response.raise_for_status()
        
        # Gestion du format de réponse MyStake (parfois string JSON)
        raw_data = response.json()
        data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
        
        en_sports = data.get("EN", {}).get("Sports", {})

        for s_id in Id_sport:
            sport_node = en_sports.get(str(s_id))
            if not sport_node:
                continue

            # Identification des IDs de duels H2H (IDs négatifs et GameCount > 1)
            h2h_tasks = []
            for reg in sport_node.get("Regions", {}).values():
                for champ in reg.get("Champs", {}).values():
                    if champ.get("GameCount", 0) > 1:
                        champ_name = champ.get("Name")
                        items = champ.get("GameSmallItems", {})
                        for g_id in items.keys():
                            if str(g_id).startswith("-"):
                                h2h_tasks.append((str(g_id).lstrip('-'), champ_name))

            # Extraction des détails pour chaque duel identifié
            for o_id, champ_name in h2h_tasks:
                try:
                    url_full = f"https://analytics-sp.googleserv.tech/api/sport/GetOutrightFull/en/{o_id}"
                    resp_full = requests.get(url_full, timeout=5)
                    f_json = resp_full.json()
                    f_data = json.loads(f_json) if isinstance(f_json, str) else f_json
                    
                    teams = f_data.get("Teams", {})
                    outrights = f_data.get("Outrights", {})
                    
                    for out_val in outrights.values():
                        event_name = out_val.get("OutrighNameItem", {}).get("Name")
                        start_raw = out_val.get("st")
                        
                        cutoff = (
                            datetime.fromisoformat(start_raw).astimezone(paris_tz)
                            if start_raw else None
                        )
                        
                        games = out_val.get("Game", {})
                        # Uniquement les Face-à-face (2 sélections)
                        if len(games) == 2:
                            for g_val in games.values():
                                coureur_id = str(g_val.get("t1"))
                                name = teams.get(coureur_id, {}).get("Name", "Inconnu")
                                
                                ev = g_val.get("ev", {})
                                if ev:
                                    first_ev_id = list(ev.keys())[0]
                                    price = ev[first_ev_id].get("coef")
                                    
                                    rows.append({
                                        "Bookmaker": "MyStake",
                                        "Competition": champ_name,
                                        "Evenement": event_name,
                                        "Competiteur": name,
                                        "Cote": price,
                                        "Cutoff": cutoff,
                                    })
                except:
                    continue

    except Exception as e:
        print(f"Erreur MyStake: {e}")

    df = pd.DataFrame(rows)

    if df.empty:
        return pd.DataFrame(columns=["Bookmaker", "Competition", "Extraction", "Cutoff", "Evenement", "Competiteur", "Cote"])

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

# --- BLOC DE TEST ---
if __name__ == "__main__":
    print("Démarrage du test MyStake...")
    # On teste avec le cyclisme (16) par défaut
    df_test = scrape_mystake(Id_sport=["16"])
    
    if not df_test.empty:
        print(f"\nSuccès ! {len(df_test)} lignes extraites.")
        # Affichage trié pour mieux voir les binômes de duels
        print(df_test.sort_values(by=["Competition", "Evenement"]).to_string(index=False))
    else:
        print("\nAucune donnée trouvée. Vérifie si des duels sont ouverts sur le site.")