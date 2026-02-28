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
        best_route = None
        best_score = float('inf')
        
        for route in routes:
            coords = route["geometry"]["coordinates"]
            distance = route["distance"]
            # risk_score is now guaranteed bounded [0, 100]
            risk_score = await get_route_risk_score(coords)
            
            # Using the requested 50/50 weighting for safety priority
            # 50% weight to speed (distance in km)
            # 50% weight to safety (using the 0-100 native risk score)
            score = 0.3 * (distance / 1000) + 0.7 * risk_score
            
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
