"""
TechGeekZ Bot - Main Entry Point
Clean bot initialization with custom deployment message
"""
import os
import sys
import threading
from datetime import datetime
import requests

# Add current directory to path for imports
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
        if response.status_code == 200:
            return "Online"
        else:
            return "Offline"
    except:
        return "Offline"

def get_owner_details(bot):
    """Get owner's Telegram details"""
    try:
        owner_info = bot.get_chat(BOT_OWNER_ID)
        nickname = f"{owner_info.first_name} {owner_info.last_name}".strip() if owner_info.last_name else owner_info.first_name
        username = f"@{owner_info.username}" if owner_info.username else "No username"
        return f"{nickname} {username}"
    except:
        return f"Owner {username}" if 'username' in locals() else "Owner (Unknown)"

def main():
    """Main function to start the bot"""
    print(f"🤖 Starting {BOT_NAME}...")
    
    # Initialize database
    db = DatabaseManager()
    print("✅ Database initialized")
    
    # Add owner to whitelist
    db.add_user_to_whitelist(BOT_OWNER_ID, "Owner", "Bot Owner")
    print(f"👑 Owner {BOT_OWNER_ID} added to whitelist")
    
    # Initialize bot handlers
    bot_handlers = BotHandlers(db)
    bot = bot_handlers.bot
    
    print(f"🤖 Bot: @{bot.get_me().username}")
    print("✅ Bot handlers initialized")
    
    # Get owner details and dashboard status
    owner_details = get_owner_details(bot)
    dashboard_status = get_dashboard_status()
    start_time = format_time()
    
    # Send custom deployment notification to owner
    try:
        deployment_message = f"""{BOT_NAME}

Time: {start_time}
Owner: {owner_details}
Dashboard: {dashboard_status}

Bot is active. Send /start to begin
Send /help for all commands"""

        bot.send_message(BOT_OWNER_ID, deployment_message)
        print(f"📨 Deployment notification sent to {BOT_OWNER_ID}")
    except Exception as e:
        print(f"⚠️ Could not send deployment notification: {e}")
    
    print("🚀 Starting bot polling...")
    
    # Start bot polling
    try:
        bot.infinity_polling(none_stop=True, interval=2, timeout=20)
    except KeyboardInterrupt:
        print(f"\n🛑 {BOT_NAME} stopped by user")
    except Exception as e:
        print(f"❌ Bot polling error: {e}")

if __name__ == '__main__':
    main()
