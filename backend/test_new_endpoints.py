# backend/test_new_endpoints.py

import requests
import json

BASE_URL = "http://localhost:8000/api/v1/wiki"

def test_endpoints():
    """Test all new endpoints"""
    
    print("="*80)
    print("🧪 Testing New Wiki Endpoints")
    print("="*80)
    
    # Test 1: Get all canon data
    print("\n1️⃣  Testing: GET /canon/all")
    try:
        response = requests.get(f"{BASE_URL}/canon/all?universe=star_wars")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Total items: {data['total_items']:,}")
            print(f"   ✅ Categories: {len(data['categories'])}")
            for cat, count in list(data['categories'].items())[:5]:
                print(f"      - {cat}: {count:,}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 2: Get summary
    print("\n2️⃣  Testing: GET /canon/summary")
    try:
        response = requests.get(f"{BASE_URL}/canon/summary?universe=star_wars")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Total items: {data['total_items']:,}")
            print(f"   ✅ Categories available: {len(data['categories'])}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 3: Get specific category
    print("\n3️⃣  Testing: GET /canon/category/weapons")
    try:
        response = requests.get(
            f"{BASE_URL}/canon/category/weapons",
            params={'universe': 'star_wars', 'limit': 10}
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Total weapons: {data['total']:,}")
            print(f"   ✅ Returned: {data['returned']}")
            print(f"   ✅ First 5 weapons:")
            for weapon in data['items'][:5]:
                print(f"      - {weapon}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 4: FAZA 2 - Planets with images
    print("\n4️⃣  Testing: GET /locations/planets (FAZA 2)")
    try:
        response = requests.get(
            f"{BASE_URL}/locations/planets",
            params={'universe': 'star_wars', 'limit': 5}
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Total planets: {data['total']}")
            print(f"   ✅ First 3 planets:")
            for planet in data['planets'][:3]:
                print(f"      - {planet['name']}")
                print(f"        Image: {planet['image_url'][:50] if planet['image_url'] else 'None'}...")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 5: FAZA 3 - Items by category
    print("\n5️⃣  Testing: GET /items/category/weapons (FAZA 3)")
    try:
        response = requests.get(
            f"{BASE_URL}/items/category/weapons",
            params={'universe': 'star_wars', 'limit': 10, 'search': 'blaster'}
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Total blasters: {data['total']}")
            print(f"   ✅ Returned: {data['returned']}")
            print(f"   ✅ First 5:")
            for item in data['items'][:5]:
                print(f"      - {item}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 6: Cache stats
    print("\n6️⃣  Testing: GET /cache/stats")
    try:
        response = requests.get(f"{BASE_URL}/cache/stats?universe=star_wars")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data['cached']:
                print(f"   ✅ Cache active!")
                print(f"   ✅ Age: {data['age_hours']:.1f} hours")
                print(f"   ✅ Remaining: {data['remaining_hours']:.1f} hours")
                print(f"   ✅ Total items: {data['total_items']:,}")
            else:
                print(f"   ⚠️  No cache yet")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    print("\n" + "="*80)
    print("✅ Testing complete!")
    print("="*80)

if __name__ == "__main__":
    test_endpoints()