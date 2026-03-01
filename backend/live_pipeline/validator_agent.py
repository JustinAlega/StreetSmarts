import os
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize the Vultr-hosted client
_client = AsyncOpenAI(
    api_key=os.getenv("VULTR_API_KEY"),
    base_url=os.getenv("VULTR_BASE_URL")
)

class ValidatorAgent:
    """Validates scraped news items using Vultr-hosted Llama 3 for plausibility assessment."""
    
    def __init__(self, model_name="gpt-oss-120b"):
        self.model = model_name

    async def validate(self, article: dict) -> dict:
        """Validate a scraped article for plausibility and severity."""
        prompt = f"""You are a news validation agent for Saint Louis, MO safety intelligence.
Analyze this news article and assess its credibility and relevance.

Title: {article.get('title', 'N/A')}
URL: {article.get('url', 'N/A')}
Publisher: {article.get('publisher', 'N/A')}
Snippet: {article.get('snippet', 'N/A')}

Return a JSON object with:
- "cleaned_content": a normalized, factual description
- "summary": concise 1-2 sentence summary
- "plausibility": float 0.0-1.0 (Local STL news from KSDK, KMOV, KSDK, STL Today, FOX2 gets 0.8+)
- "severity_hint": float 0.0-1.0
- "flags": list of concerns
- "evidence": list of supporting details

Return ONLY valid JSON."""

        try:
            response = await _client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return {
                "cleaned_content": result.get("cleaned_content", article.get("snippet", "")),
                "summary": result.get("summary", ""),
                "plausibility": float(result.get("plausibility", 0.5)),
                "severity_hint": float(result.get("severity_hint", 0.3)),
                "flags": result.get("flags", []),
                "evidence": result.get("evidence", []),
                "original": article
            }
        except Exception as e:
            print(f"[VULTR-VALIDATOR] Error: {e}")
            return {
                "cleaned_content": article.get("snippet", ""),
                "summary": article.get("title", ""),
                "plausibility": 0.4,
                "severity_hint": 0.3,
                "flags": ["validation_error"],
                "evidence": [],
                "original": article
            }
    
    async def validate_batch(self, articles: list) -> list:
        """Validate a batch of articles."""
        results = []
        for article in articles:
            result = await self.validate(article)
            results.append(result)
        return results
