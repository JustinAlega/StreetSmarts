"""
Criticality Agent for StreetSmarts.
Uses Gemini for final classification: severity, category, and tweet generation.
Replaces Anthropic Claude from the original system.
"""

import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

from utils.gemini_helper import generate_with_retry

load_dotenv()

_client = None

def get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _client


class CriticalityAgent:
    """Final AI classification layer using Gemini."""
    
    async def assess(self, validated_item: dict) -> dict:
        """Assess validated content for final severity, category, and tweet.
        
        Returns:
            dict with: final_severity (0-1), category, tweet (≤280 chars)
        """
        plausibility = validated_item.get("plausibility", 0.5)
        
        prompt = f"""You are a criticality assessment agent for Saint Louis, MO safety intelligence.

Analyze this validated report and provide a final assessment.

Content: {validated_item.get('cleaned_content', '')}
Summary: {validated_item.get('summary', '')}
Plausibility: {plausibility}
Flags: {validated_item.get('flags', [])}

Return a JSON object with:
- "final_severity": float 0.0-1.0, your final assessment of how severe this is
  (consider both the event severity and plausibility)
- "category": one of ["crime", "public_safety", "transport", "infrastructure", "policy", "protest", "weather", "other"]
- "tweet": a ≤280-character neutral, factual summary suitable for a public safety feed

Tweet rules:
- If plausibility < 0.5, start with "Unverified reports:"
- No emojis
- Maximum 1 hashtag (use #STL or neighborhood-specific)
- No speculation, stick to facts
- Be concise and informative

Return ONLY valid JSON, no markdown, no explanation."""

        try:
            response = await generate_with_retry(
                get_client(), prompt,
                config=types.GenerateContentConfig(temperature=0.2),
            )
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                text = text.rsplit("```", 1)[0]

            result = json.loads(text)
            tweet = result.get("tweet", "")[:280]
            
            return {
                "final_severity": float(result.get("final_severity", 0.3)),
                "category": result.get("category", "other"),
                "tweet": tweet
            }
        except Exception as e:
            print(f"[CRITICALITY] Error: {e}")
            return {
                "final_severity": 0.3,
                "category": "other",
                "tweet": f"Safety update for St. Louis area. #STL"
            }
    
    async def assess_batch(self, validated_items: list) -> list:
        """Assess all validated items in ONE Gemini call. Returns [((lat,lng,category), result), ...]"""
        if not validated_items:
            return []
        if len(validated_items) == 1:
            v = validated_items[0]
            orig = v.get("original", {})
            r = await self.assess(v)
            return [((orig.get("lat", 0), orig.get("lng", 0), orig.get("search_category", "other")), r)]

        items = []
        for i, v in enumerate(validated_items):
            orig = v.get("original", {})
            items.append({
                "id": i,
                "content": (v.get("cleaned_content", "") or "")[:400],
                "summary": (v.get("summary", "") or "")[:200],
                "plausibility": v.get("plausibility", 0.5),
                "flags": v.get("flags", []),
                "_lat": orig.get("lat", 0),
                "_lng": orig.get("lng", 0),
                "_cat": orig.get("search_category", "other"),
            })

        prompt = f"""Assess these {len(validated_items)} validated reports for Saint Louis. Return a JSON array of {len(validated_items)} objects, same order by id.
Each: "id": int, "final_severity": float 0-1, "category": one of ["crime","public_safety","transport","infrastructure","policy","protest","weather","other"], "tweet": string ≤280 chars.
Input: {json.dumps([{k: v for k, v in x.items() if not k.startswith("_")} for x in items], indent=2)}
Return ONLY a valid JSON array."""

        try:
            response = await generate_with_retry(
                get_client(), prompt,
                config=types.GenerateContentConfig(temperature=0.2),
            )
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0]
            arr = json.loads(text)
            by_id = {r["id"]: r for r in arr}
            out = []
            for i, v in enumerate(validated_items):
                orig = v.get("original", {})
                r = by_id.get(i, {})
                out.append((
                    (orig.get("lat", 0), orig.get("lng", 0), orig.get("search_category", "other")),
                    {"final_severity": float(r.get("final_severity", 0.3)), "category": r.get("category", "other"), "tweet": (r.get("tweet", "") or "Safety update for St. Louis. #STL")[:280]}
                ))
            return out
        except Exception as e:
            print(f"[CRITICALITY] Batch error: {e}")
            return [((v.get("original", {}).get("lat", 0), v.get("original", {}).get("lng", 0), v.get("original", {}).get("search_category", "other")), {"final_severity": 0.3, "category": "other", "tweet": "Safety update for St. Louis. #STL"}) for v in validated_items]

    async def classify_post(self, content: str) -> dict:
        """Simplified classification for human community posts."""
        prompt = f"""Classify this safety report for Saint Louis, MO.

Report: "{content}"

Return JSON with:
- "final_severity": float 0.0-1.0
- "category": one of ["crime", "public_safety", "transport", "infrastructure", "policy", "protest", "weather", "other"]

Return ONLY valid JSON."""

        try:
            response = await generate_with_retry(
                get_client(), prompt,
                config=types.GenerateContentConfig(temperature=0.2),
            )
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                text = text.rsplit("```", 1)[0]

            result = json.loads(text)
            return {
                "final_severity": float(result.get("final_severity", 0.3)),
                "category": result.get("category", "other")
            }
        except Exception as e:
            print(f"[CRITICALITY] Post classification error: {e}")
            return {"final_severity": 0.3, "category": "other"}
