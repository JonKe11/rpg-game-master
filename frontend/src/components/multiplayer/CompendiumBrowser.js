// frontend/src/components/multiplayer/CompendiumBrowser.js
import React, { useState, useEffect, useCallback } from 'react';
import api from '../../api/axiosConfig';
import { wikiCache } from '../../utils/wikiCache';

// Kategorie, dla których mamy działające endpointy "with-images"
const COMPENDIUM_CATEGORIES = [
    { key: 'planets', name: 'Planets', endpoint: '/wiki/locations/planets', dataKey: 'planets' },
    { key: 'weapons', name: 'Weapons', endpoint: '/wiki/items/category/weapons/with-images', dataKey: 'items' },
    { key: 'armor', name: 'Armor', endpoint: '/wiki/items/category/armor/with-images', dataKey: 'items' },
    { key: 'items', name: 'Items', endpoint: '/wiki/items/category/items/with-images', dataKey: 'items' },
    { key: 'vehicles', name: 'Vehicles', endpoint: '/wiki/items/category/vehicles/with-images', dataKey: 'items' },
    { key: 'droids', name: 'Droids', endpoint: '/wiki/items/category/droids/with-images', dataKey: 'items' },
    // TODO: Dodać endpointy dla 'characters' i 'species', gdy będą gotowe
];

function CompendiumBrowser({ universe = 'star_wars' }) {
    const [selectedCategory, setSelectedCategory] = useState(COMPENDIUM_CATEGORIES[0]);
    const [items, setItems] = useState([]);
    const [search, setSearch] = useState('');
    const [loading, setLoading] = useState(false);

    const getProxiedImageUrl = (originalUrl) => {
        if (!originalUrl) return null;
        if (originalUrl.includes('wikia.nocookie.net') || originalUrl.includes('fandom.com')) {
            return `http://localhost:8000/api/v1/wiki/image-proxy?url=${encodeURIComponent(originalUrl)}`;
        }
        return originalUrl;
    };

    const loadItems = useCallback(async () => {
        setLoading(true);
        try {
            const cacheKey = `compendium_${selectedCategory.key}_${search}`;
            const cached = wikiCache.get(universe, cacheKey);
            
            if (cached) {
                setItems(cached);
                setLoading(false);
                return;
            }
            
            const response = await api.get(selectedCategory.endpoint, {
                params: {
                    universe: universe,
                    limit: 50,
                    search: search || undefined
                }
            });
            
            const itemsData = response.data[selectedCategory.dataKey] || [];
            setItems(itemsData);
            wikiCache.set(universe, cacheKey, itemsData);
            
        } catch (error) {
            console.error('Error loading compendium items:', error);
        } finally {
            setLoading(false);
        }
    }, [selectedCategory, search, universe]);

    useEffect(() => {
        loadItems();
    }, [loadItems]);

    // Funkcja otwierająca link do wiki
    const handleArticleSelect = async (item) => {
        // Nazwy planet są w 'name', nazwy przedmiotów też...
        const title = item.name || item.title;
        
        // Kategoria planet to 'planets', dla reszty to 'key'
        const categorySlug = selectedCategory.key;
        
        try {
            // Użyj endpointu 'get_article_by_title', który na pewno zwraca 'source_url'
            const response = await api.get(`/wiki/${universe}/${categorySlug}/${encodeURIComponent(title)}`);
            const sourceUrl = response.data.source_url;
            
            if (sourceUrl) {
                window.open(sourceUrl, '_blank');
            } else {
                alert('Source URL not found for this article.');
            }
        } catch (error) {
            console.error('Failed to get article details:', error);
            alert('Could not retrieve article URL.');
        }
    };

    return (
        <div className="bg-gray-800 rounded-lg p-6 h-full flex flex-col">
            <h3 className="text-2xl font-bold text-white mb-6">📚 Compendium</h3>

            {/* Przyciski kategorii */}
            <div className="flex gap-2 mb-6 overflow-x-auto">
                {COMPENDIUM_CATEGORIES.map((cat) => (
                    <button
                        key={cat.key}
                        onClick={() => setSelectedCategory(cat)}
                        className={`px-4 py-2 rounded-lg font-semibold whitespace-nowrap transition ${
                            selectedCategory.key === cat.key ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                        }`}
                    >
                        {cat.name}
                    </button>
                ))}
            </div>

            {/* Wyszukiwarka */}
            <div className="mb-6">
                <input
                    type="text"
                    placeholder={`Search ${selectedCategory.name}...`}
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="w-full px-4 py-3 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
            </div>

            {/* Siatka z wynikami */}
            {loading ? (
                <div className="text-center py-12 flex-1">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                    <div className="text-white text-lg">Loading {selectedCategory.name}...</div>
                </div>
            ) : items.length === 0 ? (
                <div className="text-center py-12 flex-1">
                    <div className="text-gray-400">No {selectedCategory.name} found.</div>
                </div>
            ) : (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 overflow-y-auto flex-1">
                    {items.map((item) => (
                        <div
                            key={item.name || item.title}
                            onClick={() => handleArticleSelect(item)}
                            className="bg-gray-700 hover:bg-gray-600 rounded-lg p-4 cursor-pointer transition hover:scale-105"
                        >
                            <img
                                src={getProxiedImageUrl(item.image_url)}
                                alt={item.name || item.title}
                                className="w-full h-24 object-cover rounded mb-2"
                                crossOrigin="anonymous"
                                onError={(e) => {
                                    e.target.style.display = 'none';
                                    e.target.nextSibling.style.display = 'flex';
                                }}
                            />
                            <div className="w-full h-24 bg-gray-600 rounded mb-2 items-center justify-center" style={{ display: 'none' }}>
                                <span className="text-gray-400 text-3xl">📚</span>
                            </div>
                            <h4 className="text-white font-semibold text-sm">
                                {item.name || item.title}
                            </h4>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default CompendiumBrowser;