import os
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, render_template_string, jsonify, request
import telebot
from telebot import types
import pytz

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID'))
WEBAPP_URL = os.getenv('WEBAPP_URL', '')
SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')
BOT_NAME = "ChatAudit Bot"

# Initialize Flask
app = Flask(__name__)
app.secret_key = SECRET_KEY

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
IST = pytz.timezone('Asia/Kolkata')

# Global variables
bot_status = {"status": "Starting", "last_update": None}
user_states = {}

class UserState:
    def __init__(self):
        self.menu_level = "main"
        self.selected_channel = None
        self.post_content = None
        self.post_media = None
        self.editing_post = False

# Database initialization
def init_database():
    conn = sqlite3.connect('chataudit.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            is_whitelisted BOOLEAN DEFAULT 0,
            added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Channels table  
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS channels (
            channel_id INTEGER PRIMARY KEY,
            channel_name TEXT,
            channel_username TEXT,
            added_by INTEGER,
            added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Scheduled posts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scheduled_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            channel_id INTEGER,
            content TEXT,
            media_path TEXT,
            scheduled_time TIMESTAMP,
            is_self_destruct BOOLEAN DEFAULT 0,
            self_destruct_time TIMESTAMP,
            status TEXT DEFAULT 'pending',
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Database helper functions
def add_user_to_whitelist(user_id, username=None, first_name=None):
    conn = sqlite3.connect('chataudit.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, username, first_name, is_whitelisted)
        VALUES (?, ?, ?, 1)
    ''', (user_id, username, first_name))
    conn.commit()
    conn.close()

def remove_user_from_whitelist(user_id):
    conn = sqlite3.connect('chataudit.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET is_whitelisted = 0 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def is_user_whitelisted(user_id):
    if user_id == BOT_OWNER_ID:
        return True
    conn = sqlite3.connect('chataudit.db')
    cursor = conn.cursor()
    cursor.execute('SELECT is_whitelisted FROM users WHERE user_id = ? AND is_whitelisted = 1', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def get_whitelisted_users():
    conn = sqlite3.connect('chataudit.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, username, first_name FROM users WHERE is_whitelisted = 1')
    users = cursor.fetchall()
    conn.close()
    return users

def add_channel(channel_id, channel_name, channel_username, added_by):
    conn = sqlite3.connect('chataudit.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO channels (channel_id, channel_name, channel_username, added_by)
        VALUES (?, ?, ?, ?)
    ''', (channel_id, channel_name, channel_username, added_by))
    conn.commit()
    conn.close()

def get_user_channels(user_id):
    conn = sqlite3.connect('chataudit.db')
    cursor = conn.cursor()
    cursor.execute('SELECT channel_id, channel_name, channel_username FROM channels WHERE added_by = ?', (user_id,))
    channels = cursor.fetchall()
    conn.close()
    return channels

def get_scheduled_posts():
    conn = sqlite3.connect('chataudit.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT sp.*, c.channel_name, u.username 
        FROM scheduled_posts sp
        LEFT JOIN channels c ON sp.channel_id = c.channel_id
        LEFT JOIN users u ON sp.user_id = u.user_id
        WHERE sp.status = 'pending'
        ORDER BY sp.scheduled_time ASC
    ''')
    posts = cursor.fetchall()
    conn.close()
    return posts

# Bot command handlers
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    if not is_user_whitelisted(user_id):
        bot.reply_to(message, "❌ You are not authorized to use this bot. Contact the administrator.")
        return
    
    # Update user info
    add_user_to_whitelist(user_id, username, first_name)
    
    # Initialize user state
    user_states[user_id] = UserState()
    
    welcome_text = f"""
🤖 **Welcome to {BOT_NAME}**

Hello {first_name}! You are authorized to use this bot.

**Available Commands:**
• /help - Show detailed help and commands
• Use the menu below to navigate

**Current Time (IST):** {datetime.now(IST).strftime('%d/%m %H:%M')}
"""
    
    show_main_menu(message.chat.id, welcome_text)

@bot.message_handler(commands=['help'])
def handle_help(message):
    user_id = message.from_user.id
    
    if not is_user_whitelisted(user_id):
        bot.reply_to(message, "❌ You are not authorized to use this bot.")
        return
    
    help_text = f"""
📖 **{BOT_NAME} - Complete Guide**

**🏠 Main Menu Navigation:**
• Start - Return to main menu
• User - User management (Owner only)
• New Post - Create and schedule posts
• Schedules - View and manage scheduled posts
• Dashboard - Open web dashboard

**👥 User Management (Owner Only):**
• Users - List all whitelisted users
• Permit <user_id> - Add user to whitelist (ignores - signs)
• Remove <user_id> - Remove user from whitelist

**📝 Post Creation:**
1. Select "New Post" → Choose channel
2. Send your content (text, media, or both)
3. Choose action:
   • Schedule Post - Format: dd/mm hh:mm (5/10 15:00) or hh:mm (15:00)
   • Self-Destruct - Same format, auto-delete after posting
   • Post Now - Instant posting

**📅 Schedule Management:**
• View scheduled posts and their timings
• View self-destruct posts and timings  
• Cancel scheduled or self-destruct posts

**🕐 Time Format:**
• dd/mm hh:mm - Specific date (5/10 15:00 = 5th Oct 3:00 PM)
• hh:mm - Same day (15:00 = 3:00 PM today)
• All times in IST (Indian Standard Time)

**📊 Dashboard:**
Web interface for detailed management and statistics.

**Current Time (IST):** {datetime.now(IST).strftime('%d/%m/%Y %H:%M')}
"""
    
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['addchannel'])
def handle_add_channel(message):
    user_id = message.from_user.id
    
    if not is_user_whitelisted(user_id):
        bot.reply_to(message, "❌ You are not authorized to use this bot.")
        return
    
    try:
        args = message.text.split()
        if len(args) != 2:
            bot.reply_to(message, "Usage: /addchannel @channelname")
            return
            
        channel_username = args[1].replace('@', '')
        # In a real implementation, you'd verify the channel exists and bot is admin
        # For now, we'll add it with a placeholder ID
        channel_id = hash(channel_username) % 1000000  # Simple hash for demo
        
        add_channel(channel_id, f"@{channel_username}", channel_username, user_id)
        bot.reply_to(message, f"✅ Channel @{channel_username} added successfully!")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error adding channel: {str(e)}")

@bot.message_handler(commands=['channels'])
def handle_list_channels(message):
    user_id = message.from_user.id
    
    if not is_user_whitelisted(user_id):
        bot.reply_to(message, "❌ You are not authorized to use this bot.")
        return
    
    channels = get_user_channels(user_id)
    
    if not channels:
        bot.reply_to(message, "📋 No channels added yet. Use /addchannel @channelname to add channels.")
        return
    
    channel_list = "📋 **Your Added Channels:**\n\n"
    for i, (channel_id, channel_name, channel_username) in enumerate(channels, 1):
        channel_list += f"{i}. {channel_name} (@{channel_username})\n"
    
    bot.send_message(message.chat.id, channel_list, parse_mode='Markdown')

# Menu functions
def show_main_menu(chat_id, text="🏠 **Main Menu**"):
    keyboard = types.InlineKeyboardMarkup()
    
    keyboard.row(types.InlineKeyboardButton("🏠 Start", callback_data="menu_start"))
    
    # User management for owner only
    if chat_id == BOT_OWNER_ID:
        keyboard.row(types.InlineKeyboardButton("👥 User", callback_data="menu_user"))
    
    keyboard.row(types.InlineKeyboardButton("📝 New Post", callback_data="menu_new_post"))
    keyboard.row(types.InlineKeyboardButton("📅 Schedules", callback_data="menu_schedules"))
    
    # Dashboard button if URL is configured
    if WEBAPP_URL and WEBAPP_URL.startswith('https://'):
        dashboard_url = f"{WEBAPP_URL}/dashboard"
        keyboard.row(types.InlineKeyboardButton("📊 Dashboard", web_app=types.WebApp(dashboard_url)))
    
    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode='Markdown')

def show_user_menu(chat_id):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.row("👥 Users", "➕ Permit <user_id>")
    keyboard.row("➖ Remove <user_id>", "⬅️ Back")
    
    text = """
👥 **User Management Menu**

**Available Actions:**
• **Users** - List all whitelisted users
• **Permit <user_id>** - Add user to whitelist (Example: Permit 123456789)
• **Remove <user_id>** - Remove user from whitelist (Example: Remove 123456789)
• **Back** - Return to main menu

**Note:** User IDs can be with or without minus signs (123456789 or -123456789)
"""
    
    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode='Markdown')

# Callback query handler
@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    user_id = call.from_user.id
    
    if not is_user_whitelisted(user_id):
        bot.answer_callback_query(call.id, "❌ Not authorized")
        return
    
    data = call.data
    
    if data == "menu_start":
        show_main_menu(call.message.chat.id, "🏠 **Welcome back to the main menu!**")
        
    elif data == "menu_user" and user_id == BOT_OWNER_ID:
        show_user_menu(call.message.chat.id)
        
    elif data == "menu_new_post":
        show_channel_selection(call.message.chat.id)
        
    elif data == "menu_schedules":
        show_schedules_menu(call.message.chat.id)
        
    bot.answer_callback_query(call.id)

def show_channel_selection(chat_id):
    channels = get_user_channels(chat_id)
    
    if not channels:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(types.InlineKeyboardButton("⬅️ Back", callback_data="menu_start"))
        
        text = """
📝 **New Post**

❌ No channels added yet.

Use /addchannel @channelname to add channels first.

**Example:** /addchannel @mychannel
"""
        bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode='Markdown')
        return
    
    keyboard = types.InlineKeyboardMarkup()
    
    for channel_id, channel_name, channel_username in channels:
        keyboard.row(types.InlineKeyboardButton(f"{channel_name}", callback_data=f"select_channel_{channel_id}"))
    
    keyboard.row(types.InlineKeyboardButton("⬅️ Back", callback_data="menu_start"))
    
    text = """
📝 **New Post - Select Channel**

Choose a channel to post in:
"""
    
    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode='Markdown')

def show_schedules_menu(chat_id):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.row("📋 Scheduled Posts", "💣 Self-Destruct Timings")
    keyboard.row("❌ Cancel", "⬅️ Back")
    
    text = """
📅 **Schedules Menu**

**Available Actions:**
• **Scheduled Posts** - View all scheduled posts and timings
• **Self-Destruct Timings** - View all self-destruct posts and timings  
• **Cancel** - Cancel scheduled or self-destruct tasks
• **Back** - Return to main menu
"""
    
    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode='Markdown')

# Message handler for button menu responses
@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    if not is_user_whitelisted(user_id):
        bot.reply_to(message, "❌ You are not authorized to use this bot.")
        return
    
    # Handle button menu commands
    if text == "👥 Users" and user_id == BOT_OWNER_ID:
        handle_list_users(message)
    elif text.startswith("➕ Permit") and user_id == BOT_OWNER_ID:
        handle_permit_user(message)
    elif text.startswith("➖ Remove") and user_id == BOT_OWNER_ID:
        handle_remove_user(message)
    elif text == "⬅️ Back":
        show_main_menu(message.chat.id)
    elif text == "📋 Scheduled Posts":
        handle_show_scheduled_posts(message)
    elif text == "💣 Self-Destruct Timings":
        handle_show_self_destruct_posts(message)
    elif text == "❌ Cancel":
        show_cancel_menu(message.chat.id)
    else:
        # Handle as potential post content
        handle_post_content(message)

def handle_list_users(message):
    users = get_whitelisted_users()
    
    if not users:
        bot.reply_to(message, "📋 No whitelisted users found.")
        return
    
    user_list = "👥 **Whitelisted Users:**\n\n"
    for user_id, username, first_name in users:
        display_name = f"@{username}" if username else first_name or "Unknown"
        user_list += f"• **{display_name}** (ID: {user_id})\n"
    
    bot.send_message(message.chat.id, user_list, parse_mode='Markdown')

def handle_permit_user(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "Usage: Permit <user_id>\nExample: Permit 123456789")
            return
        
        user_id_str = parts[1].replace('-', '')  # Remove minus signs
        user_id = int(user_id_str)
        
        add_user_to_whitelist(user_id)
        bot.reply_to(message, f"✅ User {user_id} added to whitelist!")
        
    except ValueError:
        bot.reply_to(message, "❌ Invalid user ID. Please provide a numeric user ID.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

def handle_remove_user(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "Usage: Remove <user_id>\nExample: Remove 123456789")
            return
        
        user_id_str = parts[1].replace('-', '')  # Remove minus signs  
        user_id = int(user_id_str)
        
        if user_id == BOT_OWNER_ID:
            bot.reply_to(message, "❌ Cannot remove bot owner from whitelist!")
            return
        
        remove_user_from_whitelist(user_id)
        bot.reply_to(message, f"✅ User {user_id} removed from whitelist!")
        
    except ValueError:
        bot.reply_to(message, "❌ Invalid user ID. Please provide a numeric user ID.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

def handle_show_scheduled_posts(message):
    posts = get_scheduled_posts()
    scheduled = [p for p in posts if not p[6]]  # is_self_destruct = False
    
    if not scheduled:
        bot.reply_to(message, "📋 No scheduled posts found.")
        return
    
    text = "📋 **Scheduled Posts:**\n\n"
    for post in scheduled:
        channel_name = post[8] or "Unknown Channel"
        scheduled_time = post[5]
        content_preview = post[3][:50] + "..." if len(post[3]) > 50 else post[3]
        text += f"📅 **{scheduled_time}**\n📢 {channel_name}\n📄 {content_preview}\n\n"
    
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

def handle_show_self_destruct_posts(message):
    posts = get_scheduled_posts()
    self_destruct = [p for p in posts if p[6]]  # is_self_destruct = True
    
    if not self_destruct:
        bot.reply_to(message, "💣 No self-destruct posts found.")
        return
    
    text = "💣 **Self-Destruct Posts:**\n\n"
    for post in self_destruct:
        channel_name = post[8] or "Unknown Channel"
        scheduled_time = post[5]
        destruct_time = post[7]
        content_preview = post[3][:50] + "..." if len(post[3]) > 50 else post[3]
        text += f"📅 **Post:** {scheduled_time}\n💥 **Destruct:** {destruct_time}\n📢 {channel_name}\n📄 {content_preview}\n\n"
    
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

def show_cancel_menu(chat_id):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(types.InlineKeyboardButton("💣 Self-Destruct", callback_data="cancel_self_destruct"))
    keyboard.row(types.InlineKeyboardButton("📅 Scheduled Post", callback_data="cancel_scheduled"))
    keyboard.row(types.InlineKeyboardButton("⬅️ Back", callback_data="menu_schedules"))
    
    text = """
❌ **Cancel Tasks**

Choose task type to cancel:
"""
    
    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode='Markdown')

def handle_post_content(message):
    # Placeholder for post content handling
    bot.reply_to(message, "📝 Post content received. Advanced post editor coming soon!")

# Bot startup function
def start_bot():
    global bot_status
    try:
        bot_status["status"] = "Starting"
        
        # Initialize database
        init_database()
        
        # Add owner to whitelist
        add_user_to_whitelist(BOT_OWNER_ID)
        
        bot_status["status"] = "Online"
        bot_status["last_update"] = datetime.now(IST).isoformat()
        
        print(f"✅ {BOT_NAME} started successfully!")
        print(f"🤖 Bot: @{bot.get_me().username}")
        print(f"👑 Owner: {BOT_OWNER_ID}")
        
        # Start polling
        bot.infinity_polling(none_stop=True, interval=1)
        
    except Exception as e:
        print(f"❌ Bot error: {e}")
        bot_status["status"] = f"Error: {str(e)}"

# Flask routes
@app.route('/')
def index():
    return """
    <h1>ChatAudit Bot Dashboard</h1>
    <p>Bot is running successfully!</p>
    <a href="/dashboard">Open Dashboard</a><br>
    <a href="/health">Health Check</a>
    """

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "bot_status": bot_status,
        "timestamp": datetime.now(IST).isoformat()
    })

@app.route('/dashboard')
def dashboard():
    # Get statistics
    users = get_whitelisted_users()
    posts = get_scheduled_posts()
    
    current_time = datetime.now(IST).strftime('%d/%m/%Y %H:%M:%S IST')
    
    dashboard_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{BOT_NAME} Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .card {{ background: white; border-radius: 8px; padding: 20px; margin: 10px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .status-online {{ color: #28a745; }}
            .status-error {{ color: #dc3545; }}
            .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; }}
            .stat-card {{ background: #007bff; color: white; padding: 15px; border-radius: 5px; text-align: center; }}
            .user-list {{ list-style: none; padding: 0; }}
            .user-item {{ background: #f8f9fa; margin: 5px 0; padding: 10px; border-radius: 4px; border-left: 4px solid #007bff; }}
            h1, h2 {{ color: #333; }}
            .refresh-btn {{ background: #28a745; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }}
            .refresh-btn:hover {{ background: #218838; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <h1>🤖 {BOT_NAME} Dashboard</h1>
                <p><strong>Current Time:</strong> {current_time}</p>
                <p><strong>Bot Status:</strong> 
                    <span class="{'status-online' if bot_status['status'] == 'Online' else 'status-error'}">
                        {bot_status['status']}
                    </span>
                </p>
                <button class="refresh-btn" onclick="location.reload()">🔄 Refresh</button>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <h3>{len(users)}</h3>
                    <p>Whitelisted Users</p>
                </div>
                <div class="stat-card">
                    <h3>{len(posts)}</h3>
                    <p>Scheduled Posts</p>
                </div>
                <div class="stat-card">
                    <h3>{sum(1 for p in posts if p[6])}</h3>
                    <p>Self-Destruct Posts</p>
                </div>
                <div class="stat-card">
                    <h3>8080</h3>
                    <p>Server Port</p>
                </div>
            </div>
            
            <div class="card">
                <h2>👥 Whitelisted Users</h2>
                <ul class="user-list">
                    {''.join([f'<li class="user-item"><strong>{"@" + user[1] if user[1] else user[2] or "Unknown"}</strong> (ID: {user[0]})</li>' for user in users]) if users else '<li class="user-item">No users found</li>'}
                </ul>
            </div>
            
            <div class="card">
                <h2>📅 Recent Scheduled Posts</h2>
                {'<br>'.join([f'<p><strong>{p[8] or "Unknown Channel"}</strong> - {p[5]}<br><em>{p[3][:100]}...</em></p>' for p in posts[:5]]) if posts else '<p>No scheduled posts</p>'}
            </div>
        </div>
    </body>
    </html>
    """
    
    return dashboard_html

@app.route('/api/bot-status')
def api_bot_status():
    return jsonify(bot_status)

@app.route('/api/users')
def api_users():
    return jsonify([{"user_id": u[0], "username": u[1], "first_name": u[2]} for u in get_whitelisted_users()])

# Main execution
if __name__ == '__main__':
    # Initialize database
    init_database()
    
    # Start bot in a separate thread
    if BOT_TOKEN:
        bot_thread = threading.Thread(target=start_bot, daemon=True)
        bot_thread.start()
    else:
        print("❌ BOT_TOKEN not found")
        bot_status["status"] = "Missing BOT_TOKEN"
    
    # Start Flask app
    port = int(os.getenv('PORT', 8080))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print(f"🌐 Starting web server on port {port}")
    print(f"🔗 Dashboard: http://localhost:{port}/dashboard")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
