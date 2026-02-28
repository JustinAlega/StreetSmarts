"""
Scraper Agent for StreetSmarts.
Uses Stagehand with Browserbase and Gemini to scrape live news from Bing.
"""

import os
import json
import aiohttp
from dotenv import load_dotenv

load_dotenv()

BROWSERBASE_API_KEY = os.getenv("BROWSERBASE_API_KEY")
BROWSERBASE_PROJECT_ID = os.getenv("BROWSERBASE_PROJECT_ID")


class ScraperAgent:
    """AI-powered web scraper using Browserbase + Stagehand."""
    
    def __init__(self):
        self.config = {
            "max_items_per_query": 3,
            "dom_settle_seconds": 6,
        }
    
    def tune(self, **kwargs):
        """Update scraper configuration."""
        self.config.update(kwargs)
    
    async def scrape_news(self, query: str) -> list:
        """Scrape Bing News for articles matching the query.
        
        Uses Browserbase API to create a browser session and extract
        structured article data from the rendered page.
        """
        try:
            # Create a Browserbase session
            async with aiohttp.ClientSession() as session:
                # Create browser session
                create_resp = await session.post(
                    "https://www.browserbase.com/v1/sessions",
                    headers={
                        "x-bb-api-key": BROWSERBASE_API_KEY,
                        "Content-Type": "application/json"
                    },
                    json={
                        "projectId": BROWSERBASE_PROJECT_ID,
                    }
                )
                
                if create_resp.status != 200:
                    print(f"[SCRAPER] Failed to create session: {create_resp.status}")
                    return await self._fallback_scrape(query)
                
                session_data = await create_resp.json()
                session_id = session_data.get("id")
                
                if not session_id:
                    return await self._fallback_scrape(query)
                
                # Navigate to Bing News
                search_url = f"https://www.bing.com/news/search?q={query.replace(' ', '+')}"
                
                # Use the debug URL for Stagehand-like extraction
                navigate_resp = await session.post(
                    f"https://www.browserbase.com/v1/sessions/{session_id}/navigate",
                    headers={
                        "x-bb-api-key": BROWSERBASE_API_KEY,
                        "Content-Type": "application/json"
                    },
                    json={"url": search_url}
                )
                
                # Extract content
                extract_resp = await session.post(
                    f"https://www.browserbase.com/v1/sessions/{session_id}/extract",
                    headers={
                        "x-bb-api-key": BROWSERBASE_API_KEY,
                        "Content-Type": "application/json"
                    },
                    json={
                        "schema": {
                            "type": "object",
                            "properties": {
                                "articles": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "title": {"type": "string"},
                                            "url": {"type": "string"},
                                            "publisher": {"type": "string"},
                                            "snippet": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                )
                
                if extract_resp.status == 200:
                    data = await extract_resp.json()
                    articles = data.get("articles", [])
                    return articles[:self.config["max_items_per_query"]]
                
                return await self._fallback_scrape(query)
                
        except Exception as e:
            print(f"[SCRAPER] Error: {e}")
            return await self._fallback_scrape(query)
    
    async def _fallback_scrape(self, query: str) -> list:
        """Fallback: use simple HTTP request to get Bing News results."""
        try:
            search_url = f"https://www.bing.com/news/search?q={query.replace(' ', '+')}&format=rss"
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers={
                    "User-Agent": "Mozilla/5.0 (compatible)"
                }) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        # Parse RSS items (basic XML parsing)
                        articles = []
                        import re
                        items = re.findall(r'<item>(.*?)</item>', text, re.DOTALL)
                        for item in items[:self.config["max_items_per_query"]]:
                            title_match = re.search(r'<title>(.*?)</title>', item)
                            link_match = re.search(r'<link>(.*?)</link>', item)
                            desc_match = re.search(r'<description>(.*?)</description>', item)
                            
                            if title_match:
                                articles.append({
                                    "title": title_match.group(1),
                                    "url": link_match.group(1) if link_match else "",
                                    "publisher": "Bing News",
                                    "snippet": desc_match.group(1) if desc_match else ""
                                })
                        return articles
        except Exception as e:
            print(f"[SCRAPER] Fallback error: {e}")
        
        return []
    
    async def open_and_capture(self, url: str) -> str:
        """Open a URL and capture the full article content."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (compatible)"
                }) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        # Strip HTML tags for content
                        import re
                        clean = re.sub(r'<[^>]+>', ' ', text)
                        clean = re.sub(r'\s+', ' ', clean)
                        return clean[:2000]  # Limit content length
        except Exception as e:
            print(f"[SCRAPER] Capture error: {e}")
        return ""
