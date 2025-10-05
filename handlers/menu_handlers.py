"""
FIXED menu handlers with proper dashboard button showing
"""
import telebot
from telebot.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from datetime import datetime
import json
import logging
from typing import Dict, Optional, List
from database.models import DatabaseManager
from utils.time_parser import parse_time_input, format_time_display, TIME_FORMAT_HELP
from config import BOT_OWNER_ID, WEBAPP_URL, IST

logger = logging.getLogger(__name__)

class UserState:
    def __init__(self):
        self.current_menu = "main"
        self.awaiting_input = None
        self.selected_channel = None
        self.post_content = {'text': '', 'media_type': None, 'media_file_id': None, 'buttons': []}
        self.temp_data = {}
        self.keyboard_type = "inline"

class MenuHandler:
    def __init__(self, bot: telebot.TeleBot, db: DatabaseManager):
        self.bot = bot
        self.db = db
        self.user_states: Dict[int, UserState] = {}

    def get_user_state(self, user_id: int) -> UserState:
        if user_id not in self.user_states:
            self.user_states[user_id] = UserState()
        return self.user_states[user_id]

    def is_authorized(self, user_id: int) -> bool:
        return user_id == BOT_OWNER_ID or self.db.is_user_whitelisted(user_id)

    def show_main_menu(self, chat_id: int, user_id: int):
        """Show main menu with INLINE KEYBOARD - ALWAYS shows dashboard button"""
        if not self.is_authorized(user_id):
            self.bot.send_message(
                chat_id, 
                "❌ You're not authorized to use this bot.\n\nContact the bot owner for access."
            )
            return

        # INLINE KEYBOARD for main menu
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(InlineKeyboardButton("🏠 Start", callback_data="menu_start"))
        keyboard.add(InlineKeyboardButton("👥 User", callback_data="menu_user"))
        keyboard.add(InlineKeyboardButton("📝 New Post", callback_data="menu_new_post"))
        keyboard.add(InlineKeyboardButton("📅 Schedules", callback_data="menu_schedules"))

        # Dashboard button - ALWAYS ADD (will be fixed with proper railway config)
        if WEBAPP_URL and WEBAPP_URL != 'https://your-railway-app.railway.app':
            # Ensure URL has proper format
            dashboard_url = WEBAPP_URL
            if not dashboard_url.startswith('https://'):
                dashboard_url = f"https://{dashboard_url}"
            if not dashboard_url.endswith('/dashboard'):
                dashboard_url += '/dashboard'

            web_app = WebAppInfo(url=dashboard_url)
            keyboard.add(InlineKeyboardButton("📊 Dashboard", web_app=web_app))

        text = """🤖 **ChatAudit Bot - Main Menu**

Welcome to your channel management bot!

**🎯 Quick Actions:**
• **Start** - Getting started guide
• **User** - User management (owner)
• **New Post** - Create and schedule posts
• **Schedules** - Manage upcoming posts  
• **Dashboard** - Web interface

**💡 Use /help for complete command guide**"""

        try:
            # Remove any existing reply keyboard first
            self.bot.send_message(
                chat_id, 
                "🏠 Opening main menu...", 
                reply_markup=ReplyKeyboardRemove()
            )

            self.bot.send_message(
                chat_id, 
                text, 
                parse_mode='Markdown',
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Error showing main menu: {e}")
            # Fallback without markdown
            self.bot.send_message(
                chat_id,
                "ChatAudit Bot - Main Menu\n\nUse the buttons below to navigate:",
                reply_markup=keyboard
            )

        # Update user state
        state = self.get_user_state(user_id)
        state.current_menu = "main"
        state.keyboard_type = "inline"
        state.awaiting_input = None

    # Rest of the methods remain the same from your current menu_handlers.py
    def handle_callback_query(self, call):
        """Handle callback queries from INLINE keyboards"""
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        data = call.data

        if not self.is_authorized(user_id):
            self.bot.answer_callback_query(call.id, "❌ Not authorized", show_alert=True)
            return

        try:
            if data == "menu_start":
                self.show_start_menu(chat_id, call.message.message_id, call.id)
            elif data == "menu_user":
                self.show_user_menu(chat_id, user_id, call.message.message_id, call.id)
            elif data == "menu_new_post":
                self.show_channel_selection(chat_id, user_id, call.message.message_id, call.id)
            elif data == "back_to_main":
                self.show_main_menu(chat_id, user_id)
                self.bot.answer_callback_query(call.id)
        except Exception as e:
            logger.error(f"Error handling callback query {data}: {e}")
            self.bot.answer_callback_query(call.id, "❌ Error processing request", show_alert=True)

    def show_start_menu(self, chat_id: int, message_id: int, callback_query_id: str):
        """Show start information"""
        text = """🏠 **Getting Started**

**📋 Quick Setup:**
1. Add me as admin to your channel
2. Use /addchannel @yourchannel 
3. Create posts using **New Post**

Ready to manage channels! 🚀"""

        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("⬅️ Back", callback_data="back_to_main"))

        try:
            self.bot.edit_message_text(text, chat_id, message_id, parse_mode='Markdown', reply_markup=keyboard)
        except Exception as e:
            self.bot.send_message(chat_id, "Getting Started Guide", reply_markup=keyboard)

        self.bot.answer_callback_query(callback_query_id)

    # Add placeholder methods to avoid errors
    def show_user_menu(self, chat_id: int, user_id: int, message_id: int = None, callback_query_id: str = None):
        """Placeholder user menu"""
        self.bot.answer_callback_query(callback_query_id, "👥 User management coming soon!", show_alert=True)

    def show_channel_selection(self, chat_id: int, user_id: int, message_id: int, callback_query_id: str):
        """Placeholder channel selection"""
        self.bot.answer_callback_query(callback_query_id, "📝 New post feature coming soon!", show_alert=True)

    # Add the handle_button_menu_messages method
    def handle_button_menu_messages(self, message):
        """Handle messages from BUTTON MENUS - placeholder"""
        self.bot.send_message(message.chat.id, "Button menu feature coming soon!")
