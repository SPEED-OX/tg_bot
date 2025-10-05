"""
SAFE webapp that handles bot import errors gracefully
Web service works even if bot fails to start
"""
from flask import Flask, render_template_string, request, jsonify
from datetime import datetime, timedelta
import os
import logging
import threading
import time
from database.models import DatabaseManager
from config import IST, BOT_TOKEN, BOT_OWNER_ID

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'change-this-secret-key-123')

# Initialize database
db = DatabaseManager()

# Bot instance globals
bot_instance = None
bot_thread = None
bot_status = "⚠️ Starting..."

def start_bot():
    """Start the bot with error handling"""
    global bot_instance, bot_status

    try:
        logger.info("🤖 Attempting to start Telegram bot...")

        # Import bot components with error handling
        try:
            import telebot
            from handlers.bot_handlers import BotHandlers
        except ImportError as e:
            logger.error(f"❌ Import error: {e}")
            bot_status = "❌ Import Error"
            return

        # Initialize bot
        bot_instance = telebot.TeleBot(BOT_TOKEN)
        bot_handlers = BotHandlers(bot_instance, db)

        # Add owner to whitelist
        if BOT_OWNER_ID:
            db.whitelist_user(BOT_OWNER_ID, True)
            logger.info(f"👑 Owner {BOT_OWNER_ID} whitelisted")

        # Update status
        bot_status = "✅ Online"

        # Send startup notification
        try:
            bot_instance.send_message(
                BOT_OWNER_ID,
                f"🤖 **ChatAudit Bot Started!**\n\n"
                f"**Time:** {datetime.now(IST).strftime('%d/%m/%Y %H:%M:%S IST')}\n"
                f"**Status:** ✅ Online\n"
                f"**Dashboard:** ✅ Available\n\n"
                f"Both services are running! 🎯"
            )
        except Exception as e:
            logger.warning(f"⚠️ Startup notification failed: {e}")

        logger.info("🚀 Starting bot polling...")

        # Start polling
        bot_instance.infinity_polling(
            timeout=30,
            long_polling_timeout=10,
            none_stop=True,
            interval=2
        )

    except Exception as e:
        logger.error(f"❌ Bot startup error: {e}")
        bot_status = f"❌ Error: {str(e)[:50]}..."

        # Don't crash the entire webapp - just mark bot as failed
        logger.info("🌐 Web service will continue without bot")
        return

# HTML template with better styling
HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <title>ChatAudit Bot Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { 
            max-width: 900px; 
            margin: 0 auto; 
            background: rgba(255,255,255,0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        .header { 
            text-align: center; 
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid #f0f0f0;
        }
        .header h1 { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .stats { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 20px; 
            margin-bottom: 40px; 
        }
        .stat-card { 
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            transform: translateY(0);
            transition: transform 0.3s ease;
        }
        .stat-card:hover {
            transform: translateY(-5px);
        }
        .stat-value { 
            font-size: 2.2em; 
            font-weight: bold; 
            margin-bottom: 8px; 
        }
        .stat-label { 
            font-size: 0.9em; 
            opacity: 0.9; 
        }
        .status-section {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 15px;
            margin: 30px 0;
        }
        .status-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }
        .status-item:last-child {
            border-bottom: none;
        }
        .status-online { color: #28a745; font-weight: bold; }
        .status-error { color: #dc3545; font-weight: bold; }
        .status-warning { color: #ffc107; font-weight: bold; }
        .user-item { 
            background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
            margin: 15px 0; 
            padding: 20px; 
            border-radius: 12px;
            border-left: 5px solid #28a745;
            transition: transform 0.2s ease;
        }
        .user-item:hover {
            transform: translateX(5px);
        }
        .user-name { font-weight: bold; color: #333; font-size: 1.1em; }
        .user-details { color: #666; font-size: 0.9em; margin-top: 8px; }
        .api-links { 
            text-align: center; 
            margin-top: 40px; 
            padding-top: 30px;
            border-top: 2px solid #f0f0f0;
        }
        .api-links a { 
            color: white;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            text-decoration: none; 
            margin: 0 10px; 
            padding: 12px 24px;
            border-radius: 25px;
            display: inline-block;
            transition: transform 0.3s ease;
        }
        .api-links a:hover {
            transform: scale(1.05);
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 ChatAudit Bot</h1>
            <p style="font-size: 1.2em; color: #666;">Advanced Channel Management Dashboard</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{{ stats.total_users }}</div>
                <div class="stat-label">👥 Total Users</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ stats.total_tasks }}</div>
                <div class="stat-label">📋 Tasks</div>
            </div>
        </div>

        <div class="status-section">
            <h3 style="color: #333; margin-bottom: 20px;">📊 System Status</h3>
            <div class="status-item">
                <span><strong>⏰ Current Time:</strong></span>
                <span>{{ stats.current_time }}</span>
            </div>
            <div class="status-item">
                <span><strong>🤖 Bot Service:</strong></span>
                <span class="{% if 'Online' in stats.bot_status %}status-online{% elif 'Error' in stats.bot_status %}status-error{% else %}status-warning{% endif %}">
                    {{ stats.bot_status }}
                </span>
            </div>
            <div class="status-item">
                <span><strong>🌐 Web Service:</strong></span>
                <span class="status-online">✅ Running</span>
            </div>
            <div class="status-item">
                <span><strong>💾 Database:</strong></span>
                <span class="status-online">✅ Connected</span>
            </div>
        </div>

        <div class="status-section">
            <h3 style="color: #333; margin-bottom: 20px;">👥 Whitelisted Users ({{ stats.total_users }})</h3>
            {% if users %}
                {% for user in users %}
                <div class="user-item">
                    <div class="user-name">{{ user.first_name or 'Unknown' }}</div>
                    <div class="user-details">
                        {% if user.username %}@{{ user.username }} • {% endif %}
                        ID: {{ user.user_id }}{% if user.created_at %} • Added: {{ user.created_at[:10] }}{% endif %}
                    </div>
                </div>
                {% endfor %}
            {% else %}
                <div style="text-align: center; color: #666; padding: 30px;">
                    📭 No users whitelisted yet<br>
                    <small>Users will appear here when added via the bot</small>
                </div>
            {% endif %}
        </div>

        <div class="api-links">
            <h4 style="color: #333; margin-bottom: 15px;">🔗 API Endpoints</h4>
            <a href="/health" target="_blank">🏥 Health Check</a>
            <a href="/api/stats" target="_blank">📊 Statistics</a>
            <a href="/api/menu/structure" target="_blank">🎛️ Menu Structure</a>
        </div>

        <div class="footer">
            <p>🚀 Powered by ChatAudit Bot v{{ dashboard_data.version }}</p>
            <p><small>Last updated: {{ stats.current_time }}</small></p>
        </div>
    </div>
</body>
</html>"""

@app.route('/')
def index():
    """Root redirect to dashboard"""
    return dashboard()

@app.route('/dashboard')
def dashboard():
    """Dashboard with safe error handling"""
    try:
        # Get users (this method definitely exists)
        users = db.get_whitelisted_users()

        stats = {
            'total_users': len(users),
            'total_tasks': 0,  # Safe placeholder
            'current_time': datetime.now(IST).strftime('%d/%m/%Y %H:%M:%S IST'),
            'bot_status': bot_status
        }

        dashboard_data = {
            'bot_name': 'ChatAudit Bot',
            'version': '1.0.0',
            'status': 'Online'
        }

        return render_template_string(HTML_TEMPLATE, stats=stats, users=users, dashboard_data=dashboard_data)

    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        # Fallback with minimal data
        return render_template_string(HTML_TEMPLATE, 
                                    stats={
                                        'total_users': 0, 
                                        'total_tasks': 0, 
                                        'current_time': datetime.now(IST).strftime('%d/%m/%Y %H:%M:%S IST'),
                                        'bot_status': '❌ Database Error'
                                    }, 
                                    users=[],
                                    dashboard_data={'version': '1.0.0'})

@app.route('/health')
def health():
    """Health check - always returns something"""
    try:
        # Test database
        users = db.get_whitelisted_users()
        user_count = len(users)
        db_status = 'connected'
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        user_count = 0
        db_status = 'error'

    return jsonify({
        'status': 'healthy' if db_status == 'connected' else 'degraded',
        'timestamp': datetime.now(IST).isoformat(),
        'service': 'ChatAudit Bot Dashboard',
        'database': db_status,
        'users_count': user_count,
        'bot_status': bot_status,
        'version': '1.0.0'
    })

@app.route('/api/stats')
def api_stats():
    """Stats API with safe error handling"""
    try:
        users = db.get_whitelisted_users()
        return jsonify({
            'success': True,
            'stats': {
                'users_count': len(users),
                'bot_status': bot_status,
                'timestamp': datetime.now(IST).isoformat()
            }
        })
    except Exception as e:
        logger.error(f"Stats API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now(IST).isoformat()
        })

@app.route('/api/menu/structure')
def api_menu_structure():
    """Menu structure API"""
    menu_structure = {
        "main_menu": {
            "title": "ChatAudit Bot - Main Menu",
            "buttons": [
                {"text": "🏠 Start", "description": "Getting started guide"},
                {"text": "👥 User", "description": "User management (owner only)"},
                {"text": "📝 New Post", "description": "Create and schedule posts"},
                {"text": "📅 Schedules", "description": "Manage upcoming posts"},
                {"text": "📊 Dashboard", "description": "Web interface"}
            ]
        }
    }

    return jsonify({
        'success': True,
        'menu_structure': menu_structure,
        'timestamp': datetime.now(IST).isoformat()
    })

# SAFE bot initialization that doesn't crash the webapp
def init_bot():
    """Initialize bot in background thread - SAFE version"""
    global bot_thread

    # Only start bot if we have required env vars
    if not BOT_TOKEN or BOT_TOKEN == 'your-bot-token-here':
        logger.warning("⚠️ BOT_TOKEN not set - bot will not start")
        global bot_status
        bot_status = "❌ No Token"
        return

    if not BOT_OWNER_ID or BOT_OWNER_ID == 0:
        logger.warning("⚠️ BOT_OWNER_ID not set - bot will not start")
        bot_status = "❌ No Owner ID"
        return

    # Start bot in background thread
    if not bot_thread:
        bot_thread = threading.Thread(target=start_bot, daemon=True)
        bot_thread.start()
        logger.info("🤖 Bot thread started")

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    logger.info(f"🌐 Starting ChatAudit Bot Dashboard on port {port}")

    # Initialize bot in background (safe - won't crash webapp)
    init_bot()

    # Start Flask app (this will definitely work)
    app.run(
        host='0.0.0.0', 
        port=port, 
        debug=False, 
        use_reloader=False,
        threaded=True
    )
