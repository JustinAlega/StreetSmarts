"""
SLMPD NIBRS CSV parser — convert crime data to truth table entries.
Owner: Person 2 (Backend Data + AI)

Run standalone:  python -m data.parse_slmpd path/to/nibrs.csv

This is a POST-MVP task. Focus on seed_truth.py first.
"""

import csv
from typing import Optional

from db.db_writer import DBWriter


# Mapping from NIBRS offense types to our category system
OFFENSE_TO_CATEGORY = {
    # TODO: map actual NIBRS codes/descriptions to our categories
    # Examples:
    # "ROBBERY":          "violent_crime",
    # "BURGLARY":         "property_crime",
    # "ASSAULT":          "violent_crime",
    # "LARCENY":          "property_crime",
    # "MOTOR VEHICLE THEFT": "property_crime",
}


def parse_csv(filepath: str) -> list[dict]:
    """Read an SLMPD NIBRS CSV and return list of incident dicts.

    TODO:
    1. Open CSV with csv.DictReader
    2. Extract: offense_type, date, address, district, neighborhood
    3. Return list of dicts
    """
    # STUB
    return []


def geocode_address(address: str) -> Optional[tuple[float, float]]:
    """Convert a St. Louis address to (lat, lng).

    TODO: Use Mapbox Geocoding API (free tier) or a local geocoder
    """
    # STUB
    return None


def ingest(filepath: str) -> None:
    """Parse CSV, geocode, and insert into truth table.

    TODO:
    1. Call parse_csv(filepath)
    2. For each incident, geocode the address
    3. Map offense_type → category via OFFENSE_TO_CATEGORY
    4. Call DBWriter.upsert_truth(lat, lng, category, severity)
    """
    # STUB
    incidents = parse_csv(filepath)
    print(f"Parsed {len(incidents)} incidents — geocoding not yet implemented.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m data.parse_slmpd <path_to_csv>")
    else:
        ingest(sys.argv[1])
