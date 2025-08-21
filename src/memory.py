import sqlite3
import os

DB_PATH = "conversation_memory.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS memory (
                            session_id TEXT,
                            timestamp TEXT,
                            user_input TEXT,
                            assistant_response TEXT
                        )''')

def save_to_memory(session_id, timestamp, user_input, assistant_response):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT INTO memory VALUES (?, ?, ?, ?)",
                     (session_id, timestamp, user_input, assistant_response))

def load_memory(session_id, limit=5):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT user_input, assistant_response FROM memory WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?", (session_id, limit))
        return cursor.fetchall()

init_db()