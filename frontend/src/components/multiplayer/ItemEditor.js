// frontend/src/components/multiplayer/ItemEditor.js
import React, { useState, useRef } from 'react';
import ItemBrowser from './ItemBrowser';

// Definicja kolorów dla edytora
const RARITY_OPTIONS = [
    { value: 'common', label: 'Common', color: 'text-gray-400' },
    { value: 'uncommon', label: 'Uncommon', color: 'text-green-400' },
    { value: 'rare', label: 'Rare', color: 'text-blue-400' },
    { value: 'epic', label: 'Epic', color: 'text-purple-400' },
    { value: 'legendary', label: 'Legendary', color: 'text-orange-400' },
    { value: 'unique', label: 'Unique', color: 'text-red-500' }
];

function ItemEditor({ universe, onSave, onCancel }) {
    const [mode, setMode] = useState('wiki');
    
    // ✅ Główny stan formularza przedmiotu
    const [formData, setFormData] = useState({
        name: '',
        category: 'items',
        description: '',
        image_url: '',
        rarity: 'common',
        stat_modifiers: {},
        // ✅ NOWE POLA
        slot: 'item', // Domyślnie zwykły przedmiot
        dice_config: {
            enabled: false,
            count: 1,
            sides: 6
        },
        armor_value: 0 // ✅ Dodano wartość pancerza
    });
    
    const fileInputRef = useRef(null);

    const AVAILABLE_STATS = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma', 'armor_class'];
    const [newStat, setNewStat] = useState({ name: 'strength', value: 1 });

    const getProxiedImageUrl = (originalUrl) => {
        if (!originalUrl) return null;
        if (originalUrl.startsWith('data:image')) return originalUrl;
        if (originalUrl.includes('wikia.nocookie.net') || originalUrl.includes('fandom.com')) {
            return `http://localhost:8000/api/v1/wiki/image-proxy?url=${encodeURIComponent(originalUrl)}`;
        }
        return originalUrl;
    };

    const handleFileUpload = (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onloadend = () => {
                setFormData(prev => ({
                    ...prev,
                    image_url: reader.result
                }));
            };
            reader.readAsDataURL(file);
        }
    };

    const handleWikiSelect = (item) => {
        setFormData({
            ...formData,
            name: item.name,
            image_url: item.image_url,
            description: item.description,
            category: item.category || 'items'
        });
        setMode('custom'); 
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
        if (!formData.name) return alert('Name required');
        
        // Formatowanie danych pod backend
        const submissionData = { ...formData };
        
        if (!formData.dice_config.enabled) {
            submissionData.dice_config = null;
        } else {
            submissionData.dice_config = {
                count: parseInt(formData.dice_config.count),
                sides: parseInt(formData.dice_config.sides)
            };
        }
        // Usuwamy flagę 'enabled', bo backend jej nie potrzebuje
        delete submissionData.dice_config?.enabled;

        // ✅ Upewniamy się, że armor_value jest liczbą
        submissionData.armor_value = parseInt(formData.armor_value) || 0;

        onSave(submissionData);
    };

    if (mode === 'wiki') {
        return (
            <div className="h-full flex flex-col">
                <div className="flex justify-between items-center mb-4 px-4 pt-4">
                    <h3 className="text-xl font-bold text-white">Select Base Item</h3>
                    <button onClick={() => setMode('custom')} className="text-gray-400 hover:text-white">Create Custom</button>
                </div>
                <div className="flex-1 overflow-hidden">
                    <ItemBrowser 
                        onItemSelect={handleWikiSelect} 
                        universe={universe} 
                        isGM={true} 
                        initialCategory="weapons"
                        allowedCategories={['weapons', 'armor', 'items', 'vehicles']}
                    />
                </div>
            </div>
        );
    }

    return (
        <div className="bg-gray-800 rounded-lg p-6 h-full overflow-y-auto custom-scrollbar">
            <h3 className="text-2xl font-bold text-white mb-6">🛠️ Edit Item</h3>
            
            <div className="space-y-4">
                <div className="flex gap-4">
                    
                    {/* Avatar Upload */}
                    <div 
                        onClick={() => fileInputRef.current.click()}
                        className={`w-24 h-24 bg-black rounded border-2 flex items-center justify-center overflow-hidden flex-shrink-0 cursor-pointer relative group ${
                            RARITY_OPTIONS.find(r => r.value === formData.rarity)?.color.replace('text-', 'border-') || 'border-gray-600'
                        }`}
                    >
                        {formData.image_url ? (
                            <img 
                                src={getProxiedImageUrl(formData.image_url)} 
                                alt="Item" 
                                className="w-full h-full object-contain group-hover:opacity-50 transition"
                                crossOrigin="anonymous" 
                            />
                        ) : (
                            <span className="text-4xl group-hover:opacity-50 transition">📦</span>
                        )}
                        <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition">
                            <span className="text-white text-xs font-bold bg-black/70 px-2 py-1 rounded">Upload</span>
                        </div>
                        <input type="file" ref={fileInputRef} onChange={handleFileUpload} className="hidden" accept="image/*" />
                    </div>

                    <div className="flex-1 space-y-2">
                        <input 
                            type="text" 
                            placeholder="Item Name" 
                            className="w-full bg-gray-700 text-white p-2 rounded"
                            value={formData.name} 
                            onChange={e => setFormData({...formData, name: e.target.value})} 
                        />
                        
                        <div className="flex gap-2">
                            {/* Wybór Slotu */}
                            <select 
                                className="bg-gray-700 text-white p-2 rounded flex-1 font-bold"
                                value={formData.slot} 
                                onChange={e => setFormData({...formData, slot: e.target.value})}
                            >
                                <option value="item">📦 Generic Item</option>
                                <option value="weapon">⚔️ Weapon</option>
                                <option value="armor">🛡️ Armor</option>
                                <option value="accessory">💍 Accessory</option>
                            </select>

                            {/* Wybór Rzadkości */}
                            <select 
                                className={`bg-gray-900 font-bold p-2 rounded flex-1 ${RARITY_OPTIONS.find(r => r.value === formData.rarity)?.color}`}
                                value={formData.rarity} 
                                onChange={e => setFormData({...formData, rarity: e.target.value})}
                            >
                                {RARITY_OPTIONS.map(opt => (
                                    <option key={opt.value} value={opt.value} className={opt.color}>
                                        {opt.label}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>
                </div>

                <textarea 
                    placeholder="Description..." 
                    rows={3} 
                    className="w-full bg-gray-700 text-white p-2 rounded"
                    value={formData.description} 
                    onChange={e => setFormData({...formData, description: e.target.value})} 
                />

                {/* ✅ SEKCJA PANCERZA (Widoczna tylko jeśli wybrano Armor) */}
                {formData.slot === 'armor' && (
                    <div className="bg-blue-900/30 p-3 rounded border border-blue-500/50 animate-fadeIn">
                        <div className="flex items-center justify-between">
                            <label className="text-blue-300 font-bold text-sm">🛡️ Armor Value (Damage Reduction)</label>
                            <input 
                                type="number" 
                                min="0"
                                className="w-20 bg-gray-900 text-white p-1 rounded text-center font-bold border border-blue-500"
                                value={formData.armor_value} 
                                onChange={e => setFormData({...formData, armor_value: e.target.value})} 
                            />
                        </div>
                        <p className="text-xs text-blue-400 mt-1">Reduces incoming damage by this amount.</p>
                    </div>
                )}

                {/* ✅ SEKCJA RZUTU KOŚCIĄ (Damage/Effect) */}
                <div className="bg-gray-900/50 p-3 rounded border border-gray-700">
                    <label className="flex items-center gap-2 mb-2 cursor-pointer select-none">
                        <input 
                            type="checkbox" 
                            checked={formData.dice_config.enabled} 
                            onChange={e => setFormData({
                                ...formData, 
                                dice_config: {...formData.dice_config, enabled: e.target.checked}
                            })} 
                            className="w-4 h-4 rounded text-blue-600 focus:ring-blue-500"
                        />
                        <span className="text-white font-bold text-sm">Enable Dice Roll (Damage/Effect)</span>
                    </label>
                    
                    {formData.dice_config.enabled && (
                        <div className="flex items-center gap-2 animate-fadeIn pl-6">
                            <input 
                                type="number" 
                                min="1" 
                                max="100"
                                className="w-16 bg-gray-700 text-white p-1 rounded text-center font-bold"
                                value={formData.dice_config.count} 
                                onChange={e => setFormData({
                                    ...formData, 
                                    dice_config: {...formData.dice_config, count: e.target.value}
                                })} 
                            />
                            <span className="text-gray-400 font-bold">d</span>
                            <select 
                                className="w-20 bg-gray-700 text-white p-1 rounded font-bold"
                                value={formData.dice_config.sides} 
                                onChange={e => setFormData({
                                    ...formData, 
                                    dice_config: {...formData.dice_config, sides: e.target.value}
                                })}
                            >
                                {[4,6,8,10,12,20,100].map(s => <option key={s} value={s}>{s}</option>)}
                            </select>
                            <span className="text-gray-500 text-xs ml-2">(e.g. 3d12 damage)</span>
                        </div>
                    )}
                </div>

                {/* Stats Modifiers */}
                <div className="bg-gray-900 p-3 rounded border border-gray-700">
                    <label className="text-gray-400 text-xs font-bold block mb-2">Stats & Bonuses</label>
                    <div className="flex gap-2 mb-2">
                        <select className="bg-gray-700 text-white rounded p-1 flex-1 text-sm"
                            value={newStat.name} onChange={e => setNewStat({...newStat, name: e.target.value})}>
                            {AVAILABLE_STATS.map(s => <option key={s} value={s}>{s}</option>)}
                        </select>
                        <input type="number" className="bg-gray-700 text-white rounded p-1 w-20 text-center"
                            value={newStat.value} onChange={e => setNewStat({...newStat, value: e.target.value})} />
                        <button onClick={addStat} className="bg-green-600 px-3 rounded text-white font-bold">+</button>
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {Object.entries(formData.stat_modifiers).map(([stat, val]) => (
                            <span key={stat} className="bg-blue-900 px-2 py-1 rounded text-xs text-blue-200 flex items-center gap-2 border border-blue-700">
                                {stat}: {val > 0 ? '+' : ''}{val}
                                <button onClick={() => removeStat(stat)} className="text-red-400 hover:text-red-300 font-bold">×</button>
                            </span>
                        ))}
                    </div>
                </div>

                <div className="flex gap-2 pt-4">
                    <button onClick={handleSubmit} className="flex-1 bg-blue-600 hover:bg-blue-500 py-2 rounded text-white font-bold shadow-lg">
                        Save Item
                    </button>
                    <button onClick={onCancel} className="bg-gray-600 hover:bg-gray-500 px-4 rounded text-white">
                        Cancel
                    </button>
                </div>
            </div>
        </div>
    );
}

export default ItemEditor;