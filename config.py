import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Telegram API credentials
API_ID = 23940372  # your API ID (integer)
API_HASH = "8caf9cc524474491f7f525f9d48c4b00"  # your API hash (string)

# Bot credentials
BOT_TOKEN = "7667963218:AAEpXQmQXFTZL5n0xYDeStZJZ1NVQd3l0Fc"

# Session files
USER_SESSION = os.path.join(BASE_DIR, "user_account")  # without .session extension
BOT_SESSION = os.path.join(BASE_DIR, "bot_account")

# Database
DB_PATH = os.path.join(BASE_DIR, "database.db")