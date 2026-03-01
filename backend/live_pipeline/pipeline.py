"""
Main pipeline orchestration for StreetSmarts.
Ties all agents together in an async loop:
  1. Scrape Bing News via ScraperAgent
  2. Attach geo coordinates + deduplicate URLs
  3. Validate batch via ValidatorAgent (Gemini)
  4. Filter: keep only plausibility ≥ 0.5
  5. For each validated item:
     a. Assess via CriticalityAgent (Gemini) → severity + tweet
     b. Update truth table (EMA)
     c. If severity ≥ 0.6 → insert as post
  6. Sleep between cycles
"""

import asyncio
from .scraper_agent import ScraperAgent
from .validator_agent import ValidatorAgent
from .criticality_agent import CriticalityAgent
from .observer_agent import ObserverAgent
from .query_planner import generate_queries
from db.db_writer import DBWriter

import os
CYCLE_DELAY_SECONDS = int(os.getenv("PIPELINE_CYCLE_SECONDS", "300"))
QUERIES_PER_CYCLE = int(os.getenv("PIPELINE_QUERIES_PER_CYCLE", "4"))


async def run_pipeline():
    """Main pipeline loop."""
    scraper = ScraperAgent()
    validator = ValidatorAgent()
    criticality = CriticalityAgent()
    observer = ObserverAgent()
    db = DBWriter()
    
    # Configure scraper
    observer.tune_scraper(scraper)
    
    print("[PIPELINE] Starting StreetSmarts live pipeline for Saint Louis...")
    await scraper.ensure_browserbase_session()

    seen_urls = set()
    cycle = 0

    try:
        while True:
            cycle += 1
            print(f"\n[PIPELINE] === Cycle {cycle} (every {CYCLE_DELAY_SECONDS}s) ===")

            offset = (cycle - 1) * QUERIES_PER_CYCLE
            queries = generate_queries(limit=QUERIES_PER_CYCLE, offset=offset)
            total_written = 0
            total_scraped = 0
            total_validated = 0

            for job in queries:
                query = job["query"]
                lat = job["lat"]
                lng = job["lng"]
                category = job["category"]

                print(f"[PIPELINE] Scraping: {query}")

                # 1. Scrape
                articles = await scraper.scrape_news(query)
                if not articles:
                    continue

                # 2. Deduplicate
                articles = observer.deduplicate(articles, seen_urls)
                total_scraped += len(articles)

                if not articles:
                    continue

                # Attach coordinates
                for article in articles:
                    article["lat"] = lat
                    article["lng"] = lng
                    article["search_category"] = category

                # 3. Batch validate (1 Gemini call)
                validated = await validator.validate_batch(articles)
                filtered = observer.filter_validated(validated)
                total_validated += len(filtered)

                if not filtered:
                    continue

                # 4. Batch assess (1 Gemini call)
                results = await criticality.assess_batch(filtered)

                # 5. Write
                for (lat, lng, cat), result in results:
                    await db.update_truth(lat=lat, lng=lng, category=result["category"], severity=result["final_severity"])
                    if observer.should_write_post(result):
                        await db.insert_post(lat=lat, lng=lng, content=result["tweet"], severity=result["final_severity"], category=result["category"], human=False)
                        total_written += 1
                        print(f"  [POST] severity={result['final_severity']:.2f} cat={result['category']}: {result['tweet'][:60]}...")

            print(f"[PIPELINE] Cycle {cycle} complete: "
                  f"scraped={total_scraped}, validated={total_validated}, written={total_written}")

            # 6. Rate limiting
            print(f"[PIPELINE] Sleeping {CYCLE_DELAY_SECONDS}s...")
            await asyncio.sleep(CYCLE_DELAY_SECONDS)
    finally:
        await scraper.close_browserbase_session()
        print("[PIPELINE] Browserbase session closed.")


if __name__ == "__main__":
    asyncio.run(run_pipeline())
