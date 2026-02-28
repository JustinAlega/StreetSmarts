"""
Location summary endpoint for StreetSmarts.
Generates structured safety reports for any lat/lng coordinate.
"""

from fastapi import APIRouter
from db.db_writer import DBWriter, CATEGORIES

router = APIRouter()
db = DBWriter()


def risk_label(score):
    """Convert 0-100 risk score to label."""
    if score >= 70:
        return "High"
    elif score >= 40:
        return "Moderate"
    return "Low"


def risk_recommendation(score):
    """Generate text recommendation based on risk level."""
    if score >= 70:
        return "High risk detected nearby. Consider an alternative route or avoid the area if possible. Stay aware of your surroundings."
    elif score >= 40:
        return "Moderate risk in this area. Exercise normal caution and stay on well-lit, populated streets."
    return "This area appears relatively safe. Normal precautions recommended."


@router.get("/location-summary")
async def get_location_summary(lat: float, lng: float, radius_km: float = 1.0):
    """Get a comprehensive safety summary for a location."""
    
    # Fetch nearby posts
    posts = await db.get_feed(lat, lng, radius_km)
    
    # Compute per-category averages from posts
    cat_sums = {c: 0.0 for c in CATEGORIES}
    cat_counts = {c: 0 for c in CATEGORIES}
    
    for post in posts:
        cat = post.get("category", "other")
        sev = post.get("severity", 0.0)
        if cat in CATEGORIES:
            cat_sums[cat] += sev
            cat_counts[cat] += 1
    
    cat_averages = {}
    for c in CATEGORIES:
        if cat_counts[c] > 0:
            cat_averages[c] = round(cat_sums[c] / cat_counts[c], 3)
        else:
            cat_averages[c] = 0.0
    
    # Also get truth vector
    truth = await db.get_truth_nearest(lat, lng)
    truth_vec = {}
    if truth:
        truth_vec = {c: round(truth.get(c, 0.0), 3) for c in CATEGORIES}
        # Blend post averages with truth (60% truth, 40% posts)
        for c in CATEGORIES:
            blended = 0.6 * truth_vec.get(c, 0.0) + 0.4 * cat_averages.get(c, 0.0)
            cat_averages[c] = round(blended, 3)
    
    # --- Improved risk scoring ---
    # Use a weighted sum of top categories, not just the max
    # This produces more realistic and varied scores
    sorted_vals = sorted(cat_averages.values(), reverse=True)
    
    if len(sorted_vals) >= 3:
        # Weighted: top1 * 0.5 + top2 * 0.3 + top3 * 0.2
        composite = sorted_vals[0] * 0.5 + sorted_vals[1] * 0.3 + sorted_vals[2] * 0.2
    else:
        composite = sorted_vals[0] if sorted_vals else 0.0
    
    # Scale to 0-100 with amplification
    # The raw values from Gaussian blending are typically 0.05-0.40
    # We want to map this to roughly 20-85 range for meaningful variation
    import math
    amplified = 1 - math.exp(-4.0 * composite)  # exponential stretch
    risk_score = round(amplified * 100, 1)
    
    # Ensure minimum meaningful score (urban areas always have some baseline risk)
    if truth_vec:
        risk_score = max(risk_score, 15.0)
    
    # Top 3 hotspots
    sorted_cats = sorted(cat_averages.items(), key=lambda x: x[1], reverse=True)
    hotspots = [
        {"category": c, "score": round(s, 3)}
        for c, s in sorted_cats[:3] if s > 0.01
    ]
    
    return {
        "lat": lat,
        "lng": lng,
        "risk_score": risk_score,
        "risk_label": risk_label(risk_score),
        "recommendation": risk_recommendation(risk_score),
        "report_count": len(posts),
        "radius_km": radius_km,
        "categories": cat_averages,
        "hotspots": hotspots,
        "truth_vector": truth_vec
    }
