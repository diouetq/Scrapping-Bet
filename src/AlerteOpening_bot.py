# -*- coding: utf-8 -*-
"""
Bot Telegram pour tester Sportaza avec sports par défaut
"""

import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from Scrap_Sportaza import scrape_sportaza  # ton script existant

# --- CONFIGURATION --- #
TOKEN = "8431986297:AAG5vSrmNaRgHuEH26QCMphwM3VTPje8ylo"

# Liste par défaut des sports (IDs de Sportaza)
DEFAULT_SPORTS = ["1359","923","924","1380","1405","1406","904","1411","1412","672"]

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- COMMANDES --- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Bienvenue sur AlerteOpening_bot !\n"
        "Commandes disponibles :\n"
        "- /test : tester le bot\n"
        "- /competitions : lister les compétitions disponibles pour les sports par défaut\n"
        "Exemple pour tester avec d'autres sports : /competitions 1359 923"
    )

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔔 Le bot fonctionne correctement !")

async def competitions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Récupère les compétitions et les envoie sur Telegram"""
    await update.message.reply_text("⏳ Récupération des compétitions...")

    try:
        # Utilise la liste par défaut si aucun argument n'est fourni
        if context.args:
            Id_sport = context.args  # IDs fournis par l'utilisateur
        else:
            Id_sport = DEFAULT_SPORTS  # Liste par défaut

        df = scrape_sportaza(Id_sport=Id_sport)
        competitions = df["Competition"].dropna().unique().tolist()

        if not competitions:
            await update.message.reply_text("Aucune compétition trouvée pour le moment.")
            return

        # Créer un message avec la liste
        msg = "🏆 Compétitions disponibles :\n"
        msg += "\n".join(f"- {c}" for c in competitions[:20])  # limite à 20 pour Telegram
        if len(competitions) > 20:
            msg += f"\n... et {len(competitions)-20} autres"

        await update.message.reply_text(msg)

    except Exception as e:
        await update.message.reply_text(f"❌ Erreur lors de la récupération : {e}")

# --- LANCEMENT DU BOT --- #

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test))
    app.add_handler(CommandHandler("competitions", competitions))

    print("Bot lancé...")
    app.run_polling(poll_interval=3)
