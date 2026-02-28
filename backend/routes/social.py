"""
Social endpoints — POST /api/post + GET /api/feed
Owner: Person 2 (Backend Data + AI)

Handles community reports: classify with Gemini, store, and retrieve.
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel

from db.db_writer import DBWriter
from ai.gemini_classifier import classify_post

router = APIRouter()


# ---- Request / Response models ---- #

class PostRequest(BaseModel):
    lat: float
    lng: float
    content: str


class PostResponse(BaseModel):
    id: str
    severity: float
    category: str


# ---- Endpoints ---- #

@router.post("/post", response_model=PostResponse)
async def create_post(req: PostRequest):
    """Classify a community report with Gemini, store it, and update truth table.

    TODO:
    1. Call classify_post(req.content) → {severity, category}
    2. Call DBWriter.insert_post(req.lat, req.lng, req.content, severity, category)
    3. Call DBWriter.upsert_truth(req.lat, req.lng, category, severity)
    4. Return post id + classification
    """
    # STUB
    classification = classify_post(req.content)
    severity = classification.get("severity", 0.0)
    category = classification.get("category", "other")

    post_id = DBWriter.insert_post(
        lat=req.lat, lng=req.lng,
        content=req.content,
        severity=severity,
        category=category,
    )

    DBWriter.upsert_truth(req.lat, req.lng, category, severity)

    return PostResponse(id=post_id, severity=severity, category=category)


@router.get("/feed")
async def get_feed(
    lat: float = Query(...),
    lng: float = Query(...),
    radius: float = Query(500.0, description="Search radius in meters"),
):
    """Return nearby posts sorted by recency.

    TODO: this is wired up — just needs DBWriter.get_feed() implemented.
    """
    return DBWriter.get_feed(lat, lng, radius_m=radius)
