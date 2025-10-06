"""
TechGeekZ Bot - Main Entry Point
Fixed for your existing repo structure
"""
import os
import sys
import threading
import time
from datetime import datetime, timezone, timedelta

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Simple config (avoid config.py import issues)
BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID', 0))
BOT_NAME = "TechGeekZ Bot"
WEBAPP_URL = os.getenv('WEBAPP_URL', '')
IST = timezone(timedelta(hours=5, minutes=30))

def format_time():
    return datetime.now(IST).strftime('%d/%m/%Y %H:%M:%S IST')

def init_database():
    """Simple database initialization"""
    try:
        import sqlite3
        conn = sqlite3.connect('techgeekz.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                is_whitelisted INTEGER DEFAULT 0,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add owner to whitelist
        cursor.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, username, first_name, is_whitelisted, updated_date)
            VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
        ''', (BOT_OWNER_ID, "Owner", "Bot Owner"))
        
        conn.commit()
        conn.close()
        print("✅ Database initialized")
        return True
    except Exception as e:
        print(f"❌ Database init failed: {e}")
        return False

def start_bot():
    """Start bot with your repo structure"""
    try:
        print(f"🤖 Starting {BOT_NAME}...")
        
        # Initialize database first
        if not init_database():
            print("❌ Database initialization failed")
            return
        
        # Import bot modules (fix circular imports)
        try:
            import telebot
            from telebot import types
            from telebot.types import BotCommand
            print("✅ Telebot imported successfully")
        except Exception as e:
            print(f"❌ Telebot import failed: {e}")
            return
        
        # Initialize bot
        bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
        
        # Test bot connection
        try:
            me = bot.get_me()
            print(f"✅ Bot connected: @{me.username}")
        except Exception as e:
            print(f"❌ Bot connection failed: {e}")
            return
        
        # Update commands
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
            
            bot.set_my_commands(commands)
            print("✅ Commands updated")
        except Exception as e:
            print(f"⚠️ Command update failed: {e}")
        
        # Simple database functions
        def is_user_whitelisted(user_id):
            try:
                import sqlite3
                conn = sqlite3.connect('techgeekz.db')
                cursor = conn.cursor()
                cursor.execute('SELECT is_whitelisted FROM users WHERE user_id = ? AND is_whitelisted = 1', (user_id,))
                result = cursor.fetchone()
                conn.close()
                return result is not None
            except:
                return user_id == BOT_OWNER_ID
        
        def add_user_to_whitelist(user_id, username=None, first_name=None):
            try:
                import sqlite3
                conn = sqlite3.connect('techgeekz.db')
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO users (user_id, username, first_name, is_whitelisted, updated_date)
                    VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
                ''', (user_id, username, first_name))
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                print(f"Database error: {e}")
                return False
        
        def remove_user_from_whitelist(user_id):
            try:
                import sqlite3
                conn = sqlite3.connect('techgeekz.db')
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET is_whitelisted = 0 WHERE user_id = ?', (user_id,))
                conn.commit()
                conn.close()
                return True
            except:
                return False
        
        def get_whitelisted_users():
            try:
                import sqlite3
                conn = sqlite3.connect('techgeekz.db')
                cursor = conn.cursor()
                cursor.execute('SELECT user_id, username, first_name FROM users WHERE is_whitelisted = 1')
                users = cursor.fetchall()
                conn.close()
                return users
            except:
                return []
        
        # Register handlers
        @bot.message_handler(commands=['start'])
        def handle_start(message):
            print(f"📨 /start from {message.from_user.id}")
            
            user_id = message.from_user.id
            username = message.from_user.username or "User"
            
            if not is_user_whitelisted(user_id):
                bot.reply_to(message, "You are not authorized to use this bot.")
                return
            
            add_user_to_whitelist(user_id, username, message.from_user.first_name)
            
            start_message = f"""Welcome to {BOT_NAME}

Hello @{username}! What new are we thinking today..

Owner: @Owner
Dashboard: Online
Time: {datetime.now(IST).strftime('%d/%m/%Y | %H:%M')}

Bot is active. Send /help for all commands"""

            bot.send_message(message.chat.id, start_message)
            print(f"✅ Start response sent to {user_id}")
            
            # Simple main menu
            keyboard = types.InlineKeyboardMarkup()
            keyboard.row(types.InlineKeyboardButton("start", callback_data="start"))
            
            if user_id == BOT_OWNER_ID:
                keyboard.row(types.InlineKeyboardButton("user", callback_data="user"))
            
            keyboard.row(types.InlineKeyboardButton("newpost", callback_data="newpost"))
            keyboard.row(types.InlineKeyboardButton("schedules", callback_data="schedules"))
            
            if WEBAPP_URL:
                dashboard_url = f"{WEBAPP_URL}/dashboard"
                keyboard.row(types.InlineKeyboardButton("dashboard", url=dashboard_url))
            
            bot.send_message(message.chat.id, "Main Menu:", reply_markup=keyboard)
        
        @bot.message_handler(commands=['help'])
        def handle_help(message):
            if not is_user_whitelisted(message.from_user.id):
                bot.reply_to(message, "You are not authorized.")
                return
            
            help_text = f"""{BOT_NAME} - Available Commands

/start - start the bot
/user - user settings
/newpost - create posts
/schedules - schedule settings
/dashboard - web dashboard
/permit <userid> - add user to whitelist
/remove <userid> - remove user from whitelist

Bot is working correctly!"""
            
            bot.send_message(message.chat.id, help_text)
        
        @bot.message_handler(commands=['user'])
        def handle_user(message):
            if message.from_user.id != BOT_OWNER_ID:
                bot.reply_to(message, "Owner only.")
                return
            
            users = get_whitelisted_users()
            user_list = f"Whitelisted Users ({len(users)}):\n\n"
            
            for user in users:
                user_id, username, first_name = user
                name = first_name or "Unknown"
                uname = f"@{username}" if username else "No username"
                user_list += f"{name} {uname}\nID: {user_id}\n\n"
            
            bot.send_message(message.chat.id, user_list)
        
        @bot.message_handler(commands=['dashboard'])
        def handle_dashboard(message):
            if not is_user_whitelisted(message.from_user.id):
                bot.reply_to(message, "You are not authorized.")
                return
            
            if WEBAPP_URL:
                dashboard_url = f"{WEBAPP_URL}/dashboard"
                bot.send_message(message.chat.id, f"Dashboard: {dashboard_url}")
            else:
                bot.reply_to(message, "Dashboard not available.")
        
        @bot.message_handler(commands=['permit'])
        def handle_permit(message):
            if message.from_user.id != BOT_OWNER_ID:
                bot.reply_to(message, "Owner only.")
                return
            
            parts = message.text.split()
            if len(parts) == 2:
                try:
                    user_id = int(parts[1].replace('-', ''))
                    add_user_to_whitelist(user_id)
                    bot.reply_to(message, f"User {user_id} permitted!")
                except:
                    bot.reply_to(message, "Invalid user ID.")
            else:
                bot.reply_to(message, "Format: /permit <user_id>")
        
        @bot.message_handler(commands=['remove'])
        def handle_remove(message):
            if message.from_user.id != BOT_OWNER_ID:
                bot.reply_to(message, "Owner only.")
                return
            
            parts = message.text.split()
            if len(parts) == 2:
                try:
                    user_id = int(parts[1].replace('-', ''))
                    if user_id != BOT_OWNER_ID:
                        remove_user_from_whitelist(user_id)
                        bot.reply_to(message, f"User {user_id} removed!")
                    else:
                        bot.reply_to(message, "Cannot remove owner!")
                except:
                    bot.reply_to(message, "Error removing user.")
            else:
                bot.reply_to(message, "Format: /remove <user_id>")
        
        @bot.callback_query_handler(func=lambda call: True)
        def handle_callback(call):
            if not is_user_whitelisted(call.from_user.id):
                bot.answer_callback_query(call.id, "Not authorized")
                return
            
            bot.answer_callback_query(call.id)
        
        print("✅ All handlers registered")
        
        # Send deployment message
        deployment_message = f"""{BOT_NAME}

Time: {format_time()}
Owner: Owner {BOT_OWNER_ID}
Dashboard: Online

Bot is active. Send /start to begin
Send /help for all commands"""

        try:
            bot.send_message(BOT_OWNER_ID, deployment_message)
            print("✅ Deployment message sent")
        except Exception as e:
            print(f"⚠️ Deployment message failed: {e}")
        
        # Start polling
        print("🚀 Starting bot polling...")
        bot.infinity_polling(none_stop=True, interval=2, timeout=20)
        
    except Exception as e:
        print(f"❌ Bot startup failed: {e}")
        import traceback
        traceback.print_exc()

def start_webapp():
    """Start webapp"""
    try:
        print("🌐 Starting webapp...")
        import subprocess
        import sys
        subprocess.run([sys.executable, 'webapp.py'])
    except Exception as e:
        print(f"❌ Webapp failed: {e}")

if __name__ == '__main__':
    print(f"🚀 {BOT_NAME} Starting...")
    print(f"Token: {'✅' if BOT_TOKEN else '❌'}")
    print(f"Owner ID: {BOT_OWNER_ID}")
    
    if not BOT_TOKEN or not BOT_OWNER_ID:
        print("❌ Missing credentials")
        exit(1)
    
    # Start bot in background
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    # Wait then start webapp
    time.sleep(3)
    start_webapp()
