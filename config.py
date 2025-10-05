"""
TechGeekZ Bot - Configuration
Clean configuration management with proper defaults
"""
import os
from datetime import datetime, timezone, timedelta

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID', 0))
BOT_NAME = "TechGeekZ Bot"

# Web Configuration  
SECRET_KEY = os.getenv('SECRET_KEY', 'techgeekz-default-secret-key-2024')
WEBAPP_URL = os.getenv('WEBAPP_URL', '')
PORT = int(os.getenv('PORT', 8080))

# Timezone Configuration - Native Python
IST = timezone(timedelta(hours=5, minutes=30))

# Database Configuration
DATABASE_PATH = "techgeekz.db"

# Bot Settings
MAX_MESSAGE_LENGTH = 4096
POLLING_INTERVAL = 2
POLLING_TIMEOUT = 20

# Scheduler Settings
SCHEDULER_CHECK_INTERVAL = 30

# Get current IST time
def get_ist_time():
    """Get current IST time"""
    return datetime.now(IST)

# Format time for display
def format_time(dt=None):
    """Format datetime for display"""
    if dt is None:
        dt = get_ist_time()
    return dt.strftime('%d/%m/%Y %H:%M:%S IST')

# Format time for start command
def format_start_time(dt=None):
    """Format datetime for start command"""
    if dt is None:
        dt = get_ist_time()
    return dt.strftime('%d/%m/%Y | %H:%M')

# Configuration info for debugging
def get_config_info():
    """Get configuration info for debugging"""
    return {
        'bot_name': BOT_NAME,
        'has_token': bool(BOT_TOKEN and BOT_TOKEN != 'your-bot-token-here'),
        'has_owner': bool(BOT_OWNER_ID),
        'has_webapp_url': bool(WEBAPP_URL),
        'port': PORT,
        'timezone': str(IST),
        'current_time': format_time()
    }
