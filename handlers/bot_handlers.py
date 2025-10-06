"""
TechGeekZ Bot - Fixed Bot Handlers
Direct webapp opening + Force command updates
"""
import telebot
from telebot import types
from telebot.types import BotCommand, WebApp
import os
import time
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
        
        # FORCE UPDATE COMMANDS - Multiple attempts
        self.force_update_commands()
        
        # Register handlers
        self.register_handlers()
    
    def force_update_commands(self):
        """FORCE update bot commands with retries"""
        print("🔄 Force updating bot commands...")
        
        for attempt in range(3):
            try:
                print(f"Attempt {attempt + 1}/3 to update commands...")
                
                # Delete ALL old commands first
                try:
                    self.bot.delete_my_commands()
                    print("🗑️ Old commands deleted")
                    time.sleep(3)  # Wait for deletion to propagate
                except:
                    print("⚠️ No old commands to delete")
                
                # Set NEW commands
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
                print("✅ NEW commands set successfully!")
                
                # Verify commands were actually set
                time.sleep(2)
                current_commands = self.bot.get_my_commands()
                print(f"📋 Verified: {len(current_commands)} commands now active")
                for cmd in current_commands:
                    print(f"   /{cmd.command} - {cmd.description}")
                
                return True
                
            except Exception as e:
                print(f"❌ Attempt {attempt + 1} failed: {e}")
                if attempt < 2:  # Not last attempt
                    time.sleep(5)
                
        print("❌ All command update attempts failed!")
        return False
    
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
            """FIXED - Direct webapp opening"""
            if not self.db.is_user_whitelisted(message.from_user.id):
                self.bot.reply_to(message, "You are not authorized.")
                return
            
            if WEBAPP_URL and WEBAPP_URL.startswith('https://'):
                dashboard_url = f"{WEBAPP_URL}/dashboard"
                
                try:
                    # TRY WEBAPP BUTTON FIRST (opens directly in Telegram)
                    keyboard = types.InlineKeyboardMarkup()
                    keyboard.add(types.InlineKeyboardButton(
                        "Open Dashboard", 
                        web_app=WebApp(url=dashboard_url)
                    ))
                    
                    # Send minimal message with webapp button
                    self.bot.send_message(message.chat.id, "Dashboard", reply_markup=keyboard)
                    
                except Exception as e:
                    print(f"WebApp failed: {e}")
                    
                    # FALLBACK - URL button (opens in browser)
                    keyboard = types.InlineKeyboardMarkup()
                    keyboard.add(types.InlineKeyboardButton("Open Dashboard", url=dashboard_url))
                    self.bot.send_message(message.chat.id, "Dashboard", reply_markup=keyboard)
                    
            else:
                self.bot.reply_to(message, "Dashboard URL not configured.")
        
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
        
        @self.bot.message_handler(commands=['newpost'])
        def handle_newpost(message):
            if not self.db.is_user_whitelisted(message.from_user.id):
                self.bot.reply_to(message, "Unauthorized")
                return
            
            self.bot.reply_to(message, "New post feature coming soon!")
        
        @self.bot.message_handler(commands=['schedules'])
        def handle_schedules(message):
            if not self.db.is_user_whitelisted(message.from_user.id):
                self.bot.reply_to(message, "Unauthorized")
                return
            
            self.bot.reply_to(message, "Schedules feature coming soon!")
        
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
            
            data = call.data
            chat_id = call.message.chat.id
            
            if data == "start":
                self.show_main_menu(chat_id, "Welcome back!")
            elif data == "user":
                self.bot.send_message(chat_id, "Use /user command for user management")
            elif data == "newpost":
                self.bot.send_message(chat_id, "Use /newpost command")
            elif data == "schedules":
                self.bot.send_message(chat_id, "Use /schedules command")
            
            self.bot.answer_callback_query(call.id)
    
    def show_main_menu(self, chat_id, text="Main Menu"):
        """Main menu with DIRECT webapp button"""
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(types.InlineKeyboardButton("start", callback_data="start"))
        
        if chat_id == BOT_OWNER_ID:
            keyboard.row(types.InlineKeyboardButton("user", callback_data="user"))
        
        keyboard.row(types.InlineKeyboardButton("newpost", callback_data="newpost"))
        keyboard.row(types.InlineKeyboardButton("schedules", callback_data="schedules"))
        
        # DIRECT WEBAPP BUTTON in main menu
        if WEBAPP_URL and WEBAPP_URL.startswith('https://'):
            dashboard_url = f"{WEBAPP_URL}/dashboard"
            try:
                # WebApp button (opens directly in Telegram)
                keyboard.row(types.InlineKeyboardButton("dashboard", web_app=WebApp(url=dashboard_url)))
            except:
                # Fallback URL button
                keyboard.row(types.InlineKeyboardButton("dashboard", url=dashboard_url))
        
        self.bot.send_message(chat_id, text, reply_markup=keyboard)
