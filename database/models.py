"""
Optimized database models for Controller Bot
No message/media storage - only essential data
"""
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import threading
from config import IST

class DatabaseManager:
    def __init__(self, db_path: str = "controller_bot.db"):
        self.db_path = db_path
        self._local = threading.local()
        self.init_database()

    def get_connection(self):
        """Get thread-local database connection"""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                self.db_path, 
                check_same_thread=False,
                timeout=10.0
            )
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection

    def init_database(self):
        """Initialize optimized database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Users table (minimal - only for whitelist)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                is_whitelisted INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Channels table (user-added channels)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT,
                channel_username TEXT,
                channel_name TEXT,
                added_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(channel_id, added_by)
            )
        """)

        # Scheduled posts (minimal data - no message storage)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                channel_id TEXT,
                scheduled_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending'
            )
        """)

        # Self-destruct tasks (minimal data)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS self_destruct_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT,
                message_id INTEGER,
                destruct_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending'
            )
        """)

        conn.commit()

    # User management (only check DB for non-owners)
    def is_user_whitelisted(self, user_id: int) -> bool:
        """Check whitelist only for non-owners"""
        from config import BOT_OWNER_ID
        if user_id == BOT_OWNER_ID:
            return True  # Owner bypass - no DB check

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT is_whitelisted FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return bool(result and result[0]) if result else False

    def add_user(self, user_id: int, username: str = None, first_name: str = None):
        """Add or update user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO users (user_id, username, first_name)
            VALUES (?, ?, ?)
        """, (user_id, username, first_name))
        conn.commit()

    def whitelist_user(self, user_id: int, whitelist: bool = True):
        """Add or remove user from whitelist"""
        # Remove '-' from user_id if present
        user_id = abs(int(user_id))

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO users (user_id, is_whitelisted) VALUES (?, ?)
        """, (user_id, 1 if whitelist else 0))
        cursor.execute("""
            UPDATE users SET is_whitelisted = ? WHERE user_id = ?
        """, (1 if whitelist else 0, user_id))
        conn.commit()

    def get_whitelisted_users(self) -> List[Dict]:
        """Get all whitelisted users"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, username, first_name, created_at 
            FROM users WHERE is_whitelisted = 1
        """)
        return [dict(row) for row in cursor.fetchall()]

    # Channel management
    def add_channel(self, user_id: int, channel_id: str, channel_username: str, channel_name: str):
        """Add channel for user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO channels 
            (channel_id, channel_username, channel_name, added_by)
            VALUES (?, ?, ?, ?)
        """, (channel_id, channel_username, channel_name, user_id))
        conn.commit()

    def get_user_channels(self, user_id: int) -> List[Dict]:
        """Get channels for specific user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM channels WHERE added_by = ? ORDER BY created_at DESC
        """, (user_id,))
        return [dict(row) for row in cursor.fetchall()]

    def remove_channel(self, user_id: int, channel_id: str):
        """Remove channel for user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM channels WHERE channel_id = ? AND added_by = ?
        """, (channel_id, user_id))
        conn.commit()

    # Optimized scheduling (minimal data storage)
    def schedule_post(self, user_id: int, channel_id: str, scheduled_time: datetime) -> int:
        """Schedule a post (no message storage)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO scheduled_posts (user_id, channel_id, scheduled_time)
            VALUES (?, ?, ?)
        """, (user_id, channel_id, scheduled_time))
        conn.commit()
        return cursor.lastrowid

    def schedule_self_destruct(self, channel_id: str, message_id: int, destruct_time: datetime) -> int:
        """Schedule message self-destruct"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO self_destruct_tasks (channel_id, message_id, destruct_time)
            VALUES (?, ?, ?)
        """, (channel_id, message_id, destruct_time))
        conn.commit()
        return cursor.lastrowid

    def get_upcoming_tasks(self, limit_time: datetime = None) -> Dict:
        """Get upcoming scheduled posts and self-destruct tasks"""
        if limit_time is None:
            limit_time = datetime.now(IST)

        conn = self.get_connection()
        cursor = conn.cursor()

        # Get scheduled posts
        cursor.execute("""
            SELECT * FROM scheduled_posts 
            WHERE status = 'pending' AND scheduled_time <= ?
            ORDER BY scheduled_time ASC
        """, (limit_time,))
        scheduled_posts = [dict(row) for row in cursor.fetchall()]

        # Get self-destruct tasks
        cursor.execute("""
            SELECT * FROM self_destruct_tasks 
            WHERE status = 'pending' AND destruct_time <= ?
            ORDER BY destruct_time ASC
        """, (limit_time,))
        self_destruct_tasks = [dict(row) for row in cursor.fetchall()]

        return {
            'scheduled_posts': scheduled_posts,
            'self_destruct_tasks': self_destruct_tasks
        }

    def get_next_task_time(self) -> Optional[datetime]:
        """Get the next upcoming task time for smart scheduling"""
        conn = self.get_connection()
        cursor = conn.cursor()

        now = datetime.now(IST)

        # Get next scheduled post
        cursor.execute("""
            SELECT MIN(scheduled_time) as next_time FROM scheduled_posts 
            WHERE status = 'pending' AND scheduled_time > ?
        """, (now,))
        next_post = cursor.fetchone()

        # Get next self-destruct
        cursor.execute("""
            SELECT MIN(destruct_time) as next_time FROM self_destruct_tasks 
            WHERE status = 'pending' AND destruct_time > ?
        """, (now,))
        next_destruct = cursor.fetchone()

        # Find earliest time
        times = []
        if next_post and next_post[0]:
            times.append(datetime.fromisoformat(next_post[0]))
        if next_destruct and next_destruct[0]:
            times.append(datetime.fromisoformat(next_destruct[0]))

        return min(times) if times else None

    def mark_task_completed(self, task_type: str, task_id: int):
        """Mark task as completed"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if task_type == 'scheduled_post':
            cursor.execute("""
                UPDATE scheduled_posts SET status = 'completed' WHERE id = ?
            """, (task_id,))
        elif task_type == 'self_destruct':
            cursor.execute("""
                UPDATE self_destruct_tasks SET status = 'completed' WHERE id = ?
            """, (task_id,))

        conn.commit()

    def get_daily_tasks(self, date: datetime) -> Dict:
        """Get all tasks for a specific date"""
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM scheduled_posts 
            WHERE status = 'pending' AND scheduled_time >= ? AND scheduled_time < ?
        """, (start_of_day, end_of_day))
        scheduled_count = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM self_destruct_tasks 
            WHERE status = 'pending' AND destruct_time >= ? AND destruct_time < ?
        """, (start_of_day, end_of_day))
        destruct_count = cursor.fetchone()[0]

        return {
            'scheduled_posts': scheduled_count,
            'self_destruct_tasks': destruct_count,
            'total': scheduled_count + destruct_count
        }

    def cleanup_completed_tasks(self, days_old: int = 7):
        """Clean up completed tasks older than specified days"""
        cutoff_date = datetime.now(IST) - timedelta(days=days_old)

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM scheduled_posts 
            WHERE status = 'completed' AND created_at < ?
        """, (cutoff_date,))

        cursor.execute("""
            DELETE FROM self_destruct_tasks 
            WHERE status = 'completed' AND created_at < ?
        """, (cutoff_date,))

        conn.commit()
