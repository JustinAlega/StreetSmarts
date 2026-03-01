"""
Scraper Agent for StreetSmarts.
Uses Browserbase or Bing RSS to scrape live news.
"""

import os
import time
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

BROWSERBASE_API_KEY = os.getenv("BROWSERBASE_API_KEY")
BROWSERBASE_PROJECT_ID = os.getenv("BROWSERBASE_PROJECT_ID")
BB_BASE = "https://www.browserbase.com/v1"


class ScraperAgent:
    """AI-powered web scraper using Browserbase. One session created at startup, reused for all queries, closed on shutdown."""

    def __init__(self):
        self.config = {
            "max_items_per_query": 3,
            "dom_settle_seconds": 6,
        }
        self._session_id: str | None = None
        print("[SCRAPER] Mode: Browserbase (single session, reused)")

    def tune(self, **kwargs):
        """Update scraper configuration."""
        self.config.update(kwargs)

    async def ensure_browserbase_session(self) -> bool:
        """Get or create a Browserbase session. First checks for active RUNNING sessions, otherwise creates one."""
        if self._session_id:
            return True
        if not BROWSERBASE_API_KEY or not BROWSERBASE_PROJECT_ID:
            return False
        try:
            async with aiohttp.ClientSession() as http:
                # Check for existing active session (handles orphans from prior runs)
                list_resp = await http.get(
                    f"{BB_BASE}/sessions",
                    headers={"x-bb-api-key": BROWSERBASE_API_KEY},
                    params={"status": "RUNNING"},
                )
                if list_resp.status == 200:
                    sessions = await list_resp.json()
                    for s in sessions:
                        if s.get("projectId") == BROWSERBASE_PROJECT_ID:
                            self._session_id = s.get("id")
                            if self._session_id:
                                print(f"[SCRAPER] Reusing active Browserbase session: {self._session_id[:8]}...")
                                return True

                # No active session, create one
                create_resp = await http.post(
                    f"{BB_BASE}/sessions",
                    headers={"x-bb-api-key": BROWSERBASE_API_KEY, "Content-Type": "application/json"},
                    json={"projectId": BROWSERBASE_PROJECT_ID},
                )
                if create_resp.status in (200, 201):
                    data = await create_resp.json()
                    self._session_id = data.get("id")
                    if self._session_id:
                        print(f"[SCRAPER] Browserbase session created: {self._session_id[:8]}...")
                        return True
                else:
                    body = await create_resp.text()
                    print(f"[SCRAPER] Browserbase create failed: {create_resp.status} | {body[:200]}")
        except Exception as e:
            print(f"[SCRAPER] Browserbase error: {e}")
        return False

    async def close_browserbase_session(self) -> None:
        """End the Browserbase session on shutdown. Safe to call if no session."""
        if not self._session_id:
            return
        try:
            async with aiohttp.ClientSession() as http:
                resp = await http.post(
                    f"{BB_BASE}/sessions/{self._session_id}/end",
                    headers={"x-bb-api-key": BROWSERBASE_API_KEY, "Content-Type": "application/json"},
                )
                if resp.status in (200, 204):
                    print(f"[SCRAPER] Browserbase session closed: {self._session_id[:8]}...")
                else:
                    print(f"[SCRAPER] Browserbase end session: {resp.status}")
        except Exception as e:
            print(f"[SCRAPER] Browserbase close error: {e}")
        self._session_id = None

    async def scrape_news(self, query: str) -> list:
        """Scrape Bing News for articles. Reuses the single Browserbase session; falls back to RSS on failure."""
        has_session = await self.ensure_browserbase_session()
        if not has_session:
            return await self._fallback_scrape(query)

        try:
            search_url = f"https://www.bing.com/news/search?q={query.replace(' ', '+')}"
            async with aiohttp.ClientSession() as http:
                # Navigate in existing session
                nav_resp = await http.post(
                    f"{BB_BASE}/sessions/{self._session_id}/navigate",
                    headers={"x-bb-api-key": BROWSERBASE_API_KEY, "Content-Type": "application/json"},
                    json={"url": search_url},
                )
                if nav_resp.status != 200:
                    print(f"[SCRAPER] Browserbase navigate failed: {nav_resp.status} (session may be stale)")
                    return await self._fallback_scrape(query)

                # Extract content
                extract_resp = await http.post(
                    f"{BB_BASE}/sessions/{self._session_id}/extract",
                    headers={"x-bb-api-key": BROWSERBASE_API_KEY, "Content-Type": "application/json"},
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
                                            "snippet": {"type": "string"},
                                        },
                                    },
                                }
                            },
                        }
                    },
                )

                if extract_resp.status == 200:
                    data = await extract_resp.json()
                    articles = data.get("articles", [])[: self.config["max_items_per_query"]]
                    if articles:
                        print(f"[SCRAPER] Browserbase: query=\"{query}\" → {len(articles)} articles")
                        for i, a in enumerate(articles):
                            title = (a.get("title") or "")[:60]
                            url = (a.get("url") or "")[:60]
                            print(f"  [{i+1}] {title} | {url}")
                        return articles
                print(f"[SCRAPER] Browserbase extract failed: {extract_resp.status}")
        except Exception as e:
            print(f"[SCRAPER] Error: {e}")
        return await self._fallback_scrape(query)
    
    async def _fallback_scrape(self, query: str) -> list:
        """Fallback: use simple HTTP request to get Bing News RSS."""
        import re
        try:
            search_url = f"https://www.bing.com/news/search?q={query.replace(' ', '+')}&format=rss"
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers={
                    "User-Agent": "Mozilla/5.0 (compatible)"
                }) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        articles = []
                        items = re.findall(r'<item>(.*?)</item>', text, re.DOTALL)
                        for item in items[:self.config["max_items_per_query"]]:
                            title_match = re.search(r'<title>(.*?)</title>', item)
                            link_match = re.search(r'<link>(.*?)</link>', item)
                            desc_match = re.search(r'<description>(.*?)</description>', item)
                            if title_match:
                                title = re.sub(r'<[^>]+>', '', title_match.group(1))[:80]
                                url = link_match.group(1).strip() if link_match else ""
                                snippet = (desc_match.group(1) if desc_match else "")[:120]
                                articles.append({
                                    "title": title,
                                    "url": url,
                                    "publisher": "Bing News",
                                    "snippet": re.sub(r'<[^>]+>', '', snippet) if snippet else ""
                                })
                        if articles:
                            print(f"[SCRAPER] Bing RSS: query=\"{query}\" → {len(articles)} articles")
                            for i, a in enumerate(articles):
                                print(f"  [{i+1}] {a['title']} | {a['url'][:60]}...")
                        else:
                            print(f"[SCRAPER] Bing RSS: query=\"{query}\" → 0 articles (no items)")
                        return articles
                    else:
                        print(f"[SCRAPER] Bing RSS: query=\"{query}\" → HTTP {resp.status}")
        except Exception as e:
            print(f"[SCRAPER] Bing RSS error: {e}")
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
