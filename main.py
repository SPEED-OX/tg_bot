"""
TechGeekZ Bot - Main Entry Point
Deployment welcome message sent only ONCE to owner at deployment start.
"""
import os
import sys
import threading
from datetime import datetime
import requests

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import BOT_TOKEN, BOT_OWNER_ID, BOT_NAME, IST, WEBAPP_URL, format_time
from database.models import DatabaseManager
from handlers.bot_handlers import BotHandlers

def get_dashboard_status():
    """Check if dashboard is online"""
    try:
        if not WEBAPP_URL:
            return "Offline"
        response = requests.get(f"{WEBAPP_URL}/health", timeout=5)
        return "Online" if response.status_code == 200 else "Offline"
    except:
        return "Offline"

def get_owner_details(bot):
    """Get owner's Telegram full nickname and username"""
    try:
        owner_info = bot.get_chat(BOT_OWNER_ID)
        first = owner_info.first_name or ""
        last = owner_info.last_name or ""
        nickname = f"{first} {last}".strip()
        username = f"@{owner_info.username}" if owner_info.username else "NoUsername"
        return f"{nickname} {username}".strip()
    except:
        return f"Owner @{BOT_OWNER_ID}"

def main():
    print(f"🤖 Starting {BOT_NAME}...")

    # Initialize database
    db = DatabaseManager()
    print("✅ Database initialized")

    # Add owner to whitelist in database
    db.add_user_to_whitelist(BOT_OWNER_ID, "Owner", "Bot Owner")
    print(f"👑 Owner {BOT_OWNER_ID} added to whitelist")

    # Initialize bot handlers (this starts the bot’s TeleBot instance)
    bot_handlers = BotHandlers(db)
    bot = bot_handlers.bot

    print(f"🤖 Bot: @{bot.get_me().username}")
    print("✅ Bot handlers initialized")

    # Prepare deployment welcome message sent only to owner once
    owner_details = get_owner_details(bot)
    dashboard_status = get_dashboard_status()
    start_time = format_time()

    deployment_message = f"""{BOT_NAME}

Time: {start_time}
Owner: {owner_details}
Dashboard: {dashboard_status}

Bot is active. Send /start to begin
Send /help for all commands"""

    try:
        bot.send_message(BOT_OWNER_ID, deployment_message)
        print(f"📨 Deployment notification sent to owner {BOT_OWNER_ID}")
    except Exception as e:
        print(f"⚠️ Failed to send deployment notification: {e}")

    print("🚀 Starting bot polling...")

    try:
        bot.infinity_polling(none_stop=True, interval=2, timeout=20)
    except KeyboardInterrupt:
        print(f"\n🛑 {BOT_NAME} stopped by user")
    except Exception as e:
        print(f"❌ Bot polling error: {e}")

if __name__ == '__main__':
    main()
