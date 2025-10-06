"""
TechGeekZ Bot - Simple Bot Handlers
Clean bot command handling
"""
import telebot
from telebot import types
from telebot.types import BotCommand
import os
from datetime import datetime, timezone, timedelta

# Simple config
BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID', 0))
BOT_NAME = "TechGeekZ Bot"
WEBAPP_URL = os.getenv('WEBAPP_URL', '')
IST = timezone(timedelta(hours=5, minutes=30))

def format_start_time():
    return datetime.now(IST).strftime('%d/%m/%Y | %H:%M')

class BotHandlers:
    def __init__(self, database_manager):
        self.db = database_manager
        self.bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
        
        # Update commands
        self.update_commands()
        
        # Register handlers
        self.register_handlers()
    
    def update_commands(self):
        """Update bot commands"""
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
            print("✅ Commands updated")
        except Exception as e:
            print(f"❌ Command update failed: {e}")
    
    def register_handlers(self):
        """Register all handlers"""
        
        @self.bot.message_handler(commands=['start'])
        def handle_start(message):
            user_id = message.from_user.id
            username = message.from_user.username or "User"
            
            if not self.db.is_user_whitelisted(user_id):
                self.bot.reply_to(message, "You are not authorized to use this bot.")
                return
            
            self.db.add_user_to_whitelist(user_id, username, message.from_user.first_name)
            
            start_message = f"""Welcome to {BOT_NAME}

Hello @{username}! What new are we thinking today..

Owner: @Owner
Dashboard: Online
Time: {format_start_time()}

Bot is active. Send /help for all commands"""

            self.bot.send_message(message.chat.id, start_message)
            self.show_main_menu(message.chat.id)
        
        @self.bot.message_handler(commands=['help'])
        def handle_help(message):
            if not self.db.is_user_whitelisted(message.from_user.id):
                self.bot.reply_to(message, "You are not authorized.")
                return
            
            help_text = f"""{BOT_NAME} - Available Commands

/start - start the bot
/user - user settings
/newpost - create posts
/schedules - schedule settings
/dashboard - web dashboard
/permit <userid> - add user to whitelist
/remove <userid> - remove user from whitelist

Use menu buttons or type commands."""
            
            self.bot.send_message(message.chat.id, help_text)
        
        @self.bot.message_handler(commands=['dashboard'])
        def handle_dashboard(message):
            if not self.db.is_user_whitelisted(message.from_user.id):
                self.bot.reply_to(message, "You are not authorized.")
                return
            
            if WEBAPP_URL:
                dashboard_url = f"{WEBAPP_URL}/dashboard"
                self.bot.send_message(message.chat.id, f"Dashboard: {dashboard_url}")
            else:
                self.bot.reply_to(message, "Dashboard not available.")
        
        @self.bot.message_handler(commands=['user'])
        def handle_user(message):
            if message.from_user.id != BOT_OWNER_ID:
                self.bot.reply_to(message, "Owner only.")
                return
            
            users = self.db.get_whitelisted_users()
            user_list = f"Whitelisted Users ({len(users)}):\n\n"
            
            for user in users:
                user_id, username, first_name = user[0], user[1], user[2]
                name = first_name or "Unknown"
                uname = f"@{username}" if username else "No username"
                user_list += f"{name} {uname}\nID: {user_id}\n\n"
            
            self.bot.send_message(message.chat.id, user_list)
        
        @self.bot.message_handler(commands=['permit'])
        def handle_permit(message):
            if message.from_user.id != BOT_OWNER_ID:
                self.bot.reply_to(message, "Owner only.")
                return
            
            parts = message.text.split()
            if len(parts) == 2:
                try:
                    user_id = int(parts[1].replace('-', ''))
                    self.db.add_user_to_whitelist(user_id)
                    self.bot.reply_to(message, f"User {user_id} permitted!")
                except:
                    self.bot.reply_to(message, "Invalid user ID.")
            else:
                self.bot.reply_to(message, "Format: /permit <user_id>")
        
        @self.bot.message_handler(commands=['remove'])
        def handle_remove(message):
            if message.from_user.id != BOT_OWNER_ID:
                self.bot.reply_to(message, "Owner only.")
                return
            
            parts = message.text.split()
            if len(parts) == 2:
                try:
                    user_id = int(parts[1].replace('-', ''))
                    if user_id != BOT_OWNER_ID:
                        self.db.remove_user_from_whitelist(user_id)
                        self.bot.reply_to(message, f"User {user_id} removed!")
                    else:
                        self.bot.reply_to(message, "Cannot remove owner!")
                except:
                    self.bot.reply_to(message, "Error removing user.")
            else:
                self.bot.reply_to(message, "Format: /remove <user_id>")
        
        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_callback(call):
            if not self.db.is_user_whitelisted(call.from_user.id):
                self.bot.answer_callback_query(call.id, "Not authorized")
                return
            
            self.bot.answer_callback_query(call.id)
    
    def show_main_menu(self, chat_id):
        """Simple main menu"""
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(types.InlineKeyboardButton("start", callback_data="start"))
        keyboard.row(types.InlineKeyboardButton("user", callback_data="user"))
        keyboard.row(types.InlineKeyboardButton("newpost", callback_data="newpost"))
        keyboard.row(types.InlineKeyboardButton("schedules", callback_data="schedules"))
        
        if WEBAPP_URL:
            dashboard_url = f"{WEBAPP_URL}/dashboard"
            keyboard.row(types.InlineKeyboardButton("dashboard", url=dashboard_url))
        
        self.bot.send_message(chat_id, "Main Menu:", reply_markup=keyboard)
