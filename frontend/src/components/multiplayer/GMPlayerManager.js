// frontend/src/components/multiplayer/GMPlayerManager.js

import React, { useState, useEffect, useCallback } from 'react';
import api from '../../api/axiosConfig';
import PlayerInventoryPanel from './PlayerInventoryPanel';
import ItemBrowser from './ItemBrowser';

/**
 * GM Player Manager
 * 
 * Allows GM to:
 * - View list of players in campaign
 * - View each player's inventory
 * - View each player's character sheet
 * - Add items to player's inventory via Item Browser
 */
function GMPlayerManager({ 
    campaign, 
    isGM,
    universe = 'star_wars'
}) {
    const [players, setPlayers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedPlayer, setSelectedPlayer] = useState(null);
    const [viewMode, setViewMode] = useState(null); // 'inventory', 'character', 'add_item'
    const [characterData, setCharacterData] = useState(null);

const loadPlayers = useCallback(async () => {
        try {
            // Użyj już poprawionego adresu URL z Kroku 1
            const response = await api.get(`/multiplayer/inventory/campaigns/${campaign.id}/players`);
            const playersOnly = response.data.filter(p => p.role !== 'gm');
            setPlayers(playersOnly);
            setLoading(false);
        } catch (error) {
            console.error('Error loading players:', error);
            setLoading(false);
        }
    }, [campaign?.id]); // ✅ Dodaj zależność

    useEffect(() => {
        if (isGM && campaign?.id) {
            loadPlayers();
            
            const interval = setInterval(loadPlayers, 5000);
            return () => clearInterval(interval);
        }
    }, [campaign?.id, isGM, loadPlayers]); // ✅ Dodaj loadPlayers do zależności

    

    const handleViewInventory = (player) => {
        setSelectedPlayer(player);
        setViewMode('inventory');
        setCharacterData(null);
    };

    const handleViewCharacter = async (player) => {
        setSelectedPlayer(player);
        setViewMode('character');
        
        try {
            const response = await api.get(`/multiplayer/inventory/campaigns/${campaign.id}/player/${player.user_id}/character`);
            setCharacterData(response.data);
        } catch (error) {
            console.error('Error loading character:', error);
            alert(error.response?.data?.detail || 'Failed to load character');
        }
    };

    const handleAddItem = (player) => {
        setSelectedPlayer(player);
        setViewMode('add_item');
        setCharacterData(null);
    };

    const handleItemSelect = async (item) => {
        if (!selectedPlayer) {
            alert('Please select a player first');
            return;
        }

        try {
            await api.post(`/multiplayer/inventory/campaigns/${campaign.id}/inventory`, {
                player_user_id: selectedPlayer.user_id,
                item_name: item.name,
                item_category: item.category,
                item_image_url: item.image_url,
                item_description: item.description,
                quantity: 1
            });

            alert(`✅ Added ${item.name} to ${selectedPlayer.character_name || selectedPlayer.username}'s inventory!`);
            
            // Refresh players to update inventory count
            loadPlayers();
        } catch (error) {
            console.error('Error adding item:', error);
            alert(error.response?.data?.detail || 'Failed to add item');
        }
    };

    const handleClose = () => {
        setSelectedPlayer(null);
        setViewMode(null);
        setCharacterData(null);
    };

    if (!isGM) {
        return null;
    }

    if (loading) {
        return (
            <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-2xl font-bold text-white mb-4">👑 Player Management (GM)</h3>
                <div className="text-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                    <p className="text-gray-400">Loading players...</p>
                </div>
            </div>
        );
    }

    // If viewing specific player's details
    if (selectedPlayer && viewMode) {
        return (
            <div className="space-y-4">
                {/* Back button */}
                <button
                    onClick={handleClose}
                    className="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded-lg transition"
                >
                    ← Back to Player List
                </button>

                {/* Content based on view mode */}
                {viewMode === 'inventory' && (
                    <PlayerInventoryPanel
                        campaignId={campaign.id}
                        userId={selectedPlayer.user_id}
                        isGM={true}
                    />
                )}

                {viewMode === 'character' && (
                    <div className="bg-gray-800 rounded-lg p-6">
                        <h3 className="text-2xl font-bold text-white mb-6">
                            📋 {selectedPlayer.character_name || selectedPlayer.username}'s Character
                        </h3>
                        
                        {characterData ? (
                            <div className="space-y-6">
                                {/* Basic Info */}
                                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                                    <div>
                                        <p className="text-gray-400 text-sm">Name</p>
                                        <p className="text-white font-semibold">{characterData.name}</p>
                                    </div>
                                    <div>
                                        <p className="text-gray-400 text-sm">Race</p>
                                        <p className="text-white font-semibold">{characterData.race}</p>
                                    </div>
                                    <div>
                                        <p className="text-gray-400 text-sm">Class</p>
                                        <p className="text-white font-semibold">{characterData.class_type}</p>
                                    </div>
                                    <div>
                                        <p className="text-gray-400 text-sm">Level</p>
                                        <p className="text-white font-semibold">{characterData.level}</p>
                                    </div>
                                    <div>
                                        <p className="text-gray-400 text-sm">Homeworld</p>
                                        <p className="text-white font-semibold">{characterData.homeworld || 'Unknown'}</p>
                                    </div>
                                    <div>
                                        <p className="text-gray-400 text-sm">Universe</p>
                                        <p className="text-white font-semibold capitalize">{characterData.universe.replace('_', ' ')}</p>
                                    </div>
                                </div>

                                {/* Attributes */}
                                <div>
                                    <h4 className="text-xl font-bold text-white mb-3">Attributes</h4>
                                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                                        {Object.entries(characterData.attributes).map(([attr, value]) => (
                                            <div key={attr} className="bg-gray-700 rounded-lg p-3">
                                                <p className="text-gray-400 text-sm capitalize">{attr}</p>
                                                <p className="text-white text-2xl font-bold">{value}</p>
                                                <p className="text-gray-400 text-xs">
                                                    Modifier: {value >= 10 ? '+' : ''}{Math.floor((value - 10) / 2)}
                                                </p>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Skills */}
                                <div>
                                    <h4 className="text-xl font-bold text-white mb-3">Skills</h4>
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                        {Object.entries(characterData.skills).map(([skill, value]) => (
                                            <div key={skill} className="bg-gray-700 rounded-lg p-3">
                                                <p className="text-gray-400 text-sm capitalize">
                                                    {skill.replace(/_/g, ' ')}
                                                </p>
                                                <p className="text-white text-xl font-bold">{value}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Background */}
                                {characterData.background && (
                                    <div>
                                        <h4 className="text-xl font-bold text-white mb-3">Background</h4>
                                        <div className="bg-gray-700 rounded-lg p-4">
                                            <p className="text-gray-300">{characterData.background}</p>
                                        </div>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="text-center py-12">
                                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                                <p className="text-gray-400">Loading character...</p>
                            </div>
                        )}
                    </div>
                )}

                {viewMode === 'add_item' && (
                    <div>
                        <div className="bg-blue-900 border border-blue-500 rounded-lg p-4 mb-4">
                            <p className="text-white font-semibold">
                                🎁 Adding item to: {selectedPlayer.character_name || selectedPlayer.username}
                            </p>
                            <p className="text-blue-200 text-sm">
                                Click any item below to add it to their inventory
                            </p>
                        </div>
                        
                        <ItemBrowser
                            onItemSelect={handleItemSelect}
                            universe={universe}
                            isGM={true}
                        />
                    </div>
                )}
            </div>
        );
    }

    // Main player list view
    return (
        <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-2xl font-bold text-white mb-6">👑 Player Management (GM)</h3>

            {players.length === 0 ? (
                <div className="text-center py-12">
                    <div className="text-gray-400 text-6xl mb-4">👥</div>
                    <p className="text-gray-400">No players in campaign yet</p>
                </div>
            ) : (
                <div className="space-y-3">
                    {players.map((player) => (
                        <div
                            key={player.user_id}
                            className="bg-gray-700 rounded-lg p-4 hover:bg-gray-650 transition"
                        >
                            <div className="flex justify-between items-center">
                                <div className="flex-1">
                                    <h4 className="text-white font-semibold text-lg">
                                        {player.character_name || player.username}
                                    </h4>
                                    <div className="flex gap-4 text-sm mt-1">
                                        <span className="text-gray-400">
                                            Player: <span className="text-white">{player.username}</span>
                                        </span>
                                        <span className="text-gray-400">
                                            Items: <span className="text-white font-semibold">{player.inventory_count}</span>
                                        </span>
                                        <span className={`${player.ready ? 'text-green-400' : 'text-yellow-400'}`}>
                                            {player.ready ? '✓ Ready' : '⧗ Not Ready'}
                                        </span>
                                    </div>
                                </div>

                                <div className="flex gap-2">
                                    <button
                                        onClick={() => handleViewInventory(player)}
                                        className="bg-blue-600 hover:bg-blue-700 px-3 py-2 rounded-lg text-sm transition"
                                        title="View Inventory"
                                    >
                                        🎒 Inventory
                                    </button>
                                    <button
                                        onClick={() => handleViewCharacter(player)}
                                        className="bg-purple-600 hover:bg-purple-700 px-3 py-2 rounded-lg text-sm transition"
                                        title="View Character Sheet"
                                    >
                                        📋 Character
                                    </button>
                                    <button
                                        onClick={() => handleAddItem(player)}
                                        className="bg-green-600 hover:bg-green-700 px-3 py-2 rounded-lg text-sm transition"
                                        title="Add Item"
                                    >
                                        ➕ Add Item
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default GMPlayerManager;