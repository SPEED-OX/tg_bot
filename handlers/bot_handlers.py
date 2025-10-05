"""
ChatAudit Bot - Bot Command Handlers
Complete command handling with organized imports
"""
import telebot
from telebot import types
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import BOT_TOKEN, BOT_OWNER_ID, BOT_NAME, IST, WEBAPP_URL
from handlers.menu_handlers import MenuHandler

class BotHandlers:
    def __init__(self, database_manager):
        self.db = database_manager
        self.bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
        self.menu_handler = MenuHandler(self.bot, self.db)
        self.user_states = {}
        
        # Register handlers
        self.register_handlers()
        
    def register_handlers(self):
        """Register all bot command handlers"""
        
        @self.bot.message_handler(commands=['start'])
        def handle_start(message):
            user_id = message.from_user.id
            username = message.from_user.username
            first_name = message.from_user.first_name
            
            # Check if user is authorized
            if not self.db.is_user_whitelisted(user_id):
                self.bot.reply_to(message, 
                    "❌ You are not authorized to use this bot. Contact the administrator.")
                return
            
            # Update user info in database
            self.db.add_user_to_whitelist(user_id, username, first_name)
            
            # Send welcome message with main menu
            welcome_text = f"""🤖 **Welcome to {BOT_NAME}**

Hello {first_name}! You are authorized to use this bot.

**Available Commands:**
• /help - Show detailed help and commands
• Use the menu below to navigate

**Current Time (IST):** {datetime.now(IST).strftime('%d/%m %H:%M')}"""

            self.menu_handler.show_main_menu(message.chat.id, welcome_text)

        @self.bot.message_handler(commands=['help'])
        def handle_help(message):
            user_id = message.from_user.id
            
            if not self.db.is_user_whitelisted(user_id):
                self.bot.reply_to(message, "❌ You are not authorized to use this bot.")
                return
            
            help_text = f"""📖 **{BOT_NAME} - Complete Guide**

**🏠 Main Menu Navigation:**
• Start - Return to main menu
• User - User management (Owner only)
• New Post - Create and schedule posts  
• Schedules - View and manage scheduled posts
• Dashboard - Open web dashboard

**👥 User Management (Owner Only):**
• Users - List all whitelisted users
• Permit <user_id> - Add user to whitelist (ignores - signs)
• Remove <user_id> - Remove user from whitelist

**📝 Post Creation:**
1. Select "New Post" → Choose channel
2. Send your content (text, media, or both)
3. Choose action:
   • Schedule Post - Format: dd/mm hh:mm (5/10 15:00) or hh:mm (15:00)
   • Self-Destruct - Same format, auto-delete after posting
   • Post Now - Instant posting

**📅 Schedule Management:**
• View scheduled posts and their timings
• View self-destruct posts and timings
• Cancel scheduled or self-destruct posts

**🕐 Time Format:**
• dd/mm hh:mm - Specific date (5/10 15:00 = 5th Oct 3:00 PM)
• hh:mm - Same day (15:00 = 3:00 PM today)
• All times in IST (Indian Standard Time)

**📊 Dashboard:**
Web interface for detailed management and statistics.

**Current Time (IST):** {datetime.now(IST).strftime('%d/%m/%Y %H:%M')}"""

            self.bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

        @self.bot.message_handler(commands=['addchannel'])
        def handle_add_channel(message):
            user_id = message.from_user.id
            
            if not self.db.is_user_whitelisted(user_id):
                self.bot.reply_to(message, "❌ You are not authorized to use this bot.")
                return
            
            try:
                args = message.text.split()
                if len(args) != 2:
                    self.bot.reply_to(message, 
                        "**Usage:** /addchannel @channelname\n\n**Example:** /addchannel @mychannel")
                    return
                
                channel_username = args[1].replace('@', '')
                channel_id = hash(channel_username) % 1000000
                
                self.db.add_channel(channel_id, f"@{channel_username}", channel_username, user_id)
                self.bot.reply_to(message, f"✅ Channel @{channel_username} added successfully!")
                
            except Exception as e:
                self.bot.reply_to(message, f"❌ Error adding channel: {str(e)}")

        @self.bot.message_handler(commands=['channels'])
        def handle_list_channels(message):
            user_id = message.from_user.id
            
            if not self.db.is_user_whitelisted(user_id):
                self.bot.reply_to(message, "❌ You are not authorized to use this bot.")
                return
            
            channels = self.db.get_user_channels(user_id)
            
            if not channels:
                self.bot.reply_to(message, 
                    "📋 No channels added yet. Use /addchannel @channelname to add channels.")
                return
            
            channel_list = "📋 **Your Added Channels:**\n\n"
            for i, channel in enumerate(channels, 1):
                channel_list += f"{i}. {channel['name']} (@{channel['username']})\n"
            
            self.bot.send_message(message.chat.id, channel_list, parse_mode='Markdown')

        # Register callback query handler
        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_callback_query(call):
            self.menu_handler.handle_callback_query(call)
            
        # Register message handler for menu responses
        @self.bot.message_handler(func=lambda message: True)
        def handle_messages(message):
            self.menu_handler.handle_messages(message)
