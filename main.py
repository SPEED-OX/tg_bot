"""
main.py - CORRECTED IMPORTS for flat directory structure
Replace the import section at the top of your main.py with this:
"""
import os
import sys
import logging
import time
import signal
from datetime import datetime
import telebot
from telebot.types import BotCommand

# Corrected imports for flat structure
from config import BOT_TOKEN, BOT_OWNER_ID, IST, BOT_NAME
from models import DatabaseManager
from bot_handlers import BotHandlers

# Rest of your main.py code remains the same...

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import BOT_TOKEN, BOT_OWNER_ID, IST
from database.models import DatabaseManager
from handlers.bot_handlers import BotHandlers

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ControllerBot:
    def __init__(self):
        if not BOT_TOKEN or BOT_TOKEN == 'your-bot-token-here':
            raise ValueError("❌ BOT_TOKEN not set in environment variables")

        if not BOT_OWNER_ID:
            raise ValueError("❌ BOT_OWNER_ID not set in environment variables")

        # Initialize bot
        self.bot = telebot.TeleBot(BOT_TOKEN, parse_mode='Markdown')

        # Initialize database
        self.db = DatabaseManager()

        # Initialize handlers (includes scheduler)
        self.handlers = BotHandlers(self.bot, self.db)

        # Setup graceful shutdown
        self.setup_signal_handlers()

        logger.info("🤖 Controller Bot initialized successfully")

    def setup_signal_handlers(self):
        """Setup graceful shutdown handlers"""
        def signal_handler(signum, frame):
            logger.info(f"📞 Received signal {signum}, shutting down gracefully...")
            self.shutdown()
            sys.exit(0)

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

    def shutdown(self):
        """Graceful shutdown"""
        try:
            logger.info("⏹️ Stopping scheduler...")
            self.handlers.scheduler.stop()

            logger.info("🧹 Cleaning up database...")
            self.db.cleanup_completed_tasks(days_old=7)

            logger.info("✅ Shutdown completed")
        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")

    def run(self):
        """Start the bot with error recovery"""
        logger.info("🚀 Starting Controller Bot...")

        # Add owner to whitelist if not already
        if BOT_OWNER_ID:
            self.db.whitelist_user(BOT_OWNER_ID, True)
            logger.info(f"👑 Owner {BOT_OWNER_ID} added to whitelist")

        # Send startup notification to owner
        try:
            self.bot.send_message(
                BOT_OWNER_ID,
                f"🤖 **Controller Bot Started!**\n\n"
                f"**Time:** {datetime.now(IST).strftime('%d/%m/%Y %H:%M:%S IST')}\n"
                f"**Status:** ✅ Online\n"
                f"**Features:** All systems operational\n\n"
                f"Bot is ready to manage your channels! 🎯"
            )
        except Exception as e:
            logger.warning(f"⚠️ Could not send startup notification: {e}")

        # Start bot with automatic restart on errors
        retry_count = 0
        max_retries = 5

        while retry_count < max_retries:
            try:
                logger.info("🔄 Starting bot polling...")
                self.bot.infinity_polling(
                    timeout=30,
                    long_polling_timeout=10,
                    none_stop=True,
                    interval=2
                )

            except KeyboardInterrupt:
                logger.info("⌨️ Bot stopped by user")
                break

            except Exception as e:
                retry_count += 1
                logger.error(f"❌ Bot error (attempt {retry_count}/{max_retries}): {e}")

                if retry_count < max_retries:
                    wait_time = min(60 * retry_count, 300)  # Max 5 minutes
                    logger.info(f"⏳ Restarting in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error("💥 Max retries reached, shutting down")
                    break

        self.shutdown()

def main():
    """Main function"""
    try:
        # Environment check
        logger.info("🔍 Checking environment...")

        required_vars = ['BOT_TOKEN', 'BOT_OWNER_ID']
        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            logger.error(f"❌ Missing environment variables: {', '.join(missing_vars)}")
            logger.error("💡 Set these variables in Railway dashboard or .env file")
            sys.exit(1)

        # Initialize and run bot
        bot = ControllerBot()
        bot.run()

    except Exception as e:
        logger.error(f"💥 Critical error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
