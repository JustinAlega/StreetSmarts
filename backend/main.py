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
from db.db_writer import DBWriter
from routes import heatmap, routing, social, location_summary, safe_places

ENABLE_LIVE_PIPELINE = os.getenv("ENABLE_LIVE_PIPELINE", "true").lower() in ("1", "true", "yes")
ENABLE_FBI_CRIME_ON_STARTUP = os.getenv("ENABLE_FBI_CRIME_ON_STARTUP", "true").lower() in ("1", "true", "yes")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    await init_db()

    # Auto-seed when truth table is empty
    db = DBWriter()
    count = await db.count_truth_rows()
    if count == 0:
        print("[STARTUP] Truth table empty — running seed...")
        from data_gen import generate_data
        await generate_data()
        print("[STARTUP] Seed complete.")
    else:
        print(f"[STARTUP] Truth table has {count} rows (skip seed)")

    # FBI crime data (runs in background so server starts immediately; many Gemini calls)
    fbi_task = None
    if ENABLE_FBI_CRIME_ON_STARTUP:
        try:
            from static_analysis_pipeline.data_source_stl_crime import process_crime_data
            fbi_task = asyncio.create_task(process_crime_data())
            print("[STARTUP] FBI crime pipeline started (background)")
        except Exception as e:
            print(f"[STARTUP] FBI crime pipeline failed to start: {e}")

    # Start live pipeline in background
    pipeline_task = None
    if ENABLE_LIVE_PIPELINE:
        try:
            from live_pipeline.pipeline import run_pipeline
            pipeline_task = asyncio.create_task(run_pipeline())
            print("[STARTUP] Live pipeline started (Bing News → Gemini → truth table)")
        except Exception as e:
            print(f"[STARTUP] Live pipeline failed to start: {e}")

    print("[SERVER] StreetSmarts backend ready for Saint Louis, MO")
    yield

    if fbi_task and not fbi_task.done():
        fbi_task.cancel()
        try:
            await fbi_task
        except asyncio.CancelledError:
            pass
    if pipeline_task and not pipeline_task.done():
        pipeline_task.cancel()
        try:
            await pipeline_task
        except asyncio.CancelledError:
            pass


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
