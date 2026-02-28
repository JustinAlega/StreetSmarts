"""
Seed truth table with synthetic Gaussian-blended risk data for St. Louis.
Owner: Person 2 (Backend Data + AI)

Run standalone:  python -m data.seed_truth
"""

import random
import math

from db.database import init_db
from db.db_writer import DBWriter

# ---- St. Louis bounding box ---- #
STL_BOUNDS = {
    "min_lat": 38.53,
    "max_lat": 38.77,
    "min_lng": -90.41,
    "max_lng": -90.17,
}

# ---- Configuration ---- #
NUM_RANDOM_ANCHORS = 60
NUM_SUPER_HOTSPOTS = 6
GRID_RESOLUTION_M = 250       # ~250 m spacing
SIGMA_M = 900                 # Gaussian falloff radius in meters
EARTH_RADIUS_M = 6_371_000

# ---- St. Louis notable locations (super-hotspot candidates) ---- #
HOTSPOT_LOCATIONS = [
    {"name": "Downtown STL",      "lat": 38.6270, "lng": -90.1994},
    {"name": "Delmar Loop",       "lat": 38.6589, "lng": -90.3048},
    {"name": "Soulard",           "lat": 38.6066, "lng": -90.2091},
    {"name": "Central West End",  "lat": 38.6411, "lng": -90.2612},
    {"name": "Tower Grove",       "lat": 38.6086, "lng": -90.2541},
    {"name": "The Grove",         "lat": 38.6327, "lng": -90.2478},
]


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Return distance in meters between two lat/lng points.

    TODO: implement haversine formula
    """
    # STUB
    return 0.0


def generate_anchors() -> list[dict]:
    """Create random anchors + super-hotspots with risk values.

    TODO:
    1. Generate NUM_RANDOM_ANCHORS at random positions inside STL_BOUNDS
       - Random category, severity 0.2–0.7
    2. Add NUM_SUPER_HOTSPOTS from HOTSPOT_LOCATIONS
       - High severity 0.7–1.0
    3. Return list of {lat, lng, category, severity}
    """
    # STUB
    return []


def build_grid() -> list[tuple[float, float]]:
    """Create a lat/lng grid across STL_BOUNDS at GRID_RESOLUTION_M spacing.

    TODO:
    1. Convert GRID_RESOLUTION_M to approximate degree steps
    2. Iterate lat/lng and collect points
    """
    # STUB
    return []


def gaussian_weight(distance_m: float) -> float:
    """Gaussian kernel: exp(-d²/(2σ²))

    TODO: implement with SIGMA_M
    """
    # STUB
    return 0.0


def seed() -> None:
    """Main seeding function — populate the truth table.

    TODO:
    1. init_db()
    2. Generate anchors
    3. Build grid
    4. For each grid cell, blend nearby anchors with gaussian_weight()
    5. Call DBWriter.bulk_upsert_truth() with the blended data
    """
    # STUB
    init_db()
    anchors = generate_anchors()
    grid = build_grid()
    # ... blend and insert ...
    print(f"Seeded {len(grid)} truth points from {len(anchors)} anchors.")


if __name__ == "__main__":
    seed()
