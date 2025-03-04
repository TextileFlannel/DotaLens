import sqlite3
from contextlib import contextmanager

DB_NAME = 'users.db'

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_NAME)
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         telegram_id INTEGER UNIQUE,
                         steam_id TEXT)''')

def get_user(telegram_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
        return cursor.fetchone()

def create_or_update_user(telegram_id: int, steam_id: str):
    with get_db() as conn:
        conn.execute('''INSERT OR REPLACE INTO users 
                        (telegram_id, steam_id) 
                        VALUES (?, ?)''', (telegram_id, steam_id))
        conn.commit()