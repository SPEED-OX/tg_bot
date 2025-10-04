"""
menu_handlers.py - CORRECTED IMPORTS for flat directory structure  
Replace the import section at the top of your menu_handlers.py with this:
"""
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from datetime import datetime
import json
import logging
from typing import Dict, Optional, List

# Corrected imports for flat structure
from models import DatabaseManager
from time_parser import parse_time_input, format_time_display, TIME_FORMAT_HELP
from config import BOT_OWNER_ID, WEBAPP_URL, IST

# Rest of your menu_handlers.py code remains the same...

logger = logging.getLogger(__name__)

class MenuState:
    """Track user menu state and temporary data"""
    def __init__(self):
        self.current_menu = "main"
        self.selected_channel = None
        self.post_content = {
            'text': '',
            'media_type': None,
            'media_file_id': None,
            'buttons': []
        }
        self.awaiting_input = None  # What input we're waiting for

class MenuHandler:
    def __init__(self, bot: telebot.TeleBot, db: DatabaseManager):
        self.bot = bot
        self.db = db
        self.user_states: Dict[int, MenuState] = {}  # In-memory state storage

    def get_user_state(self, user_id: int) -> MenuState:
        """Get or create user state"""
        if user_id not in self.user_states:
            self.user_states[user_id] = MenuState()
        return self.user_states[user_id]

    def is_authorized(self, user_id: int) -> bool:
        """Check if user is authorized"""
        return user_id == BOT_OWNER_ID or self.db.is_user_whitelisted(user_id)

    def show_main_menu(self, chat_id: int, user_id: int, message_id: int = None):
        """Show main inline keyboard menu"""
        if not self.is_authorized(user_id):
            text = """
🚫 **Access Denied**

You are not authorized to use this bot.
Contact the bot owner for access.

Use /help for more information.
            """
            if message_id:
                self.bot.edit_message_text(text, chat_id, message_id, parse_mode='Markdown')
            else:
                self.bot.send_message(chat_id, text, parse_mode='Markdown')
            return

        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(InlineKeyboardButton("🏠 Start", callback_data="menu_start"))
        keyboard.add(InlineKeyboardButton("👥 User Management", callback_data="menu_users"))
        keyboard.add(InlineKeyboardButton("📝 New Post", callback_data="menu_new_post"))
        keyboard.add(InlineKeyboardButton("📅 Schedules", callback_data="menu_schedules"))
        keyboard.add(InlineKeyboardButton("📊 Dashboard", web_app=WebAppInfo(url=f"{WEBAPP_URL}/dashboard")))

        text = """
🤖 **Controller Bot - Main Menu**

Select an option below:

🏠 **Start** - Welcome message
👥 **User Management** - Manage whitelist  
📝 **New Post** - Create and send posts
📅 **Schedules** - View and manage scheduled tasks
📊 **Dashboard** - Web interface

💡 **Available Commands:**
• /help - Show help
• /addchannel - Add a channel
• /channels - View your channels
        """

        if message_id:
            self.bot.edit_message_text(text, chat_id, message_id, parse_mode='Markdown', reply_markup=keyboard)
        else:
            self.bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=keyboard)

    def handle_callback_query(self, call):
        """Handle all callback queries for menu system"""
        user_id = call.from_user.id
        data = call.data
        chat_id = call.message.chat.id
        message_id = call.message.message_id

        try:
            if data == "menu_main":
                self.show_main_menu(chat_id, user_id, message_id)
            elif data == "menu_start":
                self.handle_start_callback(chat_id, user_id, message_id)
            # More handlers would be added here

            self.bot.answer_callback_query(call.id)

        except Exception as e:
            logger.error(f"Callback error: {e}")
            self.bot.answer_callback_query(call.id, text="❌ Error occurred", show_alert=True)

    def handle_start_callback(self, chat_id: int, user_id: int, message_id: int):
        """Handle start button callback"""
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("⬅️ Back to Menu", callback_data="menu_main"))

        text = """
🤖 **Welcome to Controller Bot!**

I am your advanced Telegram channel management assistant.

**✨ What I can do:**
• 📝 Create rich posts with media and buttons
• ⏰ Schedule posts for future publishing  
• 💣 Set self-destruct timers for messages
• 👥 Manage user permissions
• 📊 Web dashboard for advanced features

**📋 Quick Commands:**
• /help - Detailed help
• /addchannel - Add a channel to manage
• /channels - View your channels

**🚀 Getting Started:**
1. Add me as admin to your channel
2. Use /addchannel to register the channel
3. Return to menu and select "New Post"
4. Create amazing content!

Ready to manage your channels like a pro? 🎯
        """

        self.bot.edit_message_text(text, chat_id, message_id, parse_mode='Markdown', reply_markup=keyboard)
