// frontend/src/components/multiplayer/LocationSelector.js
// ✅ WERSJA 2.0 - Poprawiona logika wyboru Krok 3 -> Krok 4

import React, { useState, useEffect, useCallback } from 'react';
import api from '../../api/axiosConfig';
import { wikiCache } from '../../utils/wikiCache';

// Komponent pomocniczy do ładowania
function LoadingSpinner({ text }) {
    return (
        <div className="text-center text-white py-6">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-3"></div>
            <div className="text-sm text-gray-400">{text}</div>
        </div>
    );
}

// Komponent pomocniczy do wyświetlania elementów w siatce
function LocationGridItem({ item, onClick, isSelected }) {
    const getProxiedImageUrl = (originalUrl) => {
        if (!originalUrl) return null;
        if (originalUrl.includes('wikia.nocookie.net') || originalUrl.includes('fandom.com')) {
            return `http://localhost:8000/api/v1/wiki/image-proxy?url=${encodeURIComponent(originalUrl)}`;
        }
        return originalUrl;
    };

    // Specjalna obsługa dla wirtualnego przycisku "Cała Planeta"
    const isVirtual = item.name.endsWith('(Cała Planeta)');
    
    return (
        <div
            onClick={() => onClick(item.name)}
            className={`
                cursor-pointer rounded-lg p-3 transition hover:scale-105 h-full flex flex-col
                ${isSelected 
                    ? 'bg-blue-600 ring-2 ring-blue-400' 
                    : isVirtual
                        ? 'bg-indigo-700 hover:bg-indigo-600' // Inny kolor dla wirtualnego
                        : 'bg-gray-700 hover:bg-gray-600'
                }
            `}
        >
            {item.image_url ? (
                <img
                    src={getProxiedImageUrl(item.image_url)}
                    alt={item.name}
                    className="w-full h-24 object-cover rounded mb-2"
                    crossOrigin="anonymous"
                />
            ) : (
                <div className="w-full h-24 bg-gray-600 rounded mb-2 flex items-center justify-center">
                    <span className="text-gray-400 text-4xl">{isVirtual ? '🌐' : '🌍'}</span>
                </div>
            )}
            <p className="text-white font-semibold text-sm mt-auto">{item.name}</p>
            {item.description && (
                <p className="text-gray-300 text-xs mt-1 line-clamp-2">
                    {item.description}
                </p>
            )}
        </div>
    );
}

// Komponent pomocniczy do list <select>
function LocationSelect({ label, options, onSelect, isLoading, selectedValue }) {
    if (isLoading) {
        return <LoadingSpinner text={`Loading ${label}...`} />;
    }
    
    if (!options || options.length === 0) {
        return null; // Nie pokazuj, jeśli nie ma opcji
    }

    return (
        <div className="mb-4">
            <label className="block text-sm font-medium text-gray-300 mb-2">{label}</label>
            <select
                value={selectedValue || ""}
                onChange={(e) => onSelect(e.target.value)}
                className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
                <option value="" disabled>Select {label}...</option>
                {options.map((opt) => (
                    <option key={opt} value={opt}>{opt}</option>
                ))}
            </select>
        </div>
    );
}


function LocationSelector({ 
    currentLocation, 
    onLocationChange, 
    universe = 'star_wars',
    isGM = false
}) {
    // Stany dla hierarchii
    const [regions, setRegions] = useState([]);
    const [systems, setSystems] = useState([]);
    const [planets, setPlanets] = useState([]); // Przechowuje listę planet z Kroku 3
    const [specificLocations, setSpecificLocations] = useState([]); // Przechowuje listę z Kroku 4

    // Stany dla wybranych wartości
    const [selectedRegion, setSelectedRegion] = useState(null);
    const [selectedSystem, setSelectedSystem] = useState(null);
    const [selectedPlanet, setSelectedPlanet] = useState(null); // Aktywnie wybrana planeta

    // Stany ładowania
    const [loadingRegions, setLoadingRegions] = useState(false);
    const [loadingSystems, setLoadingSystems] = useState(false);
    const [loadingPlanets, setLoadingPlanets] = useState(false);
    const [loadingLocations, setLoadingLocations] = useState(false);

    // ✅ Krok 1: Ładowanie Regionów (przy montowaniu)
    useEffect(() => {
        if (!isGM) return;
        const loadRegions = async () => {
            setLoadingRegions(true);
            const cacheKey = "tree_regions";
            const cached = wikiCache.get(universe, cacheKey);
            if (cached) {
                setRegions(cached);
                setLoadingRegions(false);
                return;
            }
            try {
                const response = await api.get('/wiki/locations/tree/regions', {
                    params: { universe }
                });
                setRegions(response.data);
                wikiCache.set(universe, cacheKey, response.data);
            } catch (error) {
                console.error('Error loading regions:', error);
            } finally {
                setLoadingRegions(false);
            }
        };
        loadRegions();
    }, [universe, isGM]);

    // ✅ Krok 2: Ładowanie Systemów (gdy zmieni się Region)
    useEffect(() => {
        if (!isGM || !selectedRegion) {
            setSystems([]);
            return;
        }
        const loadSystems = async () => {
            setLoadingSystems(true);
            const cacheKey = `tree_systems_${selectedRegion}`;
            const cached = wikiCache.get(universe, cacheKey);
            if (cached) {
                setSystems(cached);
                setLoadingSystems(false);
                return;
            }
            try {
                // Używamy nowego endpointu
                const response = await api.get('/wiki/locations/tree/systems-by-region', {
                    params: { universe, region: selectedRegion }
                });
                setSystems(response.data);
                wikiCache.set(universe, cacheKey, response.data);
            } catch (error) {
                console.error('Error loading systems:', error);
            } finally {
                setLoadingSystems(false);
            }
        };
        loadSystems();
    }, [selectedRegion, universe, isGM]);

    // ✅ Krok 3: Ładowanie Planet (gdy zmieni się System)
    useEffect(() => {
        if (!isGM || !selectedSystem) {
            setPlanets([]);
            return;
        }
        const loadPlanets = async () => {
            setLoadingPlanets(true);
            const cacheKey = `tree_planets_${selectedSystem}`;
            const cached = wikiCache.get(universe, cacheKey);
            if (cached) {
                setPlanets(cached);
                setLoadingPlanets(false);
                return;
            }
            try {
                const response = await api.get('/wiki/locations/tree/planets-by-system', {
                    params: { universe, system: selectedSystem }
                });
                setPlanets(response.data); // Zapisujemy pełne obiekty planet
                wikiCache.set(universe, cacheKey, response.data);
            } catch (error) {
                console.error('Error loading planets:', error);
            } finally {
                setLoadingPlanets(false);
            }
        };
        loadPlanets();
    }, [selectedSystem, universe, isGM]);

    // ✅ Krok 4: Ładowanie Miejsc (gdy zmieni się Planeta)
    // To jest kluczowa zmiana logiki!
    useEffect(() => {
        if (!isGM || !selectedPlanet) {
            setSpecificLocations([]);
            return;
        }
        const loadLocations = async () => {
            setLoadingLocations(true);
            const cacheKey = `tree_locations_${selectedPlanet}`;
            const cached = wikiCache.get(universe, cacheKey);
            
            let locationsData = [];

            if (cached) {
                locationsData = cached;
            } else {
                try {
                    const response = await api.get('/wiki/locations/tree/on-planet', {
                        params: { universe, planet: selectedPlanet }
                    });
                    locationsData = response.data || [];
                    wikiCache.set(universe, cacheKey, locationsData);
                } catch (error) {
                    console.error('Error loading specific locations:', error);
                }
            }

            // === NOWA LOGIKA ===
            if (locationsData.length > 0) {
                // Scenariusz A (np. Ilum): Są pod-lokacje.
                // Dodaj samą planetę jako "wirtualną" pierwszą opcję.
                const planetObject = planets.find(p => p.name === selectedPlanet);
                const planetAsLocation = {
                    name: `${selectedPlanet} (Cała Planeta)`,
                    description: `Wybierz, aby ustawić całą planetę ${selectedPlanet} jako lokację.`,
                    image_url: planetObject?.image_url || null
                };
                setSpecificLocations([planetAsLocation, ...locationsData]);
            } else {
                // Scenariusz B (np. Duro): Nie ma pod-lokacji.
                // Automatycznie ustaw planetę jako lokację.
                onLocationChange(selectedPlanet);
                setSpecificLocations([]); // Upewnij się, że lista jest pusta
            }
            
            setLoadingLocations(false);
        };
        loadLocations();
    }, [selectedPlanet, universe, isGM, onLocationChange, planets]); // 'planets' jest potrzebne do pobrania image_url


    // Handlery wyboru (czyszczą pod-kategorie)
    const handleRegionSelect = (region) => {
        setSelectedRegion(region);
        setSelectedSystem(null);
        setSelectedPlanet(null);
        setPlanets([]);
        setSpecificLocations([]);
    };

    const handleSystemSelect = (system) => {
        setSelectedSystem(system);
        setSelectedPlanet(null);
        setSpecificLocations([]);
    };

    // ✅ ZMIANA: Kliknięcie planety tylko ją "wybiera", nie ustawia lokacji
    const handlePlanetSelect = (planetName) => {
        setSelectedPlanet(planetName);
        // Usunięto onLocationChange(planetName);
    };

    // ✅ ZMIANA: Ten handler obsługuje teraz wybór z Kroku 4
    const handleLocationSelect = (locationName) => {
        // Sprawdź, czy użytkownik kliknął wirtualną opcję "Cała Planeta"
        if (locationName.endsWith('(Cała Planeta)')) {
            // Użyj nazwy planety (przechowanej w selectedPlanet)
            onLocationChange(selectedPlanet);
        } else {
            // Użytkownik kliknął prawdziwą pod-lokację
            onLocationChange(locationName);
        }
    };

    // Widok dla gracza (non-GM)
    if (!isGM) {
        return (
            <div className="location-selector bg-gray-800 rounded-lg p-4">
                <h3 className="text-xl font-bold text-white mb-4">
                    📍 Current Location
                </h3>
                <div className="mb-6 p-4 bg-gray-700 rounded-lg">
                    <p className="text-gray-400 text-sm mb-2">Current Location:</p>
                    <p className="text-white font-semibold text-lg">{currentLocation || 'Unknown'}</p>
                    <p className="text-yellow-400 text-xs mt-2">
                        👁️ View Only - Only GM can change location
                    </p>
                </div>
            </div>
        );
    }

    // Widok dla GM-a
    return (
        <div className="location-selector bg-gray-800 rounded-lg p-6">
            <h3 className="text-xl font-bold text-white mb-4">
                📍 Change Location (GM)
            </h3>

            {/* Aktualnie wybrana lokacja */}
            <div className="mb-6 p-4 bg-gray-700 rounded-lg">
                <p className="text-gray-400 text-sm mb-2">Current Location:</p>
                <p className="text-white font-semibold text-lg">{currentLocation || 'Unknown'}</p>
            </div>

            {/* Krok 1: Regiony */}
            <LocationSelect
                label="Step 1: Select Region"
                options={regions}
                onSelect={handleRegionSelect}
                isLoading={loadingRegions}
                selectedValue={selectedRegion}
            />

            {/* Krok 2: Systemy (jeśli wybrano Region) */}
            {selectedRegion && (
                <LocationSelect
                    label="Step 2: Select System"
                    options={systems}
                    onSelect={handleSystemSelect}
                    isLoading={loadingSystems}
                    selectedValue={selectedSystem}
                />
            )}

            {/* Krok 3: Planety (jeśli wybrano System) */}
            {selectedSystem && (
                <div className="mb-6">
                    <h4 className="text-lg font-semibold text-white mb-3">Step 3: Select Planet or Moon</h4>
                    {loadingPlanets ? (
                        <LoadingSpinner text="Loading planets..." />
                    ) : planets.length === 0 ? (
                        <p className="text-gray-400 text-sm">No planets found in this system.</p>
                    ) : (
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 max-h-96 overflow-y-auto p-2 bg-gray-900 rounded">
                            {planets.map((planet) => (
                                <LocationGridItem
                                    key={planet.name}
                                    item={planet}
                                    onClick={handlePlanetSelect}
                                    isSelected={selectedPlanet === planet.name}
                                />
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* Krok 4: Miejsca (jeśli wybrano Planetę I SĄ jakieś miejsca) */}
            {selectedPlanet && specificLocations.length > 0 && (
                <div className="mb-6">
                    <h4 className="text-lg font-semibold text-white mb-3">Step 4: Select Specific Location</h4>
                    {loadingLocations ? (
                        <LoadingSpinner text="Loading locations..." />
                    ) : (
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 max-h-96 overflow-y-auto p-2 bg-gray-900 rounded">
                            {specificLocations.map((loc) => (
                                <LocationGridItem
                                    key={loc.name}
                                    item={loc}
                                    onClick={handleLocationSelect}
                                    isSelected={currentLocation === loc.name || (loc.name.endsWith('(Cała Planeta)') && currentLocation === selectedPlanet)}
                                />
                            ))}
                        </div>
                    )}
                </div>
            )}

        </div>
    );
}

export default LocationSelector;