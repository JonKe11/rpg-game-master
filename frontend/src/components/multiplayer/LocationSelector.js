// frontend/src/components/multiplayer/LocationSelector.js
import React, { useState, useEffect } from 'react';
import api from '../../api/axiosConfig';
import { wikiCache } from '../../utils/wikiCache';

function LoadingSpinner({ text }) {
    return (
        <div className="text-center text-white py-6">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-3"></div>
            <div className="text-sm text-gray-400">{text}</div>
        </div>
    );
}

function LocationGridItem({ item, onClick, isSelected }) {
    const getProxiedImageUrl = (originalUrl) => {
        if (!originalUrl) return null;
        if (originalUrl.includes('wikia.nocookie.net') || originalUrl.includes('fandom.com')) {
            return `http://localhost:8000/api/v1/wiki/image-proxy?url=${encodeURIComponent(originalUrl)}`;
        }
        return originalUrl;
    };

    const isVirtual = item.name.endsWith('(Cała Planeta)');
    
    return (
        <div
            onClick={() => onClick(item.name)}
            className={`
                cursor-pointer rounded-lg p-3 transition hover:scale-105 h-full flex flex-col border
                ${isSelected 
                    ? 'bg-blue-900/50 border-blue-400 ring-2 ring-blue-400' 
                    : isVirtual
                        ? 'bg-indigo-900/30 border-indigo-600 hover:bg-indigo-800'
                        : 'bg-gray-700 hover:bg-gray-600 border-gray-600'
                }
            `}
        >
            {/* ✅ ZMIANA: Kontener obrazka z object-contain */}
            <div className="w-full h-32 bg-black rounded mb-2 flex items-center justify-center overflow-hidden border border-gray-800">
                {item.image_url ? (
                    <img
                        src={getProxiedImageUrl(item.image_url)}
                        alt={item.name}
                        className="w-full h-full object-contain"
                        crossOrigin="anonymous"
                    />
                ) : (
                    <span className="text-gray-600 text-4xl">{isVirtual ? '🌐' : '🌍'}</span>
                )}
            </div>
            
            <p className="text-white font-semibold text-sm mt-auto text-center">{item.name}</p>
        </div>
    );
}

function LocationSelect({ label, options, onSelect, isLoading, selectedValue }) {
    if (isLoading) return <LoadingSpinner text={`Loading ${label}...`} />;
    if (!options || options.length === 0) return null;

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
    const [regions, setRegions] = useState([]);
    const [systems, setSystems] = useState([]);
    const [planets, setPlanets] = useState([]);
    const [specificLocations, setSpecificLocations] = useState([]);

    const [selectedRegion, setSelectedRegion] = useState(null);
    const [selectedSystem, setSelectedSystem] = useState(null);
    const [selectedPlanet, setSelectedPlanet] = useState(null);

    const [loadingRegions, setLoadingRegions] = useState(false);
    const [loadingSystems, setLoadingSystems] = useState(false);
    const [loadingPlanets, setLoadingPlanets] = useState(false);
    const [loadingLocations, setLoadingLocations] = useState(false);

    // Krok 1: Regiony
    useEffect(() => {
        if (!isGM) return;
        const loadRegions = async () => {
            setLoadingRegions(true);
            const cacheKey = "tree_regions";
            const cached = wikiCache.get(universe, cacheKey);
            if (cached) { setRegions(cached); setLoadingRegions(false); return; }
            try {
                const response = await api.get('/wiki/locations/tree/regions', { params: { universe } });
                setRegions(response.data);
                wikiCache.set(universe, cacheKey, response.data);
            } catch (error) { console.error(error); } finally { setLoadingRegions(false); }
        };
        loadRegions();
    }, [universe, isGM]);

    // Krok 2: Systemy
    useEffect(() => {
        if (!isGM || !selectedRegion) { setSystems([]); return; }
        const loadSystems = async () => {
            setLoadingSystems(true);
            const cacheKey = `tree_systems_${selectedRegion}`;
            const cached = wikiCache.get(universe, cacheKey);
            if (cached) { setSystems(cached); setLoadingSystems(false); return; }
            try {
                const response = await api.get('/wiki/locations/tree/systems-by-region', { params: { universe, region: selectedRegion } });
                setSystems(response.data);
                wikiCache.set(universe, cacheKey, response.data);
            } catch (error) { console.error(error); } finally { setLoadingSystems(false); }
        };
        loadSystems();
    }, [selectedRegion, universe, isGM]);

    // Krok 3: Planety
    useEffect(() => {
        if (!isGM || !selectedSystem) { setPlanets([]); return; }
        const loadPlanets = async () => {
            setLoadingPlanets(true);
            const cacheKey = `tree_planets_${selectedSystem}`;
            const cached = wikiCache.get(universe, cacheKey);
            if (cached) { setPlanets(cached); setLoadingPlanets(false); return; }
            try {
                const response = await api.get('/wiki/locations/tree/planets-by-system', { params: { universe, system: selectedSystem } });
                setPlanets(response.data);
                wikiCache.set(universe, cacheKey, response.data);
            } catch (error) { console.error(error); } finally { setLoadingPlanets(false); }
        };
        loadPlanets();
    }, [selectedSystem, universe, isGM]);

    // Krok 4: Lokacje na planecie
    useEffect(() => {
        if (!isGM || !selectedPlanet) { setSpecificLocations([]); return; }
        const loadLocations = async () => {
            setLoadingLocations(true);
            const cacheKey = `tree_locations_${selectedPlanet}`;
            let locationsData = wikiCache.get(universe, cacheKey);

            if (!locationsData) {
                try {
                    const response = await api.get('/wiki/locations/tree/on-planet', { params: { universe, planet: selectedPlanet } });
                    locationsData = response.data || [];
                    wikiCache.set(universe, cacheKey, locationsData);
                } catch (error) { console.error(error); locationsData = []; }
            }

            if (locationsData.length > 0) {
                const planetObject = planets.find(p => p.name === selectedPlanet);
                const planetAsLocation = {
                    name: `${selectedPlanet} (Cała Planeta)`,
                    description: `Wybierz, aby ustawić całą planetę ${selectedPlanet} jako lokację.`,
                    image_url: planetObject?.image_url || null
                };
                setSpecificLocations([planetAsLocation, ...locationsData]);
            } else {
                if (currentLocation !== selectedPlanet) {
                    console.log(`Auto-selecting planet: ${selectedPlanet}`);
                    onLocationChange(selectedPlanet);
                }
                setSpecificLocations([]);
            }
            setLoadingLocations(false);
        };
        loadLocations();
    }, [selectedPlanet, universe, isGM, onLocationChange, planets, currentLocation]);

    const handleRegionSelect = (region) => {
        setSelectedRegion(region); setSelectedSystem(null); setSelectedPlanet(null); setPlanets([]); setSpecificLocations([]);
    };
    const handleSystemSelect = (system) => {
        setSelectedSystem(system); setSelectedPlanet(null); setSpecificLocations([]);
    };
    const handlePlanetSelect = (planetName) => {
        setSelectedPlanet(planetName);
    };
    const handleLocationSelect = (locationName) => {
        const finalName = locationName.endsWith('(Cała Planeta)') ? selectedPlanet : locationName;
        if (currentLocation !== finalName) {
            onLocationChange(finalName);
        }
    };

    if (!isGM) {
        return (
            <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="text-xl font-bold text-white mb-4">📍 Current Location</h3>
                <div className="p-4 bg-gray-700 rounded-lg">
                    <p className="text-white font-semibold text-lg">{currentLocation || 'Unknown'}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-gray-800 rounded-lg p-6 h-full flex flex-col">
            <h3 className="text-xl font-bold text-white mb-4">📍 Change Location (GM)</h3>
            
            <div className="flex-1 overflow-y-auto custom-scrollbar pr-2">
                <LocationSelect label="Region" options={regions} onSelect={handleRegionSelect} isLoading={loadingRegions} selectedValue={selectedRegion} />
                {selectedRegion && <LocationSelect label="System" options={systems} onSelect={handleSystemSelect} isLoading={loadingSystems} selectedValue={selectedSystem} />}
                
                {selectedSystem && (
                    <div className="mb-6">
                        <h4 className="text-white font-semibold mb-2">Planet</h4>
                        {loadingPlanets ? <LoadingSpinner text="Loading..." /> : (
                            <div className="grid grid-cols-2 gap-2">
                                {planets.map(p => (
                                    <LocationGridItem key={p.name} item={p} onClick={handlePlanetSelect} isSelected={selectedPlanet === p.name} />
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {selectedPlanet && specificLocations.length > 0 && (
                    <div className="mb-6">
                        <h4 className="text-white font-semibold mb-2">Specific Location</h4>
                        {loadingLocations ? <LoadingSpinner text="Loading..." /> : (
                            <div className="grid grid-cols-2 gap-2">
                                {specificLocations.map(l => (
                                    <LocationGridItem key={l.name} item={l} onClick={handleLocationSelect} isSelected={currentLocation === l.name} />
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

export default LocationSelector;