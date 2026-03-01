"""
Validator Agent for StreetSmarts.
Uses Gemini to validate scraped news for plausibility and severity hints.
Replaces Perplexity Sonar from the original system.
"""

import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

_client = None

def get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _client


class ValidatorAgent:
    """Validates scraped news items using Gemini for plausibility assessment."""
    
    async def validate(self, article: dict) -> dict:
        """Validate a scraped article for plausibility and severity.
        
        Returns:
            dict with: cleaned_content, summary, plausibility (0-1),
                      severity_hint (0-1), flags, evidence
        """
        prompt = f"""You are a news validation agent for Saint Louis, MO safety intelligence.
Analyze this news article and assess its credibility and relevance.

Title: {article.get('title', 'N/A')}
URL: {article.get('url', 'N/A')}
Publisher: {article.get('publisher', 'N/A')}
Snippet: {article.get('snippet', 'N/A')}

Return a JSON object with these fields:
- "cleaned_content": string - a normalized, factual description of the event
- "summary": string - concise 1-2 sentence summary
- "plausibility": float 0.0-1.0 - based on source credibility, corroboration, and tone
  (established news outlets get 0.7+, anonymous/sensational sources get lower)
- "severity_hint": float 0.0-1.0 - estimated impact if the report is true
- "flags": list of strings - any concerns like "sensational_language", "unverified_source", "outdated", "satire"
- "evidence": list of strings - any supporting evidence or corroborating details

Be critical but fair. Local news from KMOX, KSDK, STL Today, FOX2, KMOV are credible St. Louis sources.
Categorize findings into: ["crime", "public_safety", "transport", "infrastructure", "protest", "other"].

Return ONLY valid JSON, no markdown fences, no explanation."""

        try:
            response = get_client().models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                text = text.rsplit("```", 1)[0]
            
            result = json.loads(text)
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
            print(f"[VALIDATOR] Error validating article: {e}")
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
