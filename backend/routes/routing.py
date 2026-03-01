"""
Safety-optimized routing for StreetSmarts.
Uses Mapbox Directions API for reliable routing, with safety risk overlay.
Falls back to A* on OSMnx graph when available.
"""

import os
import math
import asyncio
import aiohttp
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from db.db_writer import DBWriter, CATEGORIES, CATEGORY_WEIGHTS
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

router = APIRouter()
db = DBWriter()

MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN", "")


class RouteRequest(BaseModel):
    start_lat: float
    start_lng: float
    end_lat: float
    end_lng: float
    priority: str = "safety"  # "safety" or "speed"


async def get_risk_at(lat, lng):
    """Look up risk at a point using nearest truth row."""
    truth = await db.get_truth_nearest(lat, lng, radius_deg=0.003)
    if truth is None:
        return 0.0
    
    # Max across weighted categories
    risk = max(truth.get(c, 0.0) * CATEGORY_WEIGHTS.get(c, 0.3) for c in CATEGORIES)
    
    # Distance decay
    dist_deg = math.sqrt((lat - truth["lat"])**2 + (lng - truth["lng"])**2)
    decay = math.exp(-dist_deg**2 / (2 * 0.002**2))
    
    return risk * decay


async def get_route_risk_score(coordinates):
    """Compute risk along a route by sampling points, heavily penalizing high-risk nodes."""
    if not coordinates or len(coordinates) < 2:
        return 0.0
    
    # Sample points thickly to accurately reflect high risk areas
    step = max(1, len(coordinates) // 50)  # at least 50 points
    sample_indices = list(range(0, len(coordinates), step))
    
    risks = []
    for i in sample_indices:
        coord = coordinates[i]
        base_risk = await get_risk_at(coord[1], coord[0])  # lat, lng
        # Spread out the risk parameters more so high risk (red blobs) 
        # are heavily penalized compared to medium risk areas.
        # base_risk is typically 0.0 to 1.0 depending on categorization weights.
        scaled_risk = base_risk ** 2.0 
        risks.append(scaled_risk)
    
    # Scale result to an intuitive 0-100 percentage
    average_risk = sum(risks) / len(risks) if risks else 0.0
    # Add a math.sqrt to slightly de-penalize the average, pulling the final max back toward 100
    # without losing the massive difference between safe and red nodes in the underlying path math
    return min(100.0, math.sqrt(average_risk) * 100.0)


async def mapbox_directions(start_lng, start_lat, end_lng, end_lat, profile="walking", waypoints=None):
    """Get a route from Mapbox Directions API, with optional intermediate waypoints."""
    coords_path = f"{start_lng},{start_lat}"
    if waypoints:
        for wp_lng, wp_lat in waypoints:
            coords_path += f";{wp_lng},{wp_lat}"
    coords_path += f";{end_lng},{end_lat}"
    
    url = (
        f"https://api.mapbox.com/directions/v5/mapbox/{profile}/"
        f"{coords_path}"
        f"?access_token={MAPBOX_TOKEN}"
        f"&geometries=geojson"
        f"&overview=full"
        f"&alternatives=true"
    )
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                print(f"Mapbox API warning: {resp.status}")
                return []
            data = await resp.json()
            return data.get("routes", [])


@router.post("/route")
async def compute_route(req: RouteRequest):
    """Compute a safety-optimized route using Mapbox Directions and detour waypoints."""
    if not MAPBOX_TOKEN:
        return {"error": "MAPBOX_TOKEN not configured"}
    
    # 1. Fetch the direct Mapbox routes
    routes = await mapbox_directions(
        req.start_lng, req.start_lat,
        req.end_lng, req.end_lat,
        profile="walking"
    )
    
    if req.priority == "safety":
        # Mapbox doesn't know our risk map, so it might only return paths straight through danger.
        # We actively force Mapbox to generate distinctly different paths by requesting physical
        # detours perpendicular to the center of the route.
        
        mid_lat = (req.start_lat + req.end_lat) / 2
        mid_lng = (req.start_lng + req.end_lng) / 2
        d_lat = req.end_lat - req.start_lat
        d_lng = req.end_lng - req.start_lng
        
        length = math.sqrt(d_lat**2 + d_lng**2)
        if length > 0.001:  # Only detour if distance is meaningful (>100m)
            # ~400-500m outward detour scale
            scale = 0.005 / length
            
            # Left side perpendicular vector
            l_lat = mid_lat + (-d_lng * scale)
            l_lng = mid_lng + (d_lat * scale)
            
            # Right side perpendicular vector
            r_lat = mid_lat + (d_lng * scale)
            r_lng = mid_lng + (-d_lat * scale)
            
            # Concurrently fetch these forced alternative paths
            left_routes, right_routes = await asyncio.gather(
                mapbox_directions(req.start_lng, req.start_lat, req.end_lng, req.end_lat, waypoints=[(l_lng, l_lat)]),
                mapbox_directions(req.start_lng, req.start_lat, req.end_lng, req.end_lat, waypoints=[(r_lng, r_lat)])
            )
            routes.extend(left_routes)
            routes.extend(right_routes)
    
    if not routes:
        return {"error": "No route found between these points"}
    
    if req.priority == "safety" and len(routes) > 1:
        best_route = None
        best_score = float('inf')
        
        for route in routes:
            coords = route["geometry"]["coordinates"]
            distance = route["distance"]
            # risk_score is now guaranteed bounded [0, 100]
            risk_score = await get_route_risk_score(coords)
            
            # Using the requested weighting
            # User currently had 0.0 * speed, 1.0 * risk
            score = 0.0 * (distance / 1000) + 1.0 * risk_score
            
            if score < best_score:
                best_score = score
                best_route = route
                
        chosen = best_route or routes[0]
    else:
        # Speed priority: 100% speed weight, just output the first route
        chosen = routes[0]
    
    coords = chosen["geometry"]["coordinates"]
    distance_m = chosen["distance"]
    duration_s = chosen["duration"]
    
    # Compute risk score for the chosen route
    # Now that it's 0-100 normalized, we just pass it natively
    route_risk = await get_route_risk_score(coords)
    
    return {
        "coordinates": coords,
        "distance_m": round(distance_m, 1),
        "duration_min": round(duration_s / 60, 1),
        "priority": req.priority,
        "num_nodes": len(coords),
        "risk_score": round(route_risk, 1),
        "alternatives_evaluated": len(routes),
    }
