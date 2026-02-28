"""
Social feed routes for StreetSmarts.
Handles community reports (POST /post) and feed retrieval (GET /feed).
Uses Gemini for post classification.
"""

import os
import json
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from db.db_writer import DBWriter
from google import genai
from dotenv import load_dotenv

load_dotenv()

_client = None

def get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _client

router = APIRouter()
db = DBWriter()


class PostRequest(BaseModel):
    lat: float
    lng: float
    content: str


class FeedRequest(BaseModel):
    lat: float
    lng: float
    radius_km: float = 2.0


async def classify_post(content: str) -> dict:
    """Use Gemini to classify a community post for severity and category."""
    prompt = f"""You are a safety report classifier for Saint Louis, MO.
Analyze this community report and return a JSON object with:
- "severity": float 0.0-1.0 (0=benign, 1=critical emergency)
- "category": one of ["crime", "public_safety", "transport", "infrastructure", "policy", "protest", "weather", "other"]

Be precise. Consider:
- 0.0-0.2: Minor observations (e.g. "street light flickering")
- 0.2-0.4: Noteworthy but low risk (e.g. "lots of parked cars blocking view")
- 0.4-0.6: Moderate concern (e.g. "someone acting suspiciously")
- 0.6-0.8: Significant safety issue (e.g. "break-in reported on Main St")
- 0.8-1.0: Critical / imminent danger (e.g. "active shooter", "building collapse")

Report: "{content}"

Return ONLY valid JSON, no markdown, no explanation."""

    try:
        response = get_client().models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        text = response.text.strip()
        # Remove markdown code fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0]
        result = json.loads(text)
        return {
            "severity": float(result.get("severity", 0.3)),
            "category": result.get("category", "other")
        }
    except Exception as e:
        print(f"[SOCIAL] Classification error: {e}")
        return {"severity": 0.3, "category": "other"}


@router.post("/post")
async def create_post(req: PostRequest):
    """Create a new community safety report."""
    classification = await classify_post(req.content)
    
    await db.insert_post(
        lat=req.lat,
        lng=req.lng,
        content=req.content,
        severity=classification["severity"],
        category=classification["category"],
        human=True
    )
    
    # Update truth table
    await db.update_truth(
        lat=req.lat,
        lng=req.lng,
        category=classification["category"],
        severity=classification["severity"]
    )
    
    return {
        "status": "ok",
        "severity": classification["severity"],
        "category": classification["category"]
    }


@router.get("/feed")
async def get_feed(lat: float, lng: float, radius_km: float = 2.0):
    """Get recent community reports near a location."""
    posts = await db.get_feed(lat, lng, radius_km)
    return {"posts": posts, "count": len(posts)}
