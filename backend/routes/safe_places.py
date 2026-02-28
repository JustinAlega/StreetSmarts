"""
Nearby safe places endpoint for StreetSmarts.
Uses Gemini 2.0 Flash with Google Search grounding to find hospitals,
police stations, fire stations, pharmacies, and other safe spaces
with real-time open/closed status near a given location.
"""

import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Query
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

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

For EACH place, determine whether it is currently OPEN or CLOSED right now based on its real business hours and the current time above.

Return ONLY a JSON array of objects. Each object must have exactly these keys:
- "name": string (the real name of the place)
- "address": string (full street address)
- "lat": number (latitude, must be accurate)
- "lng": number (longitude, must be accurate)
- "type": string (one of: "hospital", "police", "fire_station", "pharmacy", "library", "gas_station", "urgent_care", "clinic")
- "open_now": boolean (true if currently open, false if closed)
- "hours": string (today's hours, e.g. "Open 24 hours" or "9:00 AM - 9:00 PM" or "Closed today")

Return ONLY the raw JSON array. No markdown fences, no explanation, no extra text."""


def _parse_places(text: str) -> list[dict]:
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
            "label":    LABEL_MAP.get(ptype, ptype.replace("_", " ").title()),
            "color":    COLOR_MAP.get(ptype, "#6b7280"),
            "open_now": p.get("open_now"),
            "hours":    [p.get("hours", "")] if p.get("hours") else [],
        })
    return cleaned


@router.get("/nearby-safe")
async def get_nearby_safe(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
):
    """Find nearby safe spaces using Gemini with Google Search grounding."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"error": "GEMINI_API_KEY not configured", "places": []}

    now_stl = datetime.now(ZoneInfo("America/Chicago"))
    now_str = now_stl.strftime("%A, %B %d, %Y at %I:%M %p CT")

    prompt = _build_prompt(lat, lng, now_str)

    try:
        response = get_client().models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.2,
            ),
        )

        places = _parse_places(response.text)
    except Exception as e:
        print(f"[SAFE_PLACES] Gemini error: {e}")
        return {"error": str(e), "places": []}

    open_places = [p for p in places if p.get("open_now") is True]
    closed_places = [p for p in places if p.get("open_now") is not True]

    return {"places": open_places + closed_places, "count": len(places)}
