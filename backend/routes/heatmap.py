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
KERNEL_RADIUS = 40  # pixels


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
    
    # Accumulator arrays
    numerator = np.zeros((TILE_SIZE, TILE_SIZE), dtype=np.float64)
    denominator = np.zeros((TILE_SIZE, TILE_SIZE), dtype=np.float64)
    
    sigma = KERNEL_RADIUS / 2.5
    
    for pt in points:
        # Max risk across all categories
        risk = max(pt.get(c, 0.0) for c in CATEGORIES)
        if risk < 0.01:
            continue
        
        px, py = latlng_to_pixel(pt["lat"], pt["lng"],
                                  lat_min, lat_max, lng_min, lng_max)
        
        # Stamp Gaussian kernel
        x_start = max(0, int(px - KERNEL_RADIUS))
        x_end = min(TILE_SIZE, int(px + KERNEL_RADIUS))
        y_start = max(0, int(py - KERNEL_RADIUS))
        y_end = min(TILE_SIZE, int(py + KERNEL_RADIUS))
        
        for yi in range(y_start, y_end):
            for xi in range(x_start, x_end):
                dist_sq = (xi - px)**2 + (yi - py)**2
                w = math.exp(-dist_sq / (2 * sigma**2))
                numerator[yi, xi] += w * risk
                denominator[yi, xi] += w
    
    # Compute weighted average
    mask = denominator > 0
    heat = np.zeros_like(numerator)
    heat[mask] = numerator[mask] / denominator[mask]
    
    # Gamma correction
    heat = np.power(heat, 0.7)
    
    # Color map to RGBA
    rgba = np.zeros((TILE_SIZE, TILE_SIZE, 4), dtype=np.uint8)
    
    for yi in range(TILE_SIZE):
        for xi in range(TILE_SIZE):
            v = heat[yi, xi]
            if v < 0.01:
                continue
            
            r = int(min(255, v * 255 * 1.5))
            g = int(max(0, 255 * (1 - v * 2))) if v < 0.5 else 0
            b = 0
            a = int(25 + 200 * (1 - math.exp(-3 * v)))
            
            rgba[yi, xi] = [r, g, b, a]
    
    img = Image.fromarray(rgba, "RGBA")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")
