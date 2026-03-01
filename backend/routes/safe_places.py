import os
import json
import logging
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Query
from openai import AsyncOpenAI  # Swapped from google.genai
from dotenv import load_dotenv
from db.db_writer import DBWriter

# Setup Logging for Vultr Agent
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StreetSmarts.SafePlaces")

load_dotenv()

router = APIRouter()
db = DBWriter()

# Initialize Vultr Client
_client = AsyncOpenAI(
    api_key=os.getenv("VULTR_API_KEY"),
    base_url=os.getenv("VULTR_BASE_URL")
)

COLOR_MAP = {
    "hospital": "#10b981", "police": "#3b82f6", "fire_station": "#ef4444",
    "pharmacy": "#8b5cf6", "library": "#6366f1", "gas_station": "#f59e0b",
    "urgent_care": "#14b8a6", "clinic": "#10b981", "church": "#f59e0b",
    "community_center": "#6366f1",
}

LABEL_MAP = {
    "hospital": "Hospital", "police": "Police Station", "fire_station": "Fire Station",
    "pharmacy": "Pharmacy", "library": "Library", "gas_station": "Gas Station",
    "urgent_care": "Urgent Care", "clinic": "Clinic", "church": "Place of Worship",
    "community_center": "Community Center",
}

# Saint Louis metro bounds — include places only within region
STL_LAT_MIN, STL_LAT_MAX = 38.45, 38.85
STL_LNG_MIN, STL_LNG_MAX = -90.65, -90.05

MIN_PLACES = 20
FALLBACK_PLACES = [
    {"name": "Barnes-Jewish Hospital", "address": "1 Barnes-Jewish Hospital Plz", "lat": 38.6386, "lng": -90.2649, "type": "hospital", "hours": []},
    {"name": "SLMPD Central Patrol", "address": "1200 Clark Ave", "lat": 38.6330, "lng": -90.2035, "type": "police", "hours": []},
    {"name": "St. Louis Fire Dept", "address": "1421 N 2nd St", "lat": 38.6355, "lng": -90.1879, "type": "fire_station", "hours": []},
    {"name": "Central Library", "address": "1301 Olive St", "lat": 38.6296, "lng": -90.1993, "type": "library", "hours": []},
    {"name": "SSM Health Saint Louis University Hospital", "address": "3635 Vista Ave", "lat": 38.6327, "lng": -90.2275, "type": "hospital", "hours": []},
    {"name": "Mercy Hospital St. Louis", "address": "615 S New Ballas Rd", "lat": 38.6412, "lng": -90.4722, "type": "hospital", "hours": []},
    {"name": "Clayton Police Dept", "address": "10 N Bemiston Ave", "lat": 38.6506, "lng": -90.3342, "type": "police", "hours": []},
    {"name": "University City Police", "address": "6801 Delmar Blvd", "lat": 38.6564, "lng": -90.3096, "type": "police", "hours": []},
    {"name": "CVS Pharmacy Central West End", "address": "4631 Lindell Blvd", "lat": 38.6395, "lng": -90.2665, "type": "pharmacy", "hours": []},
    {"name": "Walgreens Downtown", "address": "3718 Gravois Ave", "lat": 38.5989, "lng": -90.2489, "type": "pharmacy", "hours": []},
    {"name": "Buder Branch Library", "address": "4401 Hampton Ave", "lat": 38.5862, "lng": -90.2912, "type": "library", "hours": []},
    {"name": "Carpenter Branch Library", "address": "3309 S Grand Blvd", "lat": 38.6078, "lng": -90.2667, "type": "library", "hours": []},
    {"name": "Engine House 5", "address": "4200 Delor St", "lat": 38.5895, "lng": -90.2456, "type": "fire_station", "hours": []},
    {"name": "QuikTrip", "address": "3820 Lindell Blvd", "lat": 38.6381, "lng": -90.2712, "type": "gas_station", "hours": []},
    {"name": "Urgent Care St. Louis", "address": "1001 Hampton Ave", "lat": 38.6212, "lng": -90.2789, "type": "urgent_care", "hours": []},
    {"name": "Schlafly Branch Library", "address": "225 N Euclid Ave", "lat": 38.6478, "lng": -90.3056, "type": "library", "hours": []},
    {"name": "Kirkwood Police Dept", "address": "139 S Kirkwood Rd", "lat": 38.5834, "lng": -90.4067, "type": "police", "hours": []},
    {"name": "St. Louis County Library HQ", "address": "1640 S Lindbergh Blvd", "lat": 38.6298, "lng": -90.4123, "type": "library", "hours": []},
]


def _in_stl_bounds(lat: float, lng: float) -> bool:
    return STL_LAT_MIN <= lat <= STL_LAT_MAX and STL_LNG_MIN <= lng <= STL_LNG_MAX


def _build_prompt(lat: float, lng: float, radius_km: float, now_str: str) -> str:
    miles = radius_km / 1.6
    return f"""Output ONLY valid JSON with a "places" key containing an array. No other text.

Task: List at least 25 real safe places in Saint Louis metro. MINIMUM 25 places required. More is better — aim for 30+ if you know them. Search radius: ~{miles:.0f} miles from ({lat}, {lng}).

Include: hospitals, urgent care, police, fire stations, pharmacies (CVS, Walgreens, etc), libraries, gas stations, clinics. Cover Downtown, North City, South City, Clayton, University City, North County, South County, East St. Louis. Spread across the metro.

Each place: {{"name": "...", "address": "...", "lat": 38.xx, "lng": -90.xx, "type": "...", "hours": "..."}}. Types: hospital, police, fire_station, pharmacy, library, gas_station, urgent_care, clinic. Each place MUST have unique lat/lng matching its real address — never duplicate coordinates.

Output JSON:"""


def _determine_open_now(place: dict) -> bool | None:
    """Parse hours if possible; return True/False/None (unknown)."""
    hours = place.get("hours") or []
    if isinstance(hours, str):
        hours = [h.strip() for h in hours.split(",")] if hours else []
    if not hours:
        return None
    # Simple heuristic: "24" or "24 hours" = open
    h_str = " ".join(hours).lower()
    if "24" in h_str or "24/7" in h_str:
        return True
    return None  # Don't guess for complex hours


def _format_place_for_response(place: dict) -> dict:
    """Format DB/AI place for frontend."""
    ptype = place.get("type", "hospital")
    hours = place.get("hours") or []
    if isinstance(hours, str):
        hours = [h.strip() for h in hours.split(",")] if hours else []
    return {
        "name": place.get("name", "Unknown"),
        "address": place.get("address", ""),
        "lat": float(place.get("lat", 0)),
        "lng": float(place.get("lng", 0)),
        "type": ptype,
        "label": LABEL_MAP.get(ptype, ptype.replace("_", " ").title()),
        "color": COLOR_MAP.get(ptype, "#6366f1"),
        "open_now": _determine_open_now(place),
        "hours": hours,
    }


async def _fetch_and_cache_places(lat: float, lng: float, radius_m: int = 25000) -> list[dict]:
    """Call Vultr to get fresh safe places."""
    now_stl = datetime.now(ZoneInfo("America/Chicago"))
    now_str = now_stl.strftime("%A, %B %d, %Y at %I:%M %p CT")
    radius_km = radius_m / 1000.0
    prompt = _build_prompt(lat, lng, radius_km, now_str)
    
    model_name = os.getenv("VULTR_MODEL", "deepseek-r1-distill-qwen-32b")

    logger.info(f"Refreshing safe places via Vultr ({model_name})")
    
    try:
        response = await _client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You output only valid JSON. Never any text before or after. When asked for a list, output at least 25 items."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        if not response.choices:
            raise ValueError("Vultr returned no choices")
        text = (response.choices[0].message.content or "").strip()
        if not text:
            raise ValueError("Vultr returned empty response")
        # Strip markdown code blocks if present (e.g. ```json ... ```)
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)
        try:
            places_data = json.loads(text)
        except json.JSONDecodeError as e:
            logger.warning(f"Vultr response not valid JSON (first 200 chars): {text[:200]!r}")
            # Try to extract JSON array/object from response
            m = re.search(r'\[[\s\S]*\]|\{[\s\S]*\}', text)
            if m:
                places_data = json.loads(m.group(0))
            else:
                raise e
        
        # Handle if AI wraps list in a key
        if isinstance(places_data, dict) and "places" in places_data:
            places_raw = places_data["places"]
        elif isinstance(places_data, list):
            places_raw = places_data
        else:
            places_raw = []

        # Deduplicate: skip same name+type or same location (rounded to ~10m)
        seen_names = set()
        seen_coords = set()
        deduped = []
        for p in places_raw:
            plat, plng = float(p.get("lat", 0)), float(p.get("lng", 0))
            coord = (round(plat, 4), round(plng, 4))
            name = ((p.get("name") or "").strip() or "unknown").lower()
            ptype = p.get("type", "other")
            if (name, ptype) in seen_names or coord in seen_coords:
                continue
            seen_names.add((name, ptype))
            seen_coords.add(coord)
            deduped.append(p)
        places_raw = deduped

        # Clean, filter to St Louis bounds, format for DB
        cleaned = []
        seen_names = set()
        for p in places_raw:
            plat, plng = float(p.get("lat", 0)), float(p.get("lng", 0))
            if not _in_stl_bounds(plat, plng):
                continue
            name = (p.get("name") or "").strip()
            if name.lower() in seen_names:
                continue
            seen_names.add(name.lower())
            cleaned.append({
                "name": name or "Unknown",
                "address": p.get("address", ""),
                "lat": plat,
                "lng": plng,
                "type": p.get("type", "hospital"),
                "hours": [p.get("hours", "")] if p.get("hours") else [],
            })

        # Pad to at least MIN_PLACES using fallback if Vultr returned too few
        if len(cleaned) < MIN_PLACES:
            for fp in FALLBACK_PLACES:
                if len(cleaned) >= MIN_PLACES:
                    break
                if fp["name"].lower() not in seen_names:
                    seen_names.add(fp["name"].lower())
                    cleaned.append(fp)

        await db.refresh_safe_places(cleaned)
        logger.info(f"Successfully cached {len(cleaned)} places via Vultr.")
        return cleaned

    except Exception as e:
        logger.error(f"Vultr Safe Places Error: {e}")
        raise

@router.get("/nearby-safe")
async def get_nearby_safe(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    radius: int = Query(25000, description="Search radius in meters (default 25km)"),
    force_refresh: bool = Query(False, description="Force a refresh from Vultr"),
):
    # Check cache status
    stale = await db.is_safe_places_stale(max_age_days=7)

    if not stale and not force_refresh:
        cached = await db.get_all_safe_places()
        if cached:
            places = [_format_place_for_response(p) for p in cached if _in_stl_bounds(float(p.get("lat", 0)), float(p.get("lng", 0)))]
            return {"places": sorted(places, key=lambda x: x['open_now'] is not True), "source": "cache"}

    # Refresh using Vultr
    try:
        raw_places = await _fetch_and_cache_places(lat, lng, radius_m=radius)
        places = [_format_place_for_response(p) for p in raw_places]
        return {"places": sorted(places, key=lambda x: x['open_now'] is not True), "source": "fresh"}
    except Exception as e:
        # Fallback to whatever we have
        cached = await db.get_all_safe_places()
        if cached:
            places = [_format_place_for_response(p) for p in cached if _in_stl_bounds(float(p.get("lat", 0)), float(p.get("lng", 0)))]
            return {"places": sorted(places, key=lambda x: x['open_now'] is not True), "source": "stale_cache_error"}
        places = [_format_place_for_response(p) for p in FALLBACK_PLACES]
        return {"places": places, "source": "fallback"}