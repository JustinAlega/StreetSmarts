"""
Gemini post classifier — severity + category.
Owner: Person 2 (Backend Data + AI)

Uses Google Gemini (gemini-2.0-flash) to classify community safety reports.
"""

import json
import os

# TODO: uncomment when ready to use
# import google.generativeai as genai
# genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
# model = genai.GenerativeModel("gemini-2.0-flash")

# Valid categories (must match truth table columns)
VALID_CATEGORIES = [
    "crime", "public_safety", "transport", "infrastructure",
    "violent_crime", "property_crime", "weather", "other",
]


def classify_post(content: str) -> dict:
    """Send a community report to Gemini and get severity + category.

    Args:
        content: The user-submitted safety report text.

    Returns:
        {"severity": float 0.0-1.0, "category": str}

    TODO:
    1. Build prompt asking Gemini to classify the report
    2. Parse JSON from response
    3. Validate category is in VALID_CATEGORIES (fallback to "other")
    4. Clamp severity to [0.0, 1.0]
    """
    # STUB — returns neutral classification
    return {
        "severity": 0.5,
        "category": "other",
    }
