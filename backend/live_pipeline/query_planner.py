from .locations import MONITORED_LOCATIONS

# Broad, high-impact safety keywords
KEYWORDS = [
    ("crime", "crime"),
    ("safety", "public_safety"),
    ("police", "public_safety"),
    ("incident", "other"),
    ("shooting", "crime"),
    ("emergency", "public_safety"),
    ("robbery", "crime"),
]

# City-wide broad queries for maximum data yield
BROAD_CITY_QUERIES = [
    ("St Louis crime report today", "crime", 38.6270, -90.1994),
    ("Saint Louis safety news daily", "public_safety", 38.6270, -90.1994),
    ("St Louis police blotter", "public_safety", 38.6270, -90.1994),
    ("St Louis emergency services updates", "public_safety", 38.6270, -90.1994),
    ("St Louis breaking news local safety", "other", 38.6270, -90.1994),
]

def generate_queries():
    """
    Broad Query Planner for StreetSmarts.
    Combines core locations with high-yield city-wide safety searches.
    """
    queries = []
    
    # 1. Add city-wide general queries
    for q, cat, lat, lng in BROAD_CITY_QUERIES:
        queries.append({
            "query": q,
            "category": cat,
            "lat": lat,
            "lng": lng,
            "location_name": "St Louis"
        })
    
    # 2. Add location-specific broad searches
    for loc in MONITORED_LOCATIONS:
        # Base query for the area
        queries.append({
            "query": f"{loc['name']} St Louis safety",
            "category": "public_safety",
            "lat": loc["lat"],
            "lng": loc["lng"],
            "location_name": loc["name"]
        })
        
        # Keyword coverage
        for keyword, category in KEYWORDS:
            queries.append({
                "query": f"{loc['name']} St Louis {keyword}",
                "category": category,
                "lat": loc["lat"],
                "lng": loc["lng"],
                "location_name": loc["name"]
            })
    
    return queries
