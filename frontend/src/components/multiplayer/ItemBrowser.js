// frontend/src/components/multiplayer/ItemBrowser.js
// ✅ WERSJA 4.0 - Używa /wiki/search, wyszukiwania na żywo i paginacji "load more"

import React, { useState, useEffect, useCallback, useRef } from 'react';
import api from '../../api/axiosConfig';
import useDebounce from '../../hooks/useDebounce'; // ✅ Używamy hooka

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
    const debouncedSearch = useDebounce(searchQuery, 400); // Opóźnienie wyszukiwania
    
    const [loading, setLoading] = useState(false);
    const [withImages, setWithImages] = useState(true);
    
    // Paginacja
    const [offset, setOffset] = useState(0);
    const [total, setTotal] = useState(0);
    const [loadingMore, setLoadingMore] = useState(false);
    const loaderRef = useRef(null); // Do "infinite scroll"

    const ALL_CATEGORIES = ['weapons', 'armor', 'items', 'vehicles', 'droids', 'characters', 'species', 'creatures'];
    const categoriesToShow = allowedCategories || ALL_CATEGORIES;

    const getProxiedImageUrl = (originalUrl) => {
        if (!originalUrl) return null;
        if (originalUrl.includes('wikia.nocookie.net') || originalUrl.includes('fandom.com')) {
            return `http://localhost:8000/api/v1/wiki/image-proxy?url=${encodeURIComponent(originalUrl)}`;
        }
        return originalUrl;
    };

    // ⛔️ Usunięto 'loadCategoryCounts' - niepotrzebne
    
    // ✅ Nowa funkcja ładowania danych z paginacją
    const loadItems = useCallback(async (isNewSearch = false) => {
        if (isNewSearch) {
            setLoading(true);
            setOffset(0); // Resetuj paginację
        } else {
            setLoadingMore(true);
        }

        try {
            const currentOffset = isNewSearch ? 0 : offset;
            
            const response = await api.get('/wiki/search', {
                params: {
                    universe: universe,
                    category: category,
                    q: debouncedSearch || undefined, // Użyj debounced search
                    limit: 30, // Ładuj po 30
                    offset: currentOffset,
                    with_images: withImages
                }
            });
            
            const newItems = response.data.items || [];
            
            if (isNewSearch) {
                setItems(newItems);
            } else {
                // Dodaj tylko te, których jeszcze nie ma (na wszelki wypadek)
                setItems(prevItems => [
                    ...prevItems, 
                    ...newItems.filter(newItem => !prevItems.some(prev => prev.name === newItem.name))
                ]);
            }
            
            setTotal(response.data.total || 0);
            setOffset(currentOffset + newItems.length);
            
        } catch (error) {
            console.error('Error loading items:', error);
        } finally {
            setLoading(false);
            setLoadingMore(false);
        }
    }, [category, debouncedSearch, universe, withImages, offset]); // Zależność od debouncedSearch

    // Uruchom ponownie wyszukiwanie, gdy zmieni się kategoria, query (debounced) lub filtr obrazków
    useEffect(() => {
        loadItems(true); // 'true' oznacza nowy wyszukiwanie (resetuje listę)
    }, [category, debouncedSearch, withImages, universe]); // Usunięto 'loadItems'

    // Obsługa "infinite scroll"
    useEffect(() => {
        const observer = new IntersectionObserver(
            (entries) => {
                // Załaduj więcej, jeśli widać loader, nie ładujemy już, i mamy jeszcze co ładować
                if (entries[0].isIntersecting && !loading && !loadingMore && items.length < total) {
                    loadItems(false); // 'false' oznacza ładowanie więcej
                }
            },
            { threshold: 1.0 }
        );

        const currentLoader = loaderRef.current;
        if (currentLoader) {
            observer.observe(currentLoader);
        }

        return () => {
            if (currentLoader) {
                observer.unobserve(currentLoader);
            }
        };
    }, [loaderRef, loadItems, loading, loadingMore, items, total]);


    if (!isGM) return <div className="text-center text-gray-400 p-12">Only GM can browse.</div>;

    return (
        <div className="item-browser bg-gray-800 rounded-lg p-6 border border-gray-700 h-full flex flex-col">
            <h3 className="text-xl font-bold text-white mb-4">
                📂 Browser: <span className="text-blue-400 capitalize">{category}</span>
            </h3>

            <div className="flex gap-2 mb-4 overflow-x-auto pb-2 scrollbar-thin">
                {categoriesToShow.map((cat) => (
                    <button key={cat} onClick={() => setCategory(cat)} 
                        className={`px-3 py-1 rounded-full text-sm font-semibold whitespace-nowrap transition ${category === cat ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}`}>
                        {cat.charAt(0).toUpperCase() + cat.slice(1)}
                        {/* Usunięto liczniki, bo wymagają osobnego API calla */}
                    </button>
                ))}
            </div>

            <div className="mb-4 flex gap-2">
                <input type="text" placeholder={`Search ${category}...`} value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} 
                    className="flex-1 px-3 py-2 bg-gray-700 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500" />
                <label className="flex items-center gap-2 text-gray-300 cursor-pointer bg-gray-700 px-3 rounded hover:bg-gray-600">
                    <input type="checkbox" checked={withImages} onChange={(e) => setWithImages(e.target.checked)} className="w-4 h-4" />
                    <span className="text-xs">Images</span>
                </label>
            </div>

            <div className="flex-1 overflow-y-auto pr-1">
                {loading ? (
                    <div className="text-center py-12 text-white">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
                        Loading...
                    </div>
                ) : items.length === 0 ? (
                    <div className="text-center py-12 text-gray-400">
                        No results found {searchQuery && `for "${searchQuery}"`} in {category}.
                    </div>
                ) : (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                        {items.map((item) => {
                            const itemObject = { ...item, category: category };
                            return (
                                <div key={`${item.name}-${item.id}`} onClick={() => onItemSelect(itemObject)} 
                                    className="bg-gray-700 hover:bg-gray-600 rounded p-2 cursor-pointer transition hover:scale-105 group">
                                    {withImages && item.image_url ? (
                                        <img src={getProxiedImageUrl(item.image_url)} alt={item.name} 
                                            className="w-full h-24 object-cover rounded mb-2 group-hover:opacity-90" crossOrigin="anonymous" 
                                            onError={(e) => { e.currentTarget.style.display = 'none'; e.currentTarget.nextElementSibling.style.display = 'flex'; }} />
                                    ) : null}
                                    <div className="w-full h-24 bg-gray-600 rounded mb-2 items-center justify-center text-2xl" style={{ display: (withImages && item.image_url) ? 'none' : 'flex' }}>
                                        {category === 'characters' || category === 'species' ? '👤' : category === 'creatures' ? '🐾' : '📦'}
                                    </div>
                                    <h4 className="text-white font-semibold text-xs truncate">{item.name}</h4>
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