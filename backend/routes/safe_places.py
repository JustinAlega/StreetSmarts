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

def _build_prompt(lat: float, lng: float, now_str: str) -> str:
    return f"""Output ONLY valid JSON with a "places" key containing an array. No other text.

Task: List real safe places in Saint Louis, MO — hospitals, pharmacies, libraries, police, fire stations, gas stations, urgent care. User is viewing the map near ({lat}, {lng}); find places within ~5 miles of that area.

CRITICAL: Each place must have its own lat/lng that matches its real street address. Do NOT use ({lat}, {lng}) for every place — that is only the map center. Barnes-Jewish is at 38.6386,-90.2649; Central Library at 38.6296,-90.1993; SLMPD HQ at 38.633,-90.204. Look up or estimate accurate coordinates for each address.

Each place: {{"name": "...", "address": "...", "lat": 38.6xxx, "lng": -90.2xxx, "type": "...", "hours": "..."}}
Types: hospital, police, fire_station, pharmacy, library, gas_station, urgent_care, clinic

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


async def _fetch_and_cache_places(lat: float, lng: float) -> list[dict]:
    """Call Vultr to get fresh safe places."""
    now_stl = datetime.now(ZoneInfo("America/Chicago"))
    now_str = now_stl.strftime("%A, %B %d, %Y at %I:%M %p CT")
    prompt = _build_prompt(lat, lng, now_str)
    
    model_name = os.getenv("VULTR_MODEL", "deepseek-r1-distill-qwen-32b")

    logger.info(f"Refreshing safe places via Vultr ({model_name})")
    
    try:
        response = await _client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You output only valid JSON. Never any text, explanation, or thinking before or after the JSON."},
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

        # Clean and format for DB
        cleaned = []
        for p in places_raw:
            cleaned.append({
                "name": p.get("name", "Unknown"),
                "address": p.get("address", ""),
                "lat": float(p.get("lat", 0)),
                "lng": float(p.get("lng", 0)),
                "type": p.get("type", "hospital"),
                "hours": [p.get("hours", "")] if p.get("hours") else [],
            })

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
    force_refresh: bool = Query(False, description="Force a refresh from Vultr"),
):
    # Check cache status
    stale = await db.is_safe_places_stale(max_age_days=7)

    if not stale and not force_refresh:
        cached = await db.get_all_safe_places()
        if cached:
            places = [_format_place_for_response(p) for p in cached]
            return {"places": sorted(places, key=lambda x: x['open_now'] is not True), "source": "cache"}

    # Refresh using Vultr
    try:
        raw_places = await _fetch_and_cache_places(lat, lng)
        places = [_format_place_for_response(p) for p in raw_places]
        return {"places": sorted(places, key=lambda x: x['open_now'] is not True), "source": "fresh"}
    except Exception as e:
        # Fallback to whatever we have
        cached = await db.get_all_safe_places()
        if cached:
            places = [_format_place_for_response(p) for p in cached]
            return {"places": sorted(places, key=lambda x: x['open_now'] is not True), "source": "stale_cache_error"}
        # Fallback: hardcoded STL safe places when Vultr fails and cache empty
        fallback = [
            {"name": "Barnes-Jewish Hospital", "address": "1 Barnes-Jewish Hospital Plz", "lat": 38.6386, "lng": -90.2649, "type": "hospital", "hours": []},
            {"name": "SLMPD Central Patrol", "address": "1200 Clark Ave", "lat": 38.6330, "lng": -90.2035, "type": "police", "hours": []},
            {"name": "St. Louis Fire Dept", "address": "1421 N 2nd St", "lat": 38.6355, "lng": -90.1879, "type": "fire_station", "hours": []},
            {"name": "Central Library", "address": "1301 Olive St", "lat": 38.6296, "lng": -90.1993, "type": "library", "hours": []},
        ]
        places = [_format_place_for_response(p) for p in fallback]
        return {"places": places, "source": "fallback"}