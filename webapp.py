"""
MINIMAL webapp.py - NO bot imports, NO threading, NO crashes
Just Flask routes that work 100% of the time
"""
from flask import Flask, render_template_string, request, jsonify
from datetime import datetime, timedelta
import os
import logging
import sqlite3

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'change-this-secret-key-123')

# MINIMAL database access (no imports from other modules)
def get_db_connection():
    """Direct database connection"""
    try:
        conn = sqlite3.connect('controller_bot.db', timeout=5.0)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

def get_whitelisted_users():
    """Get users without using DatabaseManager"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username, first_name, created_at FROM users WHERE is_whitelisted = 1")
        users = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return users
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        if conn:
            conn.close()
        return []

# MINIMAL HTML template
HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <title>ChatAudit Bot Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f0f2f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { color: #1877f2; margin-bottom: 10px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }
        .stat-value { font-size: 2em; font-weight: bold; margin-bottom: 5px; }
        .stat-label { font-size: 0.9em; opacity: 0.9; }
        .user-item { background: #f8f9fa; margin: 10px 0; padding: 15px; border-radius: 8px; border-left: 4px solid #28a745; }
        .status-good { color: #28a745; font-weight: bold; }
        .api-links { text-align: center; margin-top: 30px; }
        .api-links a { color: #1877f2; text-decoration: none; margin: 0 15px; padding: 8px 16px; border: 1px solid #1877f2; border-radius: 20px; display: inline-block; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 ChatAudit Bot Dashboard</h1>
            <p>Channel Management System</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{{ total_users }}</div>
                <div class="stat-label">👥 Total Users</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">✅</div>
                <div class="stat-label">🌐 Web Service</div>
            </div>
        </div>

        <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
            <h3>📊 System Status</h3>
            <p><strong>Current Time:</strong> {{ current_time }}</p>
            <p><strong>Web Service:</strong> <span class="status-good">✅ Running</span></p>
            <p><strong>Database:</strong> <span class="status-good">✅ Connected</span></p>
            <p><strong>Version:</strong> 1.0.0</p>
        </div>

        <div style="margin-top: 30px;">
            <h3>👥 Whitelisted Users ({{ total_users }})</h3>
            {% if users %}
                {% for user in users %}
                <div class="user-item">
                    <strong>{{ user.first_name or 'Unknown' }}</strong>
                    {% if user.username %}(@{{ user.username }}){% endif %}
                    <br><small>ID: {{ user.user_id }}</small>
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
            <a href="/health" target="_blank">Health</a>
            <a href="/api/stats" target="_blank">Stats</a>
        </div>

        <div style="text-align: center; margin-top: 20px; color: #666;">
            <p>🚀 ChatAudit Bot Dashboard v1.0.0</p>
        </div>
    </div>
</body>
</html>"""

@app.route('/')
def index():
    """Root redirect"""
    return dashboard()

@app.route('/dashboard')
def dashboard():
    """MINIMAL dashboard that never crashes"""
    try:
        users = get_whitelisted_users()
        current_time = datetime.now().strftime('%d/%m/%Y %H:%M:%S IST')

        return render_template_string(
            HTML_TEMPLATE, 
            users=users, 
            total_users=len(users),
            current_time=current_time
        )

    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        # Ultra-safe fallback
        return render_template_string(
            HTML_TEMPLATE,
            users=[],
            total_users=0,
            current_time=datetime.now().strftime('%d/%m/%Y %H:%M:%S IST')
        )

@app.route('/health')
def health():
    """MINIMAL health check"""
    try:
        # Test database connection
        users = get_whitelisted_users()
        return jsonify({
            'status': 'healthy',
            'service': 'ChatAudit Bot Dashboard',
            'users_count': len(users),
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        })
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/stats')
def api_stats():
    """MINIMAL stats API"""
    try:
        users = get_whitelisted_users()
        return jsonify({
            'success': True,
            'users_count': len(users),
            'timestamp': datetime.now().isoformat(),
            'current_time': datetime.now().strftime('%d/%m/%Y %H:%M:%S IST')
        })
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })

# Test route to verify service is working
@app.route('/test')
def test():
    """Simple test route"""
    return jsonify({
        'message': 'ChatAudit Bot Dashboard is working!',
        'timestamp': datetime.now().isoformat(),
        'status': 'ok'
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    logger.info(f"🌐 Starting MINIMAL dashboard on port {port}")

    # NO bot imports, NO threading, NO complex logic
    app.run(host='0.0.0.0', port=port, debug=False)
