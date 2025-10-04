"""
webapp.py - CORRECTED IMPORTS for flat directory structure
Replace the import section at the top of your webapp.py with this:
"""
from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import os
import logging

# Corrected imports for flat structure  
from models import DatabaseManager
from config import IST

# Rest of your webapp.py code remains the same...

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'change-this-secret-key-123')

# Initialize database
db = DatabaseManager()

@app.route('/')
def index():
    """Main page redirect"""
    return render_template('dashboard.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard main page"""
    try:
        # Get statistics
        users = db.get_whitelisted_users()
        channels = db.get_channels() if hasattr(db, 'get_channels') else []
        today_tasks = db.get_daily_tasks(datetime.now(IST))

        stats = {
            'total_users': len(users),
            'total_channels': len(channels),
            'pending_posts': today_tasks['scheduled_posts'],
            'self_destructs': today_tasks['self_destruct_tasks']
        }

        return render_template('dashboard.html', 
                             stats=stats, 
                             users=users, 
                             channels=channels)
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return render_template('dashboard.html', 
                             stats={'total_users': 0, 'total_channels': 0, 'pending_posts': 0, 'self_destructs': 0},
                             users=[], 
                             channels=[])

@app.route('/api/whitelist', methods=['GET', 'POST', 'DELETE'])
def api_whitelist():
    """API endpoint for managing whitelist"""
    try:
        if request.method == 'GET':
            users = db.get_whitelisted_users()
            return jsonify(users)

        elif request.method == 'POST':
            data = request.get_json()
            user_id = data.get('user_id')
            if user_id:
                db.whitelist_user(int(user_id), True)
                return jsonify({'success': True, 'message': f'User {user_id} whitelisted'})
            return jsonify({'success': False, 'message': 'Invalid user ID'})

        elif request.method == 'DELETE':
            data = request.get_json()
            user_id = data.get('user_id')
            if user_id:
                db.whitelist_user(int(user_id), False)
                return jsonify({'success': True, 'message': f'User {user_id} removed'})
            return jsonify({'success': False, 'message': 'Invalid user ID'})

    except Exception as e:
        logger.error(f"API error: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/stats')
def api_stats():
    """Get bot statistics"""
    try:
        users = db.get_whitelisted_users()
        today_tasks = db.get_daily_tasks(datetime.now(IST))

        return jsonify({
            'users': len(users),
            'scheduled_posts': today_tasks['scheduled_posts'],
            'self_destructs': today_tasks['self_destruct_tasks'],
            'timestamp': datetime.now(IST).isoformat()
        })
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({'error': str(e)})

@app.route('/health')
def health():
    """Health check for Railway"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(IST).isoformat(),
        'service': 'Controller Bot Dashboard'
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'

    logger.info(f"🌐 Starting dashboard on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
