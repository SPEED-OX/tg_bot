"""
TechGeekZ Bot - Simple Flask Web Server
Only handles web routes, uses templates/dashboard.html
"""
from flask import Flask, render_template, jsonify
import os
import sys
from datetime import datetime, timezone, timedelta

# Simple setup
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'simple-key')

# Simple timezone
IST = timezone(timedelta(hours=5, minutes=30))
BOT_NAME = "TechGeekZ Bot"

def get_users():
    """Simple database query"""
    try:
        import sqlite3
        conn = sqlite3.connect('techgeekz.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, username, first_name FROM users WHERE is_whitelisted = 1')
        users = cursor.fetchall()
        conn.close()
        return users
    except:
        return []

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/')
def index():
    return f"""
    <div style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center;">
        <h1>{BOT_NAME}</h1>
        <p>Status: <strong style="color: green;">Online</strong></p>
        <p><a href="/dashboard" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Open Dashboard</a></p>
        <p><a href="/health">Health Check</a></p>
    </div>
    """

@app.route('/dashboard')
def dashboard():
    """Uses templates/dashboard.html"""
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
            bot_status="Online"
        )
    except Exception as e:
        return f"Dashboard Error: {str(e)}"

@app.route('/health')
def health():
    try:
        users = get_users()
        return jsonify({
            'status': 'healthy',
            'bot_name': BOT_NAME,
            'users_count': len(users),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
