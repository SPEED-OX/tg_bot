from flask import Flask, render_template, jsonify
import os
from datetime import datetime, timezone, timedelta
import sqlite3

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'techgeekz-secret')

IST = timezone(timedelta(hours=5, minutes=30))
BOT_NAME = "TechGeekZ Bot"

def get_users():
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
    return f"""
    <h1>{BOT_NAME}</h1>
    <p>Status: Online</p>
    <p><a href="/dashboard">Dashboard</a></p>
    <p><a href="/health">Health Check</a></p>
    """

@app.route('/dashboard')
def dashboard():
    users = get_users()
    current_time = datetime.now(IST).strftime('%d/%m/%Y %H:%M:%S IST')
    return render_template('dashboard.html',
        bot_name=BOT_NAME,
        total_users=len(users),
        whitelisted_users=users,
        current_time=current_time,
        bot_status="Online"
    )

@app.route('/health')
def health():
    users = get_users()
    return jsonify({'status': 'healthy', 'bot_name': BOT_NAME,
                    'users_count': len(users), 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
