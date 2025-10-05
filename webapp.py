"""
FIXED Flask Web Application for ChatAudit Bot Dashboard
Works with current database structure - no missing methods
"""
from flask import Flask, render_template_string, request, jsonify
from datetime import datetime, timedelta
import os
import logging
from database.models import DatabaseManager
from config import IST

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'change-this-secret-key-123')

# Initialize database
db = DatabaseManager()

# Basic HTML template embedded
HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <title>ChatAudit Bot Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f0f2f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }
        .header { text-align: center; margin-bottom: 40px; }
        .header h1 { color: #1877f2; margin-bottom: 10px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 40px; }
        .stat-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }
        .stat-value { font-size: 2.5em; font-weight: bold; margin-bottom: 5px; }
        .stat-label { font-size: 0.9em; opacity: 0.9; }
        .section { margin: 30px 0; }
        .section h3 { color: #333; border-bottom: 2px solid #1877f2; padding-bottom: 10px; }
        .user-item { background: #f8f9fa; margin: 10px 0; padding: 15px; border-radius: 8px; border-left: 4px solid #28a745; }
        .user-name { font-weight: bold; color: #333; }
        .user-details { color: #666; font-size: 0.9em; margin-top: 5px; }
        .status-online { color: #28a745; }
        .status-error { color: #dc3545; }
        .api-links { text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; }
        .api-links a { color: #1877f2; text-decoration: none; margin: 0 15px; padding: 8px 16px; border: 1px solid #1877f2; border-radius: 20px; display: inline-block; transition: all 0.3s; }
        .api-links a:hover { background: #1877f2; color: white; }
        .feature-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 20px; }
        .feature-item { background: #e7f3ff; padding: 15px; border-radius: 8px; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 ChatAudit Bot Dashboard</h1>
            <p>Advanced Telegram Channel Management System</p>
            <p><strong>Status:</strong> <span class="status-online">{{ stats.bot_status }}</span> | <strong>Version:</strong> {{ dashboard_data.version }}</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{{ stats.total_users }}</div>
                <div class="stat-label">Total Users</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ stats.pending_posts }}</div>
                <div class="stat-label">Scheduled Posts</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ stats.self_destructs }}</div>
                <div class="stat-label">Self-Destruct Tasks</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ stats.total_tasks }}</div>
                <div class="stat-label">Total Tasks</div>
            </div>
        </div>

        <div class="section">
            <h3>📊 System Information</h3>
            <div class="feature-grid">
                <div class="feature-item">
                    <strong>⏰ Current Time</strong><br>
                    {{ stats.current_time }}
                </div>
                <div class="feature-item">
                    <strong>📅 Next Task</strong><br>
                    {{ stats.next_task }}
                </div>
                <div class="feature-item">
                    <strong>🔧 Service Status</strong><br>
                    {{ stats.bot_status }}
                </div>
                <div class="feature-item">
                    <strong>💾 Database</strong><br>
                    ✅ Connected
                </div>
            </div>
        </div>

        <div class="section">
            <h3>👥 Whitelisted Users ({{ stats.total_users }})</h3>
            {% if users %}
                {% for user in users %}
                <div class="user-item">
                    <div class="user-name">{{ user.first_name or 'Unknown' }}</div>
                    <div class="user-details">
                        {% if user.username %}@{{ user.username }} • {% endif %}
                        ID: {{ user.user_id }} • 
                        Added: {{ user.created_at[:10] if user.created_at else 'Unknown' }}
                    </div>
                </div>
                {% endfor %}
            {% else %}
                <div style="text-align: center; color: #666; padding: 20px;">
                    📭 No users whitelisted yet
                </div>
            {% endif %}
        </div>

        <div class="api-links">
            <h4>🔗 API Endpoints</h4>
            <a href="/health" target="_blank">Health Check</a>
            <a href="/api/stats" target="_blank">Statistics</a>
            <a href="/api/whitelist" target="_blank">Whitelist API</a>
            <a href="/api/menu/structure" target="_blank">Menu Structure</a>
        </div>

        <div style="text-align: center; margin-top: 20px; color: #666; font-size: 0.9em;">
            <p>🚀 Powered by ChatAudit Bot v{{ dashboard_data.version }} | Last updated: {{ stats.current_time }}</p>
        </div>
    </div>
</body>
</html>"""

@app.route('/')
def index():
    """Main page redirect to dashboard"""
    return dashboard()

@app.route('/dashboard')
def dashboard():
    """Dashboard main page with statistics - FIXED to work with current database"""
    try:
        # Get users (this method exists)
        users = db.get_whitelisted_users()

        # REMOVED calls to methods that don't exist yet
        stats = {
            'total_users': len(users),
            'pending_posts': 0,  # Placeholder - implement later
            'self_destructs': 0, # Placeholder - implement later  
            'total_tasks': 0,    # Placeholder - implement later
            'next_task': 'None', # Placeholder - implement later
            'current_time': datetime.now(IST).strftime('%d/%m/%Y %H:%M:%S IST'),
            'bot_status': '✅ Online'
        }

        dashboard_data = {
            'bot_name': 'ChatAudit Bot',
            'version': '1.0.0',
            'status': 'Online'
        }

        return render_template_string(HTML_TEMPLATE, 
                                    stats=stats, 
                                    users=users, 
                                    dashboard_data=dashboard_data)

    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        # Return fallback data
        stats = {
            'total_users': 0, 
            'pending_posts': 0, 
            'self_destructs': 0,
            'total_tasks': 0,
            'next_task': 'Error loading',
            'current_time': datetime.now(IST).strftime('%d/%m/%Y %H:%M:%S IST'),
            'bot_status': '❌ Error'
        }

        dashboard_data = {
            'bot_name': 'ChatAudit Bot',
            'version': '1.0.0',
            'status': 'Error'
        }

        return render_template_string(HTML_TEMPLATE,
                                    stats=stats,
                                    users=[], 
                                    dashboard_data=dashboard_data)

@app.route('/api/whitelist', methods=['GET', 'POST', 'DELETE'])
def api_whitelist():
    """API endpoint for managing whitelist"""
    try:
        if request.method == 'GET':
            users = db.get_whitelisted_users()
            return jsonify({
                'success': True,
                'users': users,
                'count': len(users)
            })

        elif request.method == 'POST':
            data = request.get_json()
            user_id = data.get('user_id')

            if user_id:
                clean_user_id = abs(int(str(user_id).replace('-', '')))
                db.whitelist_user(clean_user_id, True)

                return jsonify({
                    'success': True, 
                    'message': f'User {clean_user_id} whitelisted successfully',
                    'user_id': clean_user_id
                })
            return jsonify({'success': False, 'message': 'Invalid user ID'})

        elif request.method == 'DELETE':
            data = request.get_json()
            user_id = data.get('user_id')

            if user_id:
                clean_user_id = abs(int(str(user_id).replace('-', '')))
                db.whitelist_user(clean_user_id, False)

                return jsonify({
                    'success': True, 
                    'message': f'User {clean_user_id} removed successfully',
                    'user_id': clean_user_id
                })
            return jsonify({'success': False, 'message': 'Invalid user ID'})

    except Exception as e:
        logger.error(f"API whitelist error: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/stats')
def api_stats():
    """Get comprehensive bot statistics - FIXED"""
    try:
        users = db.get_whitelisted_users()

        return jsonify({
            'success': True,
            'stats': {
                'users': len(users),
                'scheduled_posts': 0,  # Placeholder
                'self_destructs': 0,   # Placeholder
                'total_tasks': 0,      # Placeholder
                'next_task': None,
                'next_task_formatted': 'None'
            },
            'timestamp': datetime.now(IST).isoformat(),
            'current_time': datetime.now(IST).strftime('%d/%m/%Y %H:%M:%S IST')
        })

    except Exception as e:
        logger.error(f"Stats API error: {e}")
        return jsonify({
            'success': False, 
            'error': str(e),
            'timestamp': datetime.now(IST).isoformat()
        })

@app.route('/api/schedule')
def api_schedule():
    """Get scheduled tasks information - SIMPLIFIED"""
    try:
        return jsonify({
            'success': True,
            'scheduled_posts': [],     # Placeholder
            'self_destruct_tasks': [], # Placeholder
            'total_upcoming': 0,
            'timestamp': datetime.now(IST).isoformat()
        })

    except Exception as e:
        logger.error(f"Schedule API error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/health')
def health():
    """Health check endpoint for Railway"""
    try:
        # Test database connection
        users = db.get_whitelisted_users()

        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now(IST).isoformat(),
            'service': 'ChatAudit Bot Dashboard',
            'database': 'connected',
            'users_count': len(users),
            'version': '1.0.0'
        })

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now(IST).isoformat(),
            'service': 'ChatAudit Bot Dashboard',
            'database': 'error',
            'error': str(e),
            'version': '1.0.0'
        }), 500

@app.route('/api/menu/structure')
def api_menu_structure():
    """API endpoint providing the inline menu structure for web dashboard"""
    menu_structure = {
        "main_menu": {
            "title": "ChatAudit Bot - Main Menu",
            "buttons": [
                {"text": "🏠 Start", "callback_data": "menu_start", "description": "Getting started guide"},
                {"text": "👥 User", "callback_data": "menu_user", "description": "User management (owner only)", "owner_only": True},
                {"text": "📝 New Post", "callback_data": "menu_new_post", "description": "Create and schedule posts"},
                {"text": "📅 Schedules", "callback_data": "menu_schedules", "description": "Manage upcoming posts"},
                {"text": "📊 Dashboard", "type": "web_app", "description": "Web interface"}
            ]
        }
    }

    return jsonify({
        'success': True,
        'menu_structure': menu_structure,
        'timestamp': datetime.now(IST).isoformat()
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'

    logger.info(f"🌐 Starting ChatAudit Bot dashboard on port {port}")
    logger.info(f"📊 Dashboard URL: http://0.0.0.0:{port}/dashboard")
    logger.info(f"🔍 Health check: http://0.0.0.0:{port}/health")

    app.run(host='0.0.0.0', port=port, debug=debug)
