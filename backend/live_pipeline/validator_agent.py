"""
Validator Agent for StreetSmarts.
Uses Gemini to validate scraped news for plausibility and severity hints.
Replaces Perplexity Sonar from the original system.
"""

import os
import json
from google import genai
from dotenv import load_dotenv

from utils.gemini_helper import generate_with_retry

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

Return ONLY valid JSON, no markdown fences, no explanation."""

        try:
            response = await generate_with_retry(get_client(), prompt)
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
        """Validate all articles in ONE Gemini call."""
        if not articles:
            return []
        if len(articles) == 1:
            return [await self.validate(articles[0])]

        items = [{"i": i, "title": a.get("title", "N/A"), "url": a.get("url", "N/A"), "publisher": a.get("publisher", "N/A"), "snippet": (a.get("snippet", "N/A") or "")[:500]} for i, a in enumerate(articles)]
        prompt = f"""Validate these {len(articles)} news items for Saint Louis safety intelligence. Return a JSON array of {len(articles)} objects, same order by index i.
Each object: "i": int, "cleaned_content": string, "summary": string, "plausibility": float 0-1, "severity_hint": float 0-1, "flags": list of strings, "evidence": list of strings.
Input: {json.dumps(items, indent=2)}
Return ONLY a valid JSON array."""

        try:
            response = await generate_with_retry(get_client(), prompt)
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0]
            arr = json.loads(text)
            by_i = {r["i"]: r for r in arr}
            results = []
            for i, article in enumerate(articles):
                r = by_i.get(i, {})
                results.append({
                    "cleaned_content": r.get("cleaned_content", article.get("snippet", "")),
                    "summary": r.get("summary", ""),
                    "plausibility": float(r.get("plausibility", 0.5)),
                    "severity_hint": float(r.get("severity_hint", 0.3)),
                    "flags": r.get("flags", []),
                    "evidence": r.get("evidence", []),
                    "original": article,
                })
            return results
        except Exception as e:
            print(f"[VALIDATOR] Batch error: {e}")
            return [await self.validate(a) for a in articles]
