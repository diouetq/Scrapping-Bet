# betify.py

import requests
import pandas as pd
from datetime import datetime
import pytz
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://betify.com/",
    "Origin": "https://betify.com",
    "Connection": "keep-alive"
}

def safe_get_json(url, label=""):
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        print(f"🌐 {label} {r.status_code} → {url}")

        if r.status_code != 200:
            print("⛔ Réponse non 200 (extrait):")
            print(r.text[:400])
            return None

        if not r.text.strip():
            print("⛔ Réponse vide")
            return None

        return r.json()

    except Exception as e:
        print(f"❌ Erreur requête {label} : {e}")
        return None


def scrape_betify(Id_sport=None) -> pd.DataFrame:

    BRAND = "2491953325260546049"
    paris_tz = pytz.timezone("Europe/Paris")
    extraction_dt = datetime.now(paris_tz)
    rows = []

    if Id_sport is None:
        Id_sport = ["17","43","44","46"]

    # ============================
    # 1️⃣ Charger /0
    # ============================
    url_0 = f"https://api-a-c7818b61-600.sptpub.com/api/v4/prematch/brand/{BRAND}/en/0"
    data_0 = safe_get_json(url_0, "BOOT")

    if not data_0:
        print("❌ Betify bloqué sur /0 (très probable sur GitHub)")
        return pd.DataFrame(columns=[
            "Bookmaker","Competition","Extraction","Cutoff",
            "Evenement","Competiteur","Cote"
        ])

    top_versions = data_0.get("top_events_versions", [])
    rest_versions = data_0.get("rest_events_versions", [])

    if len(top_versions) == 1 and isinstance(top_versions[0], list):
        top_versions = top_versions[0]

    all_versions = list(set(top_versions + rest_versions))
    print(f"📦 Versions chargées : {len(all_versions)}")

    # ============================
    # 2️⃣ Charger toutes les versions
    # ============================
    all_events = {}
    all_tournaments = {}

    for ver in all_versions:
        url = f"https://api-a-c7818b61-600.sptpub.com/api/v4/prematch/brand/{BRAND}/en/{ver}"
        data = safe_get_json(url, f"VER {ver}")
        if not data:
            continue

        all_events.update(data.get("events", {}))
        all_tournaments.update(data.get("tournaments", {}))
        time.sleep(0.3)

    print(f"📊 Events : {len(all_events)}")

    # ============================
    # 3️⃣ Marchés simples
    # ============================
    for event in all_events.values():
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
            if "variant=" in variant_key or len(outcomes) != 2:
                continue

            cutoff = datetime.fromtimestamp(desc["scheduled"], paris_tz) if desc.get("scheduled") else None
            sorted_outcomes = sorted(outcomes.items(), key=lambda x: int(x[0]))

            for idx, (_, odd) in enumerate(sorted_outcomes):
                rows.append({
                    "Bookmaker": "Betify",
                    "Competition": all_tournaments.get(desc.get("tournament"), {}).get("name"),
                    "Extraction": extraction_dt,
                    "Cutoff": cutoff,
                    "Evenement": desc.get("slug"),
                    "Competiteur": competitors[idx] if idx < len(competitors) else None,
                    "Cote": float(odd.get("k"))
                })

    # ============================
    # 4️⃣ Marchés variants
    # ============================
    for event_id, event in all_events.items():
        desc = event.get("desc", {})
        if desc.get("sport") not in Id_sport:
            continue

        cutoff = datetime.fromtimestamp(desc.get("scheduled"), paris_tz) if desc.get("scheduled") else None

        for market_id, variants in event.get("markets", {}).items():
            for variant_key, outcomes in variants.items():
                if "variant=" not in variant_key or len(outcomes) != 2:
                    continue

                variant_id = variant_key.split("variant=")[-1]

                api_url = (
                    f"https://api-a-c7818b61-600.sptpub.com/api/v3/descriptions/brand/{BRAND}"
                    f"/event/{event_id}/market/{market_id}@variant={variant_id}/fr"
                )

                api_data = safe_get_json(api_url, "V3")
                if not api_data:
                    continue

                markets_desc = api_data.get("markets", {})
                specific_market_desc = markets_desc.get(market_id, {})
                variant_list = specific_market_desc.get("variants", {}).get(f"variant={variant_id}", [])

                if variant_list:
                    variant_info = variant_list[0]
                    event_name = variant_info.get("name", desc.get("slug"))
                    outcomes_list = variant_info.get("outcomes", [])
                else:
                    event_name = desc.get("slug")
                    outcomes_list = []

                id_to_name = {o["id"]: o["name"] for o in outcomes_list}

                for oid, odd in outcomes.items():
                    rows.append({
                        "Bookmaker": "Betify",
                        "Competition": all_tournaments.get(desc.get("tournament"), {}).get("name"),
                        "Extraction": extraction_dt,
                        "Cutoff": cutoff,
                        "Evenement": event_name,
                        "Competiteur": id_to_name.get(oid, oid),
                        "Cote": float(odd.get("k"))
                    })

    df = pd.DataFrame(rows)

    print(f"✅ Betify lignes finales : {len(df)}")

    return df[[
        "Bookmaker","Competition","Extraction","Cutoff",
        "Evenement","Competiteur","Cote"
    ]]
