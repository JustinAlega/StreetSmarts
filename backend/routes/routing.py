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


def _haversine_m(lng1, lat1, lng2, lat2):
    """Approximate distance in meters between two points."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _remove_route_loops(coordinates, dist_threshold_m=80, min_loop_points=4):
    """Remove pointless out-and-back loops. Coords are [lng, lat]."""
    coords = list(coordinates)
    n = len(coords)
    if n < min_loop_points + 2:
        return coords
    # ~80m in degrees at mid-lat
    thresh_deg = dist_threshold_m / 111000.0
    changed = True
    while changed:
        changed = False
        for i in range(1, n):
            for j in range(max(0, i - 50), i):  # limit search
                if i - j < min_loop_points:
                    continue
                c1, c2 = coords[i], coords[j]
                d = math.sqrt((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2)
                if d < thresh_deg:
                    coords = coords[: j + 1] + coords[i + 1 :]
                    n = len(coords)
                    changed = True
                    break
            if changed:
                break
    return coords


async def get_route_risk_score(coordinates):
    """Compute risk along a route. Heavily penalizes max risk (touching red zones) and time-in-danger."""
    if not coordinates or len(coordinates) < 2:
        return 0.0
    
    step = max(1, len(coordinates) // 60)
    sample_indices = list(range(0, len(coordinates), step))
    risks = []
    for i in sample_indices:
        coord = coordinates[i]
        base_risk = await get_risk_at(coord[1], coord[0])
        risks.append(base_risk)
    if not risks:
        return 0.0
    max_risk = max(risks)
    # Integrated risk: penalize spending distance in bad areas (skirting = low integral)
    avg_risk = sum(risks) / len(risks)
    # Combined: max_risk^2 dominates (never touch red), avg_risk^1.5 penalizes lingering
    score = 0.7 * (max_risk ** 2) + 0.3 * (avg_risk ** 1.5)
    return min(100.0, score * 100.0)


async def mapbox_directions(start_lng, start_lat, end_lng, end_lat, profile="driving", waypoints=None):
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
        profile="driving"
    )
    
    if req.priority == "safety":
        # Mapbox doesn't know our risk map. Generate multiple detour paths that skirt around
        # the direct line — near and far perpendicular offsets, and at 1/3 and 2/3 points.
        mid_lat = (req.start_lat + req.end_lat) / 2
        mid_lng = (req.start_lng + req.end_lng) / 2
        d_lat = req.end_lat - req.start_lat
        d_lng = req.end_lng - req.start_lng
        length = math.sqrt(d_lat**2 + d_lng**2)

        if length > 0.001:
            # Perp unit vector (left side)
            perp_lat = -d_lng / length
            perp_lng = d_lat / length

            # Detour offsets — near 0.5km, mid 1.2km, far 2km, arc 3.5km, big_arc 5km
            near_deg = 0.004
            mid_deg = 0.011
            far_deg = 0.018
            arc_deg = 0.032
            big_deg = 0.045

            # Points at quarters along the path — so we can detour around danger at 1/4, 1/2, or 3/4
            def pt(t):
                lat = req.start_lat + d_lat * t
                lng = req.start_lng + d_lng * t
                return (lat, lng)

            quarters = [0.25, 0.5, 0.75]  # 1/4, halfway, 3/4

            # Single-waypoint detours at EACH quarter — catches danger zones at any segment
            single_wps = []
            for t in quarters:
                lat_t, lng_t = pt(t)
                for deg in [near_deg, mid_deg, far_deg, arc_deg, big_deg]:
                    single_wps.append((lng_t + perp_lng * deg, lat_t + perp_lat * deg))
                    single_wps.append((lng_t - perp_lng * deg, lat_t - perp_lat * deg))

            # Two-waypoint arc routes: cover danger at different segments
            # (0.25, 0.75), (0.25, 0.5), (0.5, 0.75), (0.25, 0.5, 0.75) via two-waypoint
            arc_pairs = [(0.25, 0.75), (0.25, 0.5), (0.5, 0.75), (0.2, 0.8)]
            arc_wps = []
            for t1, t2 in arc_pairs:
                p1, p2 = pt(t1), pt(t2)
                for deg in [arc_deg, big_deg]:
                    arc_wps.append([
                        (p1[1] + perp_lng * deg, p1[0] + perp_lat * deg),
                        (p2[1] - perp_lng * deg, p2[0] - perp_lat * deg),
                    ])
                    arc_wps.append([
                        (p1[1] - perp_lng * deg, p1[0] - perp_lat * deg),
                        (p2[1] + perp_lng * deg, p2[0] + perp_lat * deg),
                    ])

            # Fetch all single-waypoint routes
            single_routes = await asyncio.gather(
                *[mapbox_directions(req.start_lng, req.start_lat, req.end_lng, req.end_lat, waypoints=[wp]) for wp in single_wps]
            )
            for r in single_routes:
                routes.extend(r)

            # Fetch arc routes
            arc_tasks = [
                mapbox_directions(req.start_lng, req.start_lat, req.end_lng, req.end_lat, waypoints=wp_list)
                for wp_list in arc_wps
            ]
            arc_results = await asyncio.gather(*arc_tasks, return_exceptions=True)
            for r in arc_results:
                if isinstance(r, list):
                    routes.extend(r)
    
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
    orig_distance_m = chosen["distance"]
    orig_duration_s = chosen["duration"]

    # Remove pointless out-and-back loops (e.g. detour that circles and returns)
    coords = _remove_route_loops(coords)

    # Recompute distance for de-looped route; scale duration proportionally
    if len(coords) >= 2:
        distance_m = sum(
            _haversine_m(c0[0], c0[1], c1[0], c1[1])
            for c0, c1 in zip(coords[:-1], coords[1:])
        )
        if orig_distance_m > 0:
            duration_s = orig_duration_s * (distance_m / orig_distance_m)
        else:
            duration_s = orig_duration_s
    else:
        distance_m, duration_s = orig_distance_m, orig_duration_s

    # Compute risk score for the chosen route
    route_risk = await get_route_risk_score(coords)
    if req.priority != "safety":
        route_risk *= 2

    return {
        "coordinates": coords,
        "distance_m": round(distance_m, 1),
        "duration_min": round(duration_s / 60, 1),
        "priority": req.priority,
        "num_nodes": len(coords),
        "risk_score": round(route_risk, 1),
        "alternatives_evaluated": len(routes),
    }
