"""
Synthetic Ground Truth Generator for Saint Louis, MO.

Creates a spatially smooth, realistic-looking risk landscape using
Gaussian distance-weighted blending of random anchor points.

Saint Louis bounding box:
  lat: 38.50 - 38.80
  lng: -90.40 - -90.15
"""

import math
import random
import asyncio
import aiosqlite
from db.database import init_db, DB_PATH

CATEGORIES = ["crime", "public_safety", "transport", "infrastructure", "protest", "other"]

# Saint Louis bounding box
LAT_MIN, LAT_MAX = 38.50, 38.80
LNG_MIN, LNG_MAX = -90.40, -90.15

# Known higher-risk areas in STL (approximate coords)
HOTSPOT_LOCATIONS = [
    (38.6270, -90.1994, "Downtown"),
    (38.6495, -90.2350, "North City"),
    (38.6100, -90.2100, "Near Soulard"),
    (38.6700, -90.2600, "North County"),
    (38.6350, -90.1800, "Near Riverfront"),
    (38.6550, -90.2100, "Midtown"),
]

GRID_STEP_DEG = 0.0025  # ~250m spacing
SIGMA_DEG = 0.009       # ~900m Gaussian spread
NUM_ANCHORS = 60


def generate_anchors():
    """Create random anchor points with strengths and category vectors."""
    anchors = []
    
        # Regular anchors
    for _ in range(NUM_ANCHORS):
        lat = random.uniform(LAT_MIN, LAT_MAX)
        lng = random.uniform(LNG_MIN, LNG_MAX)
        strength = random.uniform(0.1, 0.8)
        cat_vector = {c: random.uniform(0, 1) for c in CATEGORIES}
        # Normalize to max=1.0 so spread hits genuine highs
        max_v = max(cat_vector.values())
        cat_vector = {c: v / max_v for c, v in cat_vector.items()}
        anchors.append((lat, lng, strength, cat_vector))
    
    # Super hotspots at known higher-risk areas
    for lat, lng, name in HOTSPOT_LOCATIONS:
        lat += random.uniform(-0.005, 0.005)
        lng += random.uniform(-0.005, 0.005)
        strength = random.uniform(0.7, 1.0)
        cat_vector = {c: random.uniform(0, 0.4) for c in CATEGORIES}
        cat_vector["crime"] = random.uniform(0.7, 1.0)
        cat_vector["public_safety"] = random.uniform(0.6, 1.0)
        # Normalize to max=1.0 so hotspots truly map as 100% risk centers
        max_v = max(cat_vector.values())
        cat_vector = {c: v / max_v for c, v in cat_vector.items()}
        anchors.append((lat, lng, strength, cat_vector))
        print(f"  [HOTSPOT] {name} at ({lat:.4f}, {lng:.4f}) strength={strength:.2f}")
    
    return anchors


def gaussian_weight(dist, sigma=SIGMA_DEG):
    """Gaussian distance weighting."""
    return math.exp(-dist**2 / (2 * sigma**2))


def blend_anchors(lat, lng, anchors):
    """Blend all anchors using Gaussian distance weighting."""
    weighted_vec = {c: 0.0 for c in CATEGORIES}
    total_weight = 0.0
    
    for a_lat, a_lng, strength, cat_vec in anchors:
        dist = math.sqrt((lat - a_lat)**2 + (lng - a_lng)**2)
        w = gaussian_weight(dist) * strength
        total_weight += w
        for c in CATEGORIES:
            weighted_vec[c] += w * cat_vec[c]
    
    if total_weight > 0:
        weighted_vec = {c: v / total_weight for c, v in weighted_vec.items()}
    
    return weighted_vec


async def generate_data():
    """Generate synthetic truth data for St. Louis using batch inserts."""
    await init_db()
    
    print("[DATA_GEN] Generating anchors...")
    anchors = generate_anchors()
    print(f"[DATA_GEN] Created {len(anchors)} anchors")
    
    # Generate grid
    lat_steps = int((LAT_MAX - LAT_MIN) / GRID_STEP_DEG)
    lng_steps = int((LNG_MAX - LNG_MIN) / GRID_STEP_DEG)
    total_points = lat_steps * lng_steps
    print(f"[DATA_GEN] Generating {total_points} grid points ({lat_steps}x{lng_steps})...")
    
    # Batch insert using direct SQL
    col_names = "lat, lng, " + ", ".join(CATEGORIES)
    placeholders = ", ".join(["?"] * (len(CATEGORIES) + 2))
    insert_sql = f"INSERT OR REPLACE INTO truth ({col_names}) VALUES ({placeholders})"
    
    batch = []
    batch_size = 500
    count = 0
    
    async with aiosqlite.connect(DB_PATH) as db:
        for i in range(lat_steps):
            lat = round(LAT_MIN + i * GRID_STEP_DEG, 5)
            for j in range(lng_steps):
                lng = round(LNG_MIN + j * GRID_STEP_DEG, 5)
                risk_vec = blend_anchors(lat, lng, anchors)
                
                values = [lat, lng] + [risk_vec[c] for c in CATEGORIES]
                batch.append(values)
                count += 1
                
                if len(batch) >= batch_size:
                    await db.executemany(insert_sql, batch)
                    await db.commit()
                    batch = []
                    print(f"  [{count}/{total_points}] points written")
        
        # Write remaining
        if batch:
            await db.executemany(insert_sql, batch)
            await db.commit()
    
    # Count total
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM truth")
        row = await cursor.fetchone()
        total = row[0] if row else 0
    
    print(f"[DATA_GEN] Done. {total} truth rows in database.")


if __name__ == "__main__":
    asyncio.run(generate_data())
