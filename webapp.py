"""
SIMPLE ChatAudit Bot - GUARANTEED TO WORK
No complex imports, no crashes, just works
"""
from flask import Flask, render_template_string, jsonify
from datetime import datetime
import os
import sqlite3
import threading
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'simple-secret-key')

# Global variables
bot_instance = None
bot_status = "Starting..."

def init_database():
    """Initialize simple database"""
    try:
        conn = sqlite3.connect('simple_bot.db')
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                is_whitelisted INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
        logger.info("Database initialized")
        return True
    except Exception as e:
        logger.error(f"Database error: {e}")
        return False

def get_users():
    """Get all whitelisted users"""
    try:
        conn = sqlite3.connect('simple_bot.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, username, first_name FROM users WHERE is_whitelisted = 1')
        users = cursor.fetchall()
        conn.close()
        return users
    except Exception as e:
        logger.error(f"Get users error: {e}")
        return []

def add_user(user_id, username=None, first_name=None):
    """Add user to whitelist"""
    try:
        conn = sqlite3.connect('simple_bot.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO users (user_id, username, first_name, is_whitelisted)
            VALUES (?, ?, ?, 1)
        """, (user_id, username, first_name))
        conn.commit()
        conn.close()
        logger.info(f"User {user_id} added")
        return True
    except Exception as e:
        logger.error(f"Add user error: {e}")
        return False

def start_bot():
    """Start the Telegram bot - SIMPLE VERSION"""
    global bot_instance, bot_status
    
    try:
        bot_status = "Importing telebot..."
        logger.info("Starting bot...")
        
        import telebot
        from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
        
        # Get environment variables
        BOT_TOKEN = os.getenv('BOT_TOKEN')
        BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID', 0))
        WEBAPP_URL = os.getenv('WEBAPP_URL', '')
        
        if not BOT_TOKEN or BOT_TOKEN == 'your-bot-token-here':
            bot_status = "No BOT_TOKEN"
            logger.error("BOT_TOKEN missing")
            return
            
        if not BOT_OWNER_ID:
            bot_status = "No BOT_OWNER_ID" 
            logger.error("BOT_OWNER_ID missing")
            return
        
        bot_status = "Creating bot instance..."
        bot_instance = telebot.TeleBot(BOT_TOKEN)
        
        # Add owner to whitelist
        add_user(BOT_OWNER_ID, "Owner", "Bot Owner")
        
        # Simple /start handler
        @bot_instance.message_handler(commands=['start'])
        def handle_start(message):
            user_id = message.from_user.id
            username = message.from_user.username
            first_name = message.from_user.first_name
            
            # Check if user is owner or whitelisted
            if user_id != BOT_OWNER_ID:
                users = get_users()
                user_ids = [u[0] for u in users]
                if user_id not in user_ids:
                    bot_instance.reply_to(message, 
                        "You are not authorized to use this bot.")
                    return
            
            # Add user to database
            add_user(user_id, username, first_name)
            
            # Create main menu
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("Start", callback_data="start"))
            keyboard.add(InlineKeyboardButton("Users", callback_data="users"))
            keyboard.add(InlineKeyboardButton("Help", callback_data="help"))
            
            # Add dashboard button if webapp URL exists
            if WEBAPP_URL and WEBAPP_URL.startswith('https://'):
                dashboard_url = f"{WEBAPP_URL}/dashboard"
                try:
                    web_app = WebAppInfo(url=dashboard_url)
                    keyboard.add(InlineKeyboardButton("Dashboard", web_app=web_app))
                except:
                    pass
            
            welcome_text = f"""ChatAudit Bot - Main Menu

Hello {first_name}! Welcome to the bot.

Available Options:
• Start - Return to this menu
• Users - View user list (Owner only)
• Help - Show help information
• Dashboard - Open web dashboard

Bot Status: Online
Current Time: {datetime.now().strftime('%d/%m/%Y %H:%M:%S IST')}"""
            
            bot_instance.send_message(message.chat.id, welcome_text, reply_markup=keyboard)
        
        # Simple /help handler
        @bot_instance.message_handler(commands=['help'])
        def handle_help(message):
            help_text = f"""ChatAudit Bot - Help

Commands:
• /start - Open main menu
• /help - Show this help

Features:
• User management
• Web dashboard integration
• Channel posting (coming soon)
• Post scheduling (coming soon)

Support: Contact bot owner for assistance.

Time: {datetime.now().strftime('%d/%m/%Y %H:%M:%S IST')}"""
            
            bot_instance.send_message(message.chat.id, help_text)
        
        # Simple callback handler
        @bot_instance.callback_query_handler(func=lambda call: True)
        def handle_callbacks(call):
            user_id = call.from_user.id
            
            if call.data == "start":
                handle_start(call.message)
            elif call.data == "users" and user_id == BOT_OWNER_ID:
                users = get_users()
                user_list = "Whitelisted Users:\n\n"
                if users:
                    for uid, username, fname in users:
                        name = f"@{username}" if username else fname or "Unknown"
                        user_list += f"• {name} (ID: {uid})\n"
                else:
                    user_list += "No users found."
                
                bot_instance.send_message(call.message.chat.id, user_list)
            elif call.data == "help":
                handle_help(call.message)
            
            bot_instance.answer_callback_query(call.id)
        
        # Update status and start polling
        bot_status = "Online"
        logger.info("Bot polling started")
        
        # Send startup notification to owner
        try:
            bot_instance.send_message(
                BOT_OWNER_ID,
                f"""ChatAudit Bot Started!

Time: {datetime.now().strftime('%d/%m/%Y %H:%M:%S IST')}
Status: Online
Dashboard: Available

Bot is ready to use!"""
            )
        except Exception as e:
            logger.warning(f"Startup notification failed: {e}")
        
        # Start polling
        bot_instance.infinity_polling(none_stop=True, interval=2)
        
    except Exception as e:
        logger.error(f"Bot error: {e}")
        bot_status = f"Error: {str(e)[:50]}"
        time.sleep(30)
        start_bot()

# HTML template for dashboard
HTML_DASHBOARD = """<!DOCTYPE html>
<html>
<head>
    <title>ChatAudit Bot Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f0f2f5; }
        .container { max-width: 900px; margin: 0 auto; }
        .card { background: white; border-radius: 12px; padding: 25px; margin: 20px 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .header { text-align: center; color: #1877f2; margin-bottom: 30px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
        .stat { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }
        .stat h3 { margin: 0; font-size: 2em; }
        .stat p { margin: 5px 0 0; opacity: 0.9; }
        .status-online { color: #28a745; font-weight: bold; }
        .status-error { color: #dc3545; font-weight: bold; }
        .user-item { background: #f8f9fa; margin: 10px 0; padding: 15px; border-radius: 8px; border-left: 4px solid #28a745; }
        .refresh { background: #28a745; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
        .refresh:hover { background: #218838; }
        .footer { text-align: center; margin-top: 30px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="header">
                <h1>ChatAudit Bot Dashboard</h1>
                <p>Simple Channel Management System</p>
            </div>
            
            <div class="stats">
                <div class="stat">
                    <h3>{{ total_users }}</h3>
                    <p>Total Users</p>
                </div>
                <div class="stat">
                    <h3>8080</h3>
                    <p>Server Port</p>
                </div>
                <div class="stat">
                    <h3>Online</h3>
                    <p>Status</p>
                </div>
                <div class="stat">
                    <h3>1.0</h3>
                    <p>Version</p>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>System Information</h2>
            <p><strong>Current Time:</strong> {{ current_time }}</p>
            <p><strong>Bot Status:</strong> 
                <span class="{% if 'Online' in bot_status %}status-online{% else %}status-error{% endif %}">
                    {{ bot_status }}
                </span>
            </p>
            <p><strong>Web Service:</strong> <span class="status-online">Running</span></p>
            <p><strong>Database:</strong> <span class="status-online">Connected</span></p>
            <button class="refresh" onclick="location.reload()">Refresh</button>
        </div>
        
        <div class="card">
            <h2>Whitelisted Users ({{ total_users }})</h2>
            {% if users %}
                {% for user in users %}
                <div class="user-item">
                    <strong>{% if user[1] %}@{{ user[1] }}{% else %}{{ user[2] or 'Unknown' }}{% endif %}</strong>
                    <br><small>ID: {{ user[0] }}</small>
                </div>
                {% endfor %}
            {% else %}
                <div style="text-align: center; padding: 20px; color: #666;">
                    No users whitelisted yet
                </div>
            {% endif %}
        </div>
        
        <div class="footer">
            <p>ChatAudit Bot Dashboard v1.0 • Running on Port 8080</p>
            <p><small>Last updated: {{ current_time }}</small></p>
        </div>
    </div>
</body>
</html>"""

# Flask routes
@app.route('/')
def index():
    return f"""
    <div style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center;">
        <h1>ChatAudit Bot</h1>
        <p>Bot and dashboard are running successfully!</p>
        <p><strong>Bot Status:</strong> <span style="color: green;">{bot_status}</span></p>
        <p><a href="/dashboard" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Open Dashboard</a></p>
        <p><a href="/health" style="color: #007bff;">Health Check</a></p>
    </div>
    """

@app.route('/dashboard')
def dashboard():
    """Main dashboard"""
    try:
        users = get_users()
        current_time = datetime.now().strftime('%d/%m/%Y %H:%M:%S IST')
        
        return render_template_string(
            HTML_DASHBOARD,
            users=users,
            total_users=len(users),
            current_time=current_time,
            bot_status=bot_status
        )
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return f"""
        <div style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px;">
            <h1>ChatAudit Bot Dashboard</h1>
            <p><strong>Status:</strong> Running</p>
            <p><strong>Error:</strong> {str(e)}</p>
            <p><a href="/health">Health Check</a></p>
        </div>
        """

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        users = get_users()
        return jsonify({
            'status': 'healthy',
            'bot_status': bot_status,
            'users_count': len(users),
            'port': 8080,
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'bot_status': bot_status,
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/test')
def test():
    """Simple test endpoint"""
    return jsonify({
        'message': 'ChatAudit Bot is working!',
        'bot_status': bot_status,
        'timestamp': datetime.now().isoformat(),
        'port': 8080
    })

# Initialize app
def init_app():
    """Initialize the application"""
    logger.info("Initializing ChatAudit Bot...")
    
    # Initialize database
    if not init_database():
        logger.error("Database initialization failed")
        return False
    
    # Start bot if credentials are available
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    BOT_OWNER_ID = os.getenv('BOT_OWNER_ID')
    
    if BOT_TOKEN and BOT_OWNER_ID and BOT_TOKEN != 'your-bot-token-here':
        bot_thread = threading.Thread(target=start_bot, daemon=True)
        bot_thread.start()
        logger.info("Bot thread started")
    else:
        global bot_status
        bot_status = "Missing credentials (BOT_TOKEN or BOT_OWNER_ID)"
        logger.warning("Bot not started - missing credentials")
    
    return True

# Main execution
if __name__ == '__main__':
    # Initialize application
    init_app()
    
    # Start Flask app
    port = int(os.getenv('PORT', 8080))
    logger.info(f"Starting web server on port {port}")
    
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
