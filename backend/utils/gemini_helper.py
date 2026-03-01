"""
Shared Gemini client with 429 retry + model fallback.
"""

import re
import asyncio
from google.genai import types

GEMINI_MODELS = ["gemini-2.5-flash", "gemini-2.5-flash-lite"]
RETRY_EXTRA_SECONDS = 10


def _parse_retry_delay(exc: Exception) -> float:
    """Extract retry delay in seconds from 429 error message."""
    s = str(exc)
    m = re.search(r"retry in (\d+\.?\d*)s", s, re.I) or re.search(r"retryDelay['\":]\s*['\"]?(\d+)", s, re.I)
    if m:
        return float(m.group(1))
    return 60.0


async def generate_with_retry(client, prompt, config=None, models=None):
    """
    Call Gemini with retry on 429 and model fallback.
    Returns the response object.
    """
    models = models or GEMINI_MODELS
    last_exc = None

    for model in models:
        try:
            kwargs = {"model": model, "contents": prompt}
            if config is not None:
                kwargs["config"] = config
            else:
                kwargs["config"] = types.GenerateContentConfig(temperature=0.2)
            resp = client.models.generate_content(**kwargs)
            return resp
        except Exception as e:
            last_exc = e
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                delay = _parse_retry_delay(e) + RETRY_EXTRA_SECONDS
                print(f"[GEMINI] 429 on {model}, sleeping {delay:.0f}s then trying next model...")
                await asyncio.sleep(delay)
                continue
            raise

    raise last_exc
