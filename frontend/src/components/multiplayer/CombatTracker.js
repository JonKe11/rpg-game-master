// frontend/src/components/multiplayer/CombatTracker.js
import React, { useState, useEffect } from 'react';
import api from '../../api/axiosConfig';

function CombatTracker({ campaignId, onSendEvent }) {
    // Lista aktywnych uczestników walki
    const [combatants, setCombatants] = useState([]);
    
    // Lista dostępnych kandydatów (Gracze + NPC z bazy)
    const [candidates, setCandidates] = useState([]);
    
    // Zbiór zaznaczonych ID z listy kandydatów
    const [selectedCandidateIds, setSelectedCandidateIds] = useState(new Set());

    const [round] = useState(1); 
    const [loading, setLoading] = useState(true);

    // ✅ AUTOMATYCZNE ŁADOWANIE NA STARCIE
    useEffect(() => {
        fetchAllPotentialCombatants();
        // eslint-disable-next-line
    }, [campaignId]);

    // Funkcja pobierająca Graczy (z fixem HP) oraz NPC
    const fetchAllPotentialCombatants = async () => {
        setLoading(true);
        try {
            const allCandidates = [];

            // 1. POBIERZ GRACZY (Z PEŁNYMI STATYSTYKAMI)
            const playersRes = await api.get(`/multiplayer/inventory/campaigns/${campaignId}/players`);
            const players = playersRes.data.filter(p => p.role !== 'gm');

            const playersWithStats = await Promise.all(players.map(async (p) => {
                try {
                    // Pobieramy kartę, żeby mieć aktualne HP/AC
                    const charRes = await api.get(`/multiplayer/inventory/campaigns/${campaignId}/player/${p.user_id}/character`);
                    const char = charRes.data;
                    
                    return {
                        id: `player_${char.id}`, // Unikalne ID dla listy
                        realId: char.id,         // Prawdziwe ID do bazy
                        userId: p.user_id,
                        name: char.name,
                        type: 'player',
                        hp: char.hp,
                        max_hp: char.max_hp,
                        ac: char.armor_class,
                        dr: char.damage_reduction || 0,
                        initiative: 0,
                        image_url: null 
                    };
                } catch (e) {
                    console.error(`Error loading stats for ${p.username}`, e);
                    return null;
                }
            }));
            
            allCandidates.push(...playersWithStats.filter(Boolean));

            // 2. POBIERZ NPC
            const campaignRes = await api.get(`/multiplayer/campaigns/${campaignId}`);
            if (campaignRes.data.spawned_npcs) {
                const npcs = campaignRes.data.spawned_npcs.map(npc => ({
                    id: npc.id,
                    realId: npc.id,
                    name: npc.name,
                    type: 'npc',
                    hp: npc.hp || 50,
                    max_hp: npc.hp || 50,
                    ac: npc.armor_class || 10,
                    dr: npc.damage_reduction || 0,
                    initiative: 0,
                    image_url: npc.image_url,
                    damage_dice: npc.damage_dice || '1d6'
                }));
                allCandidates.push(...npcs);
            }

            setCandidates(allCandidates);

        } catch (error) {
            console.error("Error loading combatants:", error);
        } finally {
            setLoading(false);
        }
    };

    // Obsługa zaznaczania checkboxów
    const toggleCandidate = (candidateId) => {
        const newSet = new Set(selectedCandidateIds);
        if (newSet.has(candidateId)) {
            newSet.delete(candidateId);
        } else {
            newSet.add(candidateId);
        }
        setSelectedCandidateIds(newSet);
    };

    // Dodanie zaznaczonych do aktywnej walki
    const handleAddSelected = () => {
        const toAdd = candidates.filter(c => selectedCandidateIds.has(c.id));
        
        // Filtrujemy, żeby nie dodać duplikatów, jeśli już są w walce
        setCombatants(prev => {
            const existingIds = new Set(prev.map(c => c.id));
            const uniqueToAdd = toAdd.filter(c => !existingIds.has(c.id)).map(c => ({
                ...c,
                active: false // Reset stanu aktywności przy dodawaniu
            }));
            return [...prev, ...uniqueToAdd];
        });

        // Opcjonalnie: Wyczyść zaznaczenie
        setSelectedCandidateIds(new Set());
    };

    const handleStartCombat = () => {
        if (combatants.length === 0) return alert("Add combatants to the tracker first!");
        
        const combatData = {
            round: round,
            turn_text: "Combat Started! Roll Initiative!",
            combatants: combatants
        };

        onSendEvent('combat_update', JSON.stringify(combatData));
    };

    const handleRemove = (index) => {
        setCombatants(prev => prev.filter((_, i) => i !== index));
    };

    return (
        <div className="bg-gray-800 rounded-lg p-4 h-full flex flex-col">
            <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                ⚔️ Combat Tracker
            </h3>

            {/* --- SEKCJA 1: WYBÓR UCZESTNIKÓW (Staging Area) --- */}
            <div className="bg-gray-900/50 p-3 rounded-lg border border-gray-700 mb-4 max-h-40 overflow-y-auto custom-scrollbar">
                <h4 className="text-xs font-bold text-gray-400 uppercase mb-2 flex justify-between">
                    <span>Available Participants</span>
                    <button onClick={fetchAllPotentialCombatants} className="text-blue-400 hover:text-white">↻ Refresh</button>
                </h4>
                
                {loading ? (
                    <p className="text-gray-500 text-xs text-center">Loading stats...</p>
                ) : candidates.length === 0 ? (
                    <p className="text-gray-500 text-xs text-center">No players or NPCs found.</p>
                ) : (
                    <div className="space-y-1">
                        {candidates.map(c => (
                            <label key={c.id} className="flex items-center gap-2 p-2 hover:bg-gray-700 rounded cursor-pointer transition">
                                <input 
                                    type="checkbox" 
                                    checked={selectedCandidateIds.has(c.id)}
                                    onChange={() => toggleCandidate(c.id)}
                                    className="w-4 h-4 rounded border-gray-500 text-blue-600 bg-gray-800 focus:ring-blue-500"
                                />
                                <div className="flex-1">
                                    <div className={`text-sm font-bold ${c.type === 'player' ? 'text-blue-300' : 'text-red-300'}`}>
                                        {c.name}
                                    </div>
                                    <div className="text-[10px] text-gray-500">
                                        HP: {c.hp}/{c.max_hp} • AC: {c.ac}
                                    </div>
                                </div>
                            </label>
                        ))}
                    </div>
                )}
            </div>

            {/* Przycisk dodawania */}
            <button 
                onClick={handleAddSelected}
                disabled={selectedCandidateIds.size === 0}
                className="w-full bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 text-white py-2 rounded font-bold text-sm mb-6 transition"
            >
                Add Selected ({selectedCandidateIds.size}) to Tracker ↓
            </button>

            {/* --- SEKCJA 2: AKTYWNA LISTA (Tracker) --- */}
            <div className="flex-1 overflow-y-auto space-y-2 mb-4 custom-scrollbar border-t border-gray-700 pt-4">
                <h4 className="text-xs font-bold text-gray-400 uppercase mb-2">Active Combatants</h4>
                
                {combatants.length === 0 && <p className="text-gray-600 text-center text-xs italic">Tracker is empty.</p>}
                
                {combatants.map((c, i) => (
                    <div key={i} className={`flex justify-between items-center p-2 rounded border ${c.type === 'player' ? 'bg-blue-900/20 border-blue-800' : 'bg-red-900/20 border-red-800'}`}>
                        <div>
                            <div className="font-bold text-white text-sm">{c.name}</div>
                            <div className="text-xs text-gray-400">
                                HP: {c.hp}/{c.max_hp} • AC: {c.ac}
                            </div>
                        </div>
                        <button onClick={() => handleRemove(i)} className="text-red-400 hover:text-red-300 px-2">×</button>
                    </div>
                ))}
            </div>

            <button 
                onClick={handleStartCombat}
                disabled={combatants.length === 0}
                className="w-full bg-red-600 hover:bg-red-500 disabled:bg-gray-700 text-white py-3 rounded-lg font-bold shadow-lg transition mt-auto"
            >
                ⚡ START COMBAT EVENT
            </button>
        </div>
    );
}

export default CombatTracker;