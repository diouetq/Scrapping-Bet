import requests
import time

BRAND = "2491953325260546049"
URL = f"https://api-a-c7818b61-600.sptpub.com/api/v4/prematch/brand/{BRAND}/en/0"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.betify.com/"
}

# Configuration du proxy Tor (SOCKS5h pour résoudre les DNS via Tor aussi)
PROXIES = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050'
}

def test_tor():
    try:
        # 1. Vérifions d'abord notre IP publique via Tor
        check_ip = requests.get('https://api.ipify.org', proxies=PROXIES, timeout=20)
        print(f"🌐 IP via Tor : {check_ip.text}")

        # 2. Requête vers l'API cible
        print(f"🔄 Tentative vers Betify...")
        response = requests.get(URL, headers=HEADERS, proxies=PROXIES, timeout=30)
        
        print(f"Status code : {response.status_code}")
        if response.status_code == 200:
            print("✅ SUCCÈS : L'API a répondu via Tor !")
            return True
        else:
            print(f"⚠️ Échec : {response.text[:100]}")
            
    except Exception as e:
        print(f"❌ Erreur de connexion : {e}")
    return False

if __name__ == "__main__":
    success = test_tor()
    exit(0 if success else 1)