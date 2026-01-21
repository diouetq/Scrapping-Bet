# -*- coding: utf-8 -*-
"""
Bot Telegram pour lire les compétitions du dernier data.json mis à jour par GitHub Actions
"""

import json
from pathlib import Path
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os

# --- CONFIGURATION --- #
TOKEN = os.environ.get("TELEGRAM_TOKEN")  # à mettre dans les secrets ou .env
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data.json"

logging.basicConfig(level=logging.INFO)

# --- HELPERS --- #
def load_data():
    """Charge le data.json contenant les compétitions"""
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"competitions": []}

# --- COMMANDES BOT --- #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Bienvenue sur AlerteOpening_bot !\n\n"
        "Commandes disponibles :\n"
        "- /test : tester le bot\n"
        "- /competitions : lister les compétitions disponibles (dernier data.json)"
    )

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔔 Le bot fonctionne correctement !")

async def competitions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Afficher les compétitions du dernier data.json"""
    data = load_data()
    comps = data.get("competitions", [])
    
    if not comps:
        await update.message.reply_text("⚠️ Aucune compétition disponible pour le moment.")
        return

    msg = "🏆 Compétitions disponibles :\n" + "\n".join(f"- {c}" for c in comps[:30])
    if len(comps) > 30:
        msg += f"\n... et {len(comps)-30} autres"

    await update.message.reply_text(msg)

# --- LANCEMENT DU BOT --- #
if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test))
    app.add_handler(CommandHandler("competitions", competitions))

    print("Bot lancé et prêt à répondre à Telegram !")
    app.run_polling(poll_interval=3)
