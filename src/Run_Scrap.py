# -*- coding: utf-8 -*-
"""
Created on Sat Dec 27 19:10:34 2025

@author: dioue
"""

from Excel_builder import build_excel

from Scrap_Sportaza import scrape_sportaza
from Scrap_Greenluck import scrape_greenluck
from Scrap_Betify import scrape_betify


# =========================
# 🔽 DEF RUN : choisir les sports
# =========================


def run_sportaza():
    return scrape_sportaza(
        Id_sport=["1359","1393", "904", "923", "924", "1405", "1406", "1415","2245", "1356", "1659", "893","2239"]
    )


def run_greenluck():
    return scrape_greenluck(
        Id_sport=["14", "15", "16", "17", "27","28","31", "32"]
    )


def run_betify():
    return scrape_betify(
        Id_sport=["17","22","43", "44","45", "46", "48"],use_tor=False
    )


# =========================
# 🔽 CHOIX DU BOOKMAKER
# =========================


SCRAPER = run_betify
# SCRAPER = run_greenluck
# SCRAPER = run_betify
# SCRAPER = run_sportaza


# =========================
# 🔽 CHOIX PARAM build_excel
# =========================
EXPORT_DIR = r"C:\Users\dioue\OneDrive\Bureau\Code Python\Scrapping-Bet\Extraction"
KELLY = 4
STAKE = 20




if __name__ == "__main__":
    df = SCRAPER()

    path = build_excel(
        df,
        export_dir=EXPORT_DIR,
        kelly_number=KELLY,
        stake_number=STAKE
    )

    print("✅ Excel généré :", path)