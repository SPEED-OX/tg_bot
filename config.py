import os

BOT_TOKEN = os.getenv("BOT_TOKEN")   # Telegram Bot token
OWNER_ID = int(os.getenv("OWNER_ID", "0"))  # Bot owner Telegram user id
DATABASE = "bot.db"
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://yourapp.up.railway.app")