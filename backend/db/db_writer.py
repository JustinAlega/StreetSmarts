"""
DBWriter — all database read/write operations.
Owner: Person 1 (Backend Core) — others call these methods, don't write raw SQL.

This is the ONLY place that runs INSERT / UPDATE / SELECT on the DB.
Route handlers and data scripts import DBWriter and call its methods.
"""

import sqlite3
import uuid
from typing import Optional

from db.database import get_connection

# Categories used across the project
CATEGORIES = [
    "crime", "public_safety", "transport", "infrastructure",
    "violent_crime", "property_crime", "weather", "other",
]

# Exponential moving average alpha for truth updates
EMA_ALPHA = 0.25


class DBWriter:
    """Stateless helper — every method opens and closes its own connection."""

    # ------------------------------------------------------------------ #
    #  TRUTH TABLE
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_heatmap_points(
        min_lat: float, max_lat: float,
        min_lng: float, max_lng: float,
    ) -> list[dict]:
        """Return truth rows inside a bounding box as list of dicts.

        Used by: routes/heatmap.py
        TODO: implement query + build list of dicts
        """
        # STUB
        return []

    @staticmethod
    def risk_at_point(lat: float, lng: float, radius_m: float = 300.0) -> dict:
        """Return averaged risk scores near a lat/lng.

        Used by: routes/routing.py (edge weight), routes/location_summary.py
        TODO: query truth rows within radius, average each category
        """
        # STUB — return zero-risk placeholder
        return {cat: 0.0 for cat in CATEGORIES}

    @staticmethod
    def upsert_truth(lat: float, lng: float, category: str, severity: float) -> None:
        """Insert or EMA-update a single truth cell.

        Used by: data/seed_truth.py, routes/social.py (after post classification)
        TODO: INSERT … ON CONFLICT UPDATE with EMA formula
        """
        # STUB
        pass

    @staticmethod
    def bulk_upsert_truth(rows: list[dict]) -> None:
        """Batch-insert many truth rows (used by seed_truth.py).

        Each dict: {lat, lng, category, severity}
        TODO: wrap upsert_truth in a transaction
        """
        # STUB
        pass

    # ------------------------------------------------------------------ #
    #  POSTS TABLE
    # ------------------------------------------------------------------ #

    @staticmethod
    def insert_post(
        lat: float, lng: float,
        content: str,
        severity: float,
        category: str,
        human: bool = True,
    ) -> str:
        """Insert a community report and return the new post id.

        Used by: routes/social.py
        TODO: generate uuid, insert row, return id
        """
        # STUB
        post_id = str(uuid.uuid4())
        return post_id

    @staticmethod
    def get_feed(
        lat: float, lng: float,
        radius_m: float = 500.0,
        limit: int = 50,
    ) -> list[dict]:
        """Return nearby posts sorted by recency.

        Used by: routes/social.py
        TODO: haversine filter + ORDER BY created_at DESC
        """
        # STUB
        return []

    @staticmethod
    def get_location_summary(lat: float, lng: float, radius_m: float = 500.0) -> dict:
        """Aggregate truth + posts near a point for the summary panel.

        Used by: routes/location_summary.py
        TODO: combine risk_at_point + count nearby posts + generate label
        """
        # STUB
        return {
            "risk_score": 0,
            "risk_label": "Unknown",
            "nearby_posts": 0,
            "recommendation": "",
            "truth": {cat: 0.0 for cat in CATEGORIES},
            "hotspots": [],
        }
