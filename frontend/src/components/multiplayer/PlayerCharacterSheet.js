// frontend/src/components/multiplayer/PlayerCharacterSheet.js
// ✅ WERSJA 3.0 - Poprawiona logika sumowania statystyk

import React, { useState, useEffect, useCallback } from 'react';
import api from '../../api/axiosConfig';

function LoadingSpinner({ text }) {
    return (
        <div className="text-center text-white py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-gray-400">{text}</p>
        </div>
    );
}

function PlayerCharacterSheet({ campaignId, userId, characterName }) {
    const [characterData, setCharacterData] = useState(null);
    const [inventory, setInventory] = useState([]);
    const [loading, setLoading] = useState(true);

    // Rozszerzona mapa statystyk (obsługuje różne warianty nazw)
    const statMap = {
        'str': 'strength',
        'dex': 'dexterity',
        'con': 'constitution',
        'int': 'intelligence',
        'wis': 'wisdom',
        'cha': 'charisma',
        // Mapowanie "same na siebie" dla bezpieczeństwa
        'strength': 'strength',
        'dexterity': 'dexterity',
        'constitution': 'constitution',
        'intelligence': 'intelligence',
        'wisdom': 'wisdom',
        'charisma': 'charisma'
    };

    // const calculateTotalStats = (baseStats, items) => {
    //     if (!baseStats) return {};
        
    //     // 1. Kopiuj bazowe statystyki, normalizując klucze do małych liter
    //     const total = {};
    //     Object.keys(baseStats).forEach(k => {
    //         const normalizedKey = k.toLowerCase();
    //         total[normalizedKey] = parseInt(baseStats[k]) || 0;
    //     });
        
    //     // console.log("Base Stats:", total); // Debug

    //     // 2. Dodaj modyfikatory z przedmiotów
    //     items.forEach(item => {
    //         if (item.stat_modifiers && typeof item.stat_modifiers === 'object') {
    //             Object.entries(item.stat_modifiers).forEach(([stat, val]) => {
    //                 // Normalizacja klucza statystyki z przedmiotu
    //                 const rawKey = stat.toLowerCase().trim();
    //                 // Próba znalezienia poprawnej nazwy w mapie, jeśli nie ma - użyj surowej
    //                 const key = statMap[rawKey] || rawKey;
                    
    //                 // Upewnij się, że wartość to liczba
    //                 const numVal = parseInt(val);

    //                 // Dodaj tylko jeśli statystyka istnieje w bazowych (żeby nie dodawać śmieci)
    //                 if (total[key] !== undefined && !isNaN(numVal)) {
    //                     // console.log(`Adding modifier from ${item.item_name}: ${key} += ${numVal}`); // Debug
    //                     total[key] += numVal;
    //                 }
    //             });
    //         }
    //     });
        
    //     // console.log("Final Stats:", total); // Debug
    //     return total;
    // };


    // Wewnątrz PlayerCharacterSheet.js

    const calculateTotalStats = (baseStats, items) => {
        console.group("🔍 DEBUGGING STATS"); // Grupowanie logów w konsoli
        
        if (!baseStats) {
            console.log("❌ No base stats found");
            console.groupEnd();
            return {};
        }
        
        // 1. Normalizacja bazowych statystyk
        const total = {};
        Object.keys(baseStats).forEach(k => {
            const normalizedKey = k.toLowerCase();
            total[normalizedKey] = parseInt(baseStats[k]) || 0;
        });
        console.log("📊 Base Stats (Normalized):", JSON.parse(JSON.stringify(total)));

        // 2. Przetwarzanie przedmiotów
        items.forEach(item => {
            console.log(`📦 Processing item: ${item.item_name}`, item.stat_modifiers);

            let modifiers = item.stat_modifiers;

            // 🛡️ ZABEZPIECZENIE: Jeśli przyszło jako string JSON, sparsuj to
            if (typeof modifiers === 'string') {
                console.warn(`⚠️ Modifiers for ${item.item_name} is a STRING, parsing...`);
                try {
                    modifiers = JSON.parse(modifiers);
                } catch (e) {
                    console.error(`❌ Failed to parse JSON for ${item.item_name}:`, e);
                    return;
                }
            }

            if (modifiers && typeof modifiers === 'object') {
                Object.entries(modifiers).forEach(([stat, val]) => {
                    const rawKey = stat.toLowerCase().trim();
                    const key = statMap[rawKey] || rawKey;
                    const numVal = parseInt(val);

                    console.log(`   ➡️ Found mod: ${stat} -> ${val} (Mapped to: ${key})`);

                    if (total[key] !== undefined && !isNaN(numVal)) {
                        const oldVal = total[key];
                        total[key] += numVal;
                        console.log(`      ✅ Updated ${key}: ${oldVal} -> ${total[key]}`);
                    } else {
                        console.warn(`      ⚠️ Skipped ${key} (Not found in base stats or NaN)`);
                    }
                });
            } else {
                console.log("   ❌ No valid modifiers object found");
            }
        });
        
        console.log("🏁 Final Stats:", total);
        console.groupEnd();
        return total;
    };

    const loadData = useCallback(async () => {
        if (!campaignId || !userId) return;
        setLoading(true);
        try {
            const [charRes, invRes] = await Promise.all([
                api.get(`/multiplayer/inventory/campaigns/${campaignId}/player/${userId}/character`),
                api.get(`/multiplayer/inventory/campaigns/${campaignId}/inventory/${userId}`)
            ]);
            
            setCharacterData(charRes.data);
            setInventory(invRes.data.items || []);
        } catch (error) {
            console.error('Error loading data:', error);
        } finally {
            setLoading(false);
        }
    }, [campaignId, userId]);

    useEffect(() => {
        loadData();
        // ✅ NOWOŚĆ: Odświeżaj co 5 sekund, żeby wyłapać zmiany w ekwipunku
        const interval = setInterval(() => {
            loadData();
        }, 5000);

        return () => clearInterval(interval); // Posprzątaj po sobie
    }, [loadData]);

    if (loading) return <div className="bg-gray-800 p-6 h-full"><LoadingSpinner text={`Loading ${characterName}...`} /></div>;
    if (!characterData) return <div className="bg-gray-800 p-6 h-full text-red-400">Failed to load data.</div>;

    const finalAttributes = calculateTotalStats(characterData.attributes, inventory);

    return (
        <div className="bg-gray-800 rounded-lg p-6 h-full overflow-y-auto">
            <h3 className="text-2xl font-bold text-white mb-6">📋 {characterData.name}</h3>
            
            <div className="space-y-6">
                {/* Basic Info */}
                <div className="grid grid-cols-2 gap-4 text-sm">
                    <div><span className="text-gray-400">Race:</span> <span className="text-white">{characterData.race}</span></div>
                    <div><span className="text-gray-400">Class:</span> <span className="text-white">{characterData.class_type}</span></div>
                    <div><span className="text-gray-400">Level:</span> <span className="text-white">{characterData.level}</span></div>
                </div>

                {/* Attributes */}
                <div>
                    <h4 className="text-xl font-bold text-white mb-3">Attributes (Active)</h4>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                        {/* Iterujemy po kluczach zdefiniowanych w mapie, żeby zachować kolejność */}
                        {['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma'].map((attr) => {
                            // Pobierz wartość końcową (jeśli nie ma, weź 10 jako fallback)
                            const value = finalAttributes[attr] !== undefined ? finalAttributes[attr] : 10;
                            
                            // Pobierz wartość bazową (obsługa różnych wielkości liter z backendu)
                            const base = characterData.attributes[attr] || 
                                         characterData.attributes[attr.toUpperCase()] || 
                                         characterData.attributes[attr.charAt(0).toUpperCase() + attr.slice(1)] || 
                                         10;
                                         
                            const diff = value - base;
                            
                            return (
                                <div key={attr} className={`rounded-lg p-3 ${diff !== 0 ? 'bg-blue-900 border border-blue-500' : 'bg-gray-700'}`}>
                                    <p className="text-gray-400 text-xs uppercase font-bold">{attr}</p>
                                    <div className="flex items-baseline gap-2">
                                        <p className="text-white text-2xl font-bold">{value}</p>
                                        {diff !== 0 && (
                                            <span className={`text-xs font-bold ${diff > 0 ? 'text-green-400' : 'text-red-400'}`}>
                                                ({diff > 0 ? '+' : ''}{diff})
                                            </span>
                                        )}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
                
                {/* Skills */}
                <div className="bg-gray-700 p-4 rounded-lg">
                    <h4 className="text-white font-bold mb-2">Skills</h4>
                    <div className="grid grid-cols-2 gap-2 text-sm text-gray-300">
                        {characterData.skills && Object.entries(characterData.skills).map(([k, v]) => (
                            <div key={k} className="flex justify-between">
                                <span className="capitalize">{k.replace(/_/g, ' ')}</span>
                                <span className="text-white font-mono">{v}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default PlayerCharacterSheet;