"""
TechGeekZ Bot - Combined Bot + Web Dashboard
Fixed version with proper error handling and command updates
"""
from flask import Flask, render_template, jsonify
import os
import sys
import threading
import time
import requests
import telebot
from telebot import types
from telebot.types import BotCommand
from datetime import datetime, timezone, timedelta

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import BOT_TOKEN, BOT_OWNER_ID, BOT_NAME, IST, WEBAPP_URL, format_time, format_start_time
from database.models import DatabaseManager

# Flask app initialization
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'techgeekz-secret-key')

# Global variables
bot_instance = None
bot_status = "Starting..."
db = None

class SimpleBotHandler:
    def __init__(self, database_manager):
        self.db = database_manager
        self.bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
        
        # IMPORTANT: Update commands immediately on initialization
        self.set_bot_commands()
        self.register_handlers()
        
    def set_bot_commands(self):
        """Set bot commands - FIXED VERSION"""
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
            print("✅ Bot commands updated successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to update bot commands: {e}")
            return False
    
    def get_dashboard_status(self):
        """Check dashboard status"""
        try:
            if not WEBAPP_URL:
                return "Offline"
            response = requests.get(f"{WEBAPP_URL}/health", timeout=5)
            return "Online" if response.status_code == 200 else "Offline"
        except:
            return "Offline"
    
    def get_owner_username(self):
        """Get owner username"""
        try:
            owner_info = self.bot.get_chat(BOT_OWNER_ID)
            return f"@{owner_info.username}" if owner_info.username else f"Owner{BOT_OWNER_ID}"
        except:
            return f"Owner{BOT_OWNER_ID}"
    
    def register_handlers(self):
        """Register all bot handlers"""
        
        @self.bot.message_handler(commands=['start'])
        def handle_start(message):
            user_id = message.from_user.id
            username = message.from_user.username or "User"
            
            if not self.db.is_user_whitelisted(user_id):
                self.bot.reply_to(message, "You are not authorized to use this bot. Contact administrator.")
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

Bot is active. Send /help for all commands"""

            # Send message and show main menu
            self.bot.send_message(message.chat.id, start_message)
            self.show_main_menu(message.chat.id)
        
        @self.bot.message_handler(commands=['help'])
        def handle_help(message):
            if not self.db.is_user_whitelisted(message.from_user.id):
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

Use menu buttons or type commands manually."""
            
            self.bot.send_message(message.chat.id, help_text)
        
        @self.bot.message_handler(commands=['dashboard'])
        def handle_dashboard(message):
            """FIXED DASHBOARD COMMAND"""
            if not self.db.is_user_whitelisted(message.from_user.id):
                self.bot.reply_to(message, "You are not authorized to use this bot.")
                return
            
            if WEBAPP_URL and WEBAPP_URL.startswith('https://'):
                dashboard_url = f"{WEBAPP_URL}/dashboard"
                
                # Try WebApp button first
                try:
                    keyboard = types.InlineKeyboardMarkup()
                    keyboard.add(types.InlineKeyboardButton(
                        "Open Dashboard", 
                        web_app=types.WebApp(dashboard_url)
                    ))
                    self.bot.send_message(message.chat.id, "Dashboard:", reply_markup=keyboard)
                except Exception as e:
                    # Fallback to URL button if WebApp fails
                    print(f"WebApp failed, using URL button: {e}")
                    keyboard = types.InlineKeyboardMarkup()
                    keyboard.add(types.InlineKeyboardButton("Open Dashboard", url=dashboard_url))
                    self.bot.send_message(message.chat.id, "Dashboard:", reply_markup=keyboard)
            else:
                self.bot.reply_to(message, "Dashboard URL not configured.")
        
        @self.bot.message_handler(commands=['user'])
        def handle_user(message):
            if not self.db.is_user_whitelisted(message.from_user.id):
                self.bot.reply_to(message, "Unauthorized")
                return
            if message.from_user.id != BOT_OWNER_ID:
                self.bot.reply_to(message, "User management is owner only.")
                return
            self.show_user_menu(message.chat.id)
        
        @self.bot.message_handler(commands=['permit'])
        def handle_permit(message):
            if message.from_user.id != BOT_OWNER_ID:
                self.bot.reply_to(message, "Owner only command.")
                return
            
            parts = message.text.split()
            if len(parts) != 2:
                self.bot.reply_to(message, "Format: /permit <user_id>\nExample: /permit 123456789")
                return
            
            try:
                user_id = int(parts[1].replace('-', ''))
                self.db.add_user_to_whitelist(user_id)
                self.bot.reply_to(message, f"User {user_id} added to whitelist!")
            except:
                self.bot.reply_to(message, "Invalid user ID format.")
        
        @self.bot.message_handler(commands=['remove'])
        def handle_remove(message):
            if message.from_user.id != BOT_OWNER_ID:
                self.bot.reply_to(message, "Owner only command.")
                return
            
            parts = message.text.split()
            if len(parts) != 2:
                self.bot.reply_to(message, "Format: /remove <user_id>\nExample: /remove 123456789")
                return
            
            try:
                user_id = int(parts[1].replace('-', ''))
                if user_id == BOT_OWNER_ID:
                    self.bot.reply_to(message, "Cannot remove bot owner!")
                    return
                self.db.remove_user_from_whitelist(user_id)
                self.bot.reply_to(message, f"User {user_id} removed from whitelist!")
            except:
                self.bot.reply_to(message, "Invalid user ID format.")
        
        # Simple menu handlers
        @self.bot.message_handler(func=lambda message: True)
        def handle_all_messages(message):
            if not self.db.is_user_whitelisted(message.from_user.id):
                return
            
            text = message.text.strip() if message.text else ""
            
            # Handle basic menu responses
            if text == "back":
                self.hide_keyboard(message.chat.id)
                self.show_main_menu(message.chat.id)
            elif text == "users" and message.from_user.id == BOT_OWNER_ID:
                self.list_users(message.chat.id)
    
    def show_main_menu(self, chat_id):
        """Show main inline keyboard menu"""
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(types.InlineKeyboardButton("start", callback_data="start"))
        
        if chat_id == BOT_OWNER_ID:
            keyboard.row(types.InlineKeyboardButton("user", callback_data="user"))
        
        keyboard.row(types.InlineKeyboardButton("newpost", callback_data="newpost"))
        keyboard.row(types.InlineKeyboardButton("schedules", callback_data="schedules"))
        
        # Dashboard button
        if WEBAPP_URL and WEBAPP_URL.startswith('https://'):
            dashboard_url = f"{WEBAPP_URL}/dashboard"
            try:
                keyboard.row(types.InlineKeyboardButton("dashboard", web_app=types.WebApp(dashboard_url)))
            except:
                keyboard.row(types.InlineKeyboardButton("dashboard", url=dashboard_url))
        
        self.bot.send_message(chat_id, "Main Menu:", reply_markup=keyboard)
    
    def show_user_menu(self, chat_id):
        """Show user management button menu"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
        keyboard.row("users", "permit")
        keyboard.row("remove", "back")
        
        self.bot.send_message(chat_id, "User Management:", reply_markup=keyboard)
    
    def hide_keyboard(self, chat_id):
        """Hide button keyboard"""
        keyboard = types.ReplyKeyboardRemove()
        self.bot.send_message(chat_id, "Menu hidden", reply_markup=keyboard)
    
    def list_users(self, chat_id):
        """List all whitelisted users"""
        users = self.db.get_whitelisted_users()
        
        if not users:
            self.bot.send_message(chat_id, "No whitelisted users found.")
            return
        
        user_list = f"Whitelisted Users ({len(users)}):\n\n"
        for user in users:
            user_id = user[0]
            username = user[1] if user[1] else "No username"
            first_name = user[2] if user[2] else "Unknown"
            user_list += f"{first_name} @{username}\nID: {user_id}\n\n"
        
        self.bot.send_message(chat_id, user_list)

def get_owner_details(bot):
    """Get owner details for deployment message"""
    try:
        owner_info = bot.get_chat(BOT_OWNER_ID)
        first = owner_info.first_name or ""
        last = owner_info.last_name or ""
        nickname = f"{first} {last}".strip()
        username = f"@{owner_info.username}" if owner_info.username else "NoUsername"
        return f"{nickname} {username}".strip()
    except:
        return f"Owner {BOT_OWNER_ID}"

def get_dashboard_status():
    """Check dashboard status"""
    try:
        if not WEBAPP_URL:
            return "Offline"
        response = requests.get(f"{WEBAPP_URL}/health", timeout=5)
        return "Online" if response.status_code == 200 else "Offline"
    except:
        return "Offline"

def start_bot():
    """Start bot in background thread"""
    global bot_instance, bot_status, db
    
    try:
        print(f"🤖 Starting {BOT_NAME} bot...")
        
        # Initialize database
        db = DatabaseManager()
        print("✅ Database initialized")
        
        # Add owner to whitelist
        db.add_user_to_whitelist(BOT_OWNER_ID, "Owner", "Bot Owner")
        print(f"👑 Owner {BOT_OWNER_ID} added to whitelist")
        
        # Initialize simple bot handler
        bot_handler = SimpleBotHandler(db)
        bot_instance = bot_handler.bot
        
        print(f"🤖 Bot: @{bot_instance.get_me().username}")
        print("✅ Bot commands updated")
        
        # Wait a moment for Flask to be ready
        time.sleep(2)
        
        # Send deployment notification
        owner_details = get_owner_details(bot_instance)
        dashboard_status = get_dashboard_status()
        start_time = format_time()
        
        deployment_message = f"""{BOT_NAME}

Time: {start_time}
Owner: {owner_details}
Dashboard: {dashboard_status}

Bot is active. Send /start to begin
Send /help for all commands"""

        try:
            bot_instance.send_message(BOT_OWNER_ID, deployment_message)
            print(f"📨 Deployment notification sent")
        except Exception as e:
            print(f"⚠️ Could not send deployment notification: {e}")
        
        bot_status = "Online"
        print("🚀 Bot polling started")
        
        # Start polling
        bot_instance.infinity_polling(none_stop=True, interval=2, timeout=20)
        
    except Exception as e:
        print(f"❌ Bot error: {e}")
        bot_status = f"Error: {str(e)}"

def get_users():
    """Get users from database"""
    global db
    try:
        if db:
            return db.get_whitelisted_users()
        return []
    except Exception as e:
        print(f"Database error: {e}")
        return []

# Flask routes
@app.route('/')
def index():
    return f"""
    <div style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center;">
        <h1>{BOT_NAME}</h1>
        <p>Status: <strong style="color: green;">{bot_status}</strong></p>
        <p>Bot and dashboard are running successfully!</p>
        <p><a href="/dashboard" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Open Dashboard</a></p>
        <p><a href="/health" style="color: #007bff;">Health Check</a></p>
    </div>
    """

@app.route('/dashboard')
def dashboard():
    """Dashboard route"""
    try:
        users = get_users()
        current_time = datetime.now(IST).strftime('%d/%m/%Y %H:%M:%S IST')
        
        return render_template('dashboard.html',
            bot_name=BOT_NAME,
            current_time=current_time,
            total_users=len(users),
            whitelisted_users=users,
            scheduled_posts=[],
            self_destruct_posts=[],
            bot_status=bot_status
        )
    except Exception as e:
        return f"""
        <div style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px;">
            <h1>{BOT_NAME} Dashboard</h1>
            <p><strong>Status:</strong> {bot_status}</p>
            <p><strong>Error:</strong> {str(e)}</p>
            <p><a href="/health">Health Check</a></p>
            <p><a href="/">Back to Home</a></p>
        </div>
        """

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        users = get_users()
        return jsonify({
            'status': 'healthy',
            'bot_name': BOT_NAME,
            'bot_status': bot_status,
            'users_count': len(users),
            'port': int(os.getenv('PORT', 8080)),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'bot_name': BOT_NAME,
            'bot_status': bot_status,
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/users')
def api_users():
    """API endpoint for users"""
    try:
        users = get_users()
        return jsonify([{
            'user_id': user[0] if len(user) > 0 else 0,
            'username': user[1] if len(user) > 1 else '',
            'first_name': user[2] if len(user) > 2 else ''
        } for user in users])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Main execution
if __name__ == '__main__':
    print(f"🚀 Starting {BOT_NAME} combined service...")
    
    # Start bot in background thread
    if BOT_TOKEN and BOT_OWNER_ID:
        bot_thread = threading.Thread(target=start_bot, daemon=True)
        bot_thread.start()
        print("🤖 Bot thread started in background")
        
        # Give bot a moment to initialize
        time.sleep(1)
    else:
        print("❌ Missing BOT_TOKEN or BOT_OWNER_ID")
        bot_status = "Missing credentials"
    
    # Start Flask app
    port = int(os.getenv('PORT', 8080))
    print(f"🌐 Starting Flask app on port {port}")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
    except Exception as e:
        print(f"❌ Flask error: {e}")
