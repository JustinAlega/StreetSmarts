import os
import json
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from db.db_writer import DBWriter, CATEGORIES
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize Vultr Client
_client = AsyncOpenAI(
    api_key=os.getenv("VULTR_API_KEY"),
    base_url=os.getenv("VULTR_BASE_URL")
)

router = APIRouter()
db = DBWriter()


class PostRequest(BaseModel):
    lat: float
    lng: float
    content: str


async def classify_post(content: str) -> dict:
    """Use Vultr Llama 3 to classify a community post for severity and category."""
    prompt = f"""You are a safety report classifier for Saint Louis, MO.
Analyze this community report and return a JSON object with:
- "severity": float 0.0-1.0
- "category": one of {CATEGORIES}

Report: "{content}"

Return ONLY valid JSON."""

    model_name = os.getenv("VULTR_MODEL", "meta-llama-3-1-8b-instruct")

    try:
        response = await _client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        return {
            "severity": float(result.get("severity", 0.3)),
            "category": result.get("category", "other")
        }
    except Exception as e:
        print(f"[SOCIAL-VULTR] Classification error: {e}")
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
