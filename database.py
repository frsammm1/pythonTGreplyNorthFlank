import sqlite3
import json
from datetime import datetime, timedelta
from contextlib import contextmanager

DB_NAME = 'bot_database.db'

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                is_banned INTEGER DEFAULT 0,
                join_date TEXT,
                last_active TEXT
            )
        ''')
        
        # Subscription plans table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscription_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                days INTEGER,
                price REAL
            )
        ''')
        
        # Auth keys table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS auth_keys (
                key TEXT PRIMARY KEY,
                user_id INTEGER,
                plan_id INTEGER,
                activated INTEGER DEFAULT 0,
                bot_token TEXT,
                created_at TEXT,
                expires_at TEXT,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (plan_id) REFERENCES subscription_plans (id)
            )
        ''')
        
        # Payment requests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                plan_id INTEGER,
                screenshot_file_id TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (plan_id) REFERENCES subscription_plans (id)
            )
        ''')
        
        # Payment info table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_info (
                id INTEGER PRIMARY KEY,
                qr_code_file_id TEXT,
                upi_id TEXT
            )
        ''')
        
        # Messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user_id INTEGER,
                to_user_id INTEGER,
                message_type TEXT,
                message_content TEXT,
                timestamp TEXT
            )
        ''')
        
        # Clone bots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clone_bots (
                bot_token TEXT PRIMARY KEY,
                owner_user_id INTEGER,
                auth_key TEXT,
                created_at TEXT,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (owner_user_id) REFERENCES users (user_id)
            )
        ''')
        
        conn.commit()

def add_user(user_id, username, first_name):
    with get_db() as conn:
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, username, first_name, join_date, last_active)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, now, now))
        conn.commit()

def update_last_active(user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users SET last_active = ? WHERE user_id = ?
        ''', (datetime.now().isoformat(), user_id))
        conn.commit()

def is_user_banned(user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT is_banned FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result and result['is_banned'] == 1

def ban_user(user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET is_banned = 1 WHERE user_id = ?', (user_id,))
        conn.commit()

def unban_user(user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET is_banned = 0 WHERE user_id = ?', (user_id,))
        conn.commit()

def get_all_users():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE is_banned = 0')
        return cursor.fetchall()

def get_banned_users():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE is_banned = 1')
        return cursor.fetchall()

def get_user_count():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM users WHERE is_banned = 0')
        return cursor.fetchone()['count']

def add_subscription_plan(name, days, price):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO subscription_plans (name, days, price)
            VALUES (?, ?, ?)
        ''', (name, days, price))
        conn.commit()
        return cursor.lastrowid

def get_all_plans():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM subscription_plans')
        return cursor.fetchall()

def delete_plan(plan_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM subscription_plans WHERE id = ?', (plan_id,))
        conn.commit()

def create_auth_key(user_id, plan_id):
    import secrets
    key = secrets.token_urlsafe(16)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO auth_keys (key, user_id, plan_id, created_at)
            VALUES (?, ?, ?, ?)
        ''', (key, user_id, plan_id, datetime.now().isoformat()))
        conn.commit()
    return key

def activate_auth_key(key, bot_token):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM auth_keys WHERE key = ?', (key,))
        auth = cursor.fetchone()
        
        if not auth:
            return False
        
        cursor.execute('SELECT days FROM subscription_plans WHERE id = ?', (auth['plan_id'],))
        plan = cursor.fetchone()
        
        expires_at = datetime.now() + timedelta(days=plan['days'])
        cursor.execute('''
            UPDATE auth_keys 
            SET activated = 1, bot_token = ?, expires_at = ?
            WHERE key = ?
        ''', (bot_token, expires_at.isoformat(), key))
        conn.commit()
        return True

def get_active_auth_keys():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ak.*, u.username, u.first_name, sp.name as plan_name
            FROM auth_keys ak
            JOIN users u ON ak.user_id = u.user_id
            JOIN subscription_plans sp ON ak.plan_id = sp.id
            WHERE ak.activated = 1 AND ak.is_active = 1
        ''')
        return cursor.fetchall()

def revoke_auth_key(key):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE auth_keys SET is_active = 0 WHERE key = ?', (key,))
        conn.commit()

def add_payment_request(user_id, plan_id, screenshot_file_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO payment_requests (user_id, plan_id, screenshot_file_id, created_at)
            VALUES (?, ?, ?, ?)
        ''', (user_id, plan_id, screenshot_file_id, datetime.now().isoformat()))
        conn.commit()
        return cursor.lastrowid

def get_pending_payments():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT pr.*, u.username, u.first_name, sp.name as plan_name, sp.price
            FROM payment_requests pr
            JOIN users u ON pr.user_id = u.user_id
            JOIN subscription_plans sp ON pr.plan_id = sp.id
            WHERE pr.status = 'pending'
        ''')
        return cursor.fetchall()

def approve_payment(payment_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE payment_requests SET status = 'approved' WHERE id = ?
        ''', (payment_id,))
        conn.commit()

def set_payment_info(qr_file_id, upi_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO payment_info (id, qr_code_file_id, upi_id)
            VALUES (1, ?, ?)
        ''', (qr_file_id, upi_id))
        conn.commit()

def get_payment_info():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM payment_info WHERE id = 1')
        return cursor.fetchone()
