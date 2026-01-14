# betify.py

import requests
import pandas as pd
from datetime import datetime
import pytz

def scrape_betify(Id_sport=None) -> pd.DataFrame:
    """
    Scrape Betify (CrazyBet infra)
    Brand fixé dans le script
    """
    BRAND = "2491953325260546049"
    paris_tz = pytz.timezone("Europe/Paris")
    extraction_dt = datetime.now(paris_tz)
    rows = []

    if Id_sport is None:
        Id_sport = ['43', '44', '46']

    # ============================
    # 1️⃣ Charger /0
    # ============================
    url_0 = f"https://api-a-c7818b61-600.sptpub.com/api/v4/prematch/brand/{BRAND}/en/0"
    data_0 = requests.get(url_0).json()

    top_versions = data_0.get("top_events_versions", [])
    rest_versions = data_0.get("rest_events_versions", [])

    # parfois top_events_versions est [[...]]
    if len(top_versions) == 1 and isinstance(top_versions[0], list):
        top_versions = top_versions[0]

    all_versions = list(set(top_versions + rest_versions))

    # ============================
    # 2️⃣ Charger toutes les versions (top + rest)
    # ============================
    all_events = {}
    all_tournaments = {}

    for ver in all_versions:
        url = f"https://api-a-c7818b61-600.sptpub.com/api/v4/prematch/brand/{BRAND}/en/{ver}"
        try:
            data = requests.get(url).json()
        except Exception:
            continue

        all_events.update(data.get("events", {}))
        all_tournaments.update(data.get("tournaments", {}))

    events = all_events
    tournaments = all_tournaments

    # ============================
    # 3️⃣ Marchés sans variant
    # ============================
    for event in events.values():
        desc = event.get("desc", {})
        if desc.get("sport") not in Id_sport:
            continue

        competitors = [c.get("name") for c in desc.get("competitors", [])]
        markets = event.get("markets", {})
        if not markets:
            continue

        market_id = min(markets.keys(), key=lambda x: int(x))
        market = markets[market_id]

        for variant_key, outcomes in market.items():
            if "variant=" in variant_key:
                continue
            if len(outcomes) != 2:
                continue

            sorted_outcomes = sorted(outcomes.items(), key=lambda x: int(x[0]))
            cutoff = datetime.fromtimestamp(desc["scheduled"], paris_tz) if desc.get("scheduled") else None

            for idx, (_, odd) in enumerate(sorted_outcomes):
                rows.append({
                    "Bookmaker": "Betify",
                    "Competition": tournaments.get(desc.get("tournament"), {}).get("name"),
                    "Extraction": extraction_dt,
                    "Cutoff": cutoff,
                    "Evenement": desc.get("slug"),
                    "Competiteur": competitors[idx] if idx < len(competitors) else None,
                    "Cote": float(odd.get("k"))
                })

# =====================================================
    # 4️⃣ Marchés avec variant (nouveau endpoint v3)
    # =====================================================
    for event_id, event in events.items():
        desc = event.get("desc", {})
        if desc.get("sport") not in Id_sport:
            continue
    
        cutoff = datetime.fromtimestamp(desc.get("scheduled"), paris_tz) if desc.get("scheduled") else None
    
        for market_id, variants in event.get("markets", {}).items():
            for variant_key, outcomes in variants.items():
                if "variant=" not in variant_key:
                    continue
                if len(outcomes) != 2:
                    continue
    
                # Récupération du variant_id (ex: tt:markettext:2623...)
                variant_id = variant_key.split("variant=")[-1]
    
                # Endpoint v3 de description
                api_url = (
                    f"https://api-a-c7818b61-600.sptpub.com/api/v3/descriptions/brand/{BRAND}"
                    f"/event/{event_id}/market/{market_id}@variant={variant_id}/fr"
                )
    
                try:
                    api_data = requests.get(api_url).json()
                except Exception:
                    continue
    
                # --- CORRECTION ICI ---
                # L'API v3 renvoie directement un dictionnaire avec "markets" à la racine
                markets_desc = api_data.get("markets", {})
                
                # On accède au dictionnaire du marché spécifique (ex: "150011")
                specific_market_desc = markets_desc.get(market_id, {})
                
                # On récupère la liste des données pour ce variant précis
                variant_list = specific_market_desc.get("variants", {}).get(f"variant={variant_id}", [])
                
                if variant_list:
                    variant_info = variant_list[0]  # On prend le premier (et seul) bloc
                    event_name = variant_info.get("name", desc.get("slug"))
                    outcomes_list = variant_info.get("outcomes", [])
                else:
                    event_name = desc.get("slug")
                    outcomes_list = []
    
                # Mapping id (ex: tt:outcometext:...) -> nom (ex: Slovenia)
                id_to_name = {o["id"]: o["name"] for o in outcomes_list}
    
                # Remplissage des lignes avec les noms traduits
                for oid, odd in outcomes.items():
                    rows.append({
                        "Bookmaker": "Betify",
                        "Competition": tournaments.get(desc.get("tournament"), {}).get("name"),
                        "Extraction": extraction_dt,
                        "Cutoff": cutoff,
                        "Evenement": event_name,           # Nom complet (ex: Ruhpolding Relay...)
                        "Competiteur": id_to_name.get(oid, oid), # Nom (ex: Slovenia ou USA)
                        "Cote": float(odd.get("k"))
                    })

    # ============================
    # 5️⃣ Création du DataFrame final
    # ============================
    df = pd.DataFrame(rows)

    return df[[
        "Bookmaker",
        "Competition",
        "Extraction",
        "Cutoff",
        "Evenement",
        "Competiteur",
        "Cote"
    ]]
