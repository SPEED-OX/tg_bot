"""
TechGeekZ Bot - Web Dashboard
Simple web service with health status endpoint
"""
from flask import Flask, render_template, jsonify
import os
import sqlite3
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'techgeekz-secret-key')

# Simple IST timezone
IST = timezone(timedelta(hours=5, minutes=30))

# Simple database functions
def get_users():
    """Get users from database"""
    try:
        conn = sqlite3.connect('techgeekz.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, username, first_name FROM users WHERE is_whitelisted = 1')
        users = cursor.fetchall()
        conn.close()
        return users
    except:
        return []

@app.route('/')
def index():
    return """
    <div style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center;">
        <h1>TechGeekZ Bot</h1>
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
            bot_name="TechGeekZ Bot",
            current_time=current_time,
            total_users=len(users),
            whitelisted_users=users,
            scheduled_posts=[],
            self_destruct_posts=[],
            bot_status="Online"
        )
    except Exception as e:
        return f"""
        <div style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px;">
            <h1>TechGeekZ Bot Dashboard</h1>
            <p><strong>Status:</strong> Running</p>
            <p><strong>Error:</strong> {str(e)}</p>
            <p><a href="/health">Health Check</a></p>
        </div>
        """

@app.route('/health')
def health():
    """Health check endpoint for dashboard status"""
    try:
        users = get_users()
        return jsonify({
            'status': 'healthy',
            'bot_name': 'TechGeekZ Bot',
            'users_count': len(users),
            'port': int(os.getenv('PORT', 8080)),
            'timestamp': datetime.now().isoformat(),
            'dashboard_status': 'Online'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'bot_name': 'TechGeekZ Bot',
            'timestamp': datetime.now().isoformat(),
            'dashboard_status': 'Offline'
        }), 500

@app.route('/api/users')
def api_users():
    """API endpoint for user data"""
    try:
        users = get_users()
        return jsonify([{
            'user_id': user[0],
            'username': user[1],
            'first_name': user[2]
        } for user in users])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/test')
def test():
    """Simple test endpoint"""
    return jsonify({
        'message': 'TechGeekZ Bot webapp is working!',
        'timestamp': datetime.now().isoformat(),
        'port': int(os.getenv('PORT', 8080))
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
