// frontend/src/components/multiplayer/PlayerInventoryPanel.js
import React, { useState, useEffect, useCallback } from 'react';
import api from '../../api/axiosConfig';

/**
 * Player Inventory Panel (Compact Version)
 */

const RARITY_STYLES = {
    common: { border: 'border-gray-600', text: 'text-gray-300', bg: 'bg-gray-700/50', badge: 'bg-gray-600 text-gray-200' },
    uncommon: { border: 'border-green-600', text: 'text-green-400', bg: 'bg-green-900/20', badge: 'bg-green-900 text-green-300 border-green-600' },
    rare: { border: 'border-blue-500', text: 'text-blue-400', bg: 'bg-blue-900/20', badge: 'bg-blue-900 text-blue-300 border-blue-500' },
    epic: { border: 'border-purple-500', text: 'text-purple-400', bg: 'bg-purple-900/20', badge: 'bg-purple-900 text-purple-300 border-purple-500' },
    legendary: { border: 'border-orange-500', text: 'text-orange-400', bg: 'bg-orange-900/20', badge: 'bg-orange-900 text-orange-300 border-orange-500' },
    unique: { border: 'border-red-600', text: 'text-red-500', bg: 'bg-red-900/20', badge: 'bg-red-900 text-red-300 border-red-600' },
};

function PlayerInventoryPanel({ 
    campaignId, 
    userId, 
    isGM = false,
    onClose = null 
}) {
    const [inventory, setInventory] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const getProxiedImageUrl = (originalUrl) => {
        if (!originalUrl) return null;
        if (originalUrl.includes('wikia.nocookie.net') || originalUrl.includes('fandom.com')) {
            return `http://localhost:8000/api/v1/wiki/image-proxy?url=${encodeURIComponent(originalUrl)}`;
        }
        return originalUrl;
    };

    const loadInventory = useCallback(async () => {
        try {
            const response = await api.get(`/multiplayer/inventory/campaigns/${campaignId}/inventory/${userId}`);
            setInventory(response.data);
            setLoading(false);
        } catch (error) {
            console.error('Error loading inventory:', error);
            setError(error.response?.data?.detail || 'Failed to load inventory');
            setLoading(false);
        }
    }, [campaignId, userId]);

    useEffect(() => {
        loadInventory();
        const interval = setInterval(loadInventory, 5000);
        return () => clearInterval(interval);
    }, [loadInventory]);

    const handleRemoveItem = async (itemId) => {
        if (!window.confirm('Are you sure you want to remove this item?')) return;
        try {
            await api.delete(`/multiplayer/inventory/campaigns/${campaignId}/inventory/${itemId}`);
            loadInventory();
        } catch (error) {
            console.error('Error removing item:', error);
            alert('Failed to remove item');
        }
    };

    const handleEquipToggle = async (item) => {
        try {
            await api.post(`/multiplayer/inventory/campaigns/${campaignId}/inventory/${item.id}/toggle_equip`);
            loadInventory(); 
        } catch (error) {
            console.error('Equip error:', error);
            alert(error.response?.data?.detail || 'Failed to equip item');
        }
    };

    const handleItemRoll = async (item) => {
        if (!item.dice_config) return;
        try {
            await api.post(`/multiplayer/campaigns/${campaignId}/messages`, {
                message_type: 'dice_roll',
                content: '',
                character_id: null,
                dice_type: item.dice_config.sides,
                dice_count: item.dice_config.count,
                modifier: item.dice_config.modifier || 0,
                metadata: {
                    reason: `used ${item.item_name}`, 
                    item_id: item.id
                }
            });
        } catch (error) {
            console.error('Roll failed:', error);
            alert('Failed to execute item roll');
        }
    };

    if (loading) return <div className="bg-gray-800 rounded-lg p-6 h-full flex items-center justify-center text-white">Loading inventory...</div>;
    if (error) return <div className="bg-gray-800 rounded-lg p-6 h-full text-red-400">{error}</div>;

    return (
        <div className="bg-gray-800 rounded-lg p-4 h-full flex flex-col">
            <div className="flex justify-between items-center mb-3">
                <h3 className="text-xl font-bold text-white flex items-center gap-2">🎒 Inventory <span className="text-xs font-normal text-gray-500">({inventory?.total_items || 0})</span></h3>
                {onClose && <button onClick={onClose} className="text-gray-400 hover:text-white transition">✕</button>}
            </div>

            {!inventory || inventory.items.length === 0 ? (
                <div className="text-gray-500 text-center py-10 flex-1 flex flex-col items-center justify-center">
                    <span className="text-4xl mb-2">📭</span><p>Inventory is empty.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-2 overflow-y-auto custom-scrollbar pr-1 flex-1 content-start">
                    {inventory.items.map(item => {
                        const rarity = item.item_rarity || 'common';
                        const style = RARITY_STYLES[rarity] || RARITY_STYLES['common'];

                        return (
                            <div 
                                key={item.id} 
                                className={`p-2 rounded flex gap-2 border transition relative group 
                                    ${style.bg} 
                                    ${style.border} 
                                    ${item.is_equipped ? 'ring-1 ring-yellow-400 bg-yellow-900/20' : ''}
                                `}
                            >
                                {/* Mniejszy Obrazek */}
                                <div className={`w-12 h-12 bg-black rounded flex-shrink-0 flex items-center justify-center border overflow-hidden ${style.border}`}>
                                    {item.item_image_url ? (
                                        <img 
                                            src={getProxiedImageUrl(item.item_image_url)} 
                                            alt={item.item_name}
                                            className="w-full h-full object-contain"
                                            crossOrigin="anonymous"
                                            onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'block'; }}
                                        />
                                    ) : null}
                                    <span className="text-xl" style={{ display: item.item_image_url ? 'none' : 'block' }}>📦</span>
                                </div>

                                <div className="flex-1 min-w-0 flex flex-col justify-between">
                                    <div className="flex justify-between items-start">
                                        <div className="min-w-0">
                                            <h4 className={`font-bold truncate text-xs ${style.text}`} title={item.item_name}>
                                                {item.item_name}
                                                {item.quantity > 1 && <span className="ml-1 text-gray-400">x{item.quantity}</span>}
                                            </h4>
                                            <div className="text-[9px] text-gray-400 uppercase font-bold tracking-wide flex gap-2">
                                                <span>{item.slot !== 'item' ? item.slot : item.item_category}</span>
                                            </div>
                                        </div>
                                        
                                        {/* GM Remove */}
                                        {isGM && (
                                            <button 
                                                onClick={() => handleRemoveItem(item.id)}
                                                className="text-gray-600 hover:text-red-400 -mt-1 -mr-1 p-1"
                                                title="Remove"
                                            >
                                                ×
                                            </button>
                                        )}
                                    </div>

                                    {/* Action Buttons Row - Compact */}
                                    <div className="flex gap-1 mt-1 items-center">
                                        
                                        {/* EQUIP BUTTON */}
                                        {item.slot !== 'item' && (
                                            <button 
                                                onClick={() => handleEquipToggle(item)}
                                                className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase transition border ${
                                                    item.is_equipped 
                                                    ? 'bg-yellow-600 text-white border-yellow-500 hover:bg-yellow-500' 
                                                    : 'bg-gray-700 text-gray-300 border-gray-600 hover:bg-gray-600'
                                                }`}
                                            >
                                                {item.is_equipped ? 'Unequip' : 'Equip'}
                                            </button>
                                        )}

                                        {/* ROLL BUTTON */}
                                        {item.dice_config && (
                                            <button 
                                                onClick={() => handleItemRoll(item)}
                                                className="bg-indigo-900/80 hover:bg-indigo-700 border border-indigo-500 text-indigo-200 px-2 py-0.5 rounded text-[9px] font-bold flex items-center gap-1 transition"
                                                title={`Roll ${item.dice_config.count}d${item.dice_config.sides}`}
                                            >
                                                🎲 {item.dice_config.count}d{item.dice_config.sides}
                                            </button>
                                        )}

                                        {/* Stat Badges (Mini) */}
                                        {item.stat_modifiers && Object.keys(item.stat_modifiers).length > 0 && (
                                            <div className="flex gap-1 ml-auto">
                                                {Object.entries(item.stat_modifiers).slice(0, 2).map(([stat, value]) => (
                                                    <span key={stat} className="text-[9px] text-gray-500 font-mono">
                                                        {stat.slice(0,3).toUpperCase()}{value>=0?'+':''}{value}
                                                    </span>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}

export default PlayerInventoryPanel;