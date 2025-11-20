// frontend/src/components/multiplayer/GMPlayerManager.js
import React, { useState, useEffect, useCallback } from 'react';
import api from '../../api/axiosConfig';
import PlayerInventoryPanel from './PlayerInventoryPanel';
import ItemEditor from './ItemEditor'; // ✅ ZMIANA: Używamy Editora

function GMPlayerManager({ campaign, isGM, universe = 'star_wars' }) {
    const [players, setPlayers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedPlayer, setSelectedPlayer] = useState(null);
    const [viewMode, setViewMode] = useState(null);
    const [characterData, setCharacterData] = useState(null);

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

    const handleViewInventory = (player) => { setSelectedPlayer(player); setViewMode('inventory'); };
    const handleViewCharacter = async (player) => {
        setSelectedPlayer(player);
        setViewMode('character');
        try {
            const response = await api.get(`/multiplayer/inventory/campaigns/${campaign.id}/player/${player.user_id}/character`);
            setCharacterData(response.data);
        } catch (error) { console.error(error); }
    };
    const handleAddItem = (player) => { setSelectedPlayer(player); setViewMode('add_item'); };
    const handleClose = () => { setSelectedPlayer(null); setViewMode(null); };

    // ✅ ZMIANA: Obsługa zapisu z ItemEditor
    const handleSaveItem = async (itemData) => {
        try {
            await api.post(`/multiplayer/inventory/campaigns/${campaign.id}/inventory`, {
                player_user_id: selectedPlayer.user_id,
                item_name: itemData.name,
                item_category: itemData.category,
                item_image_url: itemData.image_url,
                item_description: itemData.description,
                quantity: 1,
                stat_modifiers: itemData.stat_modifiers // ✅ PRZEKAZUJEMY STATY
            });
            alert(`✅ Added ${itemData.name}!`);
            loadPlayers();
            handleClose(); // Wróć do listy
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
                <button onClick={handleClose} className="text-gray-400 hover:text-white">← Back</button>
                
                {viewMode === 'inventory' && <PlayerInventoryPanel campaignId={campaign.id} userId={selectedPlayer.user_id} isGM={true} />}
                
                {viewMode === 'character' && characterData && (
                    <div className="bg-gray-800 p-6 rounded text-white">
                        <h3 className="text-xl font-bold mb-4">{characterData.name}</h3>
                        {/* Tu można wstawić PlayerCharacterSheet w trybie read-only, ale na razie proste info */}
                        <pre className="bg-gray-900 p-4 rounded">{JSON.stringify(characterData.attributes, null, 2)}</pre>
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
        <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-2xl font-bold text-white mb-6">👑 Players</h3>
            <div className="space-y-2">
                {players.map(p => (
                    <div key={p.user_id} className="bg-gray-700 p-4 rounded flex justify-between items-center">
                        <div>
                            <div className="text-white font-bold">{p.character_name || p.username}</div>
                            <div className="text-gray-400 text-sm">Items: {p.inventory_count}</div>
                        </div>
                        <div className="flex gap-2">
                            <button onClick={() => handleViewInventory(p)} className="bg-blue-600 px-3 py-1 rounded text-sm text-white">🎒 Inv</button>
                            <button onClick={() => handleViewCharacter(p)} className="bg-purple-600 px-3 py-1 rounded text-sm text-white">📋 Char</button>
                            <button onClick={() => handleAddItem(p)} className="bg-green-600 px-3 py-1 rounded text-sm text-white">➕ Add</button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default GMPlayerManager;