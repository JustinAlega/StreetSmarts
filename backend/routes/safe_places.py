"""
Nearby safe places endpoint for StreetSmarts.
Serves cached safe locations from the database.
Refreshes data weekly via Gemini 2.5 Flash with Google Search grounding.
"""

import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Query
from google import genai
from google.genai import types
from dotenv import load_dotenv
from db.db_writer import DBWriter

load_dotenv()

router = APIRouter()
db = DBWriter()

_client = None

def get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _client

COLOR_MAP = {
    "hospital":     "#10b981",
    "police":       "#3b82f6",
    "fire_station": "#ef4444",
    "pharmacy":     "#8b5cf6",
    "library":      "#6366f1",
    "gas_station":  "#f59e0b",
    "urgent_care":  "#14b8a6",
    "clinic":       "#10b981",
    "church":       "#f59e0b",
    "community_center": "#6366f1",
}

LABEL_MAP = {
    "hospital":     "Hospital",
    "police":       "Police Station",
    "fire_station": "Fire Station",
    "pharmacy":     "Pharmacy",
    "library":      "Library",
    "gas_station":  "Gas Station",
    "urgent_care":  "Urgent Care",
    "clinic":       "Clinic",
    "church":       "Place of Worship",
    "community_center": "Community Center",
}


def _build_prompt(lat: float, lng: float, now_str: str) -> str:
    return f"""You are a local safety assistant. Find real, currently operating safe places near the coordinates ({lat}, {lng}) in Saint Louis, Missouri.

Current local date and time: {now_str}

Search for ALL of the following categories and return as many real results as you can find (aim for 3-5 per category):
1. Hospitals and urgent care centers
2. Police stations
3. Fire stations
4. Pharmacies (like CVS, Walgreens, etc.)
5. Libraries
6. Gas stations / convenience stores that are open

For EACH place, provide its real business hours.

Return ONLY a JSON array of objects. Each object must have exactly these keys:
- "name": string (the real name of the place)
- "address": string (full street address)
- "lat": number (latitude, must be accurate)
- "lng": number (longitude, must be accurate)
- "type": string (one of: "hospital", "police", "fire_station", "pharmacy", "library", "gas_station", "urgent_care", "clinic")
- "hours": string (typical hours, e.g. "Open 24 hours" or "9:00 AM - 9:00 PM" or "Mon-Fri 8AM-8PM, Sat 9AM-5PM")

Return ONLY the raw JSON array. No markdown fences, no explanation, no extra text."""


def _parse_places_from_gemini(text: str) -> list[dict]:
    """Parse the JSON array from Gemini's response, handling markdown fences."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    places = json.loads(text)
    if not isinstance(places, list):
        return []

    cleaned = []
    for p in places:
        if not isinstance(p, dict):
            continue
        ptype = p.get("type", "hospital")
        cleaned.append({
            "name":     p.get("name", "Unknown"),
            "address":  p.get("address", ""),
            "lat":      float(p.get("lat", 0)),
            "lng":      float(p.get("lng", 0)),
            "type":     ptype,
            "hours":    [p.get("hours", "")] if p.get("hours") else [],
        })
    return cleaned


def _determine_open_now(hours_str: str) -> bool | None:
    """Determine if a place is currently open based on its hours string."""
    if not hours_str:
        return None
    hours_lower = hours_str.lower()
    if "24 hour" in hours_lower or "24/7" in hours_lower:
        return True
    if "closed" in hours_lower and ("today" in hours_lower or "permanently" in hours_lower):
        return False
    # For everything else, try simple time parsing
    now = datetime.now(ZoneInfo("America/Chicago"))
    current_hour = now.hour
    # Most places are open roughly 8am-9pm
    # This is a rough heuristic — Google Places API would be more accurate
    if 8 <= current_hour < 21:
        if "closed" not in hours_lower:
            return True
    return None


def _format_place_for_response(p: dict) -> dict:
    """Format a safe place record (from DB or Gemini) for the API response."""
    ptype = p.get("type", "hospital")
    hours_raw = p.get("hours", "")
    # hours can be a list or string depending on source
    if isinstance(hours_raw, list):
        hours_list = hours_raw
        hours_str = ", ".join(hours_raw)
    else:
        hours_str = hours_raw
        hours_list = [hours_raw] if hours_raw else []

    return {
        "name":     p.get("name", "Unknown"),
        "address":  p.get("address", ""),
        "lat":      float(p.get("lat", 0)),
        "lng":      float(p.get("lng", 0)),
        "type":     ptype,
        "label":    LABEL_MAP.get(ptype, ptype.replace("_", " ").title()),
        "color":    COLOR_MAP.get(ptype, "#6b7280"),
        "open_now": _determine_open_now(hours_str),
        "hours":    hours_list,
    }


async def _fetch_and_cache_places(lat: float, lng: float) -> list[dict]:
    """Call Gemini to get fresh safe places and store them in the database."""
    now_stl = datetime.now(ZoneInfo("America/Chicago"))
    now_str = now_stl.strftime("%A, %B %d, %Y at %I:%M %p CT")
    prompt = _build_prompt(lat, lng, now_str)

    response = get_client().models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.2,
        ),
    )

    places = _parse_places_from_gemini(response.text)

    # Save to database
    await db.refresh_safe_places(places)
    print(f"[SAFE_PLACES] Cached {len(places)} places in database")

    return places


@router.get("/nearby-safe")
async def get_nearby_safe(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    force_refresh: bool = Query(False, description="Force a refresh from Gemini"),
):
    """
    Return nearby safe places.
    Serves from database cache if data exists and is less than 7 days old.
    Otherwise fetches fresh data from Gemini and caches it.
    """
    api_key = os.getenv("GEMINI_API_KEY")

    # Check if we have fresh data in the database
    stale = await db.is_safe_places_stale(max_age_days=7)

    if not stale and not force_refresh:
        # Serve from database — instant response
        cached = await db.get_all_safe_places()
        if cached:
            places = [_format_place_for_response(p) for p in cached]
            open_places = [p for p in places if p.get("open_now") is True]
            closed_places = [p for p in places if p.get("open_now") is not True]
            print(f"[SAFE_PLACES] Serving {len(places)} cached places from DB")
            return {"places": open_places + closed_places, "count": len(places), "source": "cache"}

    # Need to fetch fresh data
    if not api_key:
        return {"error": "GEMINI_API_KEY not configured", "places": []}

    try:
        raw_places = await _fetch_and_cache_places(lat, lng)
        places = [_format_place_for_response(p) for p in raw_places]
    except Exception as e:
        print(f"[SAFE_PLACES] Gemini error: {e}")
        # If Gemini fails but we have stale data, serve it anyway
        cached = await db.get_all_safe_places()
        if cached:
            places = [_format_place_for_response(p) for p in cached]
            open_places = [p for p in places if p.get("open_now") is True]
            closed_places = [p for p in places if p.get("open_now") is not True]
            return {"places": open_places + closed_places, "count": len(places), "source": "stale_cache"}
        return {"error": str(e), "places": []}

    open_places = [p for p in places if p.get("open_now") is True]
    closed_places = [p for p in places if p.get("open_now") is not True]

    return {"places": open_places + closed_places, "count": len(places), "source": "fresh"}
