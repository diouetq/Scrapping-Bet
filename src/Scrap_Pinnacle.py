# -*- coding: utf-8 -*-
"""
Created on Fri Jan 30 13:42:36 2026

@author: dioue
"""

import requests
import json

url = "https://guest.api.arcadia.pinnacle.com/0.1/sports/33/matchups?withSpecials=false&brandId=0"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://www.pinnacle.com",
    "Referer": "https://www.pinnacle.com/",
}

response = requests.get(url, headers=headers)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"Nombre de matchups: {len(data)}")
    print(json.dumps(data[0], indent=2))  # Premier matchup
else:
    print(f"Erreur: {response.text}")