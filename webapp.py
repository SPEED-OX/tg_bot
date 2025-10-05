"""
ChatAudit Bot - Web Dashboard
Clean web service that uses templates/dashboard.html
"""
from flask import Flask, render_template, jsonify, request
import os
from datetime import datetime
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.models import DatabaseManager
from config import SECRET_KEY, BOT_NAME

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Initialize database
db = DatabaseManager()

@app.route('/')
def index():
    return f"""
    <div style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center;">
        <h1>{BOT_NAME}</h1>
        <p>Bot and dashboard are running successfully!</p>
        <p><a href="/dashboard" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Open Dashboard</a></p>
        <p><a href="/health" style="color: #007bff;">Health Check</a></p>
    </div>
    """

@app.route('/dashboard')
def dashboard():
    """Dashboard using templates/dashboard.html"""
    try:
        # Get data for dashboard
        whitelisted_users = db.get_whitelisted_users()
        total_users = len(whitelisted_users)
        
        # Get scheduled posts (mock data for now)
        scheduled_posts = []
        self_destruct_posts = []
        
        current_time = datetime.now().strftime('%d/%m/%Y %H:%M:%S IST')
        
        return render_template('dashboard.html',
            bot_name=BOT_NAME,
            current_time=current_time,
            total_users=total_users,
            whitelisted_users=whitelisted_users,
            scheduled_posts=scheduled_posts,
            self_destruct_posts=self_destruct_posts,
            bot_status="Online"
        )
    except Exception as e:
        return f"""
        <div style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px;">
            <h1>{BOT_NAME} Dashboard</h1>
            <p><strong>Status:</strong> Running</p>
            <p><strong>Error:</strong> {str(e)}</p>
            <p><a href="/health">Health Check</a></p>
        </div>
        """

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        users = db.get_whitelisted_users()
        return jsonify({
            'status': 'healthy',
            'users_count': len(users),
            'port': int(os.getenv('PORT', 8080)),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/users')
def api_users():
    """API endpoint for user data"""
    try:
        users = db.get_whitelisted_users()
        return jsonify([{
            'user_id': user[0],
            'username': user[1],
            'first_name': user[2],
            'is_whitelisted': user[3]
        } for user in users])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/test')
def test():
    """Simple test endpoint"""
    return jsonify({
        'message': f'{BOT_NAME} webapp is working!',
        'timestamp': datetime.now().isoformat(),
        'port': int(os.getenv('PORT', 8080))
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
