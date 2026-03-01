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
import json
from .scraper_agent import VultrScraper
from .validator_agent import ValidatorAgent
from .criticality_agent import CriticalityAgent
from .observer_agent import ObserverAgent
from .query_planner import generate_queries
from db.db_writer import DBWriter

CYCLE_DELAY_SECONDS = 20


async def run_pipeline():
    """Main pipeline loop."""
    scraper = VultrScraper()
    validator = ValidatorAgent()
    criticality = CriticalityAgent()
    observer = ObserverAgent()
    db = DBWriter()
    
    # Configure scraper for high density
    scraper.tune(max_items_per_query=12)
    
    print("[PIPELINE] Starting StreetSmarts live pipeline for Saint Louis...")
    
    seen_urls = set()
    cycle = 0
    
    while True:
        cycle += 1
        print(f"\n[PIPELINE] === Cycle {cycle} ===")
        
        queries = generate_queries()
        total_written = 0
        total_scraped = 0
        total_validated = 0
        
        for job in queries:
            query = job["query"]
            lat = job["lat"]
            lng = job["lng"]
            category = job["category"]
            
            print(f"[PIPELINE] Scraping: {query}")
            
            # 1. Scrape (Local Playwright + Vultr AI Extraction)
            raw_analysis = await scraper.scrape_and_analyze(query)
            
            try:
                # Vultr returns a JSON string, we need to parse it
                data = json.loads(raw_analysis)
                articles = data.get("articles", [])
            except Exception as e:
                print(f"[PIPELINE] JSON Parse Error: {e}")
                continue
                
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
            
            # 3. Validate
            validated = await validator.validate_batch(articles)
            
            # 4. Filter
            filtered = observer.filter_validated(validated)
            total_validated += len(filtered)
            
            # 5. Assess and write
            for item in filtered:
                result = await criticality.assess(item)
                
                # Update truth table
                await db.update_truth(
                    lat=lat, lng=lng,
                    category=result["category"],
                    severity=result["final_severity"]
                )
                
                # Gate: only write significant posts
                if observer.should_write_post(result):
                    await db.insert_post(
                        lat=lat, lng=lng,
                        content=result["tweet"],
                        severity=result["final_severity"],
                        category=result["category"],
                        human=False
                    )
                    total_written += 1
                    print(f"  [POST] severity={result['final_severity']:.2f} "
                          f"cat={result['category']}: {result['tweet'][:80]}...")
        
        print(f"[PIPELINE] Cycle {cycle} complete: "
              f"scraped={total_scraped}, validated={total_validated}, written={total_written}")
        
        # 6. Rate limiting
        print(f"[PIPELINE] Sleeping {CYCLE_DELAY_SECONDS}s...")
        await asyncio.sleep(CYCLE_DELAY_SECONDS)


if __name__ == "__main__":
    asyncio.run(run_pipeline())
