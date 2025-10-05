"""
Configuration settings for Controller Bot
"""
import os
from datetime import timezone, timedelta

# Bot configuration
BOT_TOKEN ="""
ChatAudit Bot - Configuration
Clean configuration management with proper defaults
"""
import os
import pytz
from datetime import datetime

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID', 0))
BOT_NAME = "ChatAudit Bot"

# Web Configuration  
SECRET_KEY = os.getenv('SECRET_KEY', 'chataudit-default-secret-key-2024')
WEBAPP_URL = os.getenv('WEBAPP_URL', '')
PORT = int(os.getenv('PORT', 8080))

# Timezone Configuration
IST = pytz.timezone('Asia/Kolkata')

# Database Configuration
DATABASE_PATH = "chataudit.db"

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Bot Settings
MAX_MESSAGE_LENGTH = 4096
POLLING_INTERVAL = 2
POLLING_TIMEOUT = 20

# Scheduler Settings
SCHEDULER_CHECK_INTERVAL = 30  # seconds

# Validation
def validate_config():
    """Validate configuration"""
    errors = []
    
    if not BOT_TOKEN or BOT_TOKEN == 'your-bot-token-here':
        errors.append("BOT_TOKEN is required")
    
    if not BOT_OWNER_ID:
        errors.append("BOT_OWNER_ID is required")
    
    if WEBAPP_URL and not WEBAPP_URL.startswith('https://'):
        errors.append("WEBAPP_URL must start with https://")
    
    return errors

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
 os.getenv('BOT_TOKEN', 'your-bot-token-here')
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID', '0'))
BOT_NAME = "ChatAudit Bot"
BOT_DESCRIPTION = "Advanced Telegram channel management bot"
# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///controller_bot.db')

# Web app configuration
WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://your-railway-app.railway.app')
PORT = int(os.getenv('PORT', 5000))
SECRET_KEY = os.getenv('SECRET_KEY', 'change-this-secret-key-123')

# Timezone configuration
IST = timezone(timedelta(hours=5, minutes=30))  # Indian Standard Time

# Bot settings
MAX_MESSAGE_LENGTH = 4096
MAX_CAPTION_LENGTH = 1024
TIMER_CHECK_INTERVAL = 3600  # 1 hour in seconds
NEAR_TIME_CHECK_INTERVAL = 900  # 15 minutes in seconds
DAILY_CHECK_TIME = "00:00"  # Check for daily schedules

# Supported media types
SUPPORTED_PHOTO_TYPES = ['photo']
SUPPORTED_VIDEO_TYPES = ['video']
SUPPORTED_DOCUMENT_TYPES = ['document', 'audio', 'voice', 'video_note', 'sticker']
