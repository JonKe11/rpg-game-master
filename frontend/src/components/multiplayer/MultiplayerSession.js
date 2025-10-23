// frontend/src/components/multiplayer/MultiplayerSession.js

import React, { useState, useEffect, useRef } from 'react';
import api from '../../api/axiosConfig';
import LocationSelector from './LocationSelector';  // ✨ DODANE!
import ItemBrowser from './ItemBrowser';            // ✨ DODANE!

function MultiplayerSession({ campaign, character, onEnd }) {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [messageType, setMessageType] = useState('player_action');
  const [connected, setConnected] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [isGM, setIsGM] = useState(false);
  
  // ✨ DODANE STATE!
  const [currentLocation, setCurrentLocation] = useState('Unknown');
  const [showLocationSelector, setShowLocationSelector] = useState(false);
  const [showItemBrowser, setShowItemBrowser] = useState(false);
  
  const messagesEndRef = useRef(null);

  // ✅ DEBUGOWANIE - sprawdź co się dzieje z GM detection
  useEffect(() => {
    console.log('🎮 Campaign data received:', campaign);
    
    const userData = localStorage.getItem('user');
    if (userData) {
      const user = JSON.parse(userData);
      console.log('👤 Current user:', user);
      console.log('👤 User ID:', user.id);
      console.log('👑 GM ID from campaign:', campaign.game_master_id);
      console.log('🎭 Is GM? (user.id === campaign.game_master_id):', user.id === campaign.game_master_id);
      
      setCurrentUser(user);
      setIsGM(campaign.game_master_id === user.id);
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
          timestamp: msg.timestamp
        })));
        console.log('✅ Loaded message history:', response.data.length, 'messages');
      } catch (error) {
        console.error('❌ Failed to load history:', error);
      }
    };

    loadHistory();
  }, [campaign.id]);

  useEffect(() => {
    if (!campaign.id) return;

    const websocket = new WebSocket(`ws://localhost:8000/ws/campaign/${campaign.id}`);

    websocket.onopen = () => {
      console.log('✅ WebSocket connected to campaign', campaign.id);
      setConnected(true);
    };

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('📨 Received:', data);
      
      // ✨ DODANE: Handle location changes
      if (data.type === 'location_change' && data.metadata?.location) {
        setCurrentLocation(data.metadata.location);
      }
      
      setMessages(prev => [...prev, {
        type: data.type,
        content: data.content,
        username: data.username || 'System',
        user_id: data.user_id,
        timestamp: data.timestamp || new Date().toISOString()
      }]);
    };

    websocket.onclose = () => {
      console.log('❌ WebSocket disconnected');
      setConnected(false);
    };

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return () => {
      if (websocket.readyState === WebSocket.OPEN) {
        websocket.close();
      }
    };
  }, [campaign.id]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // ✨ NOWA FUNKCJA!
  const handleLocationChange = async (newLocation) => {
    if (!isGM) return; // Tylko GM może zmieniać
    
    setCurrentLocation(newLocation);
    
    // Wyślij przez WebSocket
    try {
      await api.post(`/multiplayer/campaigns/${campaign.id}/messages`, {
        message_type: 'location_change',
        content: `📍 GM changed location to: ${newLocation}`,
        character_id: character.id,
        metadata: { location: newLocation }
      });
      
      setShowLocationSelector(false);
    } catch (error) {
      console.error('Failed to change location:', error);
    }
  };

  // ✨ NOWA FUNKCJA!
  const handleItemSelect = async (itemName) => {
    if (!isGM) return; // Tylko GM może dodawać itemy
    
    // Wyślij przez WebSocket
    try {
      await api.post(`/multiplayer/campaigns/${campaign.id}/messages`, {
        message_type: 'gm_event',
        content: `🎒 GM added item: ${itemName}`,
        character_id: character.id,
        metadata: { item: itemName }
      });
    } catch (error) {
      console.error('Failed to add item:', error);
    }
  };

  const sendMessage = async (e, customType = null) => {
    if (e) e.preventDefault();
    
    if (!inputMessage.trim() || !currentUser) return;

    const typeToSend = customType || messageType;

    try {
      await api.post(`/multiplayer/campaigns/${campaign.id}/messages`, {
        message_type: typeToSend,
        content: inputMessage,
        character_id: character.id,
        metadata: {}
      });

      setInputMessage('');
    } catch (error) {
      console.error('Failed to send message:', error);
      alert('Failed to send message');
    }
  };

  const handleQuickAction = (text, type = 'player_action') => {
    setInputMessage(text);
    setMessageType(type);
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

  const renderMessage = (msg, index) => {
    const isSystem = msg.type === 'system';
    const isMyMessage = msg.user_id === currentUser?.id;
    const isGMMessage = msg.type?.startsWith('gm_');
    const isDiceRoll = msg.type === 'dice_roll';
    const isLocationChange = msg.type === 'location_change';  // ✨ DODANE!

    // ✨ LOCATION CHANGE MESSAGE
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

  return (
    <div className="fixed inset-0 flex bg-gray-900">
      {/* ✨ MAIN CONTENT - FLEX LAYOUT */}
      <div className={`flex-1 flex flex-col transition-all ${
        showLocationSelector || showItemBrowser ? 'w-1/2' : 'w-full'
      }`}>
        {/* Header */}
        <div className="bg-gray-800 border-b border-gray-700 p-4 flex-shrink-0">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-xl font-bold text-white">{campaign.title}</h3>
              <div className="flex items-center gap-4 mt-1">
                <p className="text-gray-400 text-sm">
                  {connected ? '🟢 Connected' : '🔴 Disconnected'}
                  {isGM && <span className="ml-2 text-yellow-400">👑 Game Master</span>}
                </p>
                {/* ✨ LOKACJA */}
                <p className="text-yellow-400 text-sm">
                  📍 {currentLocation}
                </p>
              </div>
            </div>
            
            {/* ✨ GM TOOLS BUTTONS */}
            <div className="flex gap-2">
              {isGM && (
                <>
                  <button
                    onClick={() => setShowLocationSelector(!showLocationSelector)}
                    className={`px-4 py-2 rounded-lg font-semibold transition ${
                      showLocationSelector 
                        ? 'bg-yellow-600 hover:bg-yellow-700' 
                        : 'bg-gray-700 hover:bg-gray-600'
                    }`}
                  >
                    📍 Location
                  </button>
                  <button
                    onClick={() => setShowItemBrowser(!showItemBrowser)}
                    className={`px-4 py-2 rounded-lg font-semibold transition ${
                      showItemBrowser 
                        ? 'bg-purple-600 hover:bg-purple-700' 
                        : 'bg-gray-700 hover:bg-gray-600'
                    }`}
                  >
                    🎒 Items
                  </button>
                </>
              )}
              <button
                onClick={onEnd}
                className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg transition"
              >
                End
              </button>
            </div>
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="max-w-4xl mx-auto space-y-3 pb-32">
            {messages.length === 0 && (
              <div className="text-center text-gray-400 py-8">
                <p className="text-lg">🎲 Campaign has started!</p>
                <p className="text-sm mt-2">
                  {isGM ? 'Start the adventure with your narration...' : 'Wait for the GM to begin...'}
                </p>
              </div>
            )}
            
            {messages.map((msg, index) => renderMessage(msg, index))}
            
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area - FIXED BOTTOM */}
        <div className="bg-gray-800 border-t border-gray-700 p-4">
          <div className="max-w-4xl mx-auto">
            
            {/* GM CONTROLS - tylko dla GM */}
            {isGM && (
              <div className="mb-4 bg-gradient-to-r from-purple-900 to-indigo-900 rounded-lg p-4 border-l-4 border-purple-500">
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-yellow-400 font-bold">🎭 GM Controls</span>
                </div>
                <div className="flex gap-2 flex-wrap">
                  <button
                    onClick={() => handleGMAction('gm_narration')}
                    className="bg-yellow-700 hover:bg-yellow-600 px-3 py-2 rounded text-sm font-semibold transition flex items-center gap-2"
                  >
                    📖 Narration
                  </button>
                  <button
                    onClick={() => handleGMAction('gm_event')}
                    className="bg-orange-700 hover:bg-orange-600 px-3 py-2 rounded text-sm font-semibold transition flex items-center gap-2"
                  >
                    ⚡ Event
                  </button>
                  <button
                    onClick={() => handleGMAction('gm_choice')}
                    className="bg-blue-700 hover:bg-blue-600 px-3 py-2 rounded text-sm font-semibold transition flex items-center gap-2"
                  >
                    🎯 Choice
                  </button>
                </div>
              </div>
            )}

            {/* PLAYER Quick Actions - tylko dla graczy */}
            {!isGM && (
              <div className="flex gap-2 mb-3">
                <button
                  onClick={() => handleQuickAction('I look around the room')}
                  className="bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded text-sm text-gray-300 transition"
                >
                  👁️ Look Around
                </button>
                <button
                  onClick={() => handleQuickAction('I talk to the NPC', 'player_speech')}
                  className="bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded text-sm text-gray-300 transition"
                >
                  💬 Talk
                </button>
                <button
                  onClick={() => handleQuickAction('I search for items')}
                  className="bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded text-sm text-gray-300 transition"
                >
                  🔍 Search
                </button>
              </div>
            )}

            {/* Message Input */}
            <form onSubmit={sendMessage} className="flex gap-3">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder={isGM ? "Narrate the story..." : "What do you do? Type your action..."}
                className="flex-1 px-4 py-3 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={!connected}
              />
              <button
                type="submit"
                disabled={!connected || !inputMessage.trim()}
                className={`${
                  isGM ? 'bg-yellow-600 hover:bg-yellow-700' : 'bg-blue-600 hover:bg-blue-700'
                } disabled:bg-gray-600 px-6 py-3 rounded-lg font-semibold transition`}
              >
                Send
              </button>
            </form>

            <p className="text-gray-500 text-xs mt-2 text-center">
              {isGM ? (
                <span>Playing as: <span className="text-yellow-400 font-bold">Game Master 🎭</span></span>
              ) : (
                <span>Playing as: <span className="text-white">{character.name}</span> ({character.class_type})</span>
              )}
            </p>
          </div>
        </div>
      </div>

      {/* ✨ LOCATION SELECTOR SIDEBAR (GM ONLY!) */}
      {showLocationSelector && isGM && (
        <div className="w-1/2 border-l border-gray-700 overflow-y-auto bg-gray-900">
          <LocationSelector
            currentLocation={currentLocation}
            onLocationChange={handleLocationChange}
            universe={campaign.universe || 'star_wars'}
            isGM={isGM}
          />
        </div>
      )}

      {/* ✨ ITEM BROWSER SIDEBAR (GM ONLY!) */}
      {showItemBrowser && isGM && (
        <div className="w-1/2 border-l border-gray-700 overflow-y-auto bg-gray-900">
          <ItemBrowser
            onItemSelect={handleItemSelect}
            universe={campaign.universe || 'star_wars'}
            isGM={isGM}
          />
        </div>
      )}
    </div>
  );
}

export default MultiplayerSession;