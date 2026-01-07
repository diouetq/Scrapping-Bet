# Scrapping-Bet

Scrapping-Bet est un projet Python permettant de **scraper les cotes sportives** depuis plusieurs bookmakers (**Sportaza**, **Betify**, **Greenluck**) et de générer des fichiers Excel avec calculs de cotes, probabilités implicites, TRJ, Kelly et gains potentiels.

Ce projet est conçu pour être **propre, structuré et versionné sur GitHub**, avec un workflow clair pour exécuter, modifier et ajouter de nouveaux scrapers.

---

## ⚡ Fonctionnalités

- Scraping des cotes face-à-face pour différents sports.
- Support de plusieurs bookmakers.
- Export automatique des données dans un fichier Excel par compétition.
- Calcul des probabilités implicites, TRJ, Kelly et stakes.
- Organisation claire du projet pour faciliter l’évolution et la maintenance.

---

## 📂 Structure du projet

Scrapping-Bet/
│
├── src/
│ ├── run.py # Script principal pour lancer le scraping
│ ├── Excel_builder.py # Fonctions pour générer Excel
│ ├── Test_sportaza.py # Scraper Sportaza
│ ├── Test_Betify.py # Scraper Betify
│ └── Test_Greenluck.py # Scraper Greenluck
│
├── Extraction/ # Fichiers Excel générés (ignorés par GitHub)
├── requirements.txt # Dépendances Python
├── .gitignore # Fichiers à ignorer
└── README.md # Documentation

yaml
Copier le code

---

## 💻 Installation

1. **Cloner le projet depuis GitHub :**

```bash
git clone https://github.com/diouetq/Scrapping-Bet.git
cd Scrapping-Bet
Créer un environnement virtuel (recommandé) :

bash
Copier le code
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / Mac
python -m venv venv
source venv/bin/activate
Installer les dépendances :

bash
Copier le code
pip install -r requirements.txt
🚀 Utilisation
Choisir le scraper actif dans src/run.py :

python
Copier le code
# SCRAPER = scrape_sportaza
# SCRAPER = scrape_greenluck
# SCRAPER = scrape_betify
Configurer les paramètres Excel si besoin :

python
Copier le code
EXPORT_DIR = r"C:\Users\dioue\OneDrive\Bureau\Code Python\Scrapping-Bet\Extraction"
KELLY = 4      # Fraction de Kelly
STAKE = 20     # Mise en euros
Lancer le script principal :

bash
Copier le code
python src/run.py
Les fichiers Excel seront générés dans le dossier Extraction/.

Le nom du fichier suit le format : Extract_<Bookmaker>_YYYY-MM-DD.xlsx.

📊 Contenu des fichiers Excel
Chaque feuille correspond à une compétition et contient :

Colonne	Description
Extraction	Date et heure de l’extraction
Cutoff_<Bookmaker>	Date et heure du début de l’événement
Competition	Nom de la compétition
Evenement	Nom de l’événement
Competiteur_<Bookmaker>	Nom du compétiteur
Cote_<Bookmaker>	Cote associée
Cote_PS3838	Cote d’un autre bookmaker (placeholder)
TrueOdds_MPTO	Cote ajustée
ImpliedProb	Probabilité implicite
TrueProb_MPTO	Probabilité ajustée
TRJ	TRJ calculé
%_boost	Bonus éventuel
Kelly_<k>	Fraction Kelly
Stake_<n>	Mise
Potential_Payout	Gain potentiel
Surebet	Indicateur surebet
TRJ_Book	TRJ pour le bookmaker

🛠️ Ajouter un nouveau scraper
Placer le script Python dans src/.

Créer une fonction de scraping qui retourne un pandas.DataFrame avec les colonnes suivantes :

python
Copier le code
["Bookmaker", "Competition", "Extraction", "Cutoff", "Evenement", "Competiteur", "Cote"]
Importer la fonction dans src/run.py et ajouter une fonction run_<bookmaker>().

Décommenter la ligne correspondante dans run.py pour l’utiliser.

💡 Bonnes pratiques
Faire un commit pour chaque modification logique du projet.

Ne pas inclure les fichiers générés (Extraction/) ni les secrets (.env) sur GitHub.

Utiliser un environnement virtuel pour gérer les dépendances.

Mettre à jour requirements.txt si tu ajoutes une nouvelle librairie :

bash
Copier le code
pip freeze > requirements.txt
🔗 Liens utiles
GitHub Repository

Documentation Pandas

Documentation OpenPyXL