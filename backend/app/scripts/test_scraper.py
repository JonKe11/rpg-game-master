# backend/scripts/test_scraper.py
"""
Test scrapera - sprawdza czy pobieranie kategorii działa
"""
from app.core.scraper.wiki_scraper import WikiScraper
import time

def test_categories():
    """Testuje pobieranie kategorii z Wookiepedii"""
    
    scraper = WikiScraper()
    universe = 'star_wars'
    
    print("=" * 60)
    print("TESTING WOOKIEPEDIA SCRAPER")
    print("=" * 60)
    
    # Test 1: Pobierz gatunki (species)
    print("\n1. Testing Species/Races...")
    print("-" * 60)
    species = scraper.get_category_items(universe, 'species', limit=20)
    print(f"Found {len(species)} species:")
    for i, sp in enumerate(species[:10], 1):
        print(f"  {i}. {sp}")
    if len(species) > 10:
        print(f"  ... and {len(species) - 10} more")
    
    time.sleep(1)  # Bądź grzeczny dla serwera
    
    # Test 2: Pobierz planety
    print("\n2. Testing Planets...")
    print("-" * 60)
    planets = scraper.get_category_items(universe, 'planets', limit=20)
    print(f"Found {len(planets)} planets:")
    for i, planet in enumerate(planets[:10], 1):
        print(f"  {i}. {planet}")
    if len(planets) > 10:
        print(f"  ... and {len(planets) - 10} more")
    
    time.sleep(1)
    
    # Test 3: Pobierz organizacje
    print("\n3. Testing Organizations...")
    print("-" * 60)
    orgs = scraper.get_category_items(universe, 'organizations', limit=20)
    print(f"Found {len(orgs)} organizations:")
    for i, org in enumerate(orgs[:10], 1):
        print(f"  {i}. {org}")
    if len(orgs) > 10:
        print(f"  ... and {len(orgs) - 10} more")
    
    # Test 4: Wyszukiwanie
    print("\n4. Testing Search...")
    print("-" * 60)
    search_results = scraper.search_in_category(universe, 'species', 'human')
    print(f"Search for 'human' in species:")
    for i, result in enumerate(search_results[:10], 1):
        print(f"  {i}. {result}")
    
    time.sleep(1)
    
    # Test 5: Szczegóły planety
    print("\n5. Testing Planet Details...")
    print("-" * 60)
    if planets:
        planet_name = planets[0]
        planet_data = scraper.get_planet_data(planet_name, universe)
        if planet_data:
            print(f"Details for {planet_name}:")
            print(f"  Description: {planet_data.get('description', 'N/A')[:100]}...")
            print(f"  System: {planet_data.get('system', 'N/A')}")
            print(f"  Region: {planet_data.get('region', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("TESTING COMPLETED")
    print("=" * 60)
    
    # Podsumowanie
    print("\n📊 Summary:")
    print(f"  Species found: {len(species)}")
    print(f"  Planets found: {len(planets)}")
    print(f"  Organizations found: {len(orgs)}")
    print(f"  Cache size: {len(scraper.cache)} items")

def test_colors_and_genders():
    """Testuje hardcoded listy (kolory, płcie)"""
    
    scraper = WikiScraper()
    
    print("\n" + "=" * 60)
    print("TESTING HARDCODED LISTS")
    print("=" * 60)
    
    colors = scraper.get_category_items('star_wars', 'colors')
    print(f"\nColors ({len(colors)}): {', '.join(colors)}")
    
    genders = scraper.get_category_items('star_wars', 'genders')
    print(f"\nGenders ({len(genders)}): {', '.join(genders)}")

if __name__ == "__main__":
    try:
        test_categories()
        test_colors_and_genders()
        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()