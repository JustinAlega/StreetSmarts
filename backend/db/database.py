"""
Database initialization — creates SQLite tables.
Owner: Person 1 (Backend Core)

Other modules import `init_db()` and `get_connection()` from here.
Nobody else should touch this file.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "app.db")


def get_connection() -> sqlite3.Connection:
    """Return a new SQLite connection. Caller must close it."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they don't exist.
    Called once at app startup from main.py.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS truth (
            lat REAL NOT NULL,
            long REAL NOT NULL,
            crime REAL DEFAULT 0.0,
            public_safety REAL DEFAULT 0.0,
            transport REAL DEFAULT 0.0,
            infrastructure REAL DEFAULT 0.0,
            violent_crime REAL DEFAULT 0.0,
            property_crime REAL DEFAULT 0.0,
            weather REAL DEFAULT 0.0,
            other REAL DEFAULT 0.0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (lat, long)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            lat REAL NOT NULL,
            long REAL NOT NULL,
            severity REAL DEFAULT 0.0,
            category TEXT DEFAULT 'other',
            human INTEGER DEFAULT 1,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
