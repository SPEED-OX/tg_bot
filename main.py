import os
import sys
import threading
import time
import logging
from datetime import datetime, timezone, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Enhanced logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID', 0))
BOT_NAME = "TechGeekZ Bot"
WEBAPP_URL = os.getenv('WEBAPP_URL', '')

IST = timezone(timedelta(hours=5, minutes=30))

def format_deployment_time():
    """Format time for deployment message"""
    return datetime.now(IST).strftime('%d/%m/%Y %H:%M:%S IST')

def get_dashboard_status():
    """Get dashboard status"""
    return "Online" if WEBAPP_URL else "Offline"

def get_owner_telegram_info(bot):
    """Get REAL owner telegram info via API"""
    try:
        chat = bot.get_chat(BOT_OWNER_ID)
        first_name = chat.first_name or ""
        last_name = chat.last_name or ""
        username = chat.username or ""
        
        # Full telegram nickname + @username
        full_name = f"{first_name} {last_name}".strip()
        if username:
            return f"{full_name} @{username}"
        else:
            return full_name or f"User {BOT_OWNER_ID}"
    except Exception as e:
        logger.error(f"Failed to get owner info: {e}")
        return f"Owner {BOT_OWNER_ID}"

class BotManager:
    """Advanced bot lifecycle manager"""
    
    def __init__(self):
        self.bot_handler = None
        self.db = None
        self.is_running = False
    
    def initialize_bot(self):
        """Initialize bot with error handling and recovery"""
        from handlers.bot_handlers import BotHandlers
        from database.models import DatabaseManager
        
        try:
            logger.info(f"🤖 Initializing {BOT_NAME}...")
            
            self.db = DatabaseManager()
            self.db.add_user_to_whitelist(BOT_OWNER_ID, "Owner", "Bot Owner")
            
            self.bot_handler = BotHandlers(self.db)
            logger.info("✅ Bot handler initialized successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Bot initialization failed: {e}")
            return False
    
    def send_deployment_notification(self):
        """Send EXACT deployment notification format with REAL owner info"""
        if not self.bot_handler:
            return False
            
        try:
            # Get REAL owner info from Telegram API
            owner_info = get_owner_telegram_info(self.bot_handler.bot)
            
            # EXACT deployment message format as requested
            deployment_message = f"""TechGeekZ Bot

Time: {format_deployment_time()}
Owner: {owner_info}
Dashboard: {get_dashboard_status()}

Bot is active. Send /start to begin
Send /help for all commands"""

            self.bot_handler.bot.send_message(BOT_OWNER_ID, deployment_message)
            logger.info("📨 Deployment notification sent with real owner info")
            return True
            
        except Exception as e:
            logger.error(f"⚠️ Deployment notification failed: {e}")
            return False
    
    def start_polling(self):
        """Start bot polling with recovery"""
        if not self.bot_handler:
            logger.error("❌ Bot handler not initialized")
            return
        
        self.is_running = True
        logger.info("🚀 Starting bot polling...")
        
        while self.is_running:
            try:
                self.bot_handler.bot.infinity_polling(none_stop=True, interval=2, timeout=20)
            except Exception as e:
                logger.error(f"❌ Polling error: {e}")
                logger.info("🔄 Restarting bot in 10 seconds...")
                time.sleep(10)
                if self.is_running:
                    logger.info("🔄 Reconnecting...")
    
    def stop(self):
        """Graceful shutdown"""
        self.is_running = False
        logger.info("⏹️ Bot shutdown initiated")

def start_bot():
    """Enhanced bot startup function"""
    bot_manager = BotManager()
    
    if not bot_manager.initialize_bot():
        logger.error("❌ Failed to initialize bot. Exiting.")
        return
    
    bot_manager.send_deployment_notification()
    bot_manager.start_polling()

def start_webapp():
    """Enhanced webapp startup"""
    import subprocess
    import sys
    
    logger.info(f"🌐 Starting Flask webapp...")
    try:
        subprocess.run([sys.executable, 'webapp.py'])
    except Exception as e:
        logger.error(f"❌ Webapp startup failed: {e}")

if __name__ == '__main__':
    if not BOT_TOKEN or not BOT_OWNER_ID:
        logger.error("❌ BOT_TOKEN or BOT_OWNER_ID not set. Exiting.")
        exit(1)

    # Start bot in daemon thread
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()

    time.sleep(5)  # Allow bot initialization
    start_webapp()
