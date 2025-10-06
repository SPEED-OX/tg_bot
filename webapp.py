"""
TechGeekZ Bot - Combined Bot + Web Dashboard
Runs both Telegram bot and Flask webapp in same process
"""
from flask import Flask, render_template, jsonify
import os
import sys
import threading
import time
import requests
from datetime import datetime, timezone, timedelta

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import BOT_TOKEN, BOT_OWNER_ID, BOT_NAME, IST, WEBAPP_URL, format_time, format_start_time
from database.models import DatabaseManager
from handlers.bot_handlers import BotHandlers

# Flask app initialization
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'techgeekz-secret-key')

# Global variables
bot_instance = None
bot_status = "Starting..."
db = None

def get_dashboard_status():
    """Check if dashboard is online"""
    try:
        if not WEBAPP_URL:
            return "Offline"
        response = requests.get(f"{WEBAPP_URL}/health", timeout=5)
        return "Online" if response.status_code == 200 else "Offline"
    except:
        return "Offline"

def get_owner_details(bot):
    """Get owner's Telegram details"""
    try:
        owner_info = bot.get_chat(BOT_OWNER_ID)
        first = owner_info.first_name or ""
        last = owner_info.last_name or ""
        nickname = f"{first} {last}".strip()
        username = f"@{owner_info.username}" if owner_info.username else "NoUsername"
        return f"{nickname} {username}".strip()
    except:
        return f"Owner @{BOT_OWNER_ID}"

def start_bot():
    """Start the Telegram bot in background thread"""
    global bot_instance, bot_status, db
    
    try:
        print(f"🤖 Starting {BOT_NAME} bot thread...")
        
        # Initialize database
        db = DatabaseManager()
        print("✅ Database initialized")
        
        # Add owner to whitelist
        db.add_user_to_whitelist(BOT_OWNER_ID, "Owner", "Bot Owner")
        print(f"👑 Owner {BOT_OWNER_ID} added to whitelist")
        
        # Initialize bot handlers
        bot_handlers = BotHandlers(db)
        bot_instance = bot_handlers.bot
        
        print(f"🤖 Bot: @{bot_instance.get_me().username}")
        
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
            print(f"📨 Deployment notification sent to owner")
        except Exception as e:
            print(f"⚠️ Could not send deployment notification: {e}")
        
        bot_status = "Online"
        print("✅ Bot polling started")
        
        # Start polling (this blocks this thread)
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
    except:
        return []

# Flask routes
@app.route('/')
def index():
    return f"""
    <div style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center;">
        <h1>{BOT_NAME}</h1>
        <p>Bot Status: <strong>{bot_status}</strong></p>
        <p>Bot and dashboard are running successfully!</p>
        <p><a href="/dashboard" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Open Dashboard</a></p>
        <p><a href="/health" style="color: #007bff;">Health Check</a></p>
    </div>
    """

@app.route('/dashboard')
def dashboard():
    """Dashboard using templates/dashboard.html"""
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
            'timestamp': datetime.now().isoformat(),
            'dashboard_status': 'Online'
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
    """API endpoint for user data"""
    try:
        users = get_users()
        return jsonify([{
            'user_id': user[0] if len(user) > 0 else 0,
            'username': user[1] if len(user) > 1 else '',
            'first_name': user[2] if len(user) > 2 else ''
        } for user in users])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/test')
def test():
    """Simple test endpoint"""
    return jsonify({
        'message': f'{BOT_NAME} webapp is working!',
        'bot_status': bot_status,
        'timestamp': datetime.now().isoformat(),
        'port': int(os.getenv('PORT', 8080))
    })

# Main execution
if __name__ == '__main__':
    print(f"🚀 Starting {BOT_NAME} combined service...")
    
    # Start bot in background thread
    if BOT_TOKEN and BOT_OWNER_ID:
        bot_thread = threading.Thread(target=start_bot, daemon=True)
        bot_thread.start()
        print("🤖 Bot thread started")
        
        # Give bot time to initialize
        time.sleep(3)
    else:
        print("❌ Missing BOT_TOKEN or BOT_OWNER_ID")
        bot_status = "Missing credentials"
    
    # Start Flask app (this blocks main thread)
    port = int(os.getenv('PORT', 8080))
    print(f"🌐 Starting Flask app on port {port}")
    
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
