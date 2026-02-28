"""
Location summary endpoint — GET /api/location-summary
Owner: Person 1 (Backend Core)

Returns risk breakdown + recommendation for a clicked map point.
"""

from fastapi import APIRouter, Query

from db.db_writer import DBWriter

router = APIRouter()


@router.get("/location-summary")
async def get_location_summary(
    lat: float = Query(...),
    lng: float = Query(...),
    radius: float = Query(500.0, description="Aggregation radius in meters"),
):
    """Return aggregated risk info for the summary panel.

    TODO:
    1. Call DBWriter.get_location_summary(lat, lng, radius)
    2. Compute risk_score (0-100) from truth values
    3. Assign risk_label (Low / Moderate / High / Very High)
    4. Build recommendation string
    5. List hotspots sorted by risk descending
    """
    # STUB — wired to DBWriter which returns placeholder
    summary = DBWriter.get_location_summary(lat, lng, radius_m=radius)
    return summary
