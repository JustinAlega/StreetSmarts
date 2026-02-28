"""
Heatmap endpoint — GET /api/heatmap-data
Owner: Person 1 (Backend Core)

Returns GeoJSON FeatureCollection for the Mapbox heatmap layer.
"""

from fastapi import APIRouter, Query

from db.db_writer import DBWriter

router = APIRouter()


@router.get("/heatmap-data")
async def get_heatmap_data(
    min_lat: float = Query(..., description="South bound"),
    max_lat: float = Query(..., description="North bound"),
    min_lng: float = Query(..., description="West bound"),
    max_lng: float = Query(..., description="East bound"),
):
    """Return risk points inside the viewport as GeoJSON.

    TODO:
    1. Call DBWriter.get_heatmap_points(min_lat, max_lat, min_lng, max_lng)
    2. Convert each row to a GeoJSON Feature with "risk" property (sum/avg of categories)
    3. Return FeatureCollection
    """
    # STUB — return empty collection
    points = DBWriter.get_heatmap_points(min_lat, max_lat, min_lng, max_lng)

    features = []
    for pt in points:
        # TODO: build Feature dict from pt
        pass

    return {
        "type": "FeatureCollection",
        "features": features,
    }
