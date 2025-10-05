"""
COMBINED webapp that starts bot internally - SIMPLE approach
This runs both services in one process - most reliable for Railway
"""
from flask import Flask, render_template_string, request, jsonify
from datetime import datetime, timedelta
import os
import logging
import threading
import time
from database.models import DatabaseManager
from config import IST, BOT_TOKEN, BOT_OWNER_ID
import telebot

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'change-this-secret-key-123')

# Initialize database
db = DatabaseManager()

# Bot instance
bot_instance = None
bot_thread = None

def start_bot():
    """Start the bot in this process"""
    global bot_instance

    try:
        logger.info("🤖 Starting Telegram bot...")

        # Import and initialize bot
        from handlers.bot_handlers import BotHandlers

        bot_instance = telebot.TeleBot(BOT_TOKEN)
        bot_handlers = BotHandlers(bot_instance, db)

        # Add owner to whitelist
        if BOT_OWNER_ID:
            db.whitelist_user(BOT_OWNER_ID, True)

        # Start polling
        bot_instance.infinity_polling(none_stop=True, interval=2)

    except Exception as e:
        logger.error(f"Bot error: {e}")
        time.sleep(30)  # Wait before restart
        start_bot()  # Restart on error

# HTML template
HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <title>ChatAudit Bot Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f0f2f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 40px; }
        .header h1 { color: #1877f2; margin-bottom: 10px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 40px; }
        .stat-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }
        .stat-value { font-size: 2em; font-weight: bold; margin-bottom: 5px; }
        .stat-label { font-size: 0.9em; opacity: 0.9; }
        .user-item { background: #f8f9fa; margin: 10px 0; padding: 15px; border-radius: 8px; border-left: 4px solid #28a745; }
        .status-online { color: #28a745; }
        .api-links { text-align: center; margin-top: 30px; }
        .api-links a { color: #1877f2; text-decoration: none; margin: 0 15px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 ChatAudit Bot Dashboard</h1>
            <p>Advanced Channel Management System</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{{ stats.total_users }}</div>
                <div class="stat-label">Total Users</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ stats.total_tasks }}</div>
                <div class="stat-label">Tasks</div>
            </div>
        </div>

        <div>
            <h3>📊 System Status</h3>
            <p><strong>Current Time:</strong> {{ stats.current_time }}</p>
            <p><strong>Bot Status:</strong> <span class="status-online">✅ Online</span></p>
            <p><strong>Web Service:</strong> <span class="status-online">✅ Running</span></p>
        </div>

        <div>
            <h3>👥 Whitelisted Users ({{ stats.total_users }})</h3>
            {% if users %}
                {% for user in users %}
                <div class="user-item">
                    <strong>{{ user.first_name or 'Unknown' }}</strong>
                    {% if user.username %}(@{{ user.username }}){% endif %}
                    <br><small>ID: {{ user.user_id }}</small>
                </div>
                {% endfor %}
            {% else %}
                <p>No users whitelisted yet.</p>
            {% endif %}
        </div>

        <div class="api-links">
            <p><a href="/health">Health</a> | <a href="/api/stats">Stats</a> | <a href="/api/whitelist">Users API</a></p>
        </div>
    </div>
</body>
</html>"""

@app.route('/')
def index():
    return dashboard()

@app.route('/dashboard') 
def dashboard():
    """Dashboard with working database methods only"""
    try:
        users = db.get_whitelisted_users()

        stats = {
            'total_users': len(users),
            'total_tasks': 0,  # Placeholder
            'current_time': datetime.now(IST).strftime('%d/%m/%Y %H:%M:%S IST')
        }

        return render_template_string(HTML_TEMPLATE, stats=stats, users=users)

    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return render_template_string(HTML_TEMPLATE, 
                                    stats={'total_users': 0, 'total_tasks': 0, 'current_time': 'Error'}, 
                                    users=[])

@app.route('/health')
def health():
    """Health check"""
    try:
        users = db.get_whitelisted_users()
        return jsonify({
            'status': 'healthy',
            'service': 'ChatAudit Bot Dashboard',
            'users_count': len(users),
            'timestamp': datetime.now(IST).isoformat()
        })
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/api/stats')
def api_stats():
    """Basic stats API"""
    try:
        users = db.get_whitelisted_users()
        return jsonify({
            'success': True,
            'users_count': len(users),
            'timestamp': datetime.now(IST).isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Start bot in background when webapp starts
def init_bot():
    """Initialize bot in background thread"""
    global bot_thread
    if BOT_TOKEN and BOT_OWNER_ID and not bot_thread:
        bot_thread = threading.Thread(target=start_bot, daemon=True)
        bot_thread.start()
        logger.info("🤖 Bot thread started")

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    # Start bot in background
    init_bot()

    logger.info(f"🌐 Starting dashboard on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
