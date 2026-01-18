// frontend/src/components/multiplayer/ItemBrowser.js
import React, { useState, useEffect, useCallback, useRef } from 'react';
import api from '../../api/axiosConfig';
import useDebounce from '../../hooks/useDebounce';

function ItemBrowser({ 
    onItemSelect, 
    universe = 'star_wars',
    isGM = false,
    initialCategory = 'weapons',
    allowedCategories = null
}) {
    const [category, setCategory] = useState(initialCategory);
    const [items, setItems] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const debouncedSearch = useDebounce(searchQuery, 400);
    
    const [loading, setLoading] = useState(false);
    const [withImages, setWithImages] = useState(true);
    
    // Paginacja
    const [offset, setOffset] = useState(0);
    const [total, setTotal] = useState(0);
    const [loadingMore, setLoadingMore] = useState(false);
    const loaderRef = useRef(null);

    const ALL_CATEGORIES = ['weapons', 'armor', 'items', 'vehicles', 'droids', 'characters', 'species', 'creatures'];
    const categoriesToShow = allowedCategories || ALL_CATEGORIES;

    const getProxiedImageUrl = (originalUrl) => {
        if (!originalUrl) return null;
        if (originalUrl.includes('wikia.nocookie.net') || originalUrl.includes('fandom.com')) {
            return `http://localhost:8000/api/v1/wiki/image-proxy?url=${encodeURIComponent(originalUrl)}`;
        }
        return originalUrl;
    };

    // Reset przy zmianie kategorii/wyszukiwania
    useEffect(() => {
        setItems([]);
        setOffset(0);
        setTotal(0);
        loadItems(true);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [category, debouncedSearch, withImages, universe]);

    const loadItems = async (isFresh = false) => {
        const currentOffset = isFresh ? 0 : offset;
        // Jeśli nie jest to świeże ładowanie i mamy już wszystko, przerwij
        if (!isFresh && items.length > 0 && items.length >= total && total !== 0) return;

        isFresh ? setLoading(true) : setLoadingMore(true);

        try {
            const response = await api.get('/wiki/search', {
                params: {
                    universe,
                    category,
                    q: debouncedSearch || undefined,
                    limit: 20,
                    offset: currentOffset,
                    with_images: withImages
                }
            });

            const newItems = response.data.items || [];
            setItems(prev => isFresh ? newItems : [...prev, ...newItems]);
            setTotal(response.data.total);
            setOffset(currentOffset + 20);
        } catch (error) {
            console.error("Error fetching items:", error);
        } finally {
            isFresh ? setLoading(false) : setLoadingMore(false);
        }
    };

    // Infinite scroll observer
    useEffect(() => {
        const observer = new IntersectionObserver(entries => {
            if (entries[0].isIntersecting && !loading && !loadingMore) {
                loadItems(false);
            }
        }, { threshold: 1.0 });

        if (loaderRef.current) observer.observe(loaderRef.current);
        return () => observer.disconnect();
    }, [items, total, loading, loadingMore]);

    return (
        <div className="flex flex-col h-full bg-gray-800 rounded-lg p-4">
            {/* Header */}
            <div className="flex flex-col gap-3 mb-4">
                <div className="flex gap-2 overflow-x-auto custom-scrollbar pb-2">
                    {categoriesToShow.map(cat => (
                        <button
                            key={cat}
                            onClick={() => setCategory(cat)}
                            className={`px-3 py-1 rounded capitalize whitespace-nowrap text-sm font-semibold transition ${
                                category === cat ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                            }`}
                        >
                            {cat}
                        </button>
                    ))}
                </div>
                
                <div className="flex gap-2">
                    <input
                        type="text"
                        placeholder={`Search ${category}...`}
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="flex-1 bg-gray-700 text-white px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <button 
                        onClick={() => setWithImages(!withImages)}
                        className={`px-3 py-2 rounded ${withImages ? 'bg-green-700 text-white' : 'bg-gray-700 text-gray-400'}`}
                        title="Toggle images only"
                    >
                        🖼️
                    </button>
                </div>
            </div>

            {/* Grid */}
            <div className="flex-1 overflow-y-auto custom-scrollbar pr-2">
                {loading ? (
                    <div className="text-center py-10 text-gray-400">Loading items...</div>
                ) : (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                        {items.map((item, idx) => {
                            // Unikalny klucz dla listy
                            const key = `${item.name}-${idx}`; 
                            return (
                                <div 
                                    key={key}
                                    onClick={() => onItemSelect(item)}
                                    className="bg-gray-700 hover:bg-gray-600 p-2 rounded cursor-pointer transition hover:scale-105 border border-gray-600 flex flex-col group"
                                >
                                    {/* ✅ POPRAWKA: object-contain + stała wysokość + tło */}
                                    <div className="w-full h-32 bg-black rounded mb-2 flex items-center justify-center overflow-hidden border border-gray-800 relative">
                                        {item.image_url ? (
                                            <img 
                                                src={getProxiedImageUrl(item.image_url)} 
                                                alt={item.name}
                                                className="w-full h-full object-contain" 
                                                crossOrigin="anonymous" 
                                                onError={(e) => {
                                                    e.target.style.display = 'none';
                                                    // Pokaż ikonę zastępczą w razie błędu ładowania
                                                    if (e.target.nextSibling) e.target.nextSibling.style.display = 'block';
                                                }} 
                                            />
                                        ) : (
                                            <span className="text-gray-600 text-3xl">
                                                {category === 'characters' || category === 'species' ? '👤' : category === 'creatures' ? '🐾' : '📦'}
                                            </span>
                                        )}
                                        {/* Ikona zastępcza (ukryta domyślnie, jeśli jest url) */}
                                        {item.image_url && (
                                            <span className="text-gray-600 text-3xl absolute hidden">
                                                {category === 'characters' || category === 'species' ? '👤' : '📦'}
                                            </span>
                                        )}
                                    </div>
                                    
                                    <h4 className="text-white font-semibold text-xs text-center line-clamp-2">{item.name}</h4>
                                </div>
                            );
                        })}
                    </div>
                )}
                
                {/* Loader "Load More" */}
                <div ref={loaderRef} className="h-10 text-center py-4">
                    {loadingMore && <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-500 mx-auto"></div>}
                    {!loading && items.length > 0 && items.length >= total && (
                        <span className="text-gray-500 text-sm">End of results ({total} items)</span>
                    )}
                </div>
            </div>
        </div>
    );
}

export default ItemBrowser;