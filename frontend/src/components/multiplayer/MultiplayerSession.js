// frontend/src/components/multiplayer/MultiplayerSession.js
import React, { useState, useEffect, useRef, useCallback } from 'react';
import api from '../../api/axiosConfig';
import LocationSelector from './LocationSelector';
import PlayerInventoryPanel from './PlayerInventoryPanel';
import GMPlayerManager from './GMPlayerManager';
import CompendiumBrowser from './CompendiumBrowser';
import NpcCreator from './NpcCreator';
import PlayerCharacterSheet from './PlayerCharacterSheet';
import DiceRoller from './DiceRoller'; 
import CombatTracker from './CombatTracker';

function MultiplayerSession({ campaign, character, onEnd }) {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  
  const [messageType] = useState('player_action');
  
  const [connected, setConnected] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [isGM, setIsGM] = useState(false);
  const [currentLocation, setCurrentLocation] = useState('Unknown');
  
  const [activeCharacterStats, setActiveCharacterStats] = useState(null);
  const [npcTargetId, setNpcTargetId] = useState('');

  const [middleView, setMiddleView] = useState('compendium'); 
  const messagesEndRef = useRef(null);

  const getProxiedImageUrl = (originalUrl) => {
      if (!originalUrl) return null;
      if (originalUrl.startsWith('data:image')) return originalUrl;
      if (originalUrl.includes('wikia.nocookie.net') || originalUrl.includes('fandom.com')) {
          return `http://localhost:8000/api/v1/wiki/image-proxy?url=${encodeURIComponent(originalUrl)}`;
      }
      return originalUrl;
  };

  const rollDiceString = (diceString) => {
      if (!diceString) return 0;
      try {
          const match = diceString.toLowerCase().match(/(\d+)d(\d+)([-+]\d+)?/);
          if (!match) return parseInt(diceString) || 0; 

          const count = parseInt(match[1]);
          const sides = parseInt(match[2]);
          const modifier = match[3] ? parseInt(match[3]) : 0;

          let total = 0;
          for (let i = 0; i < count; i++) {
              total += Math.floor(Math.random() * sides) + 1;
          }
          return Math.max(1, total + modifier);
      } catch (e) {
          console.error("Error parsing dice:", diceString);
          return 0;
      }
  };

  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (userData) {
      const user = JSON.parse(userData);
      setCurrentUser(user);
      setIsGM(campaign.game_master_id === user.id);
      
      if (campaign.game_master_id === user.id) {
          setMiddleView('gmPlayers');
      } else {
          setMiddleView('inventory');
      }
    }
    if (campaign.current_location) {
        setCurrentLocation(campaign.current_location);
    }
  }, [campaign, campaign.game_master_id]);

  useEffect(() => {
    const loadHistory = async () => {
      try {
        const response = await api.get(`/multiplayer/campaigns/${campaign.id}/messages`);
        setMessages(response.data.map(msg => ({
            id: msg.id,
            type: msg.message_type,
            content: msg.content,
            username: msg.username || 'System',
            user_id: msg.user_id,
            timestamp: msg.timestamp,
            message_metadata: msg.message_metadata
        })));
      } catch (error) {
        console.error('❌ Failed to load history:', error);
      }
    };
    loadHistory();
  }, [campaign.id]);

  useEffect(() => {
    if (!campaign.id) return;
    const websocket = new WebSocket(`ws://localhost:8000/ws/campaign/${campaign.id}`);
    
    websocket.onopen = () => setConnected(true);
    
    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'session_paused') {
          alert('The Game Master has paused the session.');
          onEnd();
          return;
      }
      
      if (data.type === 'location_change') {
        setCurrentLocation(data.location || 'Unknown');
        return; 
      }

      if (data.type === 'message_update') {
          setMessages(prev => prev.map(msg => 
              msg.id === data.id ? { ...msg, content: data.content, message_metadata: data.message_metadata } : msg
          ));
          return;
      }
      
      setMessages(prev => [...prev, {
        id: data.id,
        type: data.message_type || data.type, 
        content: data.content,
        username: data.username || 'System',
        user_id: data.user_id,
        timestamp: data.timestamp || new Date().toISOString(),
        message_metadata: data.message_metadata
      }]);
    };
    
    websocket.onclose = () => setConnected(false);
    websocket.onerror = (error) => console.error('WebSocket error:', error);
    
    return () => { 
        if (websocket.readyState === WebSocket.OPEN) websocket.close(); 
    };
  }, [campaign.id, onEnd]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleLocationChange = useCallback(async (newLocation) => {
    if (!isGM) return;
    try {
      await api.post(`/multiplayer/campaigns/${campaign.id}/location`, null, { params: { location_name: newLocation } });
    } catch (error) { console.error(error); }
  }, [isGM, campaign.id]);

  const sendMessage = async (e) => {
    if (e) e.preventDefault();
    if (!inputMessage.trim() || !currentUser) return;
    try {
      await api.post(`/multiplayer/campaigns/${campaign.id}/messages`, {
        message_type: messageType,
        content: inputMessage,
        character_id: character?.id || null
      });
      setInputMessage('');
    } catch (error) { console.error(error); }
  };

  const handleSendEvent = async (type, content) => {
      try {
          await api.post(`/multiplayer/campaigns/${campaign.id}/messages`, {
              message_type: type, content: content, character_id: character?.id || null
          });
      } catch (error) { console.error(error); }
  };

  const handleQuickAction = (text) => { 
      setInputMessage(text); 
  };

  const handleAttributeRoll = async (attrName) => {
      if (!activeCharacterStats) return;
      
      const rawKey = attrName.toLowerCase();
      const score = activeCharacterStats[rawKey] || 10;
      const modifier = Math.floor((score - 10) / 2);

      try {
          await api.post(`/multiplayer/campaigns/${campaign.id}/messages`, {
              message_type: 'dice_roll',
              content: '', 
              character_id: character.id,
              dice_type: 20,
              dice_count: 1,
              modifier: modifier,
              metadata: { reason: attrName }
          });
      } catch (error) {
          console.error("Failed to roll dice:", error);
      }
  };

  const handleUpdateCombatState = async (messageId, oldContent, combatants, activeIndex) => {
      const updatedCombatants = combatants.map((c, idx) => ({
          ...c,
          active: idx === activeIndex 
      }));

      const activeName = activeIndex >= 0 ? updatedCombatants[activeIndex].name : "None";
      
      let oldData = {};
      try { oldData = JSON.parse(oldContent); } catch(e) { console.error(e); return; }

      const newData = {
          ...oldData,
          turn_text: activeName === "None" ? "Waiting for GM..." : `Active Turn: ${activeName}`,
          combatants: updatedCombatants
      };

      try {
          await api.put(`/multiplayer/campaigns/${campaign.id}/messages/${messageId}`, {
              content: JSON.stringify(newData),
              metadata: { original_type: 'combat_update' }
          });
      } catch (error) {
          console.error("Failed to update combat state:", error);
      }
  };

  const handleApplyDamage = async (messageId, combatData, damage, targetId) => {
      const targetIndex = combatData.combatants.findIndex(c => {
          if (c.type === 'npc') return c.id === targetId;
          if (c.type === 'player') {
              return c.id === targetId || c.user_id === targetId || c.id === `player_${targetId}` || c.userId === targetId;
          }
          return false;
      });

      if (targetIndex === -1) {
          console.error("Target not found:", targetId);
          return;
      }

      const target = combatData.combatants[targetIndex];
      const dr = target.dr || 0;
      const actualDamage = Math.max(0, damage - dr);
      const newHp = Math.max(0, target.hp - actualDamage);

      const newCombatants = [...combatData.combatants];
      newCombatants[targetIndex] = { ...target, hp: newHp };

      const newData = { ...combatData, combatants: newCombatants };

      try {
          await api.put(`/multiplayer/campaigns/${campaign.id}/messages/${messageId}`, {
              content: JSON.stringify(newData),
              metadata: { original_type: 'combat_update' }
          });
          
          if (target.type === 'player') {
              let realCharId = target.id;
              if (typeof realCharId === 'string' && realCharId.startsWith('player_')) {
                  realCharId = realCharId.replace('player_', '');
              }
              if (target.realId) realCharId = target.realId;

              if (realCharId && !isNaN(realCharId)) {
                  try {
                      await api.patch(`/characters/${realCharId}/stats`, { hp: newHp });
                  } catch (dbError) {
                      console.error("❌ Failed to update character HP in DB:", dbError);
                  }
              }
          }

          if (actualDamage > 0) {
              await api.post(`/multiplayer/campaigns/${campaign.id}/messages`, {
                  message_type: 'system',
                  content: `🩸 **${target.name}** took **${actualDamage}** damage! (HP: ${newHp}/${target.max_hp})`
              });
          } else {
              await api.post(`/multiplayer/campaigns/${campaign.id}/messages`, {
                  message_type: 'system',
                  content: `🛡️ **${target.name}**'s armor absorbed the hit! (0 Damage)`
              });
          }

      } catch (error) { 
          console.error("Failed to apply damage:", error); 
      }
  };

  const handleNpcAttack = async (messageId, combatData, npc) => {
      if (!npcTargetId) {
          alert("Select a target first!");
          return;
      }
      
      const damage = rollDiceString(npc.damage_dice || '1d4');
      
      await api.post(`/multiplayer/campaigns/${campaign.id}/messages`, {
          message_type: 'system',
          content: `⚔️ **${npc.name}** attacks with ${npc.damage_dice || '1d4'} and deals **${damage}** damage!`
      });

      await handleApplyDamage(messageId, combatData, damage, npcTargetId);
  };

  const handleEndCombat = async (messageId, oldContent) => {
      if (!window.confirm("Are you sure you want to end this combat event?")) return;

      let combatData = {};
      try { combatData = JSON.parse(oldContent); } catch (e) { return; }

      const newData = { ...combatData, ended: true, turn_text: "COMBAT ENDED" };

      try {
          await api.put(`/multiplayer/campaigns/${campaign.id}/messages/${messageId}`, {
              content: JSON.stringify(newData),
              metadata: { original_type: 'combat_update' }
          });

          await api.post(`/multiplayer/campaigns/${campaign.id}/messages`, {
              message_type: 'system',
              content: `🏆 **Combat Ended!** The encounter is over.`
          });
      } catch (error) {
          console.error("Failed to end combat:", error);
      }
  };

  const handleEndSession = async () => {
      if (!isGM) return;
      if (!window.confirm('Are you sure you want to end this session?')) return;
      try { await api.post(`/multiplayer/campaigns/${campaign.id}/pause`); } 
      catch (error) { console.error(error); }
  };

  // --- RENDEROWANIE WIADOMOŚCI ---
  const renderMessage = (msg, index) => {
    const isSystem = msg.type === 'system';
    const isMyMessage = msg.user_id === currentUser?.id;
    const isGMMessage = msg.type?.startsWith('gm_');
    const isDiceRoll = msg.type === 'dice_roll';
    const isDiceRollResult = msg.type === 'dice_roll_result';
    const isLocationChange = msg.type === 'location_change';
    const isNpcSpawn = msg.message_metadata?.original_type === 'npc_spawn' || msg.type === 'npc_spawn';
    const isCombatUpdate = msg.message_metadata?.original_type === 'combat_update' || msg.type === 'combat_update';
    
    // ✅ Sprawdzamy, czy nadawca jest GM-em (żeby go pokolorować na żółto)
    const isSenderGM = msg.user_id === campaign.game_master_id;

    if (isDiceRollResult || (isDiceRoll && msg.content.includes('rolled'))) {
        return (
            <div key={index} className="bg-purple-900 rounded-lg p-3 border-l-4 border-purple-500 max-w-md mx-auto my-2 shadow-lg">
                <div className="flex justify-between items-center mb-1">
                    <span className="text-purple-300 text-xs font-bold">🎲 {msg.username}</span>
                    <span className="text-purple-400 text-[10px] uppercase">{msg.message_metadata?.reason || 'Roll'}</span>
                </div>
                <div className="text-white text-center text-xl font-mono font-bold tracking-wider">{msg.content.split('=')[1] || msg.content}</div>
                <div className="text-gray-400 text-xs text-center mt-1">{msg.content.split('=')[0]}</div>
            </div>
        );
    }

    if (isNpcSpawn) {
        const npc = msg.message_metadata?.npc;
        return (
            <div key={index} className="bg-gray-800 border border-gray-600 rounded-lg p-4 max-w-2xl mx-auto my-4 shadow-2xl flex gap-6 items-center">
                <div className="w-24 h-24 bg-black rounded-lg border border-gray-500 overflow-hidden flex-shrink-0">
                    {npc?.image_url ? (
                        <img 
                            src={getProxiedImageUrl(npc.image_url)} 
                            className="w-full h-full object-cover" 
                            alt="NPC" 
                            crossOrigin="anonymous"
                        />
                    ) : (
                        <div className="w-full h-full flex items-center justify-center text-4xl">👾</div>
                    )}
                </div>
                <div className="flex-1">
                    <h4 className="text-2xl font-bold text-white mb-1">{npc?.name}</h4>
                    <p className="text-gray-400 text-sm mb-3">{npc?.race} • {npc?.attitude}</p>
                    <div className="flex gap-3 text-sm font-mono font-bold">
                        <span className="text-green-400 bg-gray-900 px-3 py-1 rounded border border-green-900">HP {npc?.hp}</span>
                        <span className="text-blue-400 bg-gray-900 px-3 py-1 rounded border border-blue-900">AC {npc?.armor_class}</span>
                        <span className="text-yellow-400 bg-gray-900 px-3 py-1 rounded border border-yellow-900">DR {npc?.damage_reduction}</span>
                    </div>
                    {npc?.damage_dice && <div className="mt-2 text-red-400 text-xs font-bold">⚔️ DMG: {npc.damage_dice}</div>}
                </div>
            </div>
        );
    }

    if (isCombatUpdate) {
        let combatData = {};
        try { combatData = JSON.parse(msg.content); } catch (e) { return <div key={index} className="text-red-500">Error parsing combat data</div>; }

        if (combatData.ended) {
            return (
                <div key={index} className="bg-gray-800/50 border border-gray-600 rounded p-4 text-center my-4 max-w-md mx-auto opacity-75">
                    <div className="text-gray-400 text-xs uppercase tracking-widest font-bold mb-1">Combat Encounter Finished</div>
                    <div className="text-white font-bold text-lg">Rounds: {combatData.round}</div>
                </div>
            );
        }

        return (
            <div key={index} className="my-6 border-2 border-red-600 rounded-lg overflow-hidden shadow-2xl bg-gray-900 max-w-2xl mx-auto relative">
                <div className="bg-gradient-to-r from-red-900 to-red-800 p-2 text-center border-b border-red-700">
                    <h3 className="text-white font-bold uppercase tracking-widest text-sm flex justify-center items-center gap-2">
                        ⚔️ Combat Event <span className="bg-black/30 px-2 rounded text-xs">Round {combatData.round}</span>
                    </h3>
                </div>

                <div className="bg-gray-800 p-2 text-center border-b border-gray-700 shadow-inner">
                    <p className="text-gray-400 text-xs uppercase font-bold mb-1">Current Turn</p>
                    <p className="text-xl text-yellow-400 font-bold animate-pulse">{combatData.turn_text || "Waiting..."}</p>
                </div>

                <div className="p-3 space-y-2 bg-black/20">
                    {combatData.combatants.map((c, i) => {
                        const isMe = c.type === 'player' && (c.user_id === currentUser?.id || c.userId === currentUser?.id);
                        const canControl = (c.active && isMe) || (c.active && c.type === 'npc' && isGM);
                        
                        return (
                            <div key={i} className={`flex flex-col rounded border transition-all ${c.active ? 'bg-yellow-900/30 border-yellow-500 shadow-[0_0_15px_rgba(234,179,8,0.1)]' : 'bg-gray-800/50 border-gray-700 opacity-80'}`}>
                                <div className="flex justify-between items-center p-3">
                                    <div className="flex items-center gap-4">
                                        <div className={`w-12 h-12 rounded-lg flex items-center justify-center text-2xl overflow-hidden border border-gray-600 ${c.type === 'player' ? 'bg-blue-900' : 'bg-red-900'}`}>
                                            {c.image_url ? (
                                                <img 
                                                    src={getProxiedImageUrl(c.image_url)} 
                                                    className="w-full h-full object-cover" 
                                                    alt="" 
                                                    crossOrigin="anonymous"
                                                />
                                            ) : (c.type === 'player' ? '👤' : '👾')}
                                        </div>
                                        
                                        <div>
                                            <span className={`font-bold text-base block ${c.active ? 'text-yellow-300' : 'text-gray-300'}`}>
                                                {c.name} {isMe && <span className="text-[10px] text-blue-400 ml-1">(YOU)</span>}
                                            </span>
                                            <div className="flex gap-3 text-xs font-mono mt-1">
                                                <span className={`${c.hp < c.max_hp/2 ? 'text-red-500 font-bold' : 'text-green-500'}`}>HP: {c.hp}/{c.max_hp}</span>
                                                <span className="text-blue-400">AC: {c.ac}</span>
                                                <span className="text-gray-500">DR: {c.dr}</span>
                                            </div>
                                        </div>
                                    </div>

                                    {isGM && (
                                        <button 
                                            onClick={() => handleUpdateCombatState(msg.id, msg.content, combatData.combatants, c.active ? -1 : i)}
                                            className={`px-3 py-1 rounded text-xs font-bold border ${c.active ? 'bg-yellow-600 text-black border-yellow-500' : 'bg-gray-700 text-gray-400 border-gray-600 hover:bg-gray-600'}`}
                                        >
                                            {c.active ? 'ACTIVE' : 'Activate'}
                                        </button>
                                    )}
                                </div>

                                {canControl && (
                                    <div className="p-3 border-t border-yellow-500/30 bg-yellow-900/10 animate-fadeIn">
                                        <p className="text-yellow-400 text-xs font-bold mb-2 text-center uppercase">
                                            ⚡ {isMe ? "It's your turn!" : `Controlling ${c.name}`}
                                        </p>
                                        
                                        {c.type === 'npc' ? (
                                            <div className="flex gap-2 items-center justify-center">
                                                <select 
                                                    className="bg-gray-800 text-white p-2 rounded text-sm border border-gray-600 outline-none"
                                                    value={npcTargetId}
                                                    onChange={(e) => setNpcTargetId(e.target.value)}
                                                >
                                                    <option value="">Select Target...</option>
                                                    {combatData.combatants.filter(t => t.id !== c.id).map(t => (
                                                        <option key={t.id} value={t.id}>{t.name} (HP: {t.hp})</option>
                                                    ))}
                                                </select>
                                                <button 
                                                    onClick={() => handleNpcAttack(msg.id, combatData, c)}
                                                    className="bg-red-600 hover:bg-red-500 text-white px-4 py-2 rounded font-bold shadow-lg transition"
                                                >
                                                    Attack ({c.damage_dice || '1d4'})
                                                </button>
                                            </div>
                                        ) : (
                                            <DiceRoller 
                                                campaignId={campaign.id} 
                                                characterId={character?.id} 
                                                characterStats={activeCharacterStats} 
                                                targets={combatData.combatants.filter(target => target.id !== c.id)}
                                                onAttack={(damage, targetId) => handleApplyDamage(msg.id, combatData, damage, targetId)}
                                            />
                                        )}
                                        
                                        <div className="mt-2 flex gap-2 justify-center">
                                            <button onClick={() => handleQuickAction(`I take the Dodge action.`)} className="bg-blue-700 hover:bg-blue-600 text-white px-3 py-1 rounded text-xs font-bold">🛡️ Dodge</button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>

                {isGM && (
                    <div className="bg-gray-800 p-2 border-t border-gray-700 text-center">
                        <button 
                            onClick={() => handleEndCombat(msg.id, msg.content)}
                            className="bg-red-900/80 hover:bg-red-800 text-red-200 text-xs px-4 py-2 rounded border border-red-700 font-bold transition uppercase tracking-wide"
                        >
                            🏁 End Combat Event
                        </button>
                    </div>
                )}
            </div>
        );
    }

    if (isLocationChange) return (
        <div key={index} className="bg-yellow-900 rounded-lg p-3 border-l-4 border-yellow-500 max-w-md mx-auto">
          <div className="text-white text-center font-semibold">{msg.content}</div>
        </div>
    );

    if (isGMMessage) return (
        <div key={index} className="bg-gradient-to-r from-yellow-900 to-orange-900 rounded-lg p-4 border-l-4 border-yellow-500">
          <div className="flex items-center gap-2 text-yellow-300 text-xs mb-2">
            <span className="font-bold">🎭 GM</span><span>•</span><span>{msg.username}</span>
          </div>
          <div className="text-white font-medium">{msg.content}</div>
        </div>
    );

    if (isSystem) return (
        <div key={index} className="bg-gray-700 rounded-lg p-3 text-center max-w-md mx-auto">
          <div className="text-gray-300 text-sm">{msg.content}</div>
        </div>
    );

    // ✅ ZMODYFIKOWANA SEKCJA RENDEROWANIA ZWYKŁYCH WIADOMOŚCI
    return (
      <div 
        key={index} 
        className={`rounded-lg p-3 my-1 ${
            isMyMessage 
                ? 'bg-blue-900 ml-auto max-w-3xl' 
                : isSenderGM 
                    ? 'bg-yellow-900/20 border border-yellow-600/50 max-w-3xl shadow-[0_0_10px_rgba(234,179,8,0.1)]' // STYL DLA GM
                    : 'bg-gray-800 max-w-3xl'
        }`}
      >
        <div className={`text-xs mb-1 ${isSenderGM && !isMyMessage ? 'text-yellow-500 font-bold' : 'text-gray-400'}`}>
          {/* Dodaj ikonkę korony dla GM */}
          {isSenderGM && !isMyMessage && '👑 '} 
          {msg.username} • {new Date(msg.timestamp).toLocaleTimeString('pl-PL')}
        </div>
        <div className={isSenderGM && !isMyMessage ? 'text-yellow-100' : 'text-white'}>
            {msg.content}
        </div>
      </div>
    );
  };

  const renderPanelButtons = () => {
    if (isGM) {
      return (
        <>
          <button onClick={() => setMiddleView('gmPlayers')} className={`px-4 py-2 rounded-lg font-semibold transition ${middleView === 'gmPlayers' ? 'bg-purple-600' : 'bg-gray-700 hover:bg-gray-600'}`}>👑 Players</button>
          <button onClick={() => setMiddleView('npcCreator')} className={`px-4 py-2 rounded-lg font-semibold transition ${middleView === 'npcCreator' ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'}`}>👤 Create NPC</button>
          <button onClick={() => setMiddleView('compendium')} className={`px-4 py-2 rounded-lg font-semibold transition ${middleView === 'compendium' ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'}`}>📚 Compendium</button>
          <button onClick={() => setMiddleView('combat')} className={`px-4 py-2 rounded-lg font-semibold transition ${middleView === 'combat' ? 'bg-red-600' : 'bg-gray-700 hover:bg-gray-600'}`}>⚔️ Combat</button>
        </>
      );
    } else {
      return (
        <>
          <button onClick={() => setMiddleView('inventory')} className={`px-4 py-2 rounded-lg font-semibold transition ${middleView === 'inventory' ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'}`}>🎒 Inventory</button>
          <button onClick={() => setMiddleView('compendium')} className={`px-4 py-2 rounded-lg font-semibold transition ${middleView === 'compendium' ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'}`}>📚 Compendium</button>
        </>
      );
    }
  };

  const renderMiddlePanel = () => {
    if (isGM) {
      switch (middleView) {
        case 'gmPlayers': return <GMPlayerManager campaign={campaign} isGM={isGM} universe={campaign.universe} />;
        case 'npcCreator': return <NpcCreator campaignId={campaign.id} universe={campaign.universe} />;
        case 'compendium': return <CompendiumBrowser universe={campaign.universe} />;
        case 'combat': return <CombatTracker campaignId={campaign.id} onSendEvent={handleSendEvent} />;
        default: return <GMPlayerManager campaign={campaign} isGM={isGM} universe={campaign.universe} />;
      }
    } else {
      switch (middleView) {
        case 'inventory': return <PlayerInventoryPanel campaignId={campaign.id} userId={currentUser.id} isGM={false} />;
        case 'compendium': return <CompendiumBrowser universe={campaign.universe} />;
        case 'combat': return <CombatTracker campaignId={campaign.id} onSendEvent={handleSendEvent} />;
        default: return <PlayerInventoryPanel campaignId={campaign.id} userId={currentUser.id} isGM={false} />;
      }
    }
  };
  
  const renderRightPanel = () => {
    if (isGM) {
      return <LocationSelector universe={campaign.universe} onLocationChange={handleLocationChange} currentLocation={currentLocation} isGM={isGM} />;
    } else {
      return <PlayerCharacterSheet campaignId={campaign.id} userId={currentUser.id} characterName={character?.name} onStatsUpdate={setActiveCharacterStats} />;
    }
  };

  return (
    <div className="fixed inset-0 flex bg-gray-900 text-white">
      <div className="w-1/3 flex flex-col h-full border-r border-gray-700">
        <div className="bg-gray-800 border-b border-gray-700 p-4 flex-shrink-0">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-xl font-bold text-white">{campaign.title}</h3>
              <div className="flex items-center gap-4 mt-1">
                <p className="text-gray-400 text-sm">
                  {connected ? '🟢 Connected' : '🔴 Disconnected'}
                  {isGM && <span className="ml-2 text-yellow-400">👑 Game Master</span>}
                </p>
              </div>
            </div>
            <button onClick={isGM ? handleEndSession : onEnd} className={`px-4 py-2 rounded-lg font-semibold transition ${isGM ? 'bg-red-600 hover:bg-red-700' : 'bg-gray-600 hover:bg-gray-700'}`}>
              {isGM ? 'End Session' : 'Leave'}
            </button>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.map((msg, index) => renderMessage(msg, index))}
          <div ref={messagesEndRef} />
        </div>
        
        <div className="bg-gray-800 border-t border-gray-700 p-4 flex-shrink-0">
          
          {!isGM && activeCharacterStats && (
            <div className="flex flex-wrap gap-2 mb-3 justify-center">
                {['Strength', 'Dexterity', 'Constitution', 'Intelligence', 'Wisdom', 'Charisma'].map(attr => {
                    const short = attr.slice(0, 3).toUpperCase();
                    const val = activeCharacterStats[attr.toLowerCase()] || 10;
                    const mod = Math.floor((val - 10) / 2);
                    const sign = mod >= 0 ? '+' : '';
                    
                    return (
                        <button 
                            key={attr}
                            onClick={() => handleAttributeRoll(attr)}
                            className="bg-gray-700 hover:bg-gray-600 text-xs px-2 py-1 rounded border border-gray-600 text-gray-300 transition flex items-center gap-1"
                            title={`Roll ${attr}`}
                        >
                            <span className="font-bold">{short}</span>
                            <span className={mod >= 0 ? "text-green-400" : "text-red-400"}>
                                {sign}{mod}
                            </span>
                        </button>
                    );
                })}
            </div>
          )}

          <form onSubmit={sendMessage} className="flex gap-3 mt-2">
            <input type="text" value={inputMessage} onChange={(e) => setInputMessage(e.target.value)} placeholder={isGM ? "Narrate, describe events..." : "Describe your action..."} className="flex-1 bg-gray-700 text-white px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            <button type="submit" className="bg-blue-600 hover:bg-blue-700 px-6 py-2 rounded-lg font-semibold transition">Send</button>
          </form>
        </div>
      </div>
      <div className="w-1/3 flex flex-col h-full border-r border-gray-700">
        <div className="bg-gray-800 border-b border-gray-700 p-4 flex-shrink-0">
          <div className="flex gap-2">{renderPanelButtons()}</div>
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          {currentUser && renderMiddlePanel()}
        </div>
      </div>
      <div className="w-1/3 flex flex-col h-full">
         <div className="bg-gray-800 border-b border-gray-700 p-4 flex-shrink-0">
             <h3 className="text-xl font-bold text-white">📍 Current Location</h3>
             <p className="text-yellow-400 text-lg font-semibold">{currentLocation}</p>
         </div>
         <div className="flex-1 overflow-y-auto p-4">
            {currentUser && renderRightPanel()}
         </div>
      </div>
    </div>
  );
}

export default MultiplayerSession;