// frontend/src/components/GameSession.js
import React, { useState, useEffect, useRef, useCallback } from 'react';
import api from '../api/axiosConfig';
import CampaignProgress from './CampaignProgress';
import DiceRoller from './multiplayer/DiceRoller'; 

function GameSession({ character, sessionConfig, onClose }) {
  const [session, setSession] = useState(null);
  const [campaign, setCampaign] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isStarting, setIsStarting] = useState(true);
  

  const [characterStats, setCharacterStats] = useState(null);

  const messagesEndRef = useRef(null);


  const getProxiedImageUrl = (originalUrl) => {
      if (!originalUrl) return null;
      if (originalUrl.startsWith('data:image')) return originalUrl;
      if (originalUrl.includes('wikia.nocookie.net') || originalUrl.includes('fandom.com')) {
          return `http://localhost:8000/api/v1/wiki/image-proxy?url=${encodeURIComponent(originalUrl)}`;
      }
      return originalUrl;
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);


  useEffect(() => {
      const fetchStats = async () => {
          try {
           
              const res = await api.get(`/characters/${character.id}`);
     
              const stats = {
                  strength: res.data.strength || 10,
                  dexterity: res.data.dexterity || 10,
                  constitution: res.data.constitution || 10,
                  intelligence: res.data.intelligence || 10,
                  wisdom: res.data.wisdom || 10,
                  charisma: res.data.charisma || 10,
                  ...res.data 
              };
              setCharacterStats(stats);
          } catch (e) {
              console.error("Failed to fetch character stats:", e);
          }
      };
      fetchStats();
  }, [character.id]);


  const fetchMessages = useCallback(async (sessionId) => {
      if (!sessionId) return;
      try {

          const response = await api.get(`/game-sessions/active`); 
  
          const mySession = response.data.find(s => s.id === sessionId);
          
          if (mySession && mySession.chat_history) {
     
              const history = mySession.chat_history.map((msg, idx) => ({
                  id: idx, 
                  role: msg.role,
                  content: msg.content,
               
                  message_type: msg.message_type || (msg.role === 'assistant' ? 'narration' : 'player_action'),
                  message_metadata: msg.message_metadata || {},
                  timestamp: msg.timestamp || new Date().toISOString()
              }));
              setMessages(history);
          }
      } catch (error) {
          console.error("Error fetching messages:", error);
      }
  }, []);

  const startSession = useCallback(async () => {
    if (session) return;
    setIsLoading(true);
    try {
      console.log('🎬 Starting new session...');
      const response = await api.post('/game-sessions/start', {
        character_id: character.id,
        title: `Przygoda ${character.name}`,
        universe: character.universe || 'star_wars'
      });

      const data = response.data;
      setSession(data);
      
      // Inicjalna wiadomość
      if (data.intro) {
        setMessages([{
          id: 'intro',
          role: 'assistant',
          content: typeof data.intro === 'string' ? data.intro : data.intro.message,
          message_type: 'narration',
          timestamp: new Date().toISOString()
        }]);
      }
      
     
      if (data.session_id) {
          await fetchMessages(data.session_id);
      }

      if (data.campaign) setCampaign(data.campaign);

    } catch (error) {
      console.error('❌ Error starting session:', error);
      setMessages(prev => [...prev, {
          id: 'error', role: 'system', content: "Błąd połączenia z Mistrzem Gry."
      }]);
    } finally {
      setIsLoading(false);
      setIsStarting(false);
    }
  }, [character, session, fetchMessages]);

  useEffect(() => {
    let mounted = true;
    const sessionKey = `session_started_${character.id}_${new Date().getDate()}`;
    const hasStarted = sessionStorage.getItem(sessionKey);
    
    if (!hasStarted && mounted && !session) {
      sessionStorage.setItem(sessionKey, 'true');
      startSession();
    } else {
      setIsStarting(false);
    }
    return () => { mounted = false; };
  }, [character.id, startSession, session]);

  const sendAction = async (e, customAction = null) => {
    if (e) e.preventDefault();
    const actionToSend = customAction || inputMessage;
    
    if (!actionToSend.trim() || !session) return;

    if (!customAction) setInputMessage('');
    setIsLoading(true);

  
    const tempId = Date.now();
    setMessages(prev => [...prev, {
      id: tempId,
      role: 'user',
      content: actionToSend,
      timestamp: new Date().toISOString()
    }]);

    try {
      const response = await api.post('/game-sessions/action', {
        session_id: session.session_id || session.id,
        action: actionToSend
      });

    
      await fetchMessages(session.session_id || session.id);

      if (response.data.campaign_update) {
        setCampaign(prev => ({...prev, ...response.data.campaign_update}));
      }

    } catch (error) {
      console.error('Error sending action:', error);
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'system',
        content: "Nie udało się połączyć z Mistrzem Gry."
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAttributeRoll = async (attrName) => {
      if (!characterStats) return;
      
      const rawKey = attrName.toLowerCase();
      const score = characterStats[rawKey] || 10;
      const modifier = Math.floor((score - 10) / 2);
      const modStr = modifier >= 0 ? `+${modifier}` : modifier;
      

      const actionText = `[System]: Rzucam na ${attrName} (${modStr}).`;
      await sendAction(null, actionText);
  };


  const handleCombatAttack = async (damage, targetId, targetName) => {

      const actionText = `[Combat]: Atakuję cel ${targetName || 'Enemy'}! Zadaję ${damage} obrażeń.`;
      await sendAction(null, actionText);
  };

  const renderMessage = (msg, index) => {

    const isSystem = msg.role === 'system';
    const isUser = msg.role === 'user';
    const isAssistant = msg.role === 'assistant';
    

    const meta = msg.message_metadata || {};
    const isNpcSpawn = meta.original_type === 'npc_spawn' || msg.message_type === 'npc_spawn';
    const isCombatUpdate = meta.original_type === 'combat_update' || msg.message_type === 'gm_event';
    const isDiceRoll = msg.content.includes('[System]: Rzucam') || msg.message_type === 'dice_roll_result';


    if (isDiceRoll) {
        return (
            <div key={index} className="flex justify-end my-2">
                <div className="bg-purple-900/80 rounded-lg p-3 border border-purple-500 text-sm max-w-xs">
                    <div className="font-bold text-purple-300 mb-1">🎲 Rzut Kością</div>
                    <div className="text-white italic">{msg.content}</div>
                </div>
            </div>
        );
    }


    if (isNpcSpawn) {
        const npc = meta.npc || {};
        return (
            <div key={index} className="bg-gray-800 border-2 border-gray-600 rounded-lg p-4 max-w-xl mx-auto my-4 shadow-2xl flex gap-4 animate-fadeIn">
                <div className="w-20 h-20 bg-black rounded border border-gray-500 overflow-hidden flex-shrink-0">
                    {npc.image_url ? (
                        <img src={getProxiedImageUrl(npc.image_url)} className="w-full h-full object-cover" alt="NPC" />
                    ) : (
                        <div className="w-full h-full flex items-center justify-center text-2xl">👤</div>
                    )}
                </div>
                <div>
                    <h4 className="text-lg font-bold text-white">{npc.name}</h4>
                    <p className="text-gray-400 text-sm mb-2">{npc.race} • {npc.attitude}</p>
                    <div className="flex gap-2 text-xs font-mono">
                        <span className="text-green-400 bg-gray-900 px-2 py-1 rounded border border-green-900">HP {npc.hp}</span>
                        <span className="text-blue-400 bg-gray-900 px-2 py-1 rounded border border-blue-900">AC {npc.armor_class}</span>
                    </div>
                </div>
            </div>
        );
    }


    if (isCombatUpdate) {
        let combatData = {};
        try { combatData = JSON.parse(msg.content); } catch (e) { return null; }

        if (combatData.ended) {
            return (
                <div key={index} className="bg-gray-800/50 border border-gray-600 p-3 rounded text-center my-2 text-gray-400 text-sm">
                    ⚔️ Walka Zakończona
                </div>
            );
        }

        return (
            <div key={index} className="my-4 border-2 border-red-600 rounded-lg overflow-hidden bg-gray-900 max-w-xl mx-auto">
                <div className="bg-red-900/80 p-2 text-center text-white font-bold text-sm">
                    ⚔️ Combat Event (Round {combatData.round})
                </div>
                <div className="p-3 space-y-2">
                    {combatData.combatants.map((c, i) => (
                        <div key={i} className={`flex justify-between items-center p-2 rounded border ${c.type === 'player' ? 'bg-blue-900/20 border-blue-800' : 'bg-red-900/20 border-red-800'}`}>
                            <div className="flex items-center gap-3">
                                <div className="font-bold text-white text-sm">{c.name}</div>
                                <div className="text-xs text-gray-400">HP: {c.hp}/{c.max_hp}</div>
                            </div>
                            
                            {/* Jeśli to gracz - pokaż DiceRoller do ataku */}
                            {/* W trybie AI Singleplayer, gracz zawsze widzi opcję ataku na wrogów */}
                            {c.type !== 'player' && (
                                <DiceRoller 
                                    campaignId={null} 
                                    characterId={character.id}
                                    characterStats={characterStats}
                                    targets={[]} 
                                    onAttack={(damage) => handleCombatAttack(damage, c.id, c.name)}
                                    compact={true} 
                                />
                            )}
                        </div>
                    ))}
                </div>
            </div>
        );
    }

   
    return (
      <div 
        key={index} 
        className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4 animate-slideIn`}
      >
        <div 
          className={`max-w-[85%] rounded-lg p-4 shadow-lg ${
            isUser 
              ? 'bg-blue-600 text-white rounded-br-none' 
              : isSystem
              ? 'bg-gray-600 text-gray-200 text-sm italic mx-auto'
              : 'bg-gray-700 text-gray-100 rounded-bl-none'
          }`}
        >
          {isAssistant && <div className="text-xs text-yellow-500 font-bold mb-1">🎭 Mistrz Gry</div>}
          <div className="whitespace-pre-wrap leading-relaxed">
            {msg.content}
          </div>
          <div className={`text-[10px] mt-2 opacity-60 ${isUser ? 'text-right' : 'text-left'}`}>
            {new Date(msg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
          </div>
        </div>
      </div>
    );
  };

  if (isStarting) {
    return (
      <div className="fixed inset-0 bg-gray-900 text-white flex items-center justify-center z-50">
        <div className="text-center">
          <div className="text-5xl mb-4 animate-bounce">🎲</div>
          <h2 className="text-2xl font-bold text-blue-400">Przygotowywanie sesji...</h2>
          <p className="text-gray-400 mt-2">Mistrz Gry generuje świat.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-gray-900 text-white flex flex-col z-50">
      {/* HEADER */}
      <header className="bg-gray-800 p-4 shadow-md flex justify-between items-center border-b border-gray-700">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span>{campaign ? campaign.title : character.name}</span>
            {session && <span className="text-xs bg-blue-900 text-blue-200 px-2 py-0.5 rounded border border-blue-700">AI MODE</span>}
          </h2>
          <p className="text-xs text-gray-400">
             {session?.id ? `Sesja #${session.id}` : 'Nowa gra'} • {character.universe}
          </p>
        </div>
        <button onClick={onClose} className="bg-red-900/80 hover:bg-red-800 text-red-100 px-4 py-2 rounded text-sm font-bold transition">
          Zakończ
        </button>
      </header>

      {/* MAIN AREA */}
      <div className="flex-1 flex overflow-hidden">
        {/* CHAT AREA */}
        <div className="flex-1 flex flex-col w-full max-w-5xl mx-auto bg-gray-900/50">
          
          <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
            {messages.map((msg, i) => renderMessage(msg, i))}
            <div ref={messagesEndRef} />
          </div>

          {/* INPUT AREA */}
          <div className="bg-gray-800 border-t border-gray-700 p-4">
            
            {/* ✅ PASEK ATRYBUTÓW (Quick Rolls) */}
            <div className="flex flex-wrap gap-2 mb-3 justify-center">
                {['Strength', 'Dexterity', 'Constitution', 'Intelligence', 'Wisdom', 'Charisma'].map(attr => {
                    const short = attr.slice(0, 3).toUpperCase();
                    const val = characterStats ? characterStats[attr.toLowerCase()] : 10;
                    const mod = Math.floor((val - 10) / 2);
                    const sign = mod >= 0 ? '+' : '';
                    
                    return (
                        <button 
                            key={attr}
                            onClick={() => handleAttributeRoll(attr)}
                            disabled={isLoading}
                            className="bg-gray-700 hover:bg-gray-600 text-xs px-3 py-1.5 rounded border border-gray-600 text-gray-300 transition flex items-center gap-1 shadow-sm hover:border-blue-500 disabled:opacity-50"
                            title={`Rzuć na ${attr}`}
                        >
                            <span className="font-bold">{short}</span>
                            <span className={mod >= 0 ? "text-green-400" : "text-red-400"}>{sign}{mod}</span>
                        </button>
                    );
                })}
            </div>

            <form onSubmit={sendAction} className="flex gap-3 max-w-4xl mx-auto">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder={isLoading ? "Mistrz Gry myśli..." : "Co robisz? (Opisz swoją akcję)"}
                className="flex-1 px-4 py-3 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 shadow-inner"
                disabled={isLoading}
                autoFocus
              />
              <button
                type="submit"
                disabled={isLoading || !inputMessage.trim()}
                className="bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 disabled:from-gray-600 disabled:to-gray-600 px-8 py-3 rounded-lg font-bold transition shadow-lg transform hover:scale-105 active:scale-95"
              >
                {isLoading ? '...' : 'Wyślij'}
              </button>
            </form>
          </div>
        </div>

        {/* SIDEBAR (Campaign Progress) */}
        {campaign && (
          <div className="w-80 bg-gray-800 border-l border-gray-700 p-4 hidden xl:block overflow-y-auto">
            <h3 className="text-gray-400 text-xs font-bold uppercase mb-4 tracking-widest">Campaign Progress</h3>
            <CampaignProgress campaign={campaign} />
          </div>
        )}
      </div>
    </div>
  );
}

export default GameSession;