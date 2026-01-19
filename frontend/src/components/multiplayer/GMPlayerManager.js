
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import api from '../../api/axiosConfig';
import PlayerInventoryPanel from './PlayerInventoryPanel';
import ItemEditor from './ItemEditor';


const statMap = {
    'str': 'strength', 'dex': 'dexterity', 'con': 'constitution', 
    'int': 'intelligence', 'wis': 'wisdom', 'cha': 'charisma',
    'strength': 'strength', 'dexterity': 'dexterity', 'constitution': 'constitution', 
    'intelligence': 'intelligence', 'wisdom': 'wisdom', 'charisma': 'charisma'
};

function GMPlayerManager({ campaign, isGM, universe = 'star_wars' }) {
    const [players, setPlayers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedPlayer, setSelectedPlayer] = useState(null);
    const [viewMode, setViewMode] = useState(null);
    
    
    const [characterData, setCharacterData] = useState(null);
    const [playerInventory, setPlayerInventory] = useState([]); 
    
    
    const [isEditingStats, setIsEditingStats] = useState(false);
    const [editStats, setEditStats] = useState({ hp: 0, max_hp: 0, level: 1 });

    const loadPlayers = useCallback(async () => {
        try {
            const response = await api.get(`/multiplayer/inventory/campaigns/${campaign.id}/players`);
            setPlayers(response.data.filter(p => p.role !== 'gm'));
            setLoading(false);
        } catch (error) {
            console.error('Error loading players:', error);
            setLoading(false);
        }
    }, [campaign?.id]);

    useEffect(() => {
        if (isGM && campaign?.id) {
            loadPlayers();
            const interval = setInterval(loadPlayers, 5000);
            return () => clearInterval(interval);
        }
    }, [campaign?.id, isGM, loadPlayers]);

    const finalAttributes = useMemo(() => {
        if (!characterData || !characterData.attributes) return {};
        const total = {};
        Object.keys(characterData.attributes).forEach(k => {
            total[k.toLowerCase()] = parseInt(characterData.attributes[k]) || 0;
        });
        playerInventory.forEach(item => {
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
    }, [characterData, playerInventory]);

    

    const handleViewInventory = (player) => { setSelectedPlayer(player); setViewMode('inventory'); };
    
    const handleViewCharacter = async (player) => {
        setSelectedPlayer(player);
        setViewMode('character');
        setIsEditingStats(false); 
        try {
            const [charRes, invRes] = await Promise.all([
                api.get(`/multiplayer/inventory/campaigns/${campaign.id}/player/${player.user_id}/character`),
                api.get(`/multiplayer/inventory/campaigns/${campaign.id}/inventory/${player.user_id}`)
            ]);
            
            setCharacterData(charRes.data);
            setPlayerInventory(invRes.data.items || []);
            
            
            setEditStats({
                hp: charRes.data.hp,
                max_hp: charRes.data.max_hp,
                level: charRes.data.level
            });
        } catch (error) { console.error(error); }
    };
    
    
    const handleSaveStats = async () => {
        if (!characterData) return;
        try {
            await api.patch(`/characters/${characterData.id}/stats`, editStats);
            alert("✅ Stats updated!");
            setIsEditingStats(false);
            
            handleViewCharacter(selectedPlayer);
        } catch (error) {
            console.error("Failed to update stats:", error);
            alert("Failed to update stats.");
        }
    };

    const handleAddItem = (player) => { setSelectedPlayer(player); setViewMode('add_item'); };
    
    const handleClose = () => { 
        setSelectedPlayer(null); 
        setViewMode(null); 
        setCharacterData(null);
        setPlayerInventory([]);
    };

    const handleSaveItem = async (itemData) => {
        try {
            await api.post(`/multiplayer/inventory/campaigns/${campaign.id}/inventory`, {
                player_user_id: selectedPlayer.user_id,
                item_name: itemData.name,
                item_category: itemData.category,
                item_image_url: itemData.image_url,
                item_description: itemData.description,
                quantity: 1,
                item_rarity: itemData.rarity,
                stat_modifiers: itemData.stat_modifiers,
                slot: itemData.slot,              
                dice_config: itemData.dice_config, 
                armor_value: itemData.armor_value
            });
            alert(`✅ Added ${itemData.name}!`);
            loadPlayers();
            handleClose(); 
        } catch (error) {
            console.error('Error adding item:', error);
            alert('Failed to add item');
        }
    };

    if (!isGM) return null;
    if (loading) return <div className="text-white text-center p-6">Loading players...</div>;

    if (selectedPlayer && viewMode) {
        return (
            <div className="space-y-4">
                <button onClick={handleClose} className="text-gray-400 hover:text-white flex items-center gap-2">
                    <span>←</span> Back to Player List
                </button>
                
                {viewMode === 'inventory' && <PlayerInventoryPanel campaignId={campaign.id} userId={selectedPlayer.user_id} isGM={true} />}
                
                {viewMode === 'character' && characterData && (
                    <div className="bg-gray-800 p-6 rounded-lg text-white border border-gray-700 shadow-xl max-h-[80vh] overflow-y-auto custom-scrollbar">
                        
                        {/* Header */}
                        <div className="flex justify-between items-start mb-6 border-b border-gray-700 pb-4">
                            <div>
                                <h3 className="text-2xl font-bold text-white">{characterData.name}</h3>
                                <p className="text-sm text-gray-400">Lvl {characterData.level} {characterData.class_type}</p>
                            </div>
                            
                            <div className="text-right">
                                <span className={`text-2xl font-bold ${characterData.hp < characterData.max_hp * 0.3 ? 'text-red-500' : 'text-green-400'}`}>
                                    {characterData.hp}
                                </span>
                                <span className="text-gray-500"> / {characterData.max_hp} HP</span>
                                
                                <button 
                                    onClick={() => setIsEditingStats(!isEditingStats)}
                                    className="block ml-auto mt-2 text-xs text-blue-400 hover:text-blue-300 underline"
                                >
                                    {isEditingStats ? 'Cancel Edit' : '✏️ Edit Stats'}
                                </button>
                            </div>
                        </div>

                        {/* ✅ EDYCJA STATYSTYK (FORMULARZ) */}
                        {isEditingStats && (
                            <div className="bg-blue-900/30 border border-blue-600 p-4 rounded-lg mb-6 animate-fadeIn">
                                <h4 className="text-blue-300 font-bold mb-3 text-sm">🔧 Edit Character Stats</h4>
                                <div className="grid grid-cols-3 gap-4 mb-4">
                                    <div>
                                        <label className="block text-xs text-gray-400 mb-1">Current HP</label>
                                        <input 
                                            type="number" 
                                            className="w-full bg-gray-900 border border-gray-600 rounded p-2 text-white"
                                            value={editStats.hp}
                                            onChange={e => setEditStats({...editStats, hp: parseInt(e.target.value)})}
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-xs text-gray-400 mb-1">Max HP</label>
                                        <input 
                                            type="number" 
                                            className="w-full bg-gray-900 border border-gray-600 rounded p-2 text-white"
                                            value={editStats.max_hp}
                                            onChange={e => setEditStats({...editStats, max_hp: parseInt(e.target.value)})}
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-xs text-gray-400 mb-1">Level</label>
                                        <input 
                                            type="number" 
                                            className="w-full bg-gray-900 border border-gray-600 rounded p-2 text-white"
                                            value={editStats.level}
                                            onChange={e => setEditStats({...editStats, level: parseInt(e.target.value)})}
                                        />
                                    </div>
                                </div>
                                <button 
                                    onClick={handleSaveStats}
                                    className="w-full bg-green-600 hover:bg-green-500 py-2 rounded font-bold text-white transition"
                                >
                                    💾 Save Changes
                                </button>
                            </div>
                        )}

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                            {/* Attributes */}
                            <div className="bg-gray-900/50 p-4 rounded border border-gray-700">
                                <h4 className="font-bold text-gray-400 mb-3 text-xs uppercase tracking-wider">Attributes (Current)</h4>
                                <div className="space-y-2">
                                    {['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma'].map((attr) => {
                                        const val = finalAttributes[attr] !== undefined ? finalAttributes[attr] : 10;
                                        const base = parseInt(characterData.attributes[attr] || 10);
                                        const diff = val - base;
                                        
                                        return (
                                            <div key={attr} className="flex justify-between items-center text-sm border-b border-gray-700/50 pb-1 last:border-0">
                                                <span className="capitalize text-gray-300">{attr}</span>
                                                <div className="flex gap-2">
                                                    <span className="font-bold text-white">{val}</span>
                                                    {diff !== 0 && (
                                                        <span className={`text-xs ${diff > 0 ? 'text-green-400' : 'text-red-400'}`}>
                                                            ({diff > 0 ? '+' : ''}{diff})
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>

                            {/* Info */}
                            <div className="bg-gray-900/50 p-4 rounded border border-gray-700">
                                <h4 className="font-bold text-gray-400 mb-3 text-xs uppercase tracking-wider">Details</h4>
                                <div className="space-y-2 text-sm">
                                    <div className="flex justify-between"><span className="text-gray-400">Race:</span> <span>{characterData.race}</span></div>
                                    <div className="flex justify-between"><span className="text-gray-400">Gender:</span> <span>{characterData.gender || '-'}</span></div>
                                    <div className="flex justify-between"><span className="text-gray-400">Age:</span> <span>{characterData.age || '?'}</span></div>
                                    <div className="flex justify-between"><span className="text-gray-400">Homeworld:</span> <span>{characterData.homeworld || '-'}</span></div>
                                </div>
                            </div>
                        </div>

                        {characterData.backstory && (
                            <div className="bg-gray-900/30 p-4 rounded border border-gray-700">
                                <h4 className="font-bold text-blue-400 mb-3 text-xs uppercase tracking-wider flex items-center gap-2">
                                    📜 Biography
                                    <span className="text-[9px] bg-blue-900 text-blue-200 px-1.5 rounded border border-blue-700">AI Generated</span>
                                </h4>
                                <div className="text-gray-300 text-sm whitespace-pre-wrap leading-relaxed italic">
                                    {characterData.backstory}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {viewMode === 'add_item' && (
                    <ItemEditor 
                        universe={universe}
                        onSave={handleSaveItem}
                        onCancel={handleClose}
                    />
                )}
            </div>
        );
    }

    return (
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                👑 Player Management
            </h3>
            <div className="space-y-2">
                {players.map(p => (
                    <div key={p.user_id} className="bg-gray-700/50 p-3 rounded flex justify-between items-center hover:bg-gray-700 transition">
                        <div className="flex items-center gap-3">
                            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center font-bold text-sm">
                                {p.username[0].toUpperCase()}
                            </div>
                            <div>
                                <div className="text-white font-bold text-sm">{p.character_name || "Unknown"}</div>
                                <div className="text-gray-400 text-xs">@{p.username} • {p.inventory_count} items</div>
                            </div>
                        </div>
                        <div className="flex gap-2">
                            <button 
                                onClick={() => handleViewInventory(p)} 
                                className="bg-blue-600 hover:bg-blue-500 px-3 py-1.5 rounded text-xs font-bold text-white transition"
                                title="View Inventory"
                            >
                                🎒 Inv
                            </button>
                            <button 
                                onClick={() => handleViewCharacter(p)} 
                                className="bg-purple-600 hover:bg-purple-500 px-3 py-1.5 rounded text-xs font-bold text-white transition"
                                title="View Character Sheet"
                            >
                                📋 Char
                            </button>
                            <button 
                                onClick={() => handleAddItem(p)} 
                                className="bg-green-600 hover:bg-green-500 px-3 py-1.5 rounded text-xs font-bold text-white transition"
                                title="Give Item"
                            >
                                🎁 Give
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default GMPlayerManager;