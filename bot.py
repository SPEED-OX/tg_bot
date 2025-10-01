import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters

def run_bot():
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not found in environment variables!")

    app = Application.builder().token(BOT_TOKEN).build()

    # Example /start command
    async def start(update, context):
        await update.message.reply_text("🤖 Bot is alive and running!")

    # Example echo handler
    async def echo(update, context):
        await update.message.reply_text(update.message.text)

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Start bot
    app.run_polling()