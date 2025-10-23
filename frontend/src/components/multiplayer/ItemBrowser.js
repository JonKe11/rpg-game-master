// frontend/src/components/multiplayer/ItemBrowser.js

import React, { useState, useEffect, useCallback } from 'react';
import api from '../../api/axiosConfig';
import { wikiCache } from '../../utils/wikiCache';

function ItemBrowser({ 
    onItemSelect, 
    universe = 'star_wars',
    isGM = false
}) {
    const [category, setCategory] = useState('weapons');
    const [items, setItems] = useState([]);
    const [search, setSearch] = useState('');
    const [loading, setLoading] = useState(false);
    const [categoryCounts, setCategoryCounts] = useState({});
    const [withImages, setWithImages] = useState(true);

    const getProxiedImageUrl = (originalUrl) => {
        if (!originalUrl) return null;
        
        if (originalUrl.includes('wikia.nocookie.net') || originalUrl.includes('fandom.com')) {
            return `http://localhost:8000/api/v1/wiki/image-proxy?url=${encodeURIComponent(originalUrl)}`;
        }
        
        return originalUrl;
    };

    const loadCategoryCounts = useCallback(async () => {
        try {
            const response = await api.get('/wiki/items/all', {
                params: { universe }
            });
            
            const counts = {};
            Object.entries(response.data.categories).forEach(([cat, data]) => {
                counts[cat] = data.count;
            });
            
            setCategoryCounts(counts);
        } catch (error) {
            console.error('Error loading category counts:', error);
        }
    }, [universe]);

    const loadItems = useCallback(async () => {
        setLoading(true);
        try {
            const cacheKey = `items_${category}_${withImages}_${search}`;
            const cached = wikiCache.get(universe, cacheKey);
            
            if (cached) {
                console.log(`✅ Loaded ${category} from FRONTEND cache!`);
                setItems(cached);
                setLoading(false);
                return;
            }
            
            const endpoint = withImages 
                ? `/wiki/items/category/${category}/with-images`
                : `/wiki/items/category/${category}`;
            
            const response = await api.get(endpoint, {
                params: {
                    universe,
                    search: search || undefined,
                    limit: 50,
                }
            });
            
            const itemsData = response.data.items || [];
            setItems(itemsData);
            
            wikiCache.set(universe, cacheKey, itemsData);
            
        } catch (error) {
            console.error('Error loading items:', error);
        } finally {
            setLoading(false);
        }
    }, [category, search, universe, withImages]);

    useEffect(() => {
        loadCategoryCounts();
    }, [loadCategoryCounts]);

    useEffect(() => {
        loadItems();
    }, [loadItems]);

    if (!isGM) {
        return (
            <div className="item-browser bg-gray-800 rounded-lg p-6">
                <h3 className="text-2xl font-bold text-white mb-4">🎒 Item Browser</h3>
                <div className="text-center py-12">
                    <div className="text-6xl mb-4">🔒</div>
                    <p className="text-gray-400 text-lg">
                        Only GM can browse and add items
                    </p>
                    <p className="text-gray-500 text-sm mt-2">
                        Your inventory is managed by the Game Master
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="item-browser bg-gray-800 rounded-lg p-6">
            <h3 className="text-2xl font-bold text-white mb-6">🎒 Item Browser (GM)</h3>

            <div className="flex gap-2 mb-6 overflow-x-auto">
                {['weapons', 'armor', 'items', 'vehicles', 'droids'].map((cat) => (
                    <button
                        key={cat}
                        onClick={() => setCategory(cat)}
                        className={`px-4 py-2 rounded-lg font-semibold whitespace-nowrap transition ${category === cat ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}`}
                    >
                        {cat.charAt(0).toUpperCase() + cat.slice(1)}
                        {categoryCounts[cat] && (
                            <span className="ml-2 text-xs opacity-75">
                                ({categoryCounts[cat]})
                            </span>
                        )}
                    </button>
                ))}
            </div>

            <div className="mb-6 space-y-3">
                <input
                    type="text"
                    placeholder={`Search ${category}...`}
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="w-full px-4 py-3 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                
                <label className="flex items-center gap-2 text-gray-300 cursor-pointer">
                    <input
                        type="checkbox"
                        checked={withImages}
                        onChange={(e) => setWithImages(e.target.checked)}
                        className="w-4 h-4"
                    />
                    <span className="text-sm">
                        Show images from wiki (slower but prettier!)
                    </span>
                </label>
            </div>

            {loading ? (
                <div className="text-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                    <div className="text-white text-lg">Loading {category}...</div>
                    {withImages && (
                        <div className="text-gray-400 text-sm mt-2">
                            Fetching images from wiki...
                        </div>
                    )}
                </div>
            ) : items.length === 0 ? (
                <div className="text-center py-12">
                    <div className="text-gray-400">No {category} found</div>
                    {search && (
                        <button
                            onClick={() => setSearch('')}
                            className="mt-4 text-blue-400 hover:text-blue-300"
                        >
                            Clear search
                        </button>
                    )}
                </div>
            ) : (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 max-h-[500px] overflow-y-auto">
                    {items.map((item) => {
                        const itemName = typeof item === 'string' ? item : item.name;
                        const imageUrl = typeof item === 'object' ? item.image_url : null;
                        const description = typeof item === 'object' ? item.description : null;
                        
                        return (
                            <div
                                key={itemName}
                                onClick={() => onItemSelect(itemName)}
                                className="bg-gray-700 hover:bg-gray-600 rounded-lg p-4 cursor-pointer transition hover:scale-105"
                            >
                                {withImages && imageUrl ? (
                                    <img
                                        src={getProxiedImageUrl(imageUrl)}
                                        alt={itemName}
                                        className="w-full h-24 object-cover rounded mb-2"
                                        crossOrigin="anonymous"
                                        onError={(e) => {
                                            console.log('❌ Image failed:', itemName);
                                            e.target.style.display = 'none';
                                        }}
                                        onLoad={() => {
                                            console.log('✅ Image loaded:', itemName);
                                        }}
                                    />
                                ) : withImages ? (
                                    <div className="w-full h-24 bg-gray-600 rounded mb-2 flex items-center justify-center">
                                        <span className="text-gray-400 text-3xl">
                                            {category === 'weapons' ? '⚔️' : category === 'armor' ? '🛡️' : category === 'vehicles' ? '🚀' : category === 'droids' ? '🤖' : '📦'}
                                        </span>
                                    </div>
                                ) : null}
                                
                                <h4 className="text-white font-semibold text-sm">
                                    {itemName}
                                </h4>
                                
                                {description && (
                                    <p className="text-gray-300 text-xs mt-1 line-clamp-2">
                                        {description}
                                    </p>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}

            <div className="mt-4 text-sm text-gray-400 text-center">
                Showing {items.length} {category}
                {search && ` matching "${search}"`}
            </div>
        </div>
    );
}

export default ItemBrowser;