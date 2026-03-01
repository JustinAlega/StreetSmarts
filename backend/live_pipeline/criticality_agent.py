import os
import json
import asyncio
from openai import AsyncOpenAI # Use OpenAI client for Vultr's vLLM
from dotenv import load_dotenv

load_dotenv()

# Initialize the Vultr-hosted client
# VULTR_BASE_URL should be something like http://your-vultr-ip:8000/v1
_client = AsyncOpenAI(
    api_key=os.getenv("VULTR_API_KEY"),
    base_url=os.getenv("VULTR_BASE_URL") 
)

class CriticalityAgent:
    """Final AI classification layer using Vultr-hosted Llama 3."""
    
    def __init__(self, model_name="meta-llama-3-1-8b-instruct"):
        self.model = model_name

    async def assess(self, validated_item: dict) -> dict:
        plausibility = validated_item.get("plausibility", 0.5)
        
        prompt = f"""You are a criticality assessment agent for Saint Louis, MO safety intelligence.
Analyze this report and return ONLY valid JSON.

Content: {validated_item.get('cleaned_content', '')}
Summary: {validated_item.get('summary', '')}
Plausibility: {plausibility}

Return JSON with:
- "final_severity": float 0.0-1.0
- "category": ["crime", "public_safety", "transport", "infrastructure", "protest", "other"]
- "tweet": factual summary ≤280 chars. (Rule: if plausibility < 0.5, start with "Unverified reports:")"""

        try:
            # Vultr/vLLM call
            response = await _client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                response_format={"type": "json_object"} # Supported by vLLM/Llama 3
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return {
                "final_severity": float(result.get("final_severity", 0.3)),
                "category": result.get("category", "other"),
                "tweet": result.get("tweet", "")[:280]
            }
        except Exception as e:
            print(f"[VULTR-CRITICALITY] Error: {e}")
            return {"final_severity": 0.3, "category": "other", "tweet": "Safety update for #STL"}

    async def classify_post(self, content: str) -> dict:
        """Simplified classification for community posts."""
        prompt = f"Classify this STL safety report into JSON: {content}"
        
        try:
            response = await _client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            result = json.loads(response.choices[0].message.content)
            return {
                "final_severity": float(result.get("final_severity", 0.3)),
                "category": result.get("category", "other")
            }
        except Exception as e:
            print(f"[VULTR-CRITICALITY] Post error: {e}")
            return {"final_severity": 0.3, "category": "other"}