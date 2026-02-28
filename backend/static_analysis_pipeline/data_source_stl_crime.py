"""
Saint Louis Crime Data Source.
Fetches real crime statistics from the FBI Crime Data Explorer (CDE) API
for the St. Louis Police Department (ORI: MOSPD0000) and processes them
through the Gemini criticality agent to populate the truth table.
"""

import asyncio
import aiohttp
import os
import math
from datetime import datetime
from db.db_writer import DBWriter
from live_pipeline.criticality_agent import CriticalityAgent

FBI_CDE_BASE = "https://api.usa.gov/crime/fbi/cde"
FBI_API_KEY = os.getenv("FBI_API_KEY", "")
STL_ORI = "MOSPD0000"

FBI_OFFENSES = [
    "homicide",
    "robbery",
    "aggravated-assault",
    "burglary",
    "larceny",
    "motor-vehicle-theft",
    "arson",
]

OFFENSE_TO_CATEGORY = {
    "homicide":             "crime",
    "robbery":              "crime",
    "aggravated-assault":   "crime",
    "burglary":             "crime",
    "larceny":              "crime",
    "motor-vehicle-theft":  "crime",
    "arson":                "crime",
}

# Maps FBI offense names to human-readable labels for post content
OFFENSE_LABELS = {
    "homicide":             "Homicide",
    "robbery":              "Robbery",
    "aggravated-assault":   "Aggravated Assault",
    "burglary":             "Burglary",
    "larceny":              "Larceny / Theft",
    "motor-vehicle-theft":  "Motor Vehicle Theft",
    "arson":                "Arson",
}

# Known STL neighborhoods with approximate centroids — used to distribute
# FBI aggregate counts spatially across the city.
STL_NEIGHBORHOODS = [
    {"lat": 38.6270, "lng": -90.1994, "name": "Downtown",          "weight": 1.4},
    {"lat": 38.6495, "lng": -90.2350, "name": "North City",        "weight": 1.6},
    {"lat": 38.6095, "lng": -90.2090, "name": "Soulard",           "weight": 0.8},
    {"lat": 38.6398, "lng": -90.2613, "name": "Central West End",  "weight": 0.9},
    {"lat": 38.6328, "lng": -90.2507, "name": "The Grove",         "weight": 0.7},
    {"lat": 38.6359, "lng": -90.2854, "name": "Forest Park SE",    "weight": 0.5},
    {"lat": 38.6100, "lng": -90.2100, "name": "Near Soulard",      "weight": 0.8},
    {"lat": 38.6200, "lng": -90.1800, "name": "Near Riverfront",   "weight": 1.0},
    {"lat": 38.6550, "lng": -90.2100, "name": "Midtown",           "weight": 1.1},
    {"lat": 38.6700, "lng": -90.2600, "name": "North County",      "weight": 1.3},
    {"lat": 38.5870, "lng": -90.2450, "name": "South City",        "weight": 0.6},
    {"lat": 38.6440, "lng": -90.2150, "name": "Grand Center",      "weight": 1.0},
]

# Fallback sample data (used only when the FBI API is completely unavailable)
SAMPLE_CRIME_DATA = [
    {"lat": 38.6270, "lng": -90.1994, "category": "Theft",          "count": 45, "area": "Downtown"},
    {"lat": 38.6559, "lng": -90.3049, "category": "Assault",        "count": 12, "area": "Delmar Loop"},
    {"lat": 38.6095, "lng": -90.2090, "category": "Burglary",       "count": 18, "area": "Soulard"},
    {"lat": 38.6398, "lng": -90.2613, "category": "Vehicle Theft",  "count": 22, "area": "Central West End"},
    {"lat": 38.6328, "lng": -90.2507, "category": "Robbery",        "count": 8,  "area": "The Grove"},
    {"lat": 38.6359, "lng": -90.2854, "category": "Theft",          "count": 15, "area": "Forest Park"},
    {"lat": 38.6495, "lng": -90.2350, "category": "Assault",        "count": 35, "area": "North City"},
    {"lat": 38.6100, "lng": -90.2100, "category": "Burglary",       "count": 20, "area": "Near Soulard"},
    {"lat": 38.6200, "lng": -90.1800, "category": "Robbery",        "count": 14, "area": "Near Riverfront"},
    {"lat": 38.6550, "lng": -90.2100, "category": "Vehicle Theft",  "count": 28, "area": "Midtown"},
]


def _date_range_params() -> dict:
    """Build from/to query params covering the most recent full calendar year.

    FBI data lags by several months, so requesting the current year often
    returns nulls.  Using the last full year (e.g. 01-2025 to 12-2025 when
    the current date is in 2026) gives the most complete dataset.
    """
    last_year = datetime.utcnow().year - 1
    return {"from": f"01-{last_year}", "to": f"12-{last_year}"}


async def fetch_fbi_crime() -> dict | None:
    """Fetch summarized crime data for STL from the FBI CDE API.

    Returns a dict mapping offense names to their monthly actual counts,
    e.g. {"robbery": {"01-2024": 46, ...}, ...}
    Returns None if the API is unreachable.
    """
    if not FBI_API_KEY:
        print("[STL_CRIME] FBI_API_KEY not set, using sample data")
        return None

    date_params = _date_range_params()
    results: dict[str, dict] = {}
    max_retries = 2

    try:
        async with aiohttp.ClientSession() as session:
            for offense in FBI_OFFENSES:
                url = f"{FBI_CDE_BASE}/summarized/agency/{STL_ORI}/{offense}"
                params = {**date_params, "API_KEY": FBI_API_KEY}

                for attempt in range(max_retries + 1):
                    try:
                        async with session.get(url, params=params,
                                               timeout=aiohttp.ClientTimeout(total=20)) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                actuals = data.get("offenses", {}).get("actuals", {})
                                key = "St. Louis Police Department Offenses"
                                if key in actuals:
                                    counts = {k: v for k, v in actuals[key].items()
                                              if v is not None}
                                    results[offense] = counts
                                    total = sum(counts.values())
                                    print(f"  [FBI] {offense}: {total} offenses")
                                else:
                                    print(f"  [FBI] {offense}: no STL actuals in response")
                                break
                            elif resp.status == 503 and attempt < max_retries:
                                wait = 2 ** (attempt + 1)
                                print(f"  [FBI] {offense}: 503, retrying in {wait}s...")
                                await asyncio.sleep(wait)
                            else:
                                print(f"  [FBI] {offense}: HTTP {resp.status}")
                                break
                    except asyncio.TimeoutError:
                        if attempt < max_retries:
                            print(f"  [FBI] {offense}: timeout, retrying...")
                            await asyncio.sleep(2)
                        else:
                            print(f"  [FBI] {offense}: timeout after {max_retries + 1} attempts")

    except Exception as e:
        print(f"[STL_CRIME] FBI API error: {e}")
        return None

    return results if results else None


def compute_intensity(crime_count: int) -> float:
    """Compute intensity score: 1 - e^(-total/40)."""
    return 1 - math.exp(-crime_count / 40)


def _distribute_to_neighborhoods(total_count: int) -> list[tuple[dict, int]]:
    """Distribute an aggregate offense count across STL neighborhoods
    proportionally to each neighborhood's weight."""
    total_weight = sum(n["weight"] for n in STL_NEIGHBORHOODS)
    distributed = []
    for nbhd in STL_NEIGHBORHOODS:
        share = int(round(total_count * nbhd["weight"] / total_weight))
        if share > 0:
            distributed.append((nbhd, share))
    return distributed


async def process_crime_data():
    """Process crime data through the pipeline."""
    db = DBWriter()
    criticality = CriticalityAgent()

    print("[STL_CRIME] Fetching crime data from FBI CDE API...")
    fbi_data = await fetch_fbi_crime()

    if fbi_data:
        for offense, monthly_counts in fbi_data.items():
            label = OFFENSE_LABELS.get(offense, offense)
            category = OFFENSE_TO_CATEGORY.get(offense, "crime")
            annual_total = sum(monthly_counts.values())

            for nbhd, count in _distribute_to_neighborhoods(annual_total):
                summary = (
                    f"{count} {label} incidents reported in "
                    f"{nbhd['name']}, St. Louis (FBI UCR, last 12 months)"
                )

                result = await criticality.classify_post(summary)
                intensity = compute_intensity(count)
                risk = 0.65 * result["final_severity"] + 0.35 * intensity

                await db.update_truth(
                    nbhd["lat"], nbhd["lng"], category, risk
                )

                await db.insert_post(
                    lat=nbhd["lat"], lng=nbhd["lng"],
                    content=summary,
                    severity=risk,
                    category=category,
                    human=False,
                )

                print(
                    f"  [{nbhd['name']}] {label}: "
                    f"count={count}, risk={risk:.2f}"
                )
    else:
        print("[STL_CRIME] FBI API unavailable — using sample crime data...")
        for crime in SAMPLE_CRIME_DATA:
            summary = (
                f"{crime['count']} {crime['category']} incidents "
                f"reported in {crime['area']}, St. Louis"
            )

            result = await criticality.classify_post(summary)
            intensity = compute_intensity(crime["count"])
            risk = 0.65 * result["final_severity"] + 0.35 * intensity

            await db.update_truth(
                crime["lat"], crime["lng"], result["category"], risk
            )

            await db.insert_post(
                lat=crime["lat"], lng=crime["lng"],
                content=summary,
                severity=risk,
                category=result["category"],
                human=False,
            )

            print(f"  [{crime['area']}] {crime['category']}: risk={risk:.2f}")

    print("[STL_CRIME] Crime data processing complete.")


if __name__ == "__main__":
    asyncio.run(process_crime_data())
