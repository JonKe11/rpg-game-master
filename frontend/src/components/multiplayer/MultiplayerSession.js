// frontend/src/components/multiplayer/MultiplayerSession.js
// ✅ WERSJA 4.1 - Logika "End Session" dla GM

import React, { useState, useEffect, useRef } from 'react';
import api from '../../api/axiosConfig';
import LocationSelector from './LocationSelector';
import PlayerInventoryPanel from './PlayerInventoryPanel';
import GMPlayerManager from './GMPlayerManager';
import CompendiumBrowser from './CompendiumBrowser';
import NpcCreator from './NpcCreator';
import PlayerCharacterSheet from './PlayerCharacterSheet';
import DiceRoller from './DiceRoller';

function MultiplayerSession({ campaign, character, onEnd }) {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [messageType, setMessageType] = useState('player_action');
  const [connected, setConnected] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [isGM, setIsGM] = useState(false);
  const [currentLocation, setCurrentLocation] = useState('Unknown');

  // 'compendium', 'npcCreator', 'gmPlayers', 'inventory'
  const [middleView, setMiddleView] = useState('compendium'); 
  
  const messagesEndRef = useRef(null);

  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (userData) {
      const user = JSON.parse(userData);
      setCurrentUser(user);
      setIsGM(campaign.game_master_id === user.id);
      
      // Ustaw domyślny widok
      if (campaign.game_master_id === user.id) {
          setMiddleView('gmPlayers');
      } else {
          setMiddleView('inventory');
      }
    }
    // Ustaw lokację początkową
    if (campaign.current_location) {
        setCurrentLocation(campaign.current_location);
    }
  }, [campaign, campaign.game_master_id]);

  useEffect(() => {
    const loadHistory = async () => {
      try {
        const response = await api.get(`/multiplayer/campaigns/${campaign.id}/messages`);
        setMessages(response.data.map(msg => ({
          type: msg.message_type,
          content: msg.content,
          username: msg.username || 'System',
          user_id: msg.user_id,
          timestamp: msg.timestamp,
          message_metadata: msg.message_metadata // ✅ Ważne dla NPC
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

      // ✅ MODYFIKACJA: Obsługa pauzy
      if (data.type === 'session_paused') {
          alert('The Game Master has paused the session. Returning to campaign list.');
          onEnd(); // Wyjdź do listy kampanii
          return; // Nie przetwarzaj dalej
      }
      
      if (data.type === 'location_change') {
        // Backend broadcastuje 'location' i 'location_image_url'
        setCurrentLocation(data.location || 'Unknown');
      }
      
      setMessages(prev => [...prev, {
        type: data.type,
        content: data.content,
        username: data.username || 'System',
        user_id: data.user_id,
        timestamp: data.timestamp || new Date().toISOString(),
        message_metadata: data.message_metadata // ✅ Ważne dla NPC
      }]);
    };
    websocket.onclose = () => setConnected(false);
    websocket.onerror = (error) => console.error('WebSocket error:', error);
    return () => {
      if (websocket.readyState === WebSocket.OPEN) websocket.close();
    };
  }, [campaign.id, onEnd]); // ✅ MODYFIKACJA: Dodano onEnd

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleLocationChange = async (newLocation) => {
    if (!isGM) return;
    try {
      // Używamy dedykowanego endpointu, który istnieje w multiplayer.py
      await api.post(
          `/multiplayer/campaigns/${campaign.id}/location`, 
          null, // Brak body
          { params: { location_name: newLocation } }
      );
    } catch (error) {
        console.error('Failed to change location via /location endpoint:', error);
        // Fallback (jeśli /location zawiedzie, spróbuj starego)
        try {
            await api.post(`/multiplayer/campaigns/${campaign.id}/messages`, {
                message_type: 'location_change',
                content: `📍 GM changed location to: ${newLocation}`,
                character_id: character.id,
                metadata: { location: newLocation }
            });
        } catch (e) {
            console.error('Failed to change location via /messages:', e);
        }
    }
  };

  const sendMessage = async (e, customType = null) => {
    if (e) e.preventDefault();
    if (!inputMessage.trim() || !currentUser) return;
    const finalType = customType || messageType;
    try {
      await api.post(`/multiplayer/campaigns/${campaign.id}/messages`, {
        message_type: finalType,
        content: inputMessage,
        character_id: character.id
      });
      setInputMessage('');
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const handleGMAction = (type) => {
    setMessageType(type);
    const placeholders = {
      'gm_narration': 'You enter a dimly lit cantina...',
      'gm_event': 'Suddenly, blaster fire erupts!',
      'gm_choice': 'What do you do? A) Fight B) Run C) Negotiate'
    };
    setInputMessage(placeholders[type] || '');
  };
  
  const handleQuickAction = (text, type = 'player_action') => {
    setInputMessage(text);
    setMessageType(type);
  };

  // ✅ NOWA FUNKCJA: GM pauzuje sesję
  const handleEndSession = async () => {
      if (!isGM) return;
      if (!window.confirm('Are you sure you want to end this session? All players will be disconnected and the game will be paused.')) {
          return;
      }
      
      try {
          // Wywołaj nowy endpoint pauzy
          await api.post(`/multiplayer/campaigns/${campaign.id}/pause`);
          // onEnd() zostanie wywołane automatycznie przez WebSocket (session_paused)
      } catch (error) {
          console.error('Failed to pause session:', error);
          alert('Could not pause session. Please try again.');
      }
  };

  const renderMessage = (msg, index) => {
    const isSystem = msg.type === 'system';
    const isMyMessage = msg.user_id === currentUser?.id;
    const isGMMessage = msg.type?.startsWith('gm_');
    const isDiceRoll = msg.type === 'dice_roll';
    const isLocationChange = msg.type === 'location_change';
    const isDiceRollResult = msg.type === 'dice_roll_result';
    const isNpcSpawn = msg.type === 'npc_spawn';

    if (isDiceRollResult) {
        return (
            <div key={index} className="bg-purple-900 rounded-lg p-3 border-l-4 border-purple-500 max-w-md mx-auto my-2">
                <div className="text-purple-300 text-xs mb-1 text-center font-bold">
                    🎲 {msg.username} rolled dice
                </div>
                <div className="text-white text-center text-lg font-mono">{msg.content}</div>
            </div>
        );
    }

    if (isNpcSpawn) {
        const npc = msg.message_metadata?.npc;
        return (
            <div key={index} className="bg-gray-800 border border-gray-600 rounded-lg p-4 max-w-md mx-auto my-2">
                <div className="flex gap-4">
                    {npc?.image_url && (
                        <img src={npc.image_url} className="w-20 h-20 object-cover rounded bg-gray-900" alt="NPC" />
                    )}
                    <div className="flex-1">
                        <h4 className="text-white font-bold text-lg">{npc?.name || 'Unknown NPC'}</h4>
                        <p className="text-gray-400 text-sm mb-2">{npc?.race}</p>
                        {npc?.stats && (
                            <div className="grid grid-cols-3 gap-1 text-center">
                                {Object.entries(npc.stats).map(([k,v]) => (
                                    <div key={k} className="bg-gray-700 rounded px-1 py-0.5">
                                        <span className="text-[10px] text-gray-400 block uppercase">{k.slice(0,3)}</span>
                                        <span className="text-xs text-white font-bold">{v}</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        );
    }

    if (isLocationChange) {
      return (
        <div key={index} className="bg-yellow-900 rounded-lg p-3 border-l-4 border-yellow-500 max-w-md mx-auto">
          <div className="text-yellow-300 text-xs mb-1 text-center">
            📍 Location Changed
          </div>
          <div className="text-white text-center font-semibold">{msg.content}</div>
        </div>
      );
    }

    if (isGMMessage) {
      return (
        <div key={index} className="bg-gradient-to-r from-yellow-900 to-orange-900 rounded-lg p-4 border-l-4 border-yellow-500">
          <div className="flex items-center gap-2 text-yellow-300 text-xs mb-2">
            <span className="font-bold">🎭 GM</span>
            <span>•</span>
            <span>{msg.username}</span>
            <span>•</span>
            <span>{new Date(msg.timestamp).toLocaleTimeString('pl-PL')}</span>
          </div>
          <div className="text-white font-medium">{msg.content}</div>
        </div>
      );
    }
    if (isDiceRoll) {
      return (
        <div key={index} className="bg-green-900 rounded-lg p-3 border-l-4 border-green-500 max-w-md mx-auto">
          <div className="text-green-300 text-xs mb-1 text-center">
            🎲 {msg.username}
          </div>
          <div className="text-white text-center font-bold">{msg.content}</div>
        </div>
      );
    }
    if (isSystem) {
      return (
        <div key={index} className="bg-gray-700 rounded-lg p-3 text-center max-w-md mx-auto">
          <div className="text-gray-300 text-sm">{msg.content}</div>
        </div>
      );
    }
    return (
      <div 
        key={index} 
        className={`rounded-lg p-3 ${
          isMyMessage ? 'bg-blue-900 ml-auto max-w-3xl' : 'bg-gray-800 max-w-3xl'
        }`}
      >
        <div className="text-xs text-gray-400 mb-1">
          {msg.username} • {new Date(msg.timestamp).toLocaleTimeString('pl-PL')}
        </div>
        <div className="text-white">{msg.content}</div>
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
        default: return <GMPlayerManager campaign={campaign} isGM={isGM} universe={campaign.universe} />;
      }
    } else {
      switch (middleView) {
        case 'inventory': return <PlayerInventoryPanel campaignId={campaign.id} userId={currentUser.id} isGM={false} />;
        case 'compendium': return <CompendiumBrowser universe={campaign.universe} />;
        default: return <PlayerInventoryPanel campaignId={campaign.id} userId={currentUser.id} isGM={false} />;
      }
    }
  };
  
  const renderRightPanel = () => {
    if (isGM) {
      return (
        <LocationSelector
          universe={campaign.universe}
          onLocationChange={handleLocationChange}
          currentLocation={currentLocation}
          isGM={isGM}
        />
      );
    } else {
      return (
        <PlayerCharacterSheet 
            campaignId={campaign.id}
            userId={currentUser.id}
            characterName={character.name}
        />
      );
    }
  };

  return (
    <div className="fixed inset-0 flex bg-gray-900 text-white">
      
      {/* Kolumna 1: Czat */}
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
            
            {/* ✅ MODYFIKACJA: Przycisk Leave/End Session */}
            <button
              onClick={isGM ? handleEndSession : onEnd}
              className={`px-4 py-2 rounded-lg font-semibold transition ${
                isGM 
                ? 'bg-red-600 hover:bg-red-700' 
                : 'bg-gray-600 hover:bg-gray-700'
              }`}
            >
              {isGM ? 'End Session' : 'Leave'}
            </button>
            
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.map((msg, index) => renderMessage(msg, index))}
          <div ref={messagesEndRef} />
        </div>

        <div className="bg-gray-800 border-t border-gray-700 p-4 flex-shrink-0">
          {isGM && (
            <div className="mb-4 bg-gradient-to-r from-purple-900 to-indigo-900 rounded-lg p-4 border-l-4 border-purple-500">
              <div className="flex gap-2 flex-wrap">
                <button onClick={() => handleGMAction('gm_narration')} className="bg-yellow-700 hover:bg-yellow-600 px-3 py-2 rounded text-sm font-semibold">📖 Narration</button>
                <button onClick={() => handleGMAction('gm_event')} className="bg-orange-700 hover:bg-orange-600 px-3 py-2 rounded text-sm font-semibold">⚡ Event</button>
                <button onClick={() => handleGMAction('gm_choice')} className="bg-blue-700 hover:bg-blue-600 px-3 py-2 rounded text-sm font-semibold">🎯 Choice</button>
              </div>
            </div>
          )}
          {!isGM && (
            <div className="flex gap-2 mb-3">
              <button onClick={() => handleQuickAction('I look around the room')} className="bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded text-sm text-gray-300">👁️ Look Around</button>
            </div>
          )}
          
          <DiceRoller campaignId={campaign.id} characterId={character.id} />
          
          <form onSubmit={sendMessage} className="flex gap-3 mt-2">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder={isGM ? "Narrate, describe events..." : "Describe your action..."}
              className="flex-1 bg-gray-700 text-white px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button type="submit" className="bg-blue-600 hover:bg-blue-700 px-6 py-2 rounded-lg font-semibold transition">Send</button>
          </form>
        </div>
      </div>

      {/* Kolumna 2: Panel Główny */}
      <div className="w-1/3 flex flex-col h-full border-r border-gray-700">
        <div className="bg-gray-800 border-b border-gray-700 p-4 flex-shrink-0">
          <div className="flex gap-2">{renderPanelButtons()}</div>
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          {currentUser && renderMiddlePanel()}
        </div>
      </div>

      {/* Kolumna 3: Panel Kontekstowy */}
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