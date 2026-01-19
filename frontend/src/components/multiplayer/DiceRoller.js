
import React, { useState, useEffect } from 'react';
import api from '../../api/axiosConfig';

const DIES = [20, 4, 6, 8, 10, 12, 100]; 

const ATTRIBUTES = [
    { key: 'none', label: 'Basic' },
    { key: 'strength', label: 'STR' },
    { key: 'dexterity', label: 'DEX' },
    { key: 'constitution', label: 'CON' },
    { key: 'intelligence', label: 'INT' },
    { key: 'wisdom', label: 'WIS' },
    { key: 'charisma', label: 'CHA' }
];

function DiceRoller({ campaignId, characterId, characterStats, targets = [], onAttack }) {
    const [selectedAttr, setSelectedAttr] = useState('none');
    const [isRolling, setIsRolling] = useState(false);
    const [equippedWeapon, setEquippedWeapon] = useState(null);
    const [selectedTargetId, setSelectedTargetId] = useState('');

    
    useEffect(() => {
        
        if (characterId === 'gm_npc' || !characterId) return;

        const fetchWeapon = async () => {
            try {
                
                const user = JSON.parse(localStorage.getItem('user'));
                if (user) {
                    
                    const res = await api.get(`/multiplayer/inventory/campaigns/${campaignId}/inventory/${user.id}`);
                    
                    const weapon = res.data.items.find(i => i.is_equipped && i.slot === 'weapon');
                    setEquippedWeapon(weapon);
                }
            } catch (error) {
                console.error("Failed to fetch weapon:", error);
            }
        };
        fetchWeapon();
    }, [campaignId, characterId]);

    
    useEffect(() => {
        if (targets.length > 0 && !selectedTargetId) {
            
            const firstEnemy = targets.find(t => t.type === 'npc') || targets[0];
            if (firstEnemy) setSelectedTargetId(firstEnemy.id);
        }
    }, [targets, selectedTargetId]);

    
    const getModifier = (attrKey) => {
        if (attrKey === 'none' || !characterStats) return 0;
        const value = characterStats[attrKey] || 10;
        return Math.floor((value - 10) / 2);
    };

    const currentModifier = getModifier(selectedAttr);

    
    const rollDice = async (sides) => {
        if (isRolling) return;
        setIsRolling(true);
        try {
            console.log(`🎲 Rolling d${sides} with ${selectedAttr} (${currentModifier})...`);
            
            const reason = selectedAttr !== 'none' 
                ? `${selectedAttr.charAt(0).toUpperCase() + selectedAttr.slice(1)} Check` 
                : '';

            await api.post(`/multiplayer/campaigns/${campaignId}/messages`, {
                message_type: 'dice_roll',
                content: '', 
                character_id: characterId === 'gm_npc' ? null : characterId,
                dice_type: sides,
                dice_count: 1,
                modifier: currentModifier,
                metadata: {
                    reason: reason,
                    attribute: selectedAttr
                }
            });
        } catch (error) {
            console.error('Roll failed:', error);
            alert('Failed to roll dice.');
        } finally {
            setIsRolling(false);
        }
    };

    
    const handleWeaponAttack = async () => {
        if (!equippedWeapon || !equippedWeapon.dice_config) return;
        if (!selectedTargetId) return alert("Select a target first!");
        if (isRolling) return;
        
        setIsRolling(true);
        try {
            const { count, sides } = equippedWeapon.dice_config;
            
            const dmgMod = currentModifier; 

            
            
            
            
            let totalRoll = 0;
            const rolls = [];
            for(let i=0; i<count; i++) {
                const r = Math.floor(Math.random() * sides) + 1;
                rolls.push(r);
                totalRoll += r;
            }
            const totalDamage = totalRoll + dmgMod;

            const targetName = targets.find(t => t.id === selectedTargetId)?.name || 'target';

            
            await api.post(`/multiplayer/campaigns/${campaignId}/messages`, {
                message_type: 'player_action',
                content: `⚔️ **Attacks ${targetName}** with ${equippedWeapon.item_name}!\n🎲 Damage Roll: [${rolls.join(' + ')}] ${dmgMod ? (dmgMod > 0 ? `+ ${dmgMod}` : dmgMod) : ''} = **${totalDamage} DMG**`,
                character_id: characterId === 'gm_npc' ? null : characterId
            });

            
            if (onAttack) {
                onAttack(totalDamage, selectedTargetId);
            }

        } catch (error) {
            console.error('Weapon attack failed:', error);
        } finally {
            setIsRolling(false);
        }
    };

    return (
        <div className="bg-gray-800 p-3 rounded-lg border border-gray-700 mb-2 animate-fadeIn">
            
            {/* SEKCJA WYBORU CELU (Targeting) */}
            {targets.length > 0 && (
                <div className="mb-3 flex items-center gap-2 bg-black/30 p-2 rounded border border-gray-600">
                    <span className="text-red-400 text-xs font-bold uppercase tracking-wider">🎯 Target:</span>
                    <select 
                        className="bg-gray-900 text-white text-xs p-1 rounded border border-gray-600 flex-1 outline-none focus:border-red-500"
                        value={selectedTargetId}
                        onChange={(e) => setSelectedTargetId(e.target.value)}
                    >
                        {targets.map((t, i) => (
                            <option key={i} value={t.id}>
                                {t.name} (HP: {t.hp}, AC: {t.ac})
                            </option>
                        ))}
                    </select>
                </div>
            )}

            {/* SEKCJA BRONI (Jeśli jest wyekwipowana) */}
            {equippedWeapon && equippedWeapon.dice_config && (
                <div className="mb-3">
                    <button 
                        onClick={handleWeaponAttack}
                        disabled={isRolling || !selectedTargetId}
                        className={`w-full py-3 rounded font-bold text-sm flex justify-center items-center gap-2 shadow-lg transition transform hover:scale-[1.02] active:scale-95
                            ${!selectedTargetId ? 'bg-gray-600 cursor-not-allowed opacity-50' : 'bg-gradient-to-r from-red-700 to-red-600 hover:from-red-600 hover:to-red-500 text-white border border-red-400'}
                        `}
                    >
                        <span>⚔️ Attack with {equippedWeapon.item_name}</span>
                        <span className="bg-black/30 px-2 py-0.5 rounded text-xs font-mono border border-white/10">
                            {equippedWeapon.dice_config.count}d{equippedWeapon.dice_config.sides}
                            {currentModifier !== 0 && (currentModifier > 0 ? `+${currentModifier}` : currentModifier)}
                        </span>
                    </button>
                    {!selectedTargetId && <p className="text-[10px] text-red-400 text-center mt-1">⚠️ Select a target to attack</p>}
                </div>
            )}

            {equippedWeapon && <div className="border-t border-gray-700 my-3 opacity-50"></div>}

            {/* 1. Wybór Atrybutu (Modyfikatory) */}
            <div className="flex gap-2 mb-3 overflow-x-auto pb-2 custom-scrollbar">
                {ATTRIBUTES.map(attr => {
                    const mod = getModifier(attr.key);
                    const modStr = mod >= 0 ? `+${mod}` : mod;
                    
                    return (
                        <button
                            key={attr.key}
                            onClick={() => setSelectedAttr(attr.key)}
                            className={`px-3 py-1 rounded text-xs font-bold transition whitespace-nowrap flex items-center gap-1 ${
                                selectedAttr === attr.key 
                                    ? 'bg-blue-600 text-white ring-2 ring-blue-400' 
                                    : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
                            }`}
                        >
                            {attr.label}
                            {attr.key !== 'none' && characterStats && (
                                <span className={mod >= 0 ? "text-green-400" : "text-red-400"}>
                                    {modStr}
                                </span>
                            )}
                        </button>
                    );
                })}
            </div>

            {/* 2. Wybór Kości (Standardowe) */}
            <div className="flex gap-2 overflow-x-auto pb-1 custom-scrollbar items-center">
                {/* Pokazujemy aktualny modyfikator */}
                <div className="text-gray-500 text-xs font-mono mr-2 bg-gray-900 px-2 py-1 rounded">
                    Mod: <span className="text-white font-bold">{currentModifier >= 0 ? '+' : ''}{currentModifier}</span>
                </div>

                {DIES.map(sides => (
                    <button
                        key={sides}
                        onClick={() => rollDice(sides)}
                        disabled={isRolling}
                        className="bg-indigo-600 hover:bg-indigo-500 disabled:bg-gray-600 text-white font-bold py-1 px-3 rounded text-sm transition shadow-md whitespace-nowrap"
                    >
                        d{sides}
                    </button>
                ))}
            </div>
        </div>
    );
}

export default DiceRoller;