import sqlite3
from contextlib import contextmanager

DB_FILE = "employee_secure_hub.db"


# ---------------- DB CONNECTION ----------------
@contextmanager
def get_db():
    conn = sqlite3.connect(DB_FILE, timeout=10)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# ---------------- INIT TABLES ----------------
def init_tables():
    with get_db() as db:
        # USERS TABLE
        db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            department TEXT NOT NULL,
            certified INTEGER DEFAULT 0
        )
        """)

        # AUDIT LOG TABLE
        db.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor TEXT NOT NULL,
            action TEXT NOT NULL,
            target TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
