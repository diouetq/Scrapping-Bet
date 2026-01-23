import time
import pytz
from datetime import datetime
from curl_cffi import requests as curl_requests
import cloudscraper
import requests

BRAND = "2491953325260546049"
URL = f"https://api-a-c7818b61-600.sptpub.com/api/v4/prematch/brand/{BRAND}/en/0"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.betify.com/"
}

def run_test(name, func):
    print(f"\n--- Test Méthode : {name} ---")
    try:
        status, text = func()
        print(f"Status : {status}")
        if status == 200:
            print(f"✅ SUCCÈS avec {name} !")
            return True
        else:
            print(f"❌ ÉCHEC {status} : {text[:100]}")
    except Exception as e:
        print(f"💥 ERREUR Critique : {e}")
    return False

# --- Méthode 1 : Requests Classique ---
def try_requests():
    r = requests.get(URL, headers=HEADERS, timeout=10)
    return r.status_code, r.text

# --- Méthode 2 : Cloudscraper (Contournement Cloudflare) ---
def try_cloudscraper():
    scraper = cloudscraper.create_scraper()
    r = scraper.get(URL, headers=HEADERS, timeout=10)
    return r.status_code, r.text

# --- Méthode 3 : Curl_cffi (Impersonation TLS/Chrome) ---
def try_curl_cffi():
    r = curl_requests.get(URL, headers=HEADERS, impersonate="chrome120", timeout=10)
    return r.status_code, r.text

if __name__ == "__main__":
    results = []
    results.append(run_test("Requests Classique", try_requests))
    results.append(run_test("Cloudscraper", try_cloudscraper))
    results.append(run_test("Curl_cffi (Chrome 120)", try_curl_cffi))

    if any(results):
        print("\n✨ Au moins une méthode a fonctionné !")
        exit(0)
    else:
        print("\n🚨 Les 3 méthodes ont échoué. Le blocage vient probablement de l'IP GitHub.")
        exit(1)