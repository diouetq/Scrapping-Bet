import requests
import json
import time

BRAND = "2491953325260546049"
URL = f"https://api-a-c7818b61-600.sptpub.com/api/v4/prematch/brand/{BRAND}/en/0"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.betify.com/"
}

PROXIES = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050'
}

def test_tor():
    try:
        # 1. Vérification de l'IP
        check_ip = requests.get('https://api.ipify.org', proxies=PROXIES, timeout=20)
        print(f"🌐 IP via Tor : {check_ip.text}")

        # 2. Requête vers l'API
        print(f"🔄 Tentative vers Betify...")
        response = requests.get(URL, headers=HEADERS, proxies=PROXIES, timeout=30)
        
        print(f"Status code : {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCÈS : L'API a répondu via Tor !")
            
            # --- AFFICHAGE DU JSON ---
            try:
                data = response.json()
                # On affiche le JSON formaté (limité aux 1000 premiers caractères pour ne pas flood les logs)
                json_str = json.dumps(data, indent=2, ensure_ascii=False)
                print("📦 Contenu du JSON reçu :")
                print(json_str[:2000] + ("..." if len(json_str) > 2000 else ""))
            except Exception as e:
                print(f"⚠️ Impossible de lire le JSON bien que le statut soit 200 : {e}")
                print(f"Contenu brut : {response.text[:200]}")
            # --------------------------
            
            return True
        else:
            print(f"⚠️ Échec {response.status_code} : {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Erreur de connexion : {e}")
    return False

if __name__ == "__main__":
    success = test_tor()
    exit(0 if success else 1)