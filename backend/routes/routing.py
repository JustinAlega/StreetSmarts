"""
Safety-optimized routing — POST /api/route
Owner: Person 1 (Backend Core)

Uses OSMnx + NetworkX A* on St. Louis walking graph.
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

# ---- Constants ---- #
STL_CENTER = (38.627, -90.199)
GRAPH_FILE = "stl_walk.graphml"
LENGTH_SCALE = 500.0  # normalizer for distance in weight formula


# ---- Request / Response models ---- #
class RouteRequest(BaseModel):
    start: list[float]      # [lng, lat]
    end: list[float]        # [lng, lat]
    lambda_val: float = 0.5 # 0 = shortest, 1 = safest


class RouteResponse(BaseModel):
    coordinates: list[list[float]]
    lambda_val: float


# ---- Graph management ---- #

def load_or_download_graph():
    """Load cached .graphml or download STL walking graph via OSMnx.

    TODO:
    1. If GRAPH_FILE exists, load with osmnx.load_graphml()
    2. Else download with osmnx.graph_from_point(STL_CENTER, dist=5000, network_type='walk')
    3. Save to GRAPH_FILE
    4. Return the graph
    """
    # STUB
    return None


def risk_at_point(lat: float, lng: float) -> float:
    """Query the truth table and return a single aggregate risk score [0-1].

    TODO: call DBWriter.risk_at_point() and average the category values
    """
    # STUB
    return 0.0


def compute_route(graph, start_lnglat: list[float], end_lnglat: list[float], lambda_val: float) -> list[list[float]]:
    """Run A* on the walking graph with safety-weighted edges.

    TODO:
    1. Find nearest nodes to start/end with osmnx.nearest_nodes()
    2. Define weight function:
         weight(u,v,d) = (1-λ)*norm_distance + λ*risk_at_midpoint
    3. Run nx.astar_path(G, start_node, end_node, weight=weight)
    4. Convert node sequence to [[lng, lat], ...] coordinate list
    """
    # STUB
    return []


# ---- Endpoint ---- #

@router.post("/route", response_model=RouteResponse)
async def get_route(req: RouteRequest):
    """Return a safety-optimized walking route.

    TODO:
    1. Load graph (lazy singleton)
    2. Call compute_route(graph, req.start, req.end, req.lambda_val)
    3. Return coordinates
    """
    # STUB
    coords = compute_route(None, req.start, req.end, req.lambda_val)
    return RouteResponse(coordinates=coords, lambda_val=req.lambda_val)
