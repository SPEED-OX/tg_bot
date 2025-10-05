"""
TechGeekZ Bot - Database Manager
Centralized database operations with user details integration
"""
import sqlite3
import os
from datetime import datetime
from typing import List, Tuple, Optional

class DatabaseManager:
    def __init__(self, db_path: str = "techgeekz.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with all required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                nickname TEXT,
                is_whitelisted INTEGER DEFAULT 0,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Channels table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS channels (
                channel_id INTEGER PRIMARY KEY,
                channel_name TEXT NOT NULL,
                channel_username TEXT,
                channel_type TEXT DEFAULT 'channel',
                added_by INTEGER,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (added_by) REFERENCES users (user_id)
            )
        ''')
        
        # Scheduled posts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                media_path TEXT,
                media_type TEXT,
                scheduled_time TIMESTAMP NOT NULL,
                is_self_destruct INTEGER DEFAULT 0,
                self_destruct_time TIMESTAMP,
                status TEXT DEFAULT 'pending',
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sent_date TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (channel_id) REFERENCES channels (channel_id)
            )
        ''')
        
        # Bot settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()

    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    # User management methods
    def add_user_to_whitelist(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None):
        """Add or update user in whitelist"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create nickname from first_name and last_name
        nickname = f"{first_name} {last_name}".strip() if first_name and last_name else first_name
        
        cursor.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, username, first_name, last_name, nickname, is_whitelisted, updated_date)
            VALUES (?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
        ''', (user_id, username, first_name, last_name, nickname))
        
        conn.commit()
        conn.close()

    def remove_user_from_whitelist(self, user_id: int):
        """Remove user from whitelist"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET is_whitelisted = 0, updated_date = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (user_id,))
        
        conn.commit()
        conn.close()

    def is_user_whitelisted(self, user_id: int) -> bool:
        """Check if user is whitelisted"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT is_whitelisted FROM users 
            WHERE user_id = ? AND is_whitelisted = 1
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result is not None

    def get_whitelisted_users(self) -> List[Tuple]:
        """Get all whitelisted users"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, username, first_name, is_whitelisted, added_date
            FROM users 
            WHERE is_whitelisted = 1
            ORDER BY added_date DESC
        ''')
        
        users = cursor.fetchall()
        conn.close()
        
        return users

    def get_whitelisted_users_with_details(self) -> List[Tuple]:
        """Get all whitelisted users with detailed information"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, username, first_name, nickname
            FROM users 
            WHERE is_whitelisted = 1
            ORDER BY added_date DESC
        ''')
        
        users = cursor.fetchall()
        conn.close()
        
        return users

    def get_user_info(self, user_id: int) -> Optional[Tuple]:
        """Get user information"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, username, first_name, last_name, nickname, is_whitelisted, added_date
            FROM users WHERE user_id = ?
        ''', (user_id,))
        
        user = cursor.fetchone()
        conn.close()
        
        return user

    # Channel management methods
    def add_channel(self, channel_id: int, channel_name: str, channel_username: str = None, added_by: int = None):
        """Add channel to database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO channels 
            (channel_id, channel_name, channel_username, added_by)
            VALUES (?, ?, ?, ?)
        ''', (channel_id, channel_name, channel_username, added_by))
        
        conn.commit()
        conn.close()

    def get_user_channels(self, user_id: int) -> List[dict]:
        """Get channels added by user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT channel_id, channel_name, channel_username, added_date
            FROM channels 
            WHERE added_by = ? AND is_active = 1
            ORDER BY added_date DESC
        ''', (user_id,))
        
        channels = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': channel[0],
                'name': channel[1],
                'username': channel[2],
                'added_date': channel[3]
            }
            for channel in channels
        ]

    def get_all_channels(self) -> List[dict]:
        """Get all active channels"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.channel_id, c.channel_name, c.channel_username, c.added_date,
                   u.username as added_by_username
            FROM channels c
            LEFT JOIN users u ON c.added_by = u.user_id
            WHERE c.is_active = 1
            ORDER BY c.added_date DESC
        ''')
        
        channels = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': channel[0],
                'name': channel[1],
                'username': channel[2],
                'added_date': channel[3],
                'added_by': channel[4]
            }
            for channel in channels
        ]

    # Scheduled posts methods
    def add_scheduled_post(self, user_id: int, channel_id: int, content: str, 
                          scheduled_time: str, is_self_destruct: bool = False,
                          self_destruct_time: str = None, media_path: str = None,
                          media_type: str = None):
        """Add scheduled post"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO scheduled_posts 
            (user_id, channel_id, content, media_path, media_type, scheduled_time,
             is_self_destruct, self_destruct_time, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        ''', (user_id, channel_id, content, media_path, media_type, scheduled_time,
              1 if is_self_destruct else 0, self_destruct_time))
        
        post_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return post_id

    def get_scheduled_posts(self, user_id: int = None) -> List[dict]:
        """Get scheduled posts"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT sp.id, sp.user_id, sp.channel_id, sp.content, sp.scheduled_time,
                   sp.is_self_destruct, sp.self_destruct_time, sp.status, sp.created_date,
                   c.channel_name, u.username
            FROM scheduled_posts sp
            LEFT JOIN channels c ON sp.channel_id = c.channel_id
            LEFT JOIN users u ON sp.user_id = u.user_id
            WHERE sp.status = 'pending'
        '''
        
        params = []
        if user_id:
            query += ' AND sp.user_id = ?'
            params.append(user_id)
        
        query += ' ORDER BY sp.scheduled_time ASC'
        
        cursor.execute(query, params)
        posts = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': post[0],
                'user_id': post[1], 
                'channel_id': post[2],
                'content': post[3],
                'scheduled_time': post[4],
                'is_self_destruct': bool(post[5]),
                'self_destruct_time': post[6],
                'status': post[7],
                'created_date': post[8],
                'channel_name': post[9],
                'username': post[10]
            }
            for post in posts
        ]

    def update_post_status(self, post_id: int, status: str):
        """Update post status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE scheduled_posts 
            SET status = ?, sent_date = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, post_id))
        
        conn.commit()
        conn.close()

    def delete_scheduled_post(self, post_id: int, user_id: int = None):
        """Delete scheduled post"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = 'DELETE FROM scheduled_posts WHERE id = ?'
        params = [post_id]
        
        if user_id:
            query += ' AND user_id = ?'
            params.append(user_id)
        
        cursor.execute(query, params)
        conn.commit()
        conn.close()

    # Settings methods
    def set_setting(self, key: str, value: str):
        """Set bot setting"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO bot_settings (key, value, updated_date)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (key, value))
        
        conn.commit()
        conn.close()

    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """Get bot setting"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT value FROM bot_settings WHERE key = ?', (key,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else default

    # Statistics methods
    def get_stats(self) -> dict:
        """Get bot statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Count whitelisted users
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_whitelisted = 1')
        total_users = cursor.fetchone()[0]
        
        # Count active channels
        cursor.execute('SELECT COUNT(*) FROM channels WHERE is_active = 1')
        total_channels = cursor.fetchone()[0]
        
        # Count pending posts
        cursor.execute('SELECT COUNT(*) FROM scheduled_posts WHERE status = "pending"')
        pending_posts = cursor.fetchone()[0]
        
        # Count self-destruct posts
        cursor.execute('''
            SELECT COUNT(*) FROM scheduled_posts 
            WHERE status = "pending" AND is_self_destruct = 1
        ''')
        self_destruct_posts = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_users': total_users,
            'total_channels': total_channels,
            'pending_posts': pending_posts,
            'self_destruct_posts': self_destruct_posts
        }
