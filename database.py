import sqlite3

DB_FILE = "bot.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # whitelist table
    c.execute("""
    CREATE TABLE IF NOT EXISTS whitelist (
        user_id INTEGER PRIMARY KEY
    )
    """)

    # scheduled posts
    c.execute("""
    CREATE TABLE IF NOT EXISTS scheduled_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel TEXT,
        content TEXT,
        post_time INTEGER,
        self_destruct INTEGER
    )
    """)
    conn.commit()
    conn.close()

def add_user(user_id):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO whitelist (user_id) VALUES (?)", (user_id,))
        conn.commit()

def remove_user(user_id):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM whitelist WHERE user_id=?", (user_id,))
        conn.commit()

def get_users():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT user_id FROM whitelist")
        return [row[0] for row in c.fetchall()]