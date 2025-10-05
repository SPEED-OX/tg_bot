"""
Flask Web Application for ChatAudit Bot Dashboard
Complete webapp with inline menu integration
"""
from flask import Flask, render_template, request, jsonify
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

@app.route('/')
def index():
    """Main page redirect to dashboard"""
    return render_template('dashboard.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard main page with statistics"""
    try:
        # Get comprehensive statistics
        users = db.get_whitelisted_users()

        # Get scheduled tasks for today
        today_tasks = db.get_daily_tasks(datetime.now(IST))

        # Get next upcoming task
        next_task = db.get_next_task_time()
        next_task_str = next_task.strftime('%d/%m/%Y %H:%M IST') if next_task else 'None'

        stats = {
            'total_users': len(users),
            'pending_posts': today_tasks['scheduled_posts'],
            'self_destructs': today_tasks['self_destruct_tasks'],
            'total_tasks': today_tasks['total'],
            'next_task': next_task_str,
            'current_time': datetime.now(IST).strftime('%d/%m/%Y %H:%M:%S IST')
        }

        # Sample channels data (you can extend this)
        channels = []  # db.get_channels() if implemented

        return render_template('dashboard.html', 
                             stats=stats, 
                             users=users, 
                             channels=channels,
                             dashboard_data={
                                 'bot_name': 'ChatAudit Bot',
                                 'version': '1.0.0',
                                 'status': 'Online'
                             })

    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        # Return fallback data
        return render_template('dashboard.html', 
                             stats={
                                 'total_users': 0, 
                                 'pending_posts': 0, 
                                 'self_destructs': 0,
                                 'total_tasks': 0,
                                 'next_task': 'Error loading',
                                 'current_time': datetime.now(IST).strftime('%d/%m/%Y %H:%M:%S IST')
                             },
                             users=[], 
                             channels=[],
                             dashboard_data={
                                 'bot_name': 'ChatAudit Bot',
                                 'version': '1.0.0',
                                 'status': 'Error'
                             })

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
                # Remove - sign if present
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
                # Remove - sign if present
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
    """Get comprehensive bot statistics"""
    try:
        users = db.get_whitelisted_users()
        today_tasks = db.get_daily_tasks(datetime.now(IST))
        next_task = db.get_next_task_time()

        return jsonify({
            'success': True,
            'stats': {
                'users': len(users),
                'scheduled_posts': today_tasks['scheduled_posts'],
                'self_destructs': today_tasks['self_destruct_tasks'],
                'total_tasks': today_tasks['total'],
                'next_task': next_task.isoformat() if next_task else None,
                'next_task_formatted': next_task.strftime('%d/%m/%Y %H:%M IST') if next_task else 'None'
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
    """Get scheduled tasks information"""
    try:
        current_time = datetime.now(IST)

        # Get upcoming tasks
        upcoming_tasks = db.get_upcoming_tasks(current_time + timedelta(hours=24))  # Next 24 hours

        return jsonify({
            'success': True,
            'scheduled_posts': upcoming_tasks['scheduled_posts'],
            'self_destruct_tasks': upcoming_tasks['self_destruct_tasks'],
            'total_upcoming': len(upcoming_tasks['scheduled_posts']) + len(upcoming_tasks['self_destruct_tasks']),
            'timestamp': current_time.isoformat()
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
                {
                    "text": "🏠 Start",
                    "callback_data": "menu_start",
                    "description": "Getting started guide"
                },
                {
                    "text": "👥 User",
                    "callback_data": "menu_user",
                    "description": "User management (owner only)",
                    "owner_only": True
                },
                {
                    "text": "📝 New Post",
                    "callback_data": "menu_new_post",
                    "description": "Create and schedule posts"
                },
                {
                    "text": "📅 Schedules",
                    "callback_data": "menu_schedules",
                    "description": "Manage upcoming posts"
                },
                {
                    "text": "📊 Dashboard",
                    "type": "web_app",
                    "description": "Web interface"
                }
            ]
        },
        "user_menu": {
            "title": "User Management - Owner Panel",
            "owner_only": True,
            "buttons": [
                {
                    "text": "👥 Users",
                    "callback_data": "user_users",
                    "description": "List whitelisted users with @username"
                },
                {
                    "text": "➕ Permit <user_id>",
                    "callback_data": "user_permit",
                    "description": "Add user to whitelist (ignores - signs)"
                },
                {
                    "text": "➖ Remove <user_id>",
                    "callback_data": "user_remove",
                    "description": "Remove user access (ignores - signs)"
                },
                {
                    "text": "⬅️ Back",
                    "callback_data": "user_back",
                    "description": "Return to main menu"
                }
            ]
        },
        "post_menu": {
            "title": "Post Editor",
            "buttons": [
                {
                    "text": "📤 Send",
                    "callback_data": "post_send",
                    "description": "Send options menu",
                    "submenu": "send_menu"
                },
                {
                    "text": "❌ Cancel",
                    "callback_data": "post_cancel",
                    "description": "Cancel current task"
                },
                {
                    "text": "👀 Preview",
                    "callback_data": "post_preview",
                    "description": "Show post preview"
                },
                {
                    "text": "🗑️ Delete All",
                    "callback_data": "post_delete_all",
                    "description": "Delete the draft/editing post"
                },
                {
                    "text": "⬅️ Back",
                    "callback_data": "post_back",
                    "description": "Return to channel selection"
                }
            ]
        },
        "send_menu": {
            "title": "Send Options",
            "buttons": [
                {
                    "text": "📅 Schedule Post",
                    "callback_data": "send_schedule",
                    "description": "Schedule post by asking date & time in IST"
                },
                {
                    "text": "💣 Self-Destruct",
                    "callback_data": "send_self_destruct",
                    "description": "Schedule self-destruct by asking date & time in IST"
                },
                {
                    "text": "🚀 Post Now",
                    "callback_data": "send_now",
                    "description": "Sends the post instantly"
                },
                {
                    "text": "⬅️ Back",
                    "callback_data": "send_back",
                    "description": "Return to post editor"
                }
            ]
        },
        "schedules_menu": {
            "title": "Schedules Management",
            "buttons": [
                {
                    "text": "📋 Scheduled Posts",
                    "callback_data": "schedules_posts",
                    "description": "Shows the scheduled posts & timings"
                },
                {
                    "text": "💣 Self-Destruct Timings",
                    "callback_data": "schedules_destructs",
                    "description": "Shows the self-destruct posts & timings"
                },
                {
                    "text": "❌ Cancel",
                    "callback_data": "schedules_cancel",
                    "description": "Cancel scheduled items",
                    "submenu": "cancel_menu"
                },
                {
                    "text": "⬅️ Back",
                    "callback_data": "schedules_back",
                    "description": "Return to main menu"
                }
            ]
        },
        "cancel_menu": {
            "title": "Cancel Options",
            "buttons": [
                {
                    "text": "💣 Self-Destruct",
                    "callback_data": "cancel_self_destruct",
                    "description": "Cancel this task"
                },
                {
                    "text": "📅 Scheduled Post",
                    "callback_data": "cancel_scheduled",
                    "description": "Cancel this task"
                },
                {
                    "text": "⬅️ Back",
                    "callback_data": "cancel_back",
                    "description": "Return to schedules menu"
                }
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
