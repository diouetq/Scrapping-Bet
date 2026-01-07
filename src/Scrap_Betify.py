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
    url_0 = (
        "https://api-a-c7818b61-600.sptpub.com/"
        f"api/v4/prematch/brand/{BRAND}/en/0"
    )
    data_0 = requests.get(url_0).json()

    tev = data_0.get("top_events_versions")
    if isinstance(tev, list):
        tev = tev[0]

    # ============================
    # 2️⃣ Charger top_events_versions
    # ============================
    url = (
        "https://api-a-c7818b61-600.sptpub.com/"
        f"api/v4/prematch/brand/{BRAND}/en/{tev}"
    )
    data = requests.get(url).json()

    events = data.get("events", {})
    tournaments = data.get("tournaments", {})

    # =====================================================
    # 3️⃣ Marchés sans variant
    # =====================================================
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

            cutoff = (
                datetime.fromtimestamp(desc["scheduled"], paris_tz)
                if desc.get("scheduled") else None
            )

            for idx, (_, odd) in enumerate(sorted_outcomes):
                rows.append({
                    "Bookmaker": "Betify",
                    "Competition": tournaments.get(
                        desc.get("tournament"), {}
                    ).get("name"),
                    "Extraction": extraction_dt,
                    "Cutoff": cutoff,
                    "Evenement": desc.get("slug"),
                    "Competiteur": competitors[idx] if idx < len(competitors) else None,
                    "Cote": float(odd.get("k"))
                })

    # =====================================================
    # 4️⃣ Marchés avec variant
    # =====================================================
    for event in events.values():
        desc = event.get("desc", {})
        if desc.get("sport") not in Id_sport:
            continue

        for market_id, variants in event.get("markets", {}).items():
            for variant_key, outcomes in variants.items():
                if "variant=" not in variant_key:
                    continue
                if len(outcomes) != 2:
                    continue

                variant_id = variant_key.split("variant=")[-1]
                api_url = (
                    "https://api-a-c7818b61-600.sptpub.com/"
                    f"api/v1/descriptions/markets/variants/{market_id}/{variant_id}/en"
                )

                try:
                    api_data = requests.get(api_url).json()
                except Exception:
                    continue

                if not api_data.get("items"):
                    continue

                item = api_data["items"][0]
                event_name = item.get("name")
                id_to_name = {
                    o["id"]: o["name"]
                    for o in item.get("outcomes", [])
                }

                cutoff = (
                    datetime.fromtimestamp(desc["scheduled"], paris_tz)
                    if desc.get("scheduled") else None
                )

                for oid, odd in outcomes.items():
                    rows.append({
                        "Bookmaker": "Betify",
                        "Competition": tournaments.get(
                            desc.get("tournament"), {}
                        ).get("name"),
                        "Extraction": extraction_dt,
                        "Cutoff": cutoff,
                        "Evenement": event_name,
                        "Competiteur": id_to_name.get(oid),
                        "Cote": float(odd.get("k"))
                    })

    df = pd.DataFrame(rows)

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
