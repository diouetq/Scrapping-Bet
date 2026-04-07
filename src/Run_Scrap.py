# -*- coding: utf-8 -*-
"""
Created on Sat Dec 27 19:10:34 2025

@author: dioue
"""

from Excel_builder import build_excel

from Scrap_Sportaza import scrape_sportaza
from Scrap_Greenluck import scrape_greenluck
from Scrap_Betify import scrape_betify
from Scrap_MyStake import scrape_mystake

# =========================
# 🔽 DEF RUN : choisir les sports
# =========================


def run_sportaza():
    return scrape_sportaza(
        Id_sport=["1248","1596","1359","1373","1393","1387", "904", "923", "924", "1405", "1406","1407","1408", "1415","2245", "1356", "1659", "893","2239","2245","1410","1409","1402"]
    )


def run_greenluck():
    return scrape_greenluck(
        Id_sport=["14", "15", "16", "17", "27","28","29","31", "32"]
    )


def run_betify():
    return scrape_betify(
        Id_sport=["90","40","30","17","43", "44","45", "46", "48","49","50","102","103","105","36","190"],use_tor=False
    )


def run_mystake():
    return scrape_mystake(
        Id_sport=["16"] #77 F1
    )


# =========================
# 🔽 CHOIX DU BOOKMAKER
# =========================


SCRAPER = run_betify
# SCRAPER = run_greenluck
# SCRAPER = run_betify
# SCRAPER = run_sportaza
# SCRAPER = run_mystake

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