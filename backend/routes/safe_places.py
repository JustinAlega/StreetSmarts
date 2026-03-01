import os
import json
import logging
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
    return f"""You are a local safety assistant for Saint Louis, Missouri.
Current local date/time: {now_str}
Location context: Nearby ({lat}, {lng})

Identify 3-5 real, currently operating safe places for these categories:
1. Hospitals/Urgent Care 2. Police 3. Fire Stations 4. Pharmacies 5. Libraries 6. Gas Stations

Return ONLY a JSON array of objects with these keys:
"name", "address", "lat", "lng", "type", "hours"

Valid types: "hospital", "police", "fire_station", "pharmacy", "library", "gas_station", "urgent_care", "clinic"

Return ONLY raw JSON."""

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
                {"role": "system", "content": "You are a helpful assistant that outputs JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        text = response.choices[0].message.content
        places_data = json.loads(text)
        
        # Handle if AI wraps list in a key
        if isinstance(places_data, dict) and "places" in places_data:
            places_raw = places_data["places"]
        elif isinstance(places_data, list):
            places_raw = places_data
        else:
            places_raw = []

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
        return {"error": str(e), "places": []}

# ... (Keep your helper functions: _determine_open_now, _format_place_for_response)