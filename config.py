import os

# Base directory (where this config.py is located)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# API credentials
API_ID = 23940372
API_HASH = "8caf9cc524474491f7f525f9d48c4b00"
BOT_TOKEN = "7667963218:AAEpXQmQXFTZL5n0xYDeStZJZ1NVQd3l0Fc"

# Paths
USER_SESSION = os.path.join(BASE_DIR, "user_account")  # no .session extension needed
BOT_SESSION = os.path.join(BASE_DIR, "bot_account")
DB_PATH = os.path.join(BASE_DIR, "monitor.db")

# Default keywords
DEFAULT_KEYWORDS = ["mediafire.com"]
