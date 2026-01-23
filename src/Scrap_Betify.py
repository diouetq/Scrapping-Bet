# Scrap_Betify.py
import requests
import pandas as pd
from datetime import datetime
import pytz
import time

def scrape_betify(Id_sport=None) -> pd.DataFrame:
    """
    Scrape Betify (CrazyBet infra) - VERSION ULTRA-ROBUSTE
    Retourne uniquement les compétitions qui proposent des cotes H2H
    """
    BRAND = "2491953325260546049"
    paris_tz = pytz.timezone("Europe/Paris")
    extraction_dt = datetime.now(paris_tz)
    
    if Id_sport is None:
        Id_sport = ['43', '44', '46']
    
    # ============================
    # 1️⃣ Charger /0 avec retry
    # ============================
    url_0 = f"https://api-a-c7818b61-600.sptpub.com/api/v4/prematch/brand/{BRAND}/en/0"
    
    for attempt in range(3):  # 3 tentatives
        try:
            print(f"🔍 Tentative {attempt + 1}/3 pour charger /0...")
            response = requests.get(
                url_0, 
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json"
                }, 
                timeout=15
            )
            
            # Vérifier le statut HTTP
            if response.status_code != 200:
                print(f"⚠️ Status code {response.status_code}")
                time.sleep(2)
                continue
            
            # Vérifier que la réponse n'est pas vide
            if not response.text.strip():
                print(f"⚠️ Réponse vide")
                time.sleep(2)
                continue
            
            data_0 = response.json()
            print(f"✅ Données /0 chargées avec succès")
            break
            
        except requests.exceptions.Timeout:
            print(f"⏱️ Timeout lors de la tentative {attempt + 1}")
            time.sleep(2)
            continue
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Erreur réseau : {e}")
            time.sleep(2)
            continue
        except ValueError as e:  # JSON decode error
            print(f"⚠️ Erreur JSON : {e}")
            print(f"🔹 Contenu reçu : {response.text[:500]}")
            time.sleep(2)
            continue
    else:
        # Si toutes les tentatives ont échoué
        print("❌ Impossible de charger /0 après 3 tentatives")
        return pd.DataFrame(columns=["Bookmaker", "Competition", "Extraction", "Cutoff"])
    
    top_versions = data_0.get("top_events_versions", [])
    rest_versions = data_0.get("rest_events_versions", [])
    
    if len(top_versions) == 1 and isinstance(top_versions[0], list):
        top_versions = top_versions[0]
    
    all_versions = list(set(top_versions + rest_versions))
    print(f"📦 {len(all_versions)} versions à charger")
    
    if not all_versions:
        print("⚠️ Aucune version trouvée")
        return pd.DataFrame(columns=["Bookmaker", "Competition", "Extraction", "Cutoff"])
    
    # ============================
    # 2️⃣ Charger toutes les versions
    # ============================
    all_events = {}
    all_tournaments = {}
    
    for i, ver in enumerate(all_versions):
        url = f"https://api-a-c7818b61-600.sptpub.com/api/v4/prematch/brand/{BRAND}/en/{ver}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200 and response.text.strip():
                data = response.json()
                all_events.update(data.get("events", {}))
                all_tournaments.update(data.get("tournaments", {}))
                print(f"✅ Version {i+1}/{len(all_versions)} chargée")
            else:
                print(f"⚠️ Version {i+1}/{len(all_versions)} : status {response.status_code}")
        except Exception as e:
            print(f"⚠️ Erreur version {ver} : {e}")
            continue
    
    events = all_events
    tournaments = all_tournaments
    
    print(f"📊 {len(events)} événements et {len(tournaments)} tournois chargés")
    
    if not events:
        print("⚠️ Aucun événement trouvé")
        return pd.DataFrame(columns=["Bookmaker", "Competition", "Extraction", "Cutoff"])
    
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
    
    print(f"🎯 {len(h2h_competitions)} compétitions H2H identifiées")
    
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
    
    print(f"✅ Betify : {len(df)} compétitions H2H retournées")
    
    return df[["Bookmaker", "Competition", "Extraction", "Cutoff"]]


if __name__ == "__main__":
    print("🔍 Test Betify H2H...")
    df = scrape_betify()
    print(f"\n✅ {len(df)} compétitions H2H trouvées")
    if not df.empty:
        print(df.head(10))