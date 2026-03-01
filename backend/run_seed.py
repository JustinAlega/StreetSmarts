"""
Seed script — generates synthetic data and processes crime data for StreetSmarts.
Run this once before starting the server.
"""

import asyncio
from data_gen import generate_data


async def main():
    print("=" * 60)
    print("StreetSmarts — Data Seeding for Saint Louis, MO")
    print("=" * 60)
    
    # Phase 1: Generate synthetic Gaussian risk field
    print("\n[PHASE 1] Generating synthetic risk landscape...")
    await generate_data()
    
    print("\n" + "=" * 60)
    print("Seeding complete! You can now start the server:")
    print("  uvicorn main:app --reload --port 8000")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())