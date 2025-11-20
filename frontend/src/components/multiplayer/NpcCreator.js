// frontend/src/components/multiplayer/NpcCreator.js
import React, { useState } from 'react';
import api from '../../api/axiosConfig';
import ItemBrowser from './ItemBrowser'; // ✅ Teraz używamy go!

function NpcCreator({ campaignId, universe }) {
    const [mode, setMode] = useState('wiki'); // 'wiki' lub 'custom'
    const [npc, setNpc] = useState({
        name: '',
        race: 'Human',
        description: '',
        image_url: '',
        stats: {
            strength: 10,
            dexterity: 10,
            constitution: 10,
            intelligence: 10,
            wisdom: 10,
            charisma: 10
        }
    });

    // Handler wyboru z Wiki
    const handleWikiSelect = (item) => {
        setNpc(prev => ({
            ...prev,
            name: item.name,
            description: item.description || '',
            image_url: item.image_url || '',
            // Próba zgadnięcia rasy z kategorii (opcjonalnie)
            race: item.category === 'species' ? item.name : 'Unknown'
        }));
        setMode('custom'); // Przełącz na edycję statystyk
    };

    const handleSpawn = async () => {
        if (!npc.name) return alert('Name required');
        try {
            await api.post(`/multiplayer/campaigns/${campaignId}/messages`, {
                message_type: 'npc_spawn',
                content: `👤 GM spawned NPC: ${npc.name}`,
                metadata: { npc: npc }
            });
            alert('NPC Spawned!');
        } catch (error) {
            console.error('Error spawning NPC:', error);
            alert('Failed to spawn NPC');
        }
    };

    // Widok wyboru z Wiki
    if (mode === 'wiki') {
        return (
            <div className="space-y-4 h-full flex flex-col">
                <div className="flex justify-between items-center flex-shrink-0 mb-2">
                    <h3 className="text-xl font-bold text-white">Select NPC Template</h3>
                    <button onClick={() => setMode('custom')} className="text-blue-400 hover:text-blue-300 text-sm">
                        Skip to Manual &rarr;
                    </button>
                </div>
                
                {/* Browser ograniczony do postaci, ras i kreatur */}
                <div className="flex-1 overflow-hidden">
                    <ItemBrowser 
                        universe={universe} 
                        isGM={true} 
                        onItemSelect={handleWikiSelect}
                        initialCategory="characters"
                        allowedCategories={['characters', 'species', 'creatures', 'droids']} 
                    />
                </div>
            </div>
        );
    }

    // Widok edycji (Custom)
    return (
        <div className="bg-gray-800 p-6 rounded-lg h-full overflow-y-auto">
            <div className="flex justify-between mb-6">
                <h3 className="text-2xl font-bold text-white">👤 Configure NPC</h3>
                <button onClick={() => setMode('wiki')} className="text-sm text-blue-400">← Back to Wiki</button>
            </div>
            
            <div className="space-y-4">
                {npc.image_url && (
                    <div className="flex justify-center">
                        <img src={npc.image_url} alt="Preview" className="h-32 w-32 object-cover rounded-full border-2 border-blue-500" />
                    </div>
                )}
                
                <div>
                    <label className="text-gray-400 text-xs uppercase font-bold">Name</label>
                    <input className="w-full bg-gray-700 text-white p-2 rounded border border-gray-600 focus:border-blue-500 outline-none"
                        value={npc.name} onChange={e => setNpc({...npc, name: e.target.value})} />
                </div>
                
                <div>
                    <label className="text-gray-400 text-xs uppercase font-bold">Race / Type</label>
                    <input className="w-full bg-gray-700 text-white p-2 rounded border border-gray-600 focus:border-blue-500 outline-none"
                        value={npc.race} onChange={e => setNpc({...npc, race: e.target.value})} />
                </div>

                <div className="pt-2">
                    <label className="text-gray-400 text-xs uppercase font-bold mb-2 block">Stats</label>
                    <div className="grid grid-cols-3 gap-3">
                        {Object.keys(npc.stats).map(stat => (
                            <div key={stat}>
                                <span className="text-[10px] text-gray-500 uppercase block mb-1">{stat.slice(0,3)}</span>
                                <input type="number" className="w-full bg-gray-900 text-white p-2 rounded text-center border border-gray-700"
                                    value={npc.stats[stat]}
                                    onChange={e => setNpc({
                                        ...npc, 
                                        stats: {...npc.stats, [stat]: parseInt(e.target.value) || 0}
                                    })}
                                />
                            </div>
                        ))}
                    </div>
                </div>

                <button onClick={handleSpawn} className="w-full bg-green-600 hover:bg-green-500 py-3 rounded text-white font-bold mt-6 shadow-lg transition transform hover:scale-105">
                    🚀 Spawn to Chat
                </button>
            </div>
        </div>
    );
}

export default NpcCreator;