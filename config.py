"""
Configuration settings for Controller Bot
"""
import os
from datetime import timezone, timedelta

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', 'your-bot-token-here')
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID', '0'))

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
