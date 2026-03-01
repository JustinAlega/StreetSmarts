import os
import asyncio
from playwright.async_api import async_playwright
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

# Vultr AI Client
_vultr_client = AsyncOpenAI(
    api_key=os.getenv("VULTR_API_KEY"),
    base_url=os.getenv("VULTR_BASE_URL")
)

class VultrScraper:
    """Uses local Playwright + Vultr AI (No Browserbase needed)."""
    
    def __init__(self, model_name="meta-llama-3-1-8b-instruct"):
        self.model = model_name
        self.config = {
            "max_items_per_query": 3,
            "dom_settle_seconds": 6,
        }

    def tune(self, **kwargs):
        """Update scraper configuration."""
        self.config.update(kwargs)

    async def scrape_and_analyze(self, query: str):
        search_url = f"https://www.bing.com/news/search?q={query.replace(' ', '+')}"
        
        async with async_playwright() as p:
            # 1. Launch a local headless browser on Vultr
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # 2. Go to the news site
            print(f"[VULTR-SCRAPER] Navigating to {search_url}")
            await page.goto(search_url, wait_until="networkidle")
            
            # 3. Grab the page content (just the text to save tokens)
            content = await page.content()
            
            # 4. Use Vultr AI to extract the safety data
            analysis = await self._ai_extract(content)
            
            await browser.close()
            return analysis

    async def _ai_extract(self, raw_html: str):
        """Feeding the raw HTML text into your local Llama 3 for cleaning."""
        try:
            response = await _vultr_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a data extractor. Extract St. Louis safety news into JSON."},
                    {"role": "user", "content": f"Find up to {self.config['max_items_per_query']} news articles in this HTML and return a JSON list of: title, url, and snippet. HTML: {raw_html[:8000]}"}
                ],
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"AI Extraction Error: {e}")
            return "[]"