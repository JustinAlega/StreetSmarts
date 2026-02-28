"""
Observer Agent for StreetSmarts.
The orchestrator that controls data flow between scraper, validator, and criticality agents.
Does NOT call any AI models itself — it's pure logic.
"""


class ObserverAgent:
    """Orchestrates the live pipeline agents."""
    
    def __init__(self):
        self.plausibility_threshold = 0.5
        self.severity_gate = 0.6
        self.deep_fetch_top_k = 3
    
    def tune_scraper(self, scraper):
        """Configure the scraper agent."""
        scraper.tune(
            max_items_per_query=3,
            dom_settle_seconds=6
        )
    
    def filter_validated(self, validated_items: list) -> list:
        """Filter out items below plausibility threshold."""
        return [
            item for item in validated_items
            if item.get("plausibility", 0) >= self.plausibility_threshold
        ]
    
    def should_write_post(self, criticality_result: dict) -> bool:
        """Gate: only write posts with severity above threshold."""
        return criticality_result.get("final_severity", 0) >= self.severity_gate
    
    def select_deep_fetch(self, validated_items: list) -> list:
        """Select top-K items for deep article extraction.
        Ranked by plausibility × severity_hint.
        """
        scored = []
        for item in validated_items:
            score = item.get("plausibility", 0) * item.get("severity_hint", 0)
            scored.append((score, item))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:self.deep_fetch_top_k]]
    
    def deduplicate(self, articles: list, seen_urls: set) -> list:
        """Remove duplicate articles by URL."""
        unique = []
        for article in articles:
            url = article.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique.append(article)
        return unique
