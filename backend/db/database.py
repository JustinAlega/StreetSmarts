"""
Database schema and initialization for StreetSmarts.
SQLite database with three core tables:
  - posts: community reports and AI-generated incident posts
  - truth: per-location risk vectors with 8 category scores
  - safe_places: cached nearby safe locations (refreshed weekly)
"""

import aiosqlite
import os

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(os.path.dirname(__file__)), "app.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lat REAL NOT NULL,
    lng REAL NOT NULL,
    content TEXT NOT NULL,
    severity REAL DEFAULT 0.0,
    category TEXT DEFAULT 'other',
    human INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS truth (
    lat REAL NOT NULL,
    lng REAL NOT NULL,
    crime REAL DEFAULT 0.0,
    public_safety REAL DEFAULT 0.0,
    transport REAL DEFAULT 0.0,
    infrastructure REAL DEFAULT 0.0,
    policy REAL DEFAULT 0.0,
    protest REAL DEFAULT 0.0,
    weather REAL DEFAULT 0.0,
    other REAL DEFAULT 0.0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (lat, lng)
);

CREATE INDEX IF NOT EXISTS idx_truth_coords ON truth(lat, lng);
CREATE INDEX IF NOT EXISTS idx_posts_coords ON posts(lat, lng);
CREATE INDEX IF NOT EXISTS idx_posts_created ON posts(created_at DESC);

CREATE TABLE IF NOT EXISTS safe_places (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT DEFAULT '',
    lat REAL NOT NULL,
    lng REAL NOT NULL,
    type TEXT NOT NULL,
    hours TEXT DEFAULT '',
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_safe_places_type ON safe_places(type);
"""


async def init_db():
    """Initialize the database with schema."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()
    print(f"[DB] Database initialized at {DB_PATH}")


async def get_db():
    """Get a database connection."""
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db
