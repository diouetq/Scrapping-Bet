# Scrap_Betify.py
import requests
import pandas as pd
from datetime import datetime
import pytz

def scrape_betify(Id_sport=None) -> pd.DataFrame:
    """
    Scrape Betify (CrazyBet infra) - VERSION OPTIMISÉE
    Retourne uniquement les compétitions qui proposent des cotes H2H
    SANS appels API supplémentaires pour les variants
    """
    BRAND = "2491953325260546049"
    paris_tz = pytz.timezone("Europe/Paris")
    extraction_dt = datetime.now(paris_tz)
    
    if Id_sport is None:
        Id_sport = ['43', '44', '46']
    
    # ============================
    # 1️⃣ Charger /0
    # ============================
    url_0 = f"https://api-a-c7818b61-600.sptpub.com/api/v4/prematch/brand/{BRAND}/en/0"
    try:
        data_0 = requests.get(url_0, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36"
        }, timeout=10).json()
    except Exception as e:
        print(f"⚠️ Erreur lors du chargement de /0 : {e}")
        return pd.DataFrame(columns=["Bookmaker", "Competition", "Extraction", "Cutoff"])
    
    top_versions = data_0.get("top_events_versions", [])
    rest_versions = data_0.get("rest_events_versions", [])
    
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
            data = requests.get(url, timeout=10).json()
            all_events.update(data.get("events", {}))
            all_tournaments.update(data.get("tournaments", {}))
        except Exception as e:
            print(f"⚠️ Erreur version {ver} : {e}")
            continue
    
    events = all_events
    tournaments = all_tournaments
    
    # ============================
    # 3️⃣ Identifier les compétitions H2H
    # ============================
    h2h_competitions = {}  # {tournament_id: earliest_cutoff}
    
    for event in events.values():
        desc = event.get("desc", {})
        
        if desc.get("sport") not in Id_sport:
            continue
        
        competitors = desc.get("competitors", [])
        
        # ✅ FILTRE H2H: exactement 2 compétiteurs
        if len(competitors) != 2:
            continue
        
        # Vérifier qu'il y a bien des marchés avec 2 outcomes
        # ⚡ ON NE FAIT PLUS D'APPELS API ICI - on se base juste sur la structure
        markets = event.get("markets", {})
        has_h2h_market = False
        
        for market_id, variants in markets.items():
            for variant_key, outcomes in variants.items():
                if len(outcomes) == 2:
                    has_h2h_market = True
                    break
            if has_h2h_market:
                break
        
        if not has_h2h_market:
            continue
        
        # Récupérer la compétition
        tournament_id = desc.get("tournament")
        if not tournament_id:
            continue
        
        # Récupérer le cutoff
        cutoff = datetime.fromtimestamp(desc.get("scheduled"), paris_tz) if desc.get("scheduled") else None
        
        # Garder le cutoff le plus proche pour chaque compétition
        if tournament_id not in h2h_competitions:
            h2h_competitions[tournament_id] = cutoff
        elif cutoff and h2h_competitions[tournament_id]:
            if cutoff < h2h_competitions[tournament_id]:
                h2h_competitions[tournament_id] = cutoff
    
    # ============================
    # 4️⃣ Créer le DataFrame des compétitions H2H
    # ============================
    rows = []
    for tournament_id, cutoff in h2h_competitions.items():
        competition_name = tournaments.get(tournament_id, {}).get("name")
        if competition_name:
            rows.append({
                "Bookmaker": "Betify",
                "Competition": competition_name,
                "Extraction": extraction_dt,
                "Cutoff": cutoff
            })
    
    df = pd.DataFrame(rows)
    
    # Trier par Cutoff (les plus proches en premier)
    if not df.empty and "Cutoff" in df.columns:
        df = df.sort_values("Cutoff").reset_index(drop=True)
    
    return df[["Bookmaker", "Competition", "Extraction", "Cutoff"]]


# ============================
# TEST RAPIDE
# ============================
if __name__ == "__main__":
    print("🔍 Test Betify H2H...")
    df = scrape_betify()
    print(f"✅ {len(df)} compétitions H2H trouvées")
    print(df.head(10))