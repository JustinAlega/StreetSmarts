"""
PickHacksSP26 — FastAPI Backend Entry Point
Owner: Person 1 (Backend Core)

Run:  uvicorn main:app --reload --port 8000
Docs: http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.database import init_db
from routes import heatmap, routing, social, location_summary

app = FastAPI(title="PickHacksSP26", version="0.1.0")

# --------------- CORS ---------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------- Routes ---------------
app.include_router(heatmap.router,          prefix="/api", tags=["heatmap"])
app.include_router(routing.router,          prefix="/api", tags=["routing"])
app.include_router(social.router,           prefix="/api", tags=["social"])
app.include_router(location_summary.router, prefix="/api", tags=["location"])


# --------------- Startup ---------------
@app.on_event("startup")
async def startup():
    """Initialize DB tables on first launch."""
    init_db()


@app.get("/health")
async def health():
    return {"status": "ok"}
