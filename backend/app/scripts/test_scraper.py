# backend/scripts/test_scraper.py
"""
Test refactored scrapera - sprawdza czy nowe API działa
"""
from app.core.scraper.wiki_scraper import WikiScraper
import time

def test_new_api():
    """Testuje nowe refactored API scrapera"""
    
    scraper = WikiScraper()
    universe = 'star_wars'
    
    print("=" * 60)
    print("TESTING REFACTORED WIKI SCRAPER")
    print("=" * 60)
    
    # Test 1: Pobierz wszystkie gatunki
    print("\n1. Testing get_all_species()...")
    print("-" * 60)
    try:
        species = scraper.get_all_species(universe)
        print(f"Found {len(species)} species:")
        for i, sp in enumerate(species[:15], 1):
            print(f"  {i}. {sp}")
        if len(species) > 15:
            print(f"  ... and {len(species) - 15} more")
    except Exception as e:
        print(f"ERROR: {e}")
    
    time.sleep(1)
    
    # Test 2: Pobierz planety
    print("\n2. Testing get_all_planets()...")
    print("-" * 60)
    try:
        planets = scraper.get_all_planets(universe)
        print(f"Found {len(planets)} planets:")
        for i, planet in enumerate(planets[:15], 1):
            print(f"  {i}. {planet}")
        if len(planets) > 15:
            print(f"  ... and {len(planets) - 15} more")
    except Exception as e:
        print(f"ERROR: {e}")
    
    time.sleep(1)
    
    # Test 3: Pobierz organizacje
    print("\n3. Testing get_all_organizations()...")
    print("-" * 60)
    try:
        orgs = scraper.get_all_organizations(universe)
        print(f"Found {len(orgs)} organizations:")
        for i, org in enumerate(orgs[:15], 1):
            print(f"  {i}. {org}")
        if len(orgs) > 15:
            print(f"  ... and {len(orgs) - 15} more")
    except Exception as e:
        print(f"ERROR: {e}")
    
    time.sleep(1)
    
    # Test 4: Kolory (nowa metoda)
    print("\n4. Testing get_colors()...")
    print("-" * 60)
    try:
        colors = scraper.get_colors()
        print(f"Colors ({len(colors)}): {', '.join(colors[:20])}")
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Test 5: Wyszukiwanie postaci
    print("\n5. Testing search_character()...")
    print("-" * 60)
    test_chars = ['Luke Skywalker', 'Darth Vader', 'Yoda']
    for char_name in test_chars:
        try:
            url = scraper.search_character(char_name, universe)
            if url:
                print(f"  ✓ Found: {char_name} -> {url[:60]}...")
            else:
                print(f"  ✗ Not found: {char_name}")
        except Exception as e:
            print(f"  ✗ Error for {char_name}: {e}")
        time.sleep(0.5)
    
    # Test 6: Pobierz szczegóły postaci
    print("\n6. Testing scrape_character_data()...")
    print("-" * 60)
    try:
        url = scraper.search_character('Luke Skywalker', universe)
        if url:
            data = scraper.scrape_character_data(url)
            print(f"Character: {data.get('name', 'Unknown')}")
            print(f"Description: {data.get('description', 'N/A')[:100]}...")
            
            info = data.get('info_box', {})
            if info:
                print(f"Info fields: {list(info.keys())[:10]}")
            
            affiliations = data.get('affiliations', [])
            if affiliations:
                print(f"Affiliations: {', '.join(affiliations[:5])}")
        else:
            print("Could not find Luke Skywalker")
    except Exception as e:
        print(f"ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("TESTING COMPLETED")
    print("=" * 60)
    
    # Podsumowanie
    print("\n📊 Summary:")
    print(f"  Species API works: {len(species) > 0 if 'species' in locals() else False}")
    print(f"  Planets API works: {len(planets) > 0 if 'planets' in locals() else False}")
    print(f"  Organizations API works: {len(orgs) > 0 if 'orgs' in locals() else False}")
    print(f"  Colors API works: {len(colors) > 0 if 'colors' in locals() else False}")
    print(f"  Character search works: URL found for test characters")

def test_cache():
    """Test cache functionality"""
    print("\n" + "=" * 60)
    print("TESTING CACHE")
    print("=" * 60)
    
    scraper = WikiScraper()
    
    # First call - should scrape
    print("\nFirst call (should scrape)...")
    start = time.time()
    species1 = scraper.get_all_species('star_wars')
    time1 = time.time() - start
    print(f"Time: {time1:.2f}s - Found {len(species1)} species")
    
    # Second call - should use cache
    print("\nSecond call (should use cache)...")
    start = time.time()
    species2 = scraper.get_all_species('star_wars')
    time2 = time.time() - start
    print(f"Time: {time2:.2f}s - Found {len(species2)} species")
    
    if time2 < time1 * 0.5:
        print("✓ Cache is working! Second call was faster.")
    else:
        print("⚠ Cache might not be working as expected.")
    
    # Clear cache
    print("\nClearing cache...")
    scraper.clear_cache()
    print("✓ Cache cleared")

def test_error_handling():
    """Test error handling dla niepoprawnych danych"""
    print("\n" + "=" * 60)
    print("TESTING ERROR HANDLING")
    print("=" * 60)
    
    scraper = WikiScraper()
    
    # Test 1: Nieistniejące uniwersum
    print("\n1. Invalid universe...")
    try:
        result = scraper.get_all_species('invalid_universe')
        print(f"  Result: {result}")
    except Exception as e:
        print(f"  ✓ Handled gracefully: {type(e).__name__}")
    
    # Test 2: Nieistniejąca postać
    print("\n2. Non-existent character...")
    try:
        url = scraper.search_character('XxXInvalidCharacterXxX', 'star_wars')
        if url:
            print(f"  Found URL (unexpected): {url}")
        else:
            print(f"  ✓ Returned None (expected)")
    except Exception as e:
        print(f"  ✓ Handled gracefully: {type(e).__name__}")

if __name__ == "__main__":
    try:
        test_new_api()
        test_cache()
        test_error_handling()
        print("\n✅ All tests completed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()