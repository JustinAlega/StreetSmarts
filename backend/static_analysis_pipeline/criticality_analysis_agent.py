"""
Criticality Analysis Agent (Static Pipeline version).
Simplified Gemini-based classifier for human post classification.
"""

import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

_client = None

def get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _client


async def classify_content(content: str, context: str = "") -> dict:
    """Classify content for severity and category using Gemini.
    
    Args:
        content: The text content to classify
        context: Optional additional context (e.g., location info)
    
    Returns:
        dict with final_severity (0-1) and category
    """
    prompt = f"""You are a safety incident classifier for Saint Louis, MO.
Analyze this content and classify it.

Content: "{content}"
{f'Context: {context}' if context else ''}

Severity scale:
- 0.0-0.2: Minor / informational
- 0.2-0.4: Low concern
- 0.4-0.6: Moderate concern
- 0.6-0.8: Significant safety issue
- 0.8-1.0: Critical / emergency

Return JSON with:
- "final_severity": float 0.0-1.0
- "category": one of ["crime", "public_safety", "transport", "infrastructure", "policy", "protest", "weather", "other"]

Return ONLY valid JSON."""

    try:
        response = get_client().models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
            )
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
        print(f"[CRITICALITY_STATIC] Error: {e}")
        return {"final_severity": 0.3, "category": "other"}
