// frontend/src/components/multiplayer/LocationSelector.js

import React, { useState, useEffect, useCallback } from 'react';
import api from '../../api/axiosConfig';
import { wikiCache } from '../../utils/wikiCache';

function LocationSelector({ 
    currentLocation, 
    onLocationChange, 
    universe = 'star_wars',
    isGM = false
}) {
    const [planets, setPlanets] = useState([]);
    const [locations, setLocations] = useState([]);
    const [selectedPlanet, setSelectedPlanet] = useState(null);
    const [loading, setLoading] = useState(true);

    // ✨ PROXY dla obrazków (CORS fix)
    const getProxiedImageUrl = (originalUrl) => {
        if (!originalUrl) return null;
        
        if (originalUrl.includes('wikia.nocookie.net') || originalUrl.includes('fandom.com')) {
            return `http://localhost:8000/api/v1/wiki/image-proxy?url=${encodeURIComponent(originalUrl)}`;
        }
        
        return originalUrl;
    };

    const loadPlanets = useCallback(async () => {
    try {
        setLoading(true);
        
        const cached = wikiCache.get(universe, 'planets_with_images');
        if (cached) {
            console.log('✅ Loaded planets from FRONTEND cache!');
            setPlanets(cached);
            setLoading(false);
            return;
        }
        
        console.log('🔄 Fetching planets from API...');
        
        // ✅ NOWY ENDPOINT: /wiki/{universe}/planets
        const response = await api.get(`/wiki/locations/planets`, {
            params: { 
                universe: universe, // Przekaż universe jako parametr zapytania
                limit: 100,
                has_image: true
            }
        });
        
        // ✅ MAPOWANIE: Backend używa 'articles' zamiast 'planets'
        const planetsData = response.data.planets || [];
        setPlanets(planetsData);
        
        wikiCache.set(universe, 'planets_with_images', planetsData);
        console.log(`💾 Cached ${planetsData.length} planets`);
        
    } catch (error) {
        console.error('Error loading planets:', error);
    } finally {
        setLoading(false);
    }
}, [universe]);

    const loadLocationsForPlanet = useCallback(async (planet) => {
    try {
        const cached = wikiCache.get(universe, `locations_${planet}`);
        if (cached) {
            console.log(`✅ Loaded locations for ${planet} from cache!`);
            setLocations(cached);
            return;
        }
        
        console.log(`🔄 Fetching locations for ${planet}...`);
        
        // ✅ NOWY ENDPOINT: /wiki/{universe}/locations
        const response = await api.get(`/wiki/${universe}/locations`, {
            params: { 
                limit: 500,
                search: planet  // Szukaj po planecie
            }
        });
        
        // ✅ MAPOWANIE
        const locationsData = response.data.articles || response.data.locations || [];
        setLocations(locationsData);
        
        wikiCache.set(universe, `locations_${planet}`, locationsData);
        
    } catch (error) {
        console.error('Error loading locations:', error);
    }
}, [universe]);

    useEffect(() => {
        loadPlanets();
    }, [loadPlanets]);

    useEffect(() => {
        if (selectedPlanet) {
            loadLocationsForPlanet(selectedPlanet);
        }
    }, [selectedPlanet, loadLocationsForPlanet]);

    const handlePlanetSelect = (planet) => {
        if (!isGM) return;
        
        setSelectedPlanet(planet.name);
        onLocationChange(planet.name);
    };

    const handleLocationSelect = (location) => {
        if (!isGM) return;
        
        onLocationChange(location);
    };

    if (loading) {
        return (
            <div className="text-center text-white py-8">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                <div>Loading locations...</div>
                <div className="text-xs text-gray-400 mt-2">
                    First time may take a moment...
                </div>
            </div>
        );
    }

    return (
        <div className="location-selector bg-gray-800 rounded-lg p-4">
            <h3 className="text-xl font-bold text-white mb-4">
                📍 {isGM ? 'Change Location (GM)' : 'Current Location'}
            </h3>

            <div className="mb-6 p-4 bg-gray-700 rounded-lg">
                <p className="text-gray-400 text-sm mb-2">Current Location:</p>
                <p className="text-white font-semibold text-lg">{currentLocation || 'Unknown'}</p>
                {!isGM && (
                    <p className="text-yellow-400 text-xs mt-2">
                        👁️ View Only - Only GM can change location
                    </p>
                )}
            </div>

            {isGM && (
                <>
                    <div className="mb-6">
                        <h4 className="text-lg font-semibold text-white mb-3">Select Planet</h4>
                        {/* ✨ INFO O CACHE */}
                        {planets.length > 0 && (
                            <div className="text-xs text-gray-400 mb-2">
                                {planets.length} planets loaded from cache
                            </div>
                        )}
                        
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 max-h-96 overflow-y-auto">
                            {planets.map((planet) => (
                                <div
                                    key={planet.name}
                                    onClick={() => handlePlanetSelect(planet)}
                                    className={`
                                        cursor-pointer rounded-lg p-3 transition hover:scale-105
                                        ${selectedPlanet === planet.name 
                                            ? 'bg-blue-600 ring-2 ring-blue-400' 
                                            : 'bg-gray-700 hover:bg-gray-600'
                                        }
                                    `}
                                >
                                    {planet.image_url ? (
                                        <img
                                            src={getProxiedImageUrl(planet.image_url)}
                                            alt={planet.name}
                                            className="w-full h-32 object-cover rounded mb-2"
                                            crossOrigin="anonymous"
                                            onError={(e) => {
                                                console.log('❌ Image failed:', planet.name);
                                                e.target.style.display = 'none';
                                            }}
                                            onLoad={() => {
                                                console.log('✅ Image loaded:', planet.name);
                                            }}
                                        />
                                    ) : (
                                        <div className="w-full h-32 bg-gray-600 rounded mb-2 flex items-center justify-center">
                                            <span className="text-gray-400 text-4xl">🌍</span>
                                        </div>
                                    )}
                                    
                                    <p className="text-white font-semibold text-sm">{planet.name}</p>
                                    
                                    {planet.description && (
                                        <p className="text-gray-300 text-xs mt-1 line-clamp-2">
                                            {planet.description}
                                        </p>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>

                    {selectedPlanet && locations.length > 0 && (
                        <div>
                            <h4 className="text-lg font-semibold text-white mb-3">
                                Specific Location on {selectedPlanet}
                            </h4>
                            <select
                                onChange={(e) => handleLocationSelect(e.target.value)}
                                className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="">Select specific location...</option>
                                {locations.map((loc) => (
                                    <option key={loc} value={loc}>{loc}</option>
                                ))}
                            </select>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}

export default LocationSelector;