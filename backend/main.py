"""
StreetSmarts — FastAPI Backend Entry Point
Real-time safety intelligence system for Saint Louis, MO.
"""

import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from db.database import init_db
from routes import heatmap, routing, social, location_summary, safe_places


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    await init_db()
    print("[SERVER] StreetSmarts backend ready for Saint Louis, MO")
    yield


app = FastAPI(
    title="StreetSmarts API",
    description="Real-time safety intelligence for Saint Louis, MO",
    version="1.0.0",
    lifespan=lifespan
)

# CORS — allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include route modules
app.include_router(heatmap.router)
app.include_router(routing.router)
app.include_router(social.router)
app.include_router(location_summary.router)
app.include_router(safe_places.router)


@app.get("/")
async def root():
    return {
        "name": "StreetSmarts",
        "version": "1.0.0",
        "city": "Saint Louis, MO",
        "status": "running"
    }


@app.get("/health")
async def health():
    from db.db_writer import DBWriter
    db = DBWriter()
    count = await db.count_truth_rows()
    return {"status": "healthy", "truth_rows": count}
