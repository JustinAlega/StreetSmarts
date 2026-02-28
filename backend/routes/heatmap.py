"""
Heatmap tile server for StreetSmarts.
Serves standard slippy map raster tiles with Gaussian-splatted risk visualization.
"""

import math
import io
import numpy as np
from PIL import Image
from fastapi import APIRouter
from fastapi.responses import Response
from db.db_writer import DBWriter, CATEGORIES

router = APIRouter()
db = DBWriter()

TILE_SIZE = 256
KERNEL_RADIUS = 80  # pixels


def tile_to_latlng(z, x, y):
    """Convert tile coordinates + pixel to lat/lng bounds."""
    n = 2.0 ** z
    lng_min = x / n * 360.0 - 180.0
    lng_max = (x + 1) / n * 360.0 - 180.0
    lat_min = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n))))
    lat_max = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    return lat_min, lat_max, lng_min, lng_max


def latlng_to_pixel(lat, lng, lat_min, lat_max, lng_min, lng_max):
    """Convert lat/lng to pixel position within tile."""
    px = (lng - lng_min) / (lng_max - lng_min) * TILE_SIZE
    py = (lat_max - lat) / (lat_max - lat_min) * TILE_SIZE
    return px, py


@router.get("/tiles/{z}/{x}/{y}.png")
async def get_tile(z: int, x: int, y: int):
    """Generate a heatmap tile."""
    lat_min, lat_max, lng_min, lng_max = tile_to_latlng(z, x, y)
    
    # Padding for Gaussian bleed
    lat_pad = (lat_max - lat_min) * 0.3
    lng_pad = (lng_max - lng_min) * 0.3
    
    points = await db.get_truth_in_bounds(
        lat_min - lat_pad, lat_max + lat_pad,
        lng_min - lng_pad, lng_max + lng_pad
    )
    
    if not points:
        # Return transparent tile
        img = Image.new("RGBA", (TILE_SIZE, TILE_SIZE), (0, 0, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return Response(content=buf.getvalue(), media_type="image/png")
    
    # Create a precomputed kernel
    sigma = KERNEL_RADIUS / 2.5
    k_size = int(KERNEL_RADIUS * 2 + 1)
    y_g, x_g = np.ogrid[-KERNEL_RADIUS:KERNEL_RADIUS+1, -KERNEL_RADIUS:KERNEL_RADIUS+1]
    dist_sq_kernel = x_g**2 + y_g**2
    
    # Mask to keep kernel strictly circular
    kernel_mask = dist_sq_kernel <= KERNEL_RADIUS**2
    base_kernel = np.exp(-dist_sq_kernel / (2 * sigma**2))
    base_kernel[~kernel_mask] = 0.0

    # Accumulator arrays
    numerator = np.zeros((TILE_SIZE, TILE_SIZE), dtype=np.float64)
    denominator = np.zeros((TILE_SIZE, TILE_SIZE), dtype=np.float64)
    
    for pt in points:
        risk = max(pt.get(c, 0.0) for c in CATEGORIES)
        if risk < 0.01:
            continue
            
        px, py = latlng_to_pixel(pt["lat"], pt["lng"], lat_min, lat_max, lng_min, lng_max)
        px_int, py_int = int(px), int(py)

        # Bounds checking for the kernel slice vs the tile
        x_start = max(0, px_int - KERNEL_RADIUS)
        x_end = min(TILE_SIZE, px_int + KERNEL_RADIUS + 1)
        y_start = max(0, py_int - KERNEL_RADIUS)
        y_end = min(TILE_SIZE, py_int + KERNEL_RADIUS + 1)
        
        if x_start >= x_end or y_start >= y_end:
            continue
            
        # Determine where the kernel intersects the tile
        k_x_start = x_start - (px_int - KERNEL_RADIUS)
        k_x_end = k_x_start + (x_end - x_start)
        k_y_start = y_start - (py_int - KERNEL_RADIUS)
        k_y_end = k_y_start + (y_end - y_start)

        # Slice kernel and add to accumulators
        k_slice = base_kernel[k_y_start:k_y_end, k_x_start:k_x_end]
        
        numerator[y_start:y_end, x_start:x_end] += k_slice * risk
        denominator[y_start:y_end, x_start:x_end] += k_slice

    # Compute weighted average where denominator > 0
    mask = denominator > 0
    heat = np.zeros_like(numerator)
    heat[mask] = numerator[mask] / denominator[mask]
    
    # Gamma correction
    heat = np.power(heat, 0.7)
    
    # Vectorized color mapping
    rgba = np.zeros((TILE_SIZE, TILE_SIZE, 4), dtype=np.uint8)
    
    # condition where heat is meaningful
    valid = heat >= 0.01
    v_valid = heat[valid]
    
    # Red: min(255, v * 255 * 1.5)
    r = np.clip(v_valid * 255 * 1.5, 0, 255).astype(np.uint8)
    
    # Green: max(0, 255 * (1 - v * 2)) if v < 0.5 else 0
    g = np.where(v_valid < 0.5, np.clip(255 * (1 - v_valid * 2), 0, 255), 0).astype(np.uint8)
    
    # Blue: always 0 for safety heatmaps
    b = np.zeros_like(v_valid, dtype=np.uint8)
    
    # Alpha: int(25 + 200 * (1 - math.exp(-3 * v)))
    a = np.clip(25 + 200 * (1 - np.exp(-3 * v_valid)), 0, 255).astype(np.uint8)
    
    rgba[valid, 0] = r
    rgba[valid, 1] = g
    rgba[valid, 2] = b
    rgba[valid, 3] = a
    
    img = Image.fromarray(rgba, "RGBA")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")
