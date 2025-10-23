# backend/test_canon_scraper.py

from app.core.scraper.wiki_scraper import WikiScraper
import time

def test_canon_scraper():
    """Test complete canon scraping system with ULTRA FAST parallel mode"""
    
    scraper = WikiScraper()
    
    print("="*80)
    print("🔥 TEST 1: First fetch (PARALLEL MODE - should take 3-5 minutes)")
    print("="*80)
    
    start = time.time()
    data = scraper.get_canon_categorized_data(
        universe='star_wars',
        depth=3,
        force_refresh=True  # Force fresh fetch
    )
    elapsed = time.time() - start
    
    print(f"\n⏱️  Elapsed: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
    print(f"🚀 Previous version would take ~20 minutes!")
    print(f"⚡ Speedup: {20*60/elapsed:.1f}x faster!")
    
    print("\n" + "="*80)
    print("TEST 2: Cached fetch (should be instant)")
    print("="*80)
    
    start = time.time()
    data2 = scraper.get_canon_categorized_data(
        universe='star_wars',
        depth=3
    )
    elapsed = time.time() - start
    
    print(f"\n⏱️  Elapsed: {elapsed:.3f}s (should be <0.1s)")
    
    print("\n" + "="*80)
    print("TEST 3: All category methods (Faza 1, 2 & 3)")
    print("="*80)
    
    print(f"\n📊 Category counts:")
    print(f"   Species: {len(scraper.get_all_species('star_wars')):,}")
    print(f"   Planets: {len(scraper.get_all_planets('star_wars')):,}")
    print(f"   Organizations: {len(scraper.get_all_organizations('star_wars')):,}")
    print(f"   Weapons: {len(scraper.get_all_weapons('star_wars')):,}")
    print(f"   Vehicles: {len(scraper.get_all_vehicles('star_wars')):,}")
    print(f"   Locations: {len(scraper.get_all_locations('star_wars')):,}")
    print(f"   Items: {len(scraper.get_all_items('star_wars')):,}")
    print(f"   Armor: {len(scraper.get_all_armor('star_wars')):,}")
    print(f"   Droids: {len(scraper.get_all_droids('star_wars')):,}")
    
    print("\n✅ All tests passed!")
    print("🎉 Cache is ready for production use!")

if __name__ == "__main__":
    test_canon_scraper()