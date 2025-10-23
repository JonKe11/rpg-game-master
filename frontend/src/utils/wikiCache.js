// frontend/src/utils/wikiCache.js

class WikiCache {
  constructor() {
    this.cache = new Map();
    this.TTL = 7 * 24 * 60 * 60 * 1000; // 7 dni (jak backend)
  }

  getKey(universe, category) {
    return `${universe}_${category}`;
  }

  get(universe, category) {
    const key = this.getKey(universe, category);
    const cached = this.cache.get(key);
    
    if (!cached) return null;
    
    // Sprawdź TTL
    if (Date.now() - cached.timestamp > this.TTL) {
      this.cache.delete(key);
      return null;
    }
    
    return cached.data;
  }

  set(universe, category, data) {
    const key = this.getKey(universe, category);
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }

  clear() {
    this.cache.clear();
  }
}

// Singleton
export const wikiCache = new WikiCache();