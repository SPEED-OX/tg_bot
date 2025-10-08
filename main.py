"""
ChatAudit Bot - Main Entry Point
Clean bot initialization with organized imports
"""
import os
import sys
import threading
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import BOT_TOKEN, BOT_OWNER_ID, BOT_NAME, IST
from database.models import DatabaseManager
from handlers.bot_handlers import BotHandlers

def main():
    """Main function to start the bot"""
    print(f"🤖 Starting {BOT_NAME}...")
    print(f"⏰ Time: {datetime.now(IST).strftime('%d/%m/%Y %H:%M:%S IST')}")
    
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
    
    # Send startup notification to owner
    try:
        startup_message = f"""🤖 **{BOT_NAME} Started Successfully!**

⏰ **Time:** {datetime.now(IST).strftime('%d/%m/%Y %H:%M:%S IST')}
🟢 **Status:** Online and Ready
👑 **Owner:** {BOT_OWNER_ID}
🌐 **Dashboard:** Available

The bot is now ready to use! Send /start to begin."""

        bot.send_message(BOT_OWNER_ID, startup_message, parse_mode='Markdown')
        print(f"📨 Startup notification sent to {BOT_OWNER_ID}")
    except Exception as e:
        print(f"⚠️ Could not send startup notification: {e}")
    
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
