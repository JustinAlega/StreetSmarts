"""
Search query generator for the live pipeline.
Combines monitored locations with safety-related keywords for Saint Louis, MO.
"""

from .locations import MONITORED_LOCATIONS

# Saint Louis safety-related keywords
KEYWORDS = [
    ("crime", "crime"),
    ("police", "public_safety"),
    ("shooting", "crime"),
    ("robbery", "crime"),
    ("carjacking", "crime"),
    ("theft", "crime"),
    ("MetroLink", "transport"),
    ("accident", "public_safety"),
    ("fire", "public_safety"),
    ("protest", "protest"),
    ("closure", "infrastructure"),
    ("assault", "crime"),
]


def generate_queries(limit: int = None, offset: int = 0):
    """Generate search queries. Use limit/offset to run a subset per cycle."""
    queries = []
    
    for loc in MONITORED_LOCATIONS:
        # Base query - just the location
        queries.append({
            "query": f"{loc['name']} St Louis",
            "category": "other",
            "lat": loc["lat"],
            "lng": loc["lng"],
            "location_name": loc["name"]
        })
        
        # Keyword-augmented queries
        for keyword, category in KEYWORDS:
            queries.append({
                "query": f"{loc['name']} St Louis {keyword}",
                "category": category,
                "lat": loc["lat"],
                "lng": loc["lng"],
                "location_name": loc["name"]
            })
    
    if limit:
        n = len(queries)
        start = offset % n
        if start + limit <= n:
            return queries[start : start + limit]
        return queries[start:] + queries[: limit - (n - start)]
    return queries
