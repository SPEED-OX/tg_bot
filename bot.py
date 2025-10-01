from telegram.ext import Application, CommandHandler
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update, context):
    await update.message.reply_text("Hello! Bot is running ✅")

def run_bot():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not set in env vars!")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    app.run_polling()   # no Updater here