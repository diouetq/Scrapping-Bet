import requests
import pandas as pd
from datetime import datetime
import pytz

# Configuration Tor
TOR_PROXIES = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050'
}

def scrape_betify(Id_sport=None, use_tor=True) -> pd.DataFrame:
    BRAND = "2491953325260546049"
    paris_tz = pytz.timezone("Europe/Paris")
    extraction_dt = datetime.now(paris_tz)
    rows = []

    # Choix du mode de connexion
    proxies = TOR_PROXIES if use_tor else None
    if Id_sport is None:
        Id_sport = ['43', '44', '46']

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.betify.com/"
    }

    # --- 1️⃣ Charger /0 ---
    url_0 = f"https://api-a-c7818b61-600.sptpub.com/api/v4/prematch/brand/{BRAND}/en/0"
    try:
        res = requests.get(url_0, headers=headers, proxies=proxies, timeout=30)
        if res.status_code != 200:
            return pd.DataFrame()
        data_0 = res.json()
    except Exception as e:
        print(f"❌ Betify Error /0: {e}")
        return pd.DataFrame()

    top_versions = data_0.get("top_events_versions", [])
    rest_versions = data_0.get("rest_events_versions", [])
    if len(top_versions) == 1 and isinstance(top_versions[0], list):
        top_versions = top_versions[0]
    all_versions = list(set(top_versions + rest_versions))

    # --- 2️⃣ Charger les versions ---
    all_events, all_tournaments = {}, {}
    for ver in all_versions:
        url = f"https://api-a-c7818b61-600.sptpub.com/api/v4/prematch/brand/{BRAND}/en/{ver}"
        try:
            r = requests.get(url, headers=headers, proxies=proxies, timeout=20)
            if r.status_code == 200:
                d = r.json()
                all_events.update(d.get("events", {}))
                all_tournaments.update(d.get("tournaments", {}))
        except: continue

    # --- 3️⃣ & 4️⃣ Traitement des marchés ---
    for event_id, event in all_events.items():
        desc = event.get("desc", {})
        if desc.get("sport") not in Id_sport: continue
        
        tournament_name = all_tournaments.get(desc.get("tournament"), {}).get("name")
        cutoff = datetime.fromtimestamp(desc["scheduled"], paris_tz) if desc.get("scheduled") else None
        
        for market_id, variants in event.get("markets", {}).items():
            for variant_key, outcomes in variants.items():
                if len(outcomes) != 2: continue

                # Cas standard (H2H)
                if "variant=" not in variant_key:
                    competitors = [c.get("name") for c in desc.get("competitors", [])]
                    sorted_o = sorted(outcomes.items(), key=lambda x: int(x[0]))
                    for idx, (_, odd) in enumerate(sorted_o):
                        rows.append({
                            "Bookmaker": "Betify", "Competition": tournament_name,
                            "Extraction": extraction_dt, "Cutoff": cutoff,
                            "Evenement": desc.get("slug"), "Cote": float(odd.get("k")),
                            "Competiteur": competitors[idx] if idx < len(competitors) else None
                        })
                
                # Cas avec Variant (Endpoint v3)
                else:
                    v_id = variant_key.split("variant=")[-1]
                    v3_url = f"https://api-a-c7818b61-600.sptpub.com/api/v3/descriptions/brand/{BRAND}/event/{event_id}/market/{market_id}@variant={v_id}/fr"
                    try:
                        v3_res = requests.get(v3_url, headers=headers, proxies=proxies, timeout=20)
                        v3_data = v3_res.json()
                        v_list = v3_data.get("markets", {}).get(market_id, {}).get("variants", {}).get(f"variant={v_id}", [])
                        if v_list:
                            v_info = v_list[0]
                            id_map = {o["id"]: o["name"] for o in v_info.get("outcomes", [])}
                            for oid, odd in outcomes.items():
                                rows.append({
                                    "Bookmaker": "Betify", "Competition": tournament_name,
                                    "Extraction": extraction_dt, "Cutoff": cutoff,
                                    "Evenement": v_info.get("name", desc.get("slug")),
                                    "Competiteur": id_map.get(oid, oid), "Cote": float(odd.get("k"))
                                })
                    except: continue

    return pd.DataFrame(rows) if rows else pd.DataFrame()