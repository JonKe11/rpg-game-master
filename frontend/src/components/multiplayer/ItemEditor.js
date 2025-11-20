import React, { useState } from 'react';
import ItemBrowser from './ItemBrowser';

function ItemEditor({ universe, onSave, onCancel }) {
    const [mode, setMode] = useState('wiki'); // 'wiki' or 'custom'
    const [formData, setFormData] = useState({
        name: '',
        category: 'items',
        description: '',
        image_url: '',
        stat_modifiers: {}
    });
    
    // Statystyki do wyboru
    const AVAILABLE_STATS = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma', 'armor_class'];
    const [newStat, setNewStat] = useState({ name: 'strength', value: 1 });

    const handleWikiSelect = (item) => {
        setFormData({
            ...formData,
            name: item.name,
            image_url: item.image_url,
            description: item.description,
            category: item.category || 'items'
        });
        setMode('custom'); // Przełącz na edycję, żeby dodać statystyki
    };

    const addStat = () => {
        setFormData(prev => ({
            ...prev,
            stat_modifiers: {
                ...prev.stat_modifiers,
                [newStat.name]: parseInt(newStat.value)
            }
        }));
    };

    const removeStat = (statName) => {
        const newStats = { ...formData.stat_modifiers };
        delete newStats[statName];
        setFormData({ ...formData, stat_modifiers: newStats });
    };

    const handleSubmit = () => {
        if (!formData.name) return alert('Name is required');
        onSave(formData);
    };

    if (mode === 'wiki') {
        return (
            <div className="space-y-4">
                <div className="flex justify-between items-center">
                    <h3 className="text-xl font-bold text-white">Select Base Item from Wiki</h3>
                    <button onClick={() => setMode('custom')} className="text-blue-400 hover:text-blue-300">
                        Skip to Custom Creator &rarr;
                    </button>
                </div>
                <ItemBrowser 
                    universe={universe} 
                    isGM={true} 
                    onItemSelect={handleWikiSelect} 
                />
            </div>
        );
    }

    return (
        <div className="bg-gray-700 p-4 rounded-lg space-y-4">
            <h3 className="text-xl font-bold text-white">Create/Edit Item</h3>
            
            {/* Basic Info */}
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm text-gray-400">Name</label>
                    <input 
                        className="w-full bg-gray-600 text-white rounded p-2"
                        value={formData.name}
                        onChange={e => setFormData({...formData, name: e.target.value})}
                    />
                </div>
                <div>
                    <label className="block text-sm text-gray-400">Category</label>
                    <select 
                        className="w-full bg-gray-600 text-white rounded p-2"
                        value={formData.category}
                        onChange={e => setFormData({...formData, category: e.target.value})}
                    >
                        {['weapons', 'armor', 'items', 'vehicles', 'droids'].map(c => (
                            <option key={c} value={c}>{c}</option>
                        ))}
                    </select>
                </div>
            </div>

            {/* Image Preview */}
            {formData.image_url && (
                <div className="flex gap-4 items-center bg-gray-800 p-2 rounded">
                    <img src={formData.image_url} alt="Preview" className="w-16 h-16 object-cover rounded" />
                    <span className="text-gray-400 text-sm">Image selected from wiki</span>
                </div>
            )}

            {/* Stat Modifiers */}
            <div className="border-t border-gray-600 pt-4">
                <h4 className="text-white font-semibold mb-2">Stat Modifiers</h4>
                
                <div className="flex gap-2 mb-2">
                    <select 
                        className="bg-gray-600 text-white rounded p-1 flex-1"
                        value={newStat.name}
                        onChange={e => setNewStat({...newStat, name: e.target.value})}
                    >
                        {AVAILABLE_STATS.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                    <input 
                        type="number" 
                        className="bg-gray-600 text-white rounded p-1 w-20"
                        value={newStat.value}
                        onChange={e => setNewStat({...newStat, value: e.target.value})}
                    />
                    <button onClick={addStat} className="bg-green-600 px-3 rounded text-white">+</button>
                </div>

                <div className="flex flex-wrap gap-2">
                    {Object.entries(formData.stat_modifiers).map(([stat, val]) => (
                        <span key={stat} className="bg-blue-900 px-2 py-1 rounded text-xs text-blue-200 flex items-center gap-2">
                            {stat}: {val > 0 ? '+' : ''}{val}
                            <button onClick={() => removeStat(stat)} className="text-red-400 hover:text-red-300">×</button>
                        </span>
                    ))}
                </div>
            </div>

            <div className="flex gap-2 pt-4">
                <button onClick={handleSubmit} className="flex-1 bg-blue-600 hover:bg-blue-500 py-2 rounded text-white font-bold">
                    Create Item
                </button>
                <button onClick={onCancel} className="bg-gray-600 hover:bg-gray-500 px-4 rounded text-white">
                    Cancel
                </button>
            </div>
        </div>
    );
}

export default ItemEditor;