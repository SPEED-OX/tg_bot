"""
TechGeekZ Bot - Bot Command Handlers
/start sends custom welcome ONLY on command (not on deploy)
All commands updated automatically at startup
"""
import telebot
from telebot import types
from telebot.types import BotCommand
import sys
import os
import requests
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import BOT_TOKEN, BOT_OWNER_ID, BOT_NAME, IST, WEBAPP_URL, format_start_time
from handlers.menu_handlers import MenuHandler

class BotHandlers:
    def __init__(self, database_manager):
        self.db = database_manager
        self.bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
        self.menu_handler = MenuHandler(self.bot, self.db)
        self.user_states = {}
        
        # Auto-update all bot commands on startup deployment
        self.set_bot_commands()
        # Register all Telegram handlers
        self.register_handlers()
        
    def get_dashboard_status(self):
        try:
            if not WEBAPP_URL:
                return "Offline"
            r = requests.get(f"{WEBAPP_URL}/health", timeout=5)
            return "Online" if r.status_code == 200 else "Offline"
        except:
            return "Offline"
    
    def get_owner_username(self):
        try:
            owner_info = self.bot.get_chat(BOT_OWNER_ID)
            return f"@{owner_info.username}" if owner_info.username else f"{BOT_OWNER_ID}"
        except:
            return f"{BOT_OWNER_ID}"

    def set_bot_commands(self):
        try:
            commands = [
                BotCommand("start", "start the bot"),
                BotCommand("user", "user settings"),
                BotCommand("newpost", "create posts"),
                BotCommand("schedules", "schedule settings"),
                BotCommand("dashboard", "web dashboard"),
                BotCommand("permit", "add user to whitelist"),
                BotCommand("remove", "remove user from whitelist"),
            ]
            self.bot.set_my_commands(commands)
            print("✅ Bot commands updated on deployment")
            return True
        except Exception as e:
            print(f"⚠️ Failed to update commands: {e}")
            return False
    
    def register_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def handle_start(message):
            user_id = message.from_user.id
            username = message.from_user.username or "User"
            
            if not self.db.is_user_whitelisted(user_id):
                self.bot.reply_to(message, "You are not authorized to use this bot. Contact admin.")
                return
            
            self.db.add_user_to_whitelist(user_id, username, message.from_user.first_name)
            
            owner_username = self.get_owner_username()
            dashboard_status = self.get_dashboard_status()
            current_time = format_start_time()
            
            start_message = f"""Welcome to {BOT_NAME}

Hello @{username}! What new are we thinking today..

Owner: {owner_username}
Dashboard: {dashboard_status}
Time: {current_time}

Bot is active. Send /help for all commands
"""
            self.bot.send_message(message.chat.id, start_message)
            self.menu_handler.show_main_menu(message.chat.id)
        
        @self.bot.message_handler(commands=['help'])
        def handle_help(message):
            if not self.db.is_user_whitelisted(message.from_user.id):
                self.bot.reply_to(message, "You are not authorized to use this bot.")
                return
            
            help_text = f"""/start - start the bot
/user - user settings
/newpost - create posts
/schedules - schedule settings
/dashboard - web dashboard
/permit <userid> - add user to whitelist
/remove <userid> - remove user from whitelist

Use menu buttons or type commands directly."""
            self.bot.send_message(message.chat.id, help_text)
        
        # Register other commands similarly, all callable manually or from menu:
        # /user, /newpost, /schedules, /dashboard, /permit, /remove
        # Call corresponding menu_handler show functions or db update functions
        
        # ... your other handlers from previous code here ...
        
        @self.bot.message_handler(commands=['user'])
        def handle_user(message):
            if not self.db.is_user_whitelisted(message.from_user.id):
                self.bot.reply_to(message, "Unauthorized")
                return
            if message.from_user.id != BOT_OWNER_ID:
                self.bot.reply_to(message, "User management is owner only.")
                return
            self.menu_handler.show_user_menu(message.chat.id)
        
        @self.bot.message_handler(commands=['newpost'])
        def handle_newpost(message):
            if not self.db.is_user_whitelisted(message.from_user.id):
                self.bot.reply_to(message, "Unauthorized")
                return
            self.menu_handler.show_newpost_menu(message.chat.id)
        
        @self.bot.message_handler(commands=['schedules'])
        def handle_schedules(message):
            if not self.db.is_user_whitelisted(message.from_user.id):
                self.bot.reply_to(message, "Unauthorized")
                return
            self.menu_handler.show_schedules_menu(message.chat.id)
        
        @self.bot.message_handler(commands=['dashboard'])
        def handle_dashboard(message):
            if not self.db.is_user_whitelisted(message.from_user.id):
                self.bot.reply_to(message, "Unauthorized")
                return
            if WEBAPP_URL and WEBAPP_URL.startswith('https://'):
                dashboard_url = f"{WEBAPP_URL}/dashboard"
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(types.InlineKeyboardButton("Open Dashboard", web_app=types.WebApp(dashboard_url)))
                self.bot.send_message(message.chat.id, "Dashboard:", reply_markup=keyboard)
            else:
                self.bot.reply_to(message, "Dashboard not available.")
        
        @self.bot.message_handler(commands=['permit'])
        def handle_permit(message):
            if message.from_user.id != BOT_OWNER_ID:
                self.bot.reply_to(message, "Owner only.")
                return
            parts = message.text.split()
            if len(parts) != 2:
                self.bot.reply_to(message, "Format: /permit <user_id>")
                return
            try:
                user_id = int(parts[1].replace('-', ''))
                self.db.add_user_to_whitelist(user_id)
                self.bot.reply_to(message, f"User {user_id} permitted.")
            except:
                self.bot.reply_to(message, "Invalid user ID.")
        
        @self.bot.message_handler(commands=['remove'])
        def handle_remove(message):
            if message.from_user.id != BOT_OWNER_ID:
                self.bot.reply_to(message, "Owner only.")
                return
            parts = message.text.split()
            if len(parts) != 2:
                self.bot.reply_to(message, "Format: /remove <user_id>")
                return
            try:
                user_id = int(parts[1].replace('-', ''))
                if user_id == BOT_OWNER_ID:
                    self.bot.reply_to(message, "Cannot remove owner.")
                    return
                self.db.remove_user_from_whitelist(user_id)
                self.bot.reply_to(message, f"User {user_id} removed.")
            except:
                self.bot.reply_to(message, "Invalid user ID.")
        
        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_callback(call):
            self.menu_handler.handle_callback_query(call)
        
        @self.bot.message_handler(func=lambda message: True)
        def handle_messages(message):
            self.menu_handler.handle_messages(message)
