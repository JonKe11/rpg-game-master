// frontend/src/components/multiplayer/CompendiumBrowser.js
import React, { useState, useEffect, useCallback } from 'react';
import api from '../../api/axiosConfig';
import { wikiCache } from '../../utils/wikiCache';

const COMPENDIUM_CATEGORIES = [
    { key: 'planets', name: 'Planets', categoryParam: 'planets' },
    { key: 'weapons', name: 'Weapons', categoryParam: 'weapons' },
    { key: 'armor', name: 'Armor', categoryParam: 'armor' },
    { key: 'items', name: 'Items', categoryParam: 'items' },
    { key: 'vehicles', name: 'Vehicles', categoryParam: 'vehicles' },
    { key: 'droids', name: 'Droids', categoryParam: 'droids' },
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
            
            const response = await api.get('/wiki/search', {
                params: {
                    universe: universe,
                    category: selectedCategory.categoryParam,
                    q: search || undefined,
                    limit: 50,
                    with_images: false 
                }
            });
            
            const itemsData = response.data.items || [];
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

    const handleArticleSelect = async (item) => {
        const title = item.name || item.title;
        if (item.source_url) {
            window.open(item.source_url, '_blank');
        } else {
            try {
                const response = await api.get(`/wiki/${universe}/${selectedCategory.key}/${encodeURIComponent(title)}`);
                if (response.data.source_url) {
                    window.open(response.data.source_url, '_blank');
                } else {
                    alert('No source URL available');
                }
            } catch (e) {
                console.error(e);
            }
        }
    };

    return (
        <div className="bg-gray-800 rounded-lg p-6 h-full flex flex-col">
            <h3 className="text-2xl font-bold text-white mb-6">📚 Compendium</h3>

            <div className="flex gap-2 mb-6 overflow-x-auto custom-scrollbar pb-2">
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

            <div className="mb-6">
                <input
                    type="text"
                    placeholder={`Search ${selectedCategory.name}...`}
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="w-full px-4 py-3 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
            </div>

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
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 overflow-y-auto flex-1 custom-scrollbar pr-2">
                    {items.map((item) => (
                        <div
                            key={item.name || item.title}
                            onClick={() => handleArticleSelect(item)}
                            className="bg-gray-700 hover:bg-gray-600 rounded-lg p-3 cursor-pointer transition hover:scale-105 flex flex-col h-full border border-gray-600"
                        >
                            {/* ✅ ZMIANA: object-contain + tło + większa wysokość */}
                            <div className="w-full h-32 bg-black rounded mb-2 flex items-center justify-center overflow-hidden border border-gray-800">
                                {item.image_url ? (
                                    <img
                                        src={getProxiedImageUrl(item.image_url)}
                                        alt={item.name}
                                        className="w-full h-full object-contain"
                                        crossOrigin="anonymous"
                                        onError={(e) => e.target.style.display = 'none'}
                                    />
                                ) : (
                                    <span className="text-gray-600 text-3xl">📷</span>
                                )}
                            </div>
                            
                            <h4 className="text-white font-semibold text-sm mt-auto text-center">
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