// frontend/src/components/multiplayer/NpcCreator.js
import React, { useState, useRef } from 'react';
import api from '../../api/axiosConfig';
import ItemBrowser from './ItemBrowser';

const RARITY_OPTIONS = [
    { value: 'common', label: 'Common NPC', color: 'border-gray-500 text-gray-300' },
    { value: 'uncommon', label: 'Elite (Green)', color: 'border-green-500 text-green-400' },
    { value: 'rare', label: 'Rare (Blue)', color: 'border-blue-500 text-blue-400' },
    { value: 'epic', label: 'Boss (Purple)', color: 'border-purple-500 text-purple-400' },
    { value: 'legendary', label: 'Legendary (Orange)', color: 'border-orange-500 text-orange-400' },
    { value: 'unique', label: 'Unique (Red)', color: 'border-red-600 text-red-500' }
];

function NpcCreator({ campaignId, universe }) {
    const [mode, setMode] = useState('wiki'); 
    
   
    const [npc, setNpc] = useState({
        name: '',
        race: 'Human',
        description: '',
        image_url: '',
        rarity: 'common',
        hp: 50,
        armor_class: 10,       
        damage_reduction: 0,   
        attitude: 'Hostile',   
        
        damage_dice: '1d6' 
    });

    const fileInputRef = useRef(null);

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
                setNpc(prev => ({
                    ...prev,
                    image_url: reader.result
                }));
            };
            reader.readAsDataURL(file);
        }
    };

    const handleWikiSelect = (item) => {
        setNpc(prev => ({
            ...prev,
            name: item.name,
            description: item.description || '',
            image_url: item.image_url || '',
            race: item.category === 'species' ? item.name : 'Unknown'
        }));
        setMode('custom');
    };

    const handleSpawn = async () => {
        if (!npc.name) return alert('Name required');
        
        try {
            await api.post(`/multiplayer/campaigns/${campaignId}/messages`, {
                message_type: 'npc_spawn',
                content: `Spawned NPC: ${npc.name}`,
                character_id: null,
                metadata: { npc }
            });
            alert('NPC Spawned to chat successfully!');
        } catch (error) {
            console.error("Error spawning NPC:", error);
            alert("Failed to spawn NPC.");
        }
    };

    
    if (mode === 'wiki') {
        return (
            <div className="h-full flex flex-col">
                <div className="flex justify-between items-center mb-4 px-4 pt-4">
                    <h3 className="text-xl font-bold text-white">Select NPC Template</h3>
                    <button onClick={() => setMode('custom')} className="text-gray-400 hover:text-white">
                        Skip to Manual Editor
                    </button>
                </div>
                <div className="flex-1 overflow-hidden">
                    <ItemBrowser 
                        onItemSelect={handleWikiSelect} 
                        universe={universe} 
                        isGM={true} 
                        initialCategory="characters"
                        allowedCategories={['characters', 'species', 'droids', 'creatures']}
                    />
                </div>
            </div>
        );
    }

    const currentRarity = RARITY_OPTIONS.find(r => r.value === npc.rarity) || RARITY_OPTIONS[0];

   
    return (
        <div className="bg-gray-800 rounded-lg p-6 h-full overflow-y-auto space-y-4 custom-scrollbar">
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-2xl font-bold text-white">👤 Create NPC</h3>
                <button onClick={() => setMode('wiki')} className="text-sm text-blue-400 hover:text-blue-300">
                    Back to Wiki
                </button>
            </div>

            <div className="flex gap-4">
                {/* Avatar Upload */}
                <div 
                    onClick={() => fileInputRef.current.click()}
                    className={`w-32 h-32 bg-black rounded border-4 flex items-center justify-center overflow-hidden flex-shrink-0 cursor-pointer relative group ${currentRarity.color.split(' ')[0]}`}
                >
                    {npc.image_url ? (
                        <img 
                            src={getProxiedImageUrl(npc.image_url)} 
                            alt="Avatar" 
                            className="w-full h-full object-cover group-hover:opacity-50 transition"
                            crossOrigin="anonymous" 
                        />
                    ) : (
                        <span className="text-5xl group-hover:opacity-50 transition">👾</span>
                    )}

                    <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition">
                        <span className="text-white text-xs font-bold bg-black/70 px-2 py-1 rounded">Upload</span>
                    </div>

                    <input 
                        type="file" 
                        ref={fileInputRef}
                        onChange={handleFileUpload}
                        className="hidden"
                        accept="image/*"
                    />
                </div>

                <div className="flex-1 space-y-2">
                    <input 
                        type="text" 
                        placeholder="Name" 
                        className="w-full bg-gray-700 text-white p-2 rounded focus:ring-2 focus:ring-blue-500 outline-none font-bold text-lg"
                        value={npc.name} 
                        onChange={e => setNpc({...npc, name: e.target.value})} 
                    />
                    
                    <div className="flex gap-2">
                        <input 
                            type="text" 
                            placeholder="Race / Type" 
                            className="w-full bg-gray-700 text-white p-2 rounded flex-1"
                            value={npc.race} 
                            onChange={e => setNpc({...npc, race: e.target.value})} 
                        />
                        
                        <select 
                            className={`bg-gray-900 font-bold p-2 rounded flex-1 ${currentRarity.color.split(' ')[1]}`}
                            value={npc.rarity} 
                            onChange={e => setNpc({...npc, rarity: e.target.value})}
                        >
                            {RARITY_OPTIONS.map(opt => (
                                <option key={opt.value} value={opt.value} className={opt.color.split(' ')[1]}>
                                    {opt.label}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="flex gap-2">
                        <select 
                            className={`bg-gray-700 p-2 rounded flex-1 font-bold ${
                                npc.attitude === 'Hostile' ? 'text-red-400' : 
                                npc.attitude === 'Friendly' ? 'text-green-400' : 'text-yellow-400'
                            }`}
                            value={npc.attitude} 
                            onChange={e => setNpc({...npc, attitude: e.target.value})}
                        >
                            <option value="Hostile">⚔️ Hostile</option>
                            <option value="Neutral">😐 Neutral</option>
                            <option value="Friendly">🤝 Friendly</option>
                        </select>
                    </div>
                </div>
            </div>

            {/*  UPROSZCZONA SEKCJA STATYSTYK */}
            <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-700">
                <h4 className="text-gray-400 text-xs uppercase font-bold mb-3">Combat Stats</h4>
                <div className="grid grid-cols-2 gap-4 mb-4">
                    <div>
                        <label className="text-[10px] text-gray-500 uppercase block mb-1">Hit Points (HP)</label>
                        <input 
                            type="number" 
                            className="bg-gray-800 text-green-400 font-bold p-3 rounded w-full text-center border border-gray-600 text-xl" 
                            value={npc.hp} 
                            onChange={e => setNpc({...npc, hp: parseInt(e.target.value) || 0})} 
                        />
                    </div>
                    <div>
                        <label className="text-[10px] text-gray-500 uppercase block mb-1">Attack Damage</label>
                        <input 
                            type="text" 
                            className="bg-gray-800 text-red-400 font-bold p-3 rounded w-full text-center border border-gray-600 text-xl placeholder-gray-600"
                            placeholder="e.g. 2d6+3"
                            value={npc.damage_dice} 
                            onChange={e => setNpc({...npc, damage_dice: e.target.value})} 
                        />
                        <p className="text-[10px] text-gray-500 text-center mt-1">Dice notation (e.g. 1d8, 2d6+4)</p>
                    </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="text-[10px] text-gray-500 uppercase block mb-1">Armor Class (AC)</label>
                        <input 
                            type="number" 
                            className="bg-gray-800 text-blue-400 font-bold p-2 rounded w-full text-center border border-gray-600"
                            value={npc.armor_class} 
                            onChange={e => setNpc({...npc, armor_class: parseInt(e.target.value) || 0})} 
                        />
                    </div>
                    <div>
                        <label className="text-[10px] text-gray-500 uppercase block mb-1">Damage Reduction</label>
                        <input 
                            type="number" 
                            className="bg-gray-800 text-yellow-400 font-bold p-2 rounded w-full text-center border border-gray-600"
                            value={npc.damage_reduction} 
                            onChange={e => setNpc({...npc, damage_reduction: parseInt(e.target.value) || 0})} 
                        />
                    </div>
                </div>
            </div>

            <button 
                onClick={handleSpawn} 
                className="w-full bg-gradient-to-r from-green-600 to-green-500 hover:from-green-500 hover:to-green-400 py-4 rounded-lg text-white font-bold text-lg mt-4 shadow-lg transition transform hover:scale-[1.02]"
            >
                🚀 Spawn to Combat
            </button>
        </div>
    );
}

export default NpcCreator;