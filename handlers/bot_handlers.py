"""
TechGeekZ Bot - Bot Command Handlers
Complete command handling with custom messages and menu updates
"""
import telebot
from telebot import types
from telebot.types import BotCommand
import sys
import os
import requests
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import BOT_TOKEN, BOT_OWNER_ID, BOT_NAME, IST, WEBAPP_URL, format_start_time
from handlers.menu_handlers import MenuHandler

class BotHandlers:
    def __init__(self, database_manager):
        self.db = database_manager
        self.bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
        self.menu_handler = MenuHandler(self.bot, self.db)
        self.user_states = {}
        
        # Register handlers and auto-update commands
        self.register_handlers()
        
    def get_dashboard_status(self):
        """Check if dashboard is online"""
        try:
            if not WEBAPP_URL:
                return "Offline"
            
            response = requests.get(f"{WEBAPP_URL}/health", timeout=5)
            return "Online" if response.status_code == 200 else "Offline"
        except:
            return "Offline"
    
    def get_user_details(self, user_id):
        """Get user's Telegram details"""
        try:
            user_info = self.bot.get_chat(user_id)
            username = f"@{user_info.username}" if user_info.username else "No username"
            return username
        except:
            return "Unknown"
    
    def get_owner_username(self):
        """Get owner's username"""
        try:
            owner_info = self.bot.get_chat(BOT_OWNER_ID)
            return f"@{owner_info.username}" if owner_info.username else "Owner"
        except:
            return "Owner"

    def set_bot_commands(self):
        """Set bot commands - called automatically on deployment"""
        try:
            commands = [
                BotCommand("start", "start the bot"),
                BotCommand("user", "user settings"),
                BotCommand("newpost", "create posts"),
                BotCommand("schedules", "schedule settings"),
                BotCommand("dashboard", "web dashboard"),
            ]
            
            self.bot.set_my_commands(commands)
            print("✅ Bot commands updated automatically on deployment")
            return True
            
        except Exception as e:
            print(f"⚠️ Failed to update bot commands: {e}")
            return False
    
    def register_handlers(self):
        """Register all bot command handlers"""
        
        # AUTO-UPDATE COMMANDS ON STARTUP
        self.set_bot_commands()
        
        @self.bot.message_handler(commands=['start'])
        def handle_start(message):
            user_id = message.from_user.id
            username = message.from_user.username
            first_name = message.from_user.first_name
            
            # Check if user is authorized
            if not self.db.is_user_whitelisted(user_id):
                self.bot.reply_to(message, 
                    "You are not authorized to use this bot. Contact the administrator.")
                return
            
            # Update user info in database
            self.db.add_user_to_whitelist(user_id, username, first_name)
            
            # Get user details and status
            user_username = f"@{username}" if username else "User"
            owner_username = self.get_owner_username()
            dashboard_status = self.get_dashboard_status()
            current_time = format_start_time()
            
            # Custom start message
            start_message = f"""Welcome to {BOT_NAME}

Hello {user_username}! What new are we thinking today..

Owner: {owner_username}
Dashboard: {dashboard_status}
Time: {current_time}

Bot is active. Send /help for all commands"""

            # Send custom message and show main menu
            self.bot.send_message(message.chat.id, start_message)
            self.menu_handler.show_main_menu(message.chat.id)

        @self.bot.message_handler(commands=['help'])
        def handle_help(message):
            user_id = message.from_user.id
            
            if not self.db.is_user_whitelisted(user_id):
                self.bot.reply_to(message, "You are not authorized to use this bot.")
                return
            
            help_text = f"""{BOT_NAME} - Available Commands

/start - start the bot
/user - user settings  
/newpost - create posts
/schedules - schedule settings
/dashboard - web dashboard
/permit <userid> - add user to whitelist
/remove <userid> - remove user from whitelist

Use the menu buttons or type commands manually."""

            self.bot.send_message(message.chat.id, help_text)

        @self.bot.message_handler(commands=['user'])
        def handle_user_command(message):
            user_id = message.from_user.id
            
            if not self.db.is_user_whitelisted(user_id):
                self.bot.reply_to(message, "You are not authorized to use this bot.")
                return
            
            if user_id != BOT_OWNER_ID:
                self.bot.reply_to(message, "User management is owner only.")
                return
            
            self.menu_handler.show_user_menu(message.chat.id)

        @self.bot.message_handler(commands=['newpost'])
        def handle_newpost_command(message):
            user_id = message.from_user.id
            
            if not self.db.is_user_whitelisted(user_id):
                self.bot.reply_to(message, "You are not authorized to use this bot.")
                return
            
            self.menu_handler.show_newpost_menu(message.chat.id)

        @self.bot.message_handler(commands=['schedules'])
        def handle_schedules_command(message):
            user_id = message.from_user.id
            
            if not self.db.is_user_whitelisted(user_id):
                self.bot.reply_to(message, "You are not authorized to use this bot.")
                return
            
            self.menu_handler.show_schedules_menu(message.chat.id)

        @self.bot.message_handler(commands=['dashboard'])
        def handle_dashboard_command(message):
            user_id = message.from_user.id
            
            if not self.db.is_user_whitelisted(user_id):
                self.bot.reply_to(message, "You are not authorized to use this bot.")
                return
            
            if WEBAPP_URL and WEBAPP_URL.startswith('https://'):
                dashboard_url = f"{WEBAPP_URL}/dashboard"
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(types.InlineKeyboardButton("Open Dashboard", web_app=types.WebApp(dashboard_url)))
                self.bot.send_message(message.chat.id, "Dashboard", reply_markup=keyboard)
            else:
                self.bot.reply_to(message, "Dashboard is not available.")

        @self.bot.message_handler(commands=['permit'])
        def handle_permit_command(message):
            if message.from_user.id != BOT_OWNER_ID:
                self.bot.reply_to(message, "Owner only command.")
                return
            
            try:
                args = message.text.split()
                if len(args) != 2:
                    self.bot.reply_to(message, "Usage: /permit <user_id>\nExample: /permit 123456789")
                    return
                
                user_id_str = args[1].replace('-', '')
                user_id = int(user_id_str)
                
                self.db.add_user_to_whitelist(user_id)
                self.bot.reply_to(message, f"User {user_id} added to whitelist!")
                
            except ValueError:
                self.bot.reply_to(message, "Invalid user ID. Please provide a numeric user ID.")
            except Exception as e:
                self.bot.reply_to(message, f"Error: {str(e)}")

        @self.bot.message_handler(commands=['remove'])
        def handle_remove_command(message):
            if message.from_user.id != BOT_OWNER_ID:
                self.bot.reply_to(message, "Owner only command.")
                return
            
            try:
                args = message.text.split()
                if len(args) != 2:
                    self.bot.reply_to(message, "Usage: /remove <user_id>\nExample: /remove 123456789")
                    return
                
                user_id_str = args[1].replace('-', '')
                user_id = int(user_id_str)
                
                if user_id == BOT_OWNER_ID:
                    self.bot.reply_to(message, "Cannot remove bot owner from whitelist!")
                    return
                
                self.db.remove_user_from_whitelist(user_id)
                self.bot.reply_to(message, f"User {user_id} removed from whitelist!")
                
            except ValueError:
                self.bot.reply_to(message, "Invalid user ID. Please provide a numeric user ID.")
            except Exception as e:
                self.bot.reply_to(message, f"Error: {str(e)}")

        # Register callback query handler
        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_callback_query(call):
            self.menu_handler.handle_callback_query(call)
            
        # Register message handler for menu responses
        @self.bot.message_handler(func=lambda message: True)
        def handle_messages(message):
            self.menu_handler.handle_messages(message)
