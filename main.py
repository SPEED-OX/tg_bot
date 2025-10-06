"""
TechGeekZ Bot - Main Entry Point
Starts both bot and webapp in separate threads
"""
import os
import threading
import subprocess
import sys
from datetime import datetime, timezone, timedelta

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Simple config
BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID', 0))
BOT_NAME = "TechGeekZ Bot"
IST = timezone(timedelta(hours=5, minutes=30))

def format_time():
    return datetime.now(IST).strftime('%d/%m/%Y %H:%M:%S IST')

def start_bot():
    """Start bot using handlers"""
    try:
        from handlers.bot_handlers import BotHandlers
        from database.models import DatabaseManager
        
        print(f"🤖 Starting {BOT_NAME}...")
        
        # Initialize database
        db = DatabaseManager()
        db.add_user_to_whitelist(BOT_OWNER_ID, "Owner", "Bot Owner")
        
        # Start bot handlers
        bot_handlers = BotHandlers(db)
        bot = bot_handlers.bot
        
        print(f"🤖 Bot: @{bot.get_me().username}")
        
        # Send deployment message
        deployment_message = f"""{BOT_NAME}

Time: {format_time()}
Owner: Owner {BOT_OWNER_ID}
Dashboard: Online

Bot is active. Send /start to begin
Send /help for all commands"""

        try:
            bot.send_message(BOT_OWNER_ID, deployment_message)
            print("📨 Deployment notification sent")
        except Exception as e:
            print(f"⚠️ Notification failed: {e}")
        
        print("🚀 Bot polling started")
        bot.infinity_polling(none_stop=True)
        
    except Exception as e:
        print(f"❌ Bot error: {e}")

def start_webapp():
    """Start Flask webapp"""
    try:
        print("🌐 Starting Flask webapp...")
        subprocess.run([sys.executable, 'webapp.py'])
    except Exception as e:
        print(f"❌ Webapp error: {e}")

def clear_old_commands():
    """Clear old commands before starting"""
    try:
        import telebot
        temp_bot = telebot.TeleBot(BOT_TOKEN)
        temp_bot.delete_my_commands()
        print("🗑️ Cleared old commands before startup")
    except:
        print("⚠️ Could not clear old commands")

# Add this before starting bot in main.py
if __name__ == '__main__':
    if not BOT_TOKEN or not BOT_OWNER_ID:
        print("❌ Missing BOT_TOKEN or BOT_OWNER_ID")
        exit(1)
    
    # Clear old commands first
    clear_old_commands()
    
    print(f"🚀 Starting {BOT_NAME} services...")
    # ... rest of your code

    # Start bot in background thread
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    # Start webapp in main thread
    start_webapp()
