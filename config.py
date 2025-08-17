import os
from telethon.sessions import StringSession
from telethon import TelegramClient

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load from Railway environment variables
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
SESSION_STRING = os.getenv("SESSION_STRING", None)  # Optional if you use a string session

# Database
DB_PATH = os.path.join(BASE_DIR, "database.db")

# Create Telegram client (using session string if provided)
if SESSION_STRING:
    user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
else:
    # fallback: if SESSION_STRING not set, will use .session file
    USER_SESSION = os.path.join(BASE_DIR, "user_account")
    user_client = TelegramClient(USER_SESSION, API_ID, API_HASH)

# Optional: bot client
if BOT_TOKEN:
    bot_client = TelegramClient("bot_account", API_ID, API_HASH).start(bot_token=BOT_TOKEN)
else:
    bot_client = None
