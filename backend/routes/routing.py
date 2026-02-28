"""
Safety-optimized routing for StreetSmarts.
Uses Mapbox Directions API for reliable routing, with safety risk overlay.
Falls back to A* on OSMnx graph when available.
"""

import os
import math
import aiohttp
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from db.db_writer import DBWriter, CATEGORIES
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
    
    # Max across categories
    risk = max(truth.get(c, 0.0) for c in CATEGORIES)
    
    # Distance decay
    dist_deg = math.sqrt((lat - truth["lat"])**2 + (lng - truth["lng"])**2)
    decay = math.exp(-dist_deg**2 / (2 * 0.002**2))
    
    return risk * decay


async def get_route_risk_score(coordinates):
    """Compute average risk along a route by sampling points."""
    if not coordinates or len(coordinates) < 2:
        return 0.0
    
    # Sample up to 10 points along the route
    step = max(1, len(coordinates) // 10)
    sample_indices = list(range(0, len(coordinates), step))
    
    risks = []
    for i in sample_indices:
        coord = coordinates[i]
        risk = await get_risk_at(coord[1], coord[0])  # lat, lng
        risks.append(risk)
    
    return sum(risks) / len(risks) if risks else 0.0


async def mapbox_directions(start_lng, start_lat, end_lng, end_lat, profile="walking"):
    """Get a route from Mapbox Directions API."""
    url = (
        f"https://api.mapbox.com/directions/v5/mapbox/{profile}/"
        f"{start_lng},{start_lat};{end_lng},{end_lat}"
        f"?access_token={MAPBOX_TOKEN}"
        f"&geometries=geojson"
        f"&overview=full"
        f"&alternatives=true"
    )
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            return data.get("routes", [])


@router.post("/route")
async def compute_route(req: RouteRequest):
    """Compute a safety-optimized route using Mapbox Directions."""
    
    if not MAPBOX_TOKEN:
        return {"error": "MAPBOX_TOKEN not configured"}
    
    # Get routes from Mapbox (including alternatives)
    routes = await mapbox_directions(
        req.start_lng, req.start_lat,
        req.end_lng, req.end_lat,
        profile="walking"
    )
    
    if not routes:
        return {"error": "No route found between these points"}
    
    if req.priority == "safety" and len(routes) > 1:
        # Score each route by risk and pick the safest
        best_route = None
        best_score = float('inf')
        
        for route in routes:
            coords = route["geometry"]["coordinates"]
            distance = route["distance"]
            risk = await get_route_risk_score(coords)
            
            # Combined score: lower is better
            # For safety priority: weight risk heavily
            score = 0.3 * (distance / 1000) + 0.7 * (risk * 100)
            
            if score < best_score:
                best_score = score
                best_route = route
        
        chosen = best_route or routes[0]
    else:
        # Speed priority: just use the first (shortest) route
        chosen = routes[0]
    
    coords = chosen["geometry"]["coordinates"]
    distance_m = chosen["distance"]
    duration_s = chosen["duration"]
    
    # Compute risk score for the chosen route
    route_risk = await get_route_risk_score(coords)
    
    return {
        "coordinates": coords,
        "distance_m": round(distance_m, 1),
        "duration_min": round(duration_s / 60, 1),
        "priority": req.priority,
        "num_nodes": len(coords),
        "risk_score": round(route_risk * 100, 1),
        "alternatives_evaluated": len(routes),
    }
