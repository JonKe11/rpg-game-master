// frontend/src/components/multiplayer/PlayerInventoryPanel.js

import React, { useState, useEffect, useCallback } from 'react';
import api from '../../api/axiosConfig';

/**
 * Player Inventory Panel
 * 
 * Shows player's inventory with images.
 * Players see their own inventory.
 * GM can see any player's inventory when viewing from GMPlayerManager.
 */
function PlayerInventoryPanel({ 
    campaignId, 
    userId,  // userId of player whose inventory to show
    isGM = false,
    onClose = null  // Optional close button for modal view
}) {
    const [inventory, setInventory] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

   // ✅ Opakuj funkcję w useCallback
    const loadInventory = useCallback(async () => {
        try {
            // Użyj już poprawionego adresu URL z Kroku 1
            const response = await api.get(`/multiplayer/inventory/campaigns/${campaignId}/inventory/${userId}`);
            setInventory(response.data);
            setLoading(false);
        } catch (error) {
            console.error('Error loading inventory:', error);
            setError(error.response?.data?.detail || 'Failed to load inventory');
            setLoading(false);
        }
    }, [campaignId, userId]); // ✅ Dodaj zależności

    useEffect(() => {
        loadInventory();
        
        if (isGM) {
            const interval = setInterval(loadInventory, 5000);
            return () => clearInterval(interval);
        }
    }, [campaignId, userId, isGM, loadInventory]); // ✅ Dodaj loadInventory do zależności

    const getProxiedImageUrl = (originalUrl) => {
        if (!originalUrl) return null;
        
        if (originalUrl.includes('wikia.nocookie.net') || originalUrl.includes('fandom.com')) {
            return `http://localhost:8000/api/v1/wiki/image-proxy?url=${encodeURIComponent(originalUrl)}`;
        }
        
        return originalUrl;
    };

    const getCategoryIcon = (category) => {
        const icons = {
            weapons: '⚔️',
            armor: '🛡️',
            items: '📦',
            vehicles: '🚀',
            droids: '🤖'
        };
        return icons[category] || '📦';
    };

    const getCategoryColor = (category) => {
        const colors = {
            weapons: 'bg-red-600',
            armor: 'bg-blue-600',
            items: 'bg-green-600',
            vehicles: 'bg-purple-600',
            droids: 'bg-yellow-600'
        };
        return colors[category] || 'bg-gray-600';
    };

    if (loading) {
        return (
            <div className="bg-gray-800 rounded-lg p-6">
                <div className="text-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                    <p className="text-gray-400">Loading inventory...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-gray-800 rounded-lg p-6">
                <div className="text-center py-12">
                    <div className="text-red-500 text-6xl mb-4">⚠️</div>
                    <p className="text-red-400">{error}</p>
                </div>
            </div>
        );
    }

    if (!inventory) {
        return null;
    }

    return (
        <div className="bg-gray-800 rounded-lg p-6">
            {/* Header */}
            <div className="flex justify-between items-start mb-6">
                <div>
                    <h3 className="text-2xl font-bold text-white mb-2">
                        🎒 {inventory.character_name || inventory.username}'s Inventory
                    </h3>
                    <div className="flex gap-4 text-sm">
                        <span className="text-gray-400">
                            Total Items: <span className="text-white font-semibold">{inventory.total_items}</span>
                        </span>
                        <span className="text-gray-400">
                            Unique: <span className="text-white font-semibold">{inventory.items.length}</span>
                        </span>
                    </div>
                </div>
                
                {onClose && (
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-white transition"
                    >
                        ✕
                    </button>
                )}
            </div>

            {/* Category Summary */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-2 mb-6">
                {Object.entries(inventory.items_by_category).map(([category, count]) => (
                    <div 
                        key={category}
                        className={`${getCategoryColor(category)} rounded-lg p-3 text-center`}
                    >
                        <div className="text-2xl mb-1">{getCategoryIcon(category)}</div>
                        <div className="text-white font-semibold">{count}</div>
                        <div className="text-xs text-white opacity-75 capitalize">{category}</div>
                    </div>
                ))}
            </div>

            {/* Items Grid */}
            {inventory.items.length === 0 ? (
                <div className="text-center py-12">
                    <div className="text-gray-400 text-6xl mb-4">🎒</div>
                    <p className="text-gray-400 text-lg">Inventory is empty</p>
                    <p className="text-gray-500 text-sm mt-2">
                        {isGM ? 'Use Item Browser to add items' : 'Wait for GM to give you items'}
                    </p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-[500px] overflow-y-auto">
                    {inventory.items.map((item) => (
                        <div
                            key={item.id}
                            className="bg-gray-700 rounded-lg p-4 hover:bg-gray-650 transition"
                        >
                            {/* Item Image */}
                            {item.item_image_url ? (
                                <img
                                    src={getProxiedImageUrl(item.item_image_url)}
                                    alt={item.item_name}
                                    className="w-full h-32 object-cover rounded mb-3"
                                    crossOrigin="anonymous"
                                    onError={(e) => {
                                        e.target.style.display = 'none';
                                        e.target.nextSibling.style.display = 'flex';
                                    }}
                                />
                            ) : null}
                            
                            {/* Fallback icon if no image */}
                            <div 
                                className="w-full h-32 bg-gray-600 rounded mb-3 items-center justify-center"
                                style={{ display: item.item_image_url ? 'none' : 'flex' }}
                            >
                                <span className="text-6xl">
                                    {getCategoryIcon(item.item_category)}
                                </span>
                            </div>

                            {/* Item Info */}
                            <div className="space-y-2">
                                <div className="flex justify-between items-start">
                                    <h4 className="text-white font-semibold flex-1">
                                        {item.item_name}
                                    </h4>
                                    {item.quantity > 1 && (
                                        <span className="bg-blue-600 text-white text-xs px-2 py-1 rounded font-bold">
                                            ×{item.quantity}
                                        </span>
                                    )}
                                </div>

                                <div className="flex items-center gap-2">
                                    <span className={`${getCategoryColor(item.item_category)} text-white text-xs px-2 py-1 rounded capitalize`}>
                                        {item.item_category}
                                    </span>
                                </div>

                                {item.item_description && (
                                    <p className="text-gray-300 text-xs line-clamp-2">
                                        {item.item_description}
                                    </p>
                                )}

                                {item.notes && (
                                    <div className="mt-2 p-2 bg-gray-600 rounded">
                                        <p className="text-yellow-300 text-xs">
                                            📝 GM Note: {item.notes}
                                        </p>
                                    </div>
                                )}

                                <div className="text-gray-400 text-xs pt-2 border-t border-gray-600">
                                    Added: {new Date(item.added_at).toLocaleDateString()}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default PlayerInventoryPanel;