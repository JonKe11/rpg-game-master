// frontend/src/components/multiplayer/PlayerCharacterSheet.js
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import api from '../../api/axiosConfig';

function LoadingSpinner({ text }) {
    return (
        <div className="text-center text-white py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-gray-400">{text}</p>
        </div>
    );
}

function EquipmentSlot({ label, item, icon }) {
    const getProxiedImageUrl = (originalUrl) => {
        if (!originalUrl) return null;
        if (originalUrl.startsWith('data:image')) return originalUrl;
        if (originalUrl.includes('wikia.nocookie.net') || originalUrl.includes('fandom.com')) {
            return `http://localhost:8000/api/v1/wiki/image-proxy?url=${encodeURIComponent(originalUrl)}`;
        }
        return originalUrl;
    };

    return (
        <div className="bg-gray-900 rounded p-2 border border-gray-700 flex gap-3 items-center h-16 relative overflow-hidden group">
            <div className="w-12 h-12 bg-black rounded flex-shrink-0 flex items-center justify-center overflow-hidden border border-gray-600">
                {item?.item_image_url ? (
                    <img src={getProxiedImageUrl(item.item_image_url)} className="w-full h-full object-contain" alt={item.item_name} crossOrigin="anonymous" />
                ) : (
                    <span className="text-2xl opacity-50">{icon}</span>
                )}
            </div>
            <div className="min-w-0 flex-1 z-10">
                <p className="text-[10px] text-gray-500 uppercase font-bold tracking-wider">{label}</p>
                <p className={`text-xs truncate font-semibold ${item ? 'text-white' : 'text-gray-600 italic'}`}>
                    {item ? item.item_name : "Empty"}
                </p>
            </div>
            {item && <div className={`absolute right-0 top-0 bottom-0 w-1 ${
                item.item_rarity === 'legendary' ? 'bg-orange-500' : 
                item.item_rarity === 'epic' ? 'bg-purple-500' : 
                item.item_rarity === 'rare' ? 'bg-blue-500' : 
                item.item_rarity === 'uncommon' ? 'bg-green-500' : 'bg-gray-600'
            }`}></div>}
        </div>
    );
}

function PlayerCharacterSheet({ 
    campaignId, 
    userId, 
    characterName,
    onStatsUpdate
}) {
    const [characterData, setCharacterData] = useState(null);
    const [inventory, setInventory] = useState([]);
    const [loading, setLoading] = useState(true);

    const statMap = {
        'str': 'strength', 'dex': 'dexterity', 'con': 'constitution', 
        'int': 'intelligence', 'wis': 'wisdom', 'cha': 'charisma',
        'strength': 'strength', 'dexterity': 'dexterity', 'constitution': 'constitution', 
        'intelligence': 'intelligence', 'wisdom': 'wisdom', 'charisma': 'charisma'
    };

    const calculateTotalStats = (baseStats, items) => {
        if (!baseStats) return {};
        
        const total = {};
        Object.keys(baseStats).forEach(k => {
            total[k.toLowerCase()] = parseInt(baseStats[k]) || 0;
        });

        items.forEach(item => {
            if (!item.is_equipped) return;

            let modifiers = item.stat_modifiers;
            if (typeof modifiers === 'string') {
                try { modifiers = JSON.parse(modifiers); } catch (e) {}
            }

            if (modifiers && typeof modifiers === 'object') {
                Object.entries(modifiers).forEach(([stat, val]) => {
                    const rawKey = stat.toLowerCase().trim();
                    const key = statMap[rawKey] || rawKey;
                    const numVal = parseInt(val);
                    if (total[key] !== undefined && !isNaN(numVal)) {
                        total[key] += numVal;
                    }
                });
            }
        });
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
        const interval = setInterval(loadData, 5000); 
        return () => clearInterval(interval);
    }, [loadData]);

    const finalAttributes = useMemo(() => {
        if (!characterData) return {};
        return calculateTotalStats(characterData.attributes, inventory);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [characterData, inventory]); 

    useEffect(() => {
        if (onStatsUpdate && Object.keys(finalAttributes).length > 0) {
            onStatsUpdate(finalAttributes);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [JSON.stringify(finalAttributes), onStatsUpdate]);

    if (loading) return <div className="bg-gray-800 p-6 h-full"><LoadingSpinner text={`Loading ${characterName}...`} /></div>;
    if (!characterData) return <div className="bg-gray-800 p-6 h-full text-red-400">Failed to load data.</div>;

    const equippedWeapon = inventory.find(i => i.is_equipped && i.slot === 'weapon');
    const equippedArmor = inventory.find(i => i.is_equipped && i.slot === 'armor');
    const equippedAccessories = inventory.filter(i => i.is_equipped && i.slot === 'accessory');

    return (
        <div className="bg-gray-800 rounded-lg p-6 h-full overflow-y-auto custom-scrollbar">
            
            {/* Header: Name & HP */}
            <div className="flex justify-between items-start mb-6 border-b border-gray-700 pb-4">
                <div>
                    <h3 className="text-2xl font-bold text-white">{characterData.name}</h3>
                    <p className="text-sm text-gray-400">Lvl {characterData.level} {characterData.class_type}</p>
                    <p className="text-xs text-gray-500">{characterData.race}</p>
                </div>
                
                <div className="text-right bg-gray-900 px-4 py-2 rounded-lg border border-gray-700">
                    <p className="text-[10px] text-gray-400 uppercase font-bold mb-1 tracking-wider">Health Points</p>
                    <div className="flex items-baseline justify-end gap-2">
                        <span className={`text-2xl font-bold ${characterData.hp < characterData.max_hp * 0.3 ? 'text-red-500 animate-pulse' : 'text-green-400'}`}>
                            {characterData.hp}
                        </span>
                        <span className="text-sm text-gray-500 font-bold">/ {characterData.max_hp}</span>
                    </div>
                    <div className="w-24 h-1.5 bg-gray-700 rounded-full mt-1 overflow-hidden">
                        <div 
                            className="h-full bg-green-500 transition-all duration-500" 
                            style={{ width: `${Math.min(100, Math.max(0, (characterData.hp / characterData.max_hp) * 100))}%` }}
                        ></div>
                    </div>
                </div>
            </div>

            {/* Equipment Grid */}
            <h4 className="text-white font-bold mb-3 text-sm uppercase tracking-wider flex items-center gap-2">
                🛡️ Equipment
            </h4>
            <div className="grid grid-cols-2 gap-3 mb-6">
                <EquipmentSlot label="Main Weapon" item={equippedWeapon} icon="⚔️" />
                <EquipmentSlot label="Armor / Suit" item={equippedArmor} icon="🛡️" />
                {[0, 1, 2, 3].map(idx => (
                    <EquipmentSlot 
                        key={idx} 
                        label={`Accessory ${idx+1}`} 
                        item={equippedAccessories[idx]} 
                        icon="💍" 
                    />
                ))}
            </div>

            {/* Attributes Grid */}
            <h4 className="text-white font-bold mb-3 text-sm uppercase tracking-wider">Attributes</h4>
            <div className="grid grid-cols-3 gap-2 mb-6">
                {['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma'].map((attr) => {
                    const value = finalAttributes[attr] !== undefined ? finalAttributes[attr] : 10;
                    const base = characterData.attributes[attr] || 10;
                    const mod = Math.floor((value - 10) / 2);
                    const diff = value - base;
                    
                    return (
                        <div key={attr} className={`rounded p-2 text-center border ${diff !== 0 ? 'bg-blue-900/40 border-blue-500/50' : 'bg-gray-700/50 border-transparent'}`}>
                            <p className="text-gray-400 text-[9px] uppercase font-bold tracking-widest mb-1">{attr.slice(0,3)}</p>
                            <p className="text-white text-xl font-bold leading-none">{value}</p>
                            <p className={`text-[10px] font-bold mt-1 ${mod >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                {mod >= 0 ? '+' : ''}{mod}
                            </p>
                        </div>
                    );
                })}
            </div>
            
            {/* Skills List (Compact) */}
            <div className="bg-gray-700/30 p-3 rounded-lg border border-gray-700 mb-6">
                <h4 className="text-gray-400 font-bold mb-2 text-xs uppercase">Skills</h4>
                <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                    {characterData.skills && Object.entries(characterData.skills).map(([k, v]) => (
                        <div key={k} className="flex justify-between items-center border-b border-gray-700/50 pb-1 last:border-0">
                            <span className="text-gray-300 capitalize">{k.replace(/_/g, ' ')}</span>
                            <span className="text-white font-mono font-bold">{v}</span>
                        </div>
                    ))}
                </div>
            </div>

            {/* ✅ NOWOŚĆ: Sekcja Biografii */}
            {characterData.backstory && (
                <div className="bg-gray-900/30 p-4 rounded-lg border border-gray-700">
                     <h4 className="text-blue-400 font-bold mb-3 text-xs uppercase tracking-wider flex items-center gap-2">
                        📜 Biography
                        <span className="text-[9px] bg-blue-900 text-blue-200 px-1.5 rounded border border-blue-700">AI Generated</span>
                    </h4>
                    <div className="text-gray-300 text-sm whitespace-pre-wrap leading-relaxed italic">
                        {characterData.backstory}
                    </div>
                </div>
            )}
        </div>
    );
}

export default PlayerCharacterSheet;