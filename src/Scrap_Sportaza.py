# -*- coding: utf-8 -*-
"""
Created on Sat Dec 27 18:38:53 2025

@author: dioue
"""

# sportaza.py

import requests
import pandas as pd
from datetime import datetime
import pytz


def scrape_sportaza(Id_sport=None) -> pd.DataFrame:
    """
    Scrape Sportaza (face-à-face / sc==2)
    
    Id_sport : liste des IDs de sports que tu veux scraper, ex: ["1359","923"]
               Si None, utilise la liste par défaut.
    """
    paris_tz = pytz.timezone("Europe/Paris")
    rows = []

    # Valeur par défaut si rien n'est passé
    if Id_sport is None:
        Id_sport = ["1596","1359","923","924","1380","1405","1406","904","1411","1412","672"]

    # endpoints dynamiques
    endpoints = [(",".join(Id_sport), "GetOutrightEvents"),
                 (",".join(Id_sport), "GetEvents")]

    for cat_ids, suffix in endpoints:
        url = f"https://sb2frontend-altenar2.biahosted.com/api/widget/{suffix}"
        params = {
            "culture": "fr-FR",
            "timezoneOffset": -120,
            "integration": "sportaza",
            "deviceType": 1,
            "numFormat": "en-GB",
            "countryCode": "LI",
            "eventCount": 0,
            "sportId": 0,
            "catIds": cat_ids
        }

        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        odds = {o["id"]: o for o in data.get("odds", [])}
        champs = {c["id"]: c for c in data.get("champs", [])}
        events = {e["id"]: e for e in data.get("events", [])}

        for market in data.get("markets", []):
            event = next(
                (e for e in events.values() if market["id"] in e.get("marketIds", [])),
                None
            )
            if not event:
                continue

            if len(event.get("competitorIds", [])) != 2 and event.get("sc") != 2:
                continue

            odds_list = [odds[o] for o in market.get("oddIds", []) if o in odds]
            if len(odds_list) != 2:
                continue

            champ = champs.get(event.get("champId"), {})
            start_raw = event.get("startDate")

            cutoff = (
                datetime.fromisoformat(start_raw.replace("Z", "+00:00"))
                .astimezone(paris_tz)
                if start_raw else None
            )

            for i in range(2):
                rows.append({
                    "Bookmaker": "Sportaza",
                    "Competition": champ.get("name"),
                    "Evenement": event.get("name"),
                    "Competiteur": odds_list[i].get("name"),
                    "Cote": odds_list[i].get("price"),
                    "Cutoff": cutoff,
                })

    df = pd.DataFrame(rows)

    df = df[~df["Competiteur"].isin(["oui", "non"])]
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