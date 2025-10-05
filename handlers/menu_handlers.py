"""
Menu handlers for Controller Bot - Corrected Imports
"""
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
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
        if not self.is_authorized(user_id):
            self.bot.send_message(chat_id, "❌ You're not authorized to use this bot.")
            return

        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(InlineKeyboardButton("🏠 Start", callback_data="menu_start"))

        if user_id == BOT_OWNER_ID:
            keyboard.add(InlineKeyboardButton("👥 User Management", callback_data="menu_user_mgmt"))

        keyboard.add(InlineKeyboardButton("📝 New Post", callback_data="menu_new_post"))
        keyboard.add(InlineKeyboardButton("📅 Schedules", callback_data="menu_schedules"))

        if WEBAPP_URL and WEBAPP_URL != 'https://your-railway-app.railway.app':
            web_app = WebAppInfo(url=f"{WEBAPP_URL}/dashboard")
            keyboard.add(InlineKeyboardButton("📊 Dashboard", web_app=web_app))

        text = """🤖 **Controller Bot - Main Menu**

Welcome to your advanced channel management bot!

**🎯 Quick Actions:**
• **New Post** - Create and schedule posts
• **Schedules** - Manage upcoming posts
• **Dashboard** - Web interface for advanced features

**💡 Need help?** Use /help for complete guide"""

        try:
            self.bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=keyboard)
        except Exception as e:
            logger.error(f"Error showing main menu: {e}")
            self.bot.send_message(chat_id, "❌ Error showing main menu. Please try /start again.")

        state = self.get_user_state(user_id)
        state.current_menu = "main"
        state.awaiting_input = None

    def handle_callback_query(self, call):
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        data = call.data

        if not self.is_authorized(user_id):
            self.bot.answer_callback_query(call.id, "❌ Not authorized", show_alert=True)
            return

        try:
            if data == "menu_start":
                self.show_start_info(chat_id, call.id)
            elif data == "menu_user_mgmt":
                self.show_user_management_menu(chat_id, user_id, call.id)
            elif data == "menu_new_post":
                self.show_channel_selection(chat_id, user_id, call.id)
            elif data == "menu_schedules":
                self.show_schedules_menu(chat_id, user_id, call.id)
            elif data == "back_to_main":
                self.show_main_menu(chat_id, user_id)
                self.bot.answer_callback_query(call.id)
        except Exception as e:
            logger.error(f"Error handling callback query {data}: {e}")
            self.bot.answer_callback_query(call.id, "❌ Error processing request", show_alert=True)

    def show_start_info(self, chat_id: int, callback_query_id: str):
        text = """🏠 **Getting Started**

**📋 Setup Steps:**
1. Add me as admin to your channel
2. Use `/addchannel @yourchannel`
3. Create posts using **New Post**

Ready to manage your channels! 🚀"""

        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("⬅️ Back", callback_data="back_to_main"))

        try:
            self.bot.edit_message_text(text, chat_id, reply_markup=keyboard, parse_mode='Markdown')
        except:
            self.bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=keyboard)

        self.bot.answer_callback_query(callback_query_id)

    def show_user_management_menu(self, chat_id: int, user_id: int, callback_query_id: str):
        if user_id != BOT_OWNER_ID:
            self.bot.answer_callback_query(callback_query_id, "❌ Owner access only", show_alert=True)
            return

        text = "👥 **User Management** - Coming soon!"
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("⬅️ Back", callback_data="back_to_main"))

        try:
            self.bot.edit_message_text(text, chat_id, reply_markup=keyboard)
        except:
            self.bot.send_message(chat_id, text, reply_markup=keyboard)

        self.bot.answer_callback_query(callback_query_id)

    def show_channel_selection(self, chat_id: int, user_id: int, callback_query_id: str):
        text = "📝 **New Post** - Coming soon!"
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("⬅️ Back", callback_data="back_to_main"))

        try:
            self.bot.edit_message_text(text, chat_id, reply_markup=keyboard)
        except:
            self.bot.send_message(chat_id, text, reply_markup=keyboard)

        self.bot.answer_callback_query(callback_query_id)

    def show_schedules_menu(self, chat_id: int, user_id: int, callback_query_id: str):
        text = "📅 **Schedules** - Coming soon!"
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("⬅️ Back", callback_data="back_to_main"))

        try:
            self.bot.edit_message_text(text, chat_id, reply_markup=keyboard)
        except:
            self.bot.send_message(chat_id, text, reply_markup=keyboard)

        self.bot.answer_callback_query(callback_query_id)
