import requests
import pandas as pd
from datetime import datetime
import pytz
import time
import random

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def get_browser_session(max_retries=3):
    """Initialise une session navigateur avec retry"""
    for attempt in range(max_retries):
        try:
            options = Options()
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-gpu")
            options.add_argument("--enable-javascript")
            
            # Headers plus réalistes
            options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
            
            # Désactiver l'automatisation
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)

            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options
            )

            # Masquer webdriver
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                '''
            })

            print(f"🔄 Tentative {attempt + 1}/{max_retries} : Chargement Betify...")
            driver.get("https://betify.com/")
            
            # Attente plus longue et aléatoire
            wait_time = random.uniform(8, 12)
            time.sleep(wait_time)
            
            # Scroll pour simuler comportement humain
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(1)

            cookies = driver.get_cookies()
            user_agent = driver.execute_script("return navigator.userAgent;")
            driver.quit()

            session = requests.Session()
            session.headers.update({
                "User-Agent": user_agent,
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Referer": "https://betify.com/",
                "Origin": "https://betify.com",
                "Connection": "keep-alive",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "cross-site",
                "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"'
            })

            for c in cookies:
                session.cookies.set(c['name'], c['value'])

            print(f"✅ Session créée avec {len(cookies)} cookies")
            return session

        except Exception as e:
            print(f"❌ Tentative {attempt + 1} échouée : {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
            else:
                raise

    raise Exception("Impossible de créer une session après plusieurs tentatives")


def safe_get_json(session, url, label="", max_retries=3):
    """Requête avec retry et backoff exponentiel"""
    for attempt in range(max_retries):
        try:
            # Délai aléatoire entre requêtes
            if attempt > 0:
                backoff = (2 ** attempt) + random.uniform(0, 1)
                print(f"⏳ Retry {attempt + 1}/{max_retries} dans {backoff:.1f}s...")
                time.sleep(backoff)
            
            r = session.get(url, timeout=30)
            print(f"🌐 {label} {r.status_code} → {url[:80]}...")

            if r.status_code == 200:
                if not r.text.strip():
                    print("⛔ Réponse vide")
                    return None
                return r.json()
            
            elif r.status_code == 503:
                print(f"⚠️ Service indisponible (503) - tentative {attempt + 1}")
                if attempt == max_retries - 1:
                    return None
                continue
            
            elif r.status_code == 429:
                print("⚠️ Rate limit (429)")
                time.sleep(10)
                continue
            
            else:
                print(f"⛔ Status {r.status_code}")
                print(r.text[:400])
                return None

        except requests.exceptions.Timeout:
            print(f"⏱️ Timeout {label}")
            if attempt == max_retries - 1:
                return None
        except Exception as e:
            print(f"❌ Erreur {label} : {e}")
            if attempt == max_retries - 1:
                return None

    return None


def scrape_betify(Id_sport=None) -> pd.DataFrame:
    """Scrape Betify avec gestion d'erreurs améliorée"""
    
    BRAND = "2491953325260546049"
    paris_tz = pytz.timezone("Europe/Paris")
    extraction_dt = datetime.now(paris_tz)
    rows = []

    if Id_sport is None:
        Id_sport = ["17", "43", "44", "46"]

    # Colonnes pour DataFrame vide en cas d'échec
    columns = ["Bookmaker", "Competition", "Extraction", "Cutoff", 
               "Evenement", "Competiteur", "Cote"]

    try:
        # Création session avec retry
        SESSION = get_browser_session(max_retries=3)
        
    except Exception as e:
        print(f"❌ Impossible d'initialiser la session : {e}")
        return pd.DataFrame(columns=columns)

    # ============================
    # 1️⃣ Charger /0
    # ============================
    url_0 = f"https://api-a-c7818b61-600.sptpub.com/api/v4/prematch/brand/{BRAND}/en/0"
    data_0 = safe_get_json(SESSION, url_0, "BOOT", max_retries=5)

    if not data_0:
        print("❌ Betify bloqué sur /0 même après retries")
        return pd.DataFrame(columns=columns)

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

    for idx, ver in enumerate(all_versions):
        # Délai aléatoire entre requêtes
        if idx > 0:
            time.sleep(random.uniform(0.5, 1.5))
        
        url = f"https://api-a-c7818b61-600.sptpub.com/api/v4/prematch/brand/{BRAND}/en/{ver}"
        data = safe_get_json(SESSION, url, f"VER {ver}")
        if not data:
            continue

        all_events.update(data.get("events", {}))
        all_tournaments.update(data.get("tournaments", {}))

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

                # Délai avant chaque requête variant
                time.sleep(random.uniform(0.3, 0.8))
                
                api_data = safe_get_json(SESSION, api_url, "V3")
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

    return df[columns]