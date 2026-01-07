import requests, pandas as pd, re
from datetime import datetime
import pytz

def scrape_greenluck(Id_sport=None) -> pd.DataFrame:
    """
    Scrape Greenluck face-à-face pour les sports donnés.

    Id_sport : liste d'IDs de sports (ex: ["16","27","28"]), None = valeur par défaut.
    """
    paris_tz = pytz.timezone("Europe/Paris")
    all_rows = []

    # Valeur par défaut
    if Id_sport is None:
        Id_sport = ["16","27","28"]  # format chaîne comme pour Sportaza

    BASE_CACHE = "https://pre-161o-sp.sbx.bet/cache/161/fr/EE/Europe-Paris/init"

    for sport_id in Id_sport:
        ENDPOINT = f"{BASE_CACHE}/{sport_id}/welcome-popular.json?filters="
        response = requests.get(ENDPOINT)
        if response.status_code != 200:
            print(f"⚠️ Erreur {response.status_code} pour SPORT_ID {sport_id}, passage au suivant")
            continue
        data = response.json()
        events = data.get("events", [])

        for event in events:
            main_odds = event.get("main_odds", {}).get("main", {})
            if len(main_odds) != 2:
                continue

            sorted_odds = sorted(main_odds.values(), key=lambda x: x.get("team_side"))

            def normalize_name(name):
                return re.sub(r"[^a-zA-Z0-9\s]", "", name).strip().lower() if name else ""

            name1 = normalize_name(sorted_odds[0].get("team_name"))
            name2 = normalize_name(sorted_odds[1].get("team_name"))

            date_raw = event.get("date_start")
            cutoff = (datetime.fromisoformat(date_raw.replace("Z", "+00:00"))
                      .astimezone(paris_tz) if date_raw else None)

            # Ligne 1
            all_rows.append({
                "Bookmaker": "Greenluck",
                "Competition": event.get("tournament_name"),
                "Evenement": f"{sorted_odds[0]['team_name']} vs {sorted_odds[1]['team_name']}",
                "Competiteur": sorted_odds[0].get("team_name"),
                "Cote": sorted_odds[0].get("odd_value"),
                "Cutoff": cutoff,
                "Extraction": datetime.now(paris_tz)
            })

            # Ligne 2
            all_rows.append({
                "Bookmaker": "Greenluck",
                "Competition": event.get("tournament_name"),
                "Evenement": f"{sorted_odds[0]['team_name']} vs {sorted_odds[1]['team_name']}",
                "Competiteur": sorted_odds[1].get("team_name"),
                "Cote": sorted_odds[1].get("odd_value"),
                "Cutoff": cutoff,
                "Extraction": datetime.now(paris_tz)
            })

    df = pd.DataFrame(all_rows)
    df = df[~df["Competiteur"].str.lower().isin(["oui", "non"])]
    
    
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
