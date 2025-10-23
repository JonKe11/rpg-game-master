# backend/scripts/prewarm_wiki_cache.py
"""
Pre-fetches popularnych artykułów do cache
Uruchom przed grą aby wszystko było szybkie
"""
from app.services.wiki_fetcher_service import WikiFetcherService
from app.core.scraper.wiki_scraper import WikiScraper

def prewarm_cache(universe: str = 'star_wars', limit: int = 50):
    """
    Pobiera z góry najpopularniejsze artykuły
    
    Args:
        universe: star_wars, lotr, etc.
        limit: Ile artykułów pobrać
    """
    
    print(f"🔥 Pre-warming wiki cache for {universe}...")
    print(f"   Fetching up to {limit} articles...")
    
    fetcher = WikiFetcherService()
    scraper = WikiScraper()
    
    # Get categories
    print("\n📡 Fetching category lists...")
    planets = scraper.get_all_planets(universe)[:20]
    species = scraper.get_all_species(universe)[:15]
    orgs = scraper.get_all_organizations(universe)[:15]
    
    # Combine
    all_articles = planets + species + orgs
    all_articles = all_articles[:limit]
    
    print(f"✅ Found {len(all_articles)} articles to fetch\n")
    
    # Fetch each
    success = 0
    failed = 0
    
    for i, article_name in enumerate(all_articles, 1):
        print(f"[{i}/{len(all_articles)}] Fetching: {article_name}")
        
        result = fetcher.fetch_article(article_name, universe)
        if result:
            success += 1
        else:
            failed += 1
            print(f"   ⚠️ Failed")
    
    print(f"\n✅ Cache warming complete!")
    print(f"   Success: {success}")
    print(f"   Failed: {failed}")
    print(f"   Total: {len(all_articles)}")
    print(f"\n🎮 Your game will now be FAST!")

if __name__ == "__main__":
    import sys
    
    universe = sys.argv[1] if len(sys.argv) > 1 else 'star_wars'
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    
    prewarm_cache(universe, limit)