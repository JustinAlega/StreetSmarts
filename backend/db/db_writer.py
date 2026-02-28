"""
Database access layer for StreetSmarts.
Handles all CRUD operations for the posts and truth tables.
Uses exponential moving average (EMA) for truth updates.
"""

import aiosqlite
import math
from .database import DB_PATH

CATEGORIES = ["crime", "public_safety", "transport", "infrastructure",
               "policy", "protest", "weather", "other"]


class DBWriter:
    """Provides all database CRUD operations."""

    def __init__(self):
        self.db_path = DB_PATH
        self.alpha = 0.25  # EMA smoothing factor

    def _connect(self):
        """Get an async context manager for a database connection."""
        return aiosqlite.connect(self.db_path)

    async def insert_post(self, lat: float, lng: float, content: str,
                          severity: float = 0.0, category: str = "other",
                          human: bool = True):
        """Insert a new community or AI post."""
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            await db.execute(
                """INSERT INTO posts (lat, lng, content, severity, category, human)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (lat, lng, content, severity, category, 1 if human else 0)
            )
            await db.commit()

    async def update_truth(self, lat: float, lng: float, category: str,
                           severity: float, alpha: float = None):
        """Update truth table using exponential moving average (EMA).
        new = (1 - alpha) * old + alpha * severity
        """
        if alpha is None:
            alpha = self.alpha

        lat_r = round(lat, 5)
        lng_r = round(lng, 5)

        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM truth WHERE lat = ? AND lng = ?",
                (lat_r, lng_r)
            )
            row = await cursor.fetchone()

            if row is None:
                cols = {c: 0.0 for c in CATEGORIES}
                cols[category] = severity
                placeholders = ", ".join(["?"] * (len(CATEGORIES) + 2))
                col_names = "lat, lng, " + ", ".join(CATEGORIES)
                values = [lat_r, lng_r] + [cols[c] for c in CATEGORIES]
                await db.execute(
                    f"INSERT INTO truth ({col_names}) VALUES ({placeholders})",
                    values
                )
            else:
                old_val = row[category] if category in CATEGORIES else 0.0
                new_val = (1 - alpha) * old_val + alpha * severity
                await db.execute(
                    f"UPDATE truth SET {category} = ?, updated_at = CURRENT_TIMESTAMP WHERE lat = ? AND lng = ?",
                    (new_val, lat_r, lng_r)
                )
            await db.commit()

    async def get_truth(self, lat: float, lng: float):
        """Exact-match lookup of truth vector at coordinates."""
        lat_r = round(lat, 5)
        lng_r = round(lng, 5)
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM truth WHERE lat = ? AND lng = ?",
                (lat_r, lng_r)
            )
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None

    async def get_truth_nearest(self, lat: float, lng: float, radius_deg: float = 0.005):
        """Nearest-neighbor lookup using Euclidean approximation."""
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT *, 
                   (lat - ?) * (lat - ?) + (lng - ?) * (lng - ?) AS dist_sq
                   FROM truth
                   WHERE lat BETWEEN ? AND ? AND lng BETWEEN ? AND ?
                   ORDER BY dist_sq ASC LIMIT 1""",
                (lat, lat, lng, lng,
                 lat - radius_deg, lat + radius_deg,
                 lng - radius_deg, lng + radius_deg)
            )
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None

    async def get_truth_in_bounds(self, lat_min: float, lat_max: float,
                                  lng_min: float, lng_max: float):
        """Get all truth rows within bounding box."""
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT * FROM truth 
                   WHERE lat BETWEEN ? AND ? AND lng BETWEEN ? AND ?""",
                (lat_min, lat_max, lng_min, lng_max)
            )
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def get_feed(self, lat: float, lng: float, radius_km: float = 2.0,
                       limit: int = 50):
        """Fetch recent posts within radius, using haversine distance."""
        # approx degree offset for prefilter
        deg_offset = radius_km / 111.0
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT * FROM posts
                   WHERE lat BETWEEN ? AND ? AND lng BETWEEN ? AND ?
                   ORDER BY created_at DESC LIMIT ?""",
                (lat - deg_offset, lat + deg_offset,
                 lng - deg_offset, lng + deg_offset, limit)
            )
            rows = await cursor.fetchall()
            results = []
            for r in rows:
                d = dict(r)
                # compute haversine distance
                d["distance_km"] = self._haversine(lat, lng, d["lat"], d["lng"])
                if d["distance_km"] <= radius_km:
                    results.append(d)
            return results

    async def count_truth_rows(self):
        """Count total rows in truth table."""
        async with self._connect() as db:
            cursor = await db.execute("SELECT COUNT(*) FROM truth")
            row = await cursor.fetchone()
            return row[0] if row else 0

    @staticmethod
    def _haversine(lat1, lng1, lat2, lng2):
        """Calculate haversine distance in km."""
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlng / 2) ** 2)
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
