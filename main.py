import os
import sys
import threading
import time
from datetime import datetime, timezone, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID', 0))
BOT_NAME = "TechGeekZ Bot"
WEBAPP_URL = os.getenv('WEBAPP_URL', '')

IST = timezone(timedelta(hours=5, minutes=30))

def format_time():
    return datetime.now(IST).strftime('%d/%m/%Y %H:%M:%S IST')

def start_bot():
    from handlers.bot_handlers import BotHandlers
    from database.models import DatabaseManager

    print(f"🤖 Starting {BOT_NAME} bot...")

    db = DatabaseManager()
    db.add_user_to_whitelist(BOT_OWNER_ID, "Owner", "Bot Owner")

    bot_handler = BotHandlers(db)
    bot = bot_handler.bot

    try:
        deployment_message = f"""{BOT_NAME}

Time: {format_time()}
Owner: Owner {BOT_OWNER_ID}
Dashboard: Online

Bot is active. Send /start to begin
Send /help for all commands"""

        bot.send_message(BOT_OWNER_ID, deployment_message)
        print("📨 Deployment message sent to owner")
    except Exception as e:
        print(f"⚠️ Deployment message failed: {e}")

    bot.infinity_polling(none_stop=True, interval=2, timeout=20)

def start_webapp():
    import subprocess
    import sys
    print(f"🌐 Starting Flask webapp...")
    subprocess.run([sys.executable, 'webapp.py'])

if __name__ == '__main__':
    if not BOT_TOKEN or not BOT_OWNER_ID:
        print("❌ BOT_TOKEN or BOT_OWNER_ID not set. Exiting.")
        exit(1)

    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()

    time.sleep(5)  # give bot time to init

    start_webapp()
