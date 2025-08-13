import os
import sqlite3
from flask import g

DB_PATH = os.path.join(os.path.dirname(__file__), "chat_memory.db")

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(_=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        role TEXT,
        content TEXT,
        ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    db.commit()

def add_message(user_id, role, content):
    db = get_db()
    db.execute("INSERT INTO messages(user_id, role, content) VALUES (?, ?, ?)",
               (user_id, role, content))
    db.commit()

def fetch_history(user_id, limit_pairs=8):
    db = get_db()
    rows = db.execute(
        "SELECT role, content FROM messages WHERE user_id=? ORDER BY id DESC LIMIT ?",
        (user_id, limit_pairs*2)
    ).fetchall()
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

