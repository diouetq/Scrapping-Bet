# test_api.py
import requests
import time
import random
from datetime import datetime
import pytz

BRAND = "2491953325260546049"
URL = f"https://api-a-c7818b61-600.sptpub.com/api/v4/prematch/brand/{BRAND}/en/0"

paris_tz = pytz.timezone("Europe/Paris")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
    "Referer": "https://www.betify.com/"
}

def test_api(max_retries=3):
    print("🕒 Heure Paris :", datetime.now(paris_tz))

    for attempt in range(1, max_retries + 1):
        try:
            print(f"🔄 Tentative {attempt}...")
            
            response = requests.get(
                URL,
                headers=HEADERS,
                timeout=15
            )

            print("Status code :", response.status_code)

            if response.status_code == 200:
                data = response.json()
                top_versions = data.get("top_events_versions", [])
                rest_versions = data.get("rest_events_versions", [])

                print("✅ API accessible")
                print("Top versions :", len(top_versions))
                print("Rest versions :", len(rest_versions))
                return True

            else:
                print("⚠️ Réponse non OK :", response.text[:200])

        except Exception as e:
            print("❌ Erreur :", e)

        # pause aléatoire (anti-détection)
        sleep_time = random.uniform(3, 7)
        print(f"⏳ Pause {sleep_time:.1f}s avant retry...")
        time.sleep(sleep_time)

    print("🚨 API inaccessible après plusieurs tentatives")
    return False


if __name__ == "__main__":
    success = test_api()
    exit(0 if success else 1)
