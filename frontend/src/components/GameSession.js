// frontend/src/components/GameSession.js
import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  }
});

function GameSession({ character, onClose }) {
  const [session, setSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isStarting, setIsStarting] = useState(true);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    startSession();
  }, []);

  const startSession = async () => {
    if (!character?.id) {
      console.error('No character ID provided');
      alert('Error: Invalid character data');
      onClose();
      return;
    }

    try {
      setIsStarting(true);
      const response = await api.post('/game-sessions/start', {
        character_id: character.id,
        title: `Adventure of ${character.name}`
      });
      
      // Save session data
      setSession({
        session_id: response.data.session_id,
        character_id: character.id,
        universe: character.universe
      });

      // Add intro message
      const introMessage = response.data.intro;
      if (introMessage) {
        setMessages([{
          type: 'narration',
          message: introMessage.message || introMessage,
          timestamp: introMessage.timestamp || new Date().toISOString()
        }]);
      } else {
        // Fallback intro
        setMessages([{
          type: 'narration',
          message: `Welcome, ${character.name}! Your adventure in ${character.universe.replace('_', ' ')} begins...`,
          timestamp: new Date().toISOString()
        }]);
      }
      
      setIsStarting(false);
    } catch (error) {
      console.error('Error starting session:', error);
      setIsStarting(false);
      alert('Failed to start game session. Please try again.');
      onClose();
    }
  };

  const sendAction = async (e) => {
    e.preventDefault();
    
    if (!inputMessage.trim()) return;
    
    if (!session?.session_id) {
      console.error('No active session');
      alert('Error: No active game session');
      return;
    }

    // Add player message
    const playerMessage = {
      type: 'player',
      message: inputMessage,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, playerMessage]);
    
    const action = inputMessage;
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await api.post('/game-sessions/action', {
        action: action,
        session_id: session.session_id
      });

      // Add AI response
      const aiMessage = {
        type: response.data.type || 'narration',
        message: response.data.message,
        timestamp: response.data.timestamp || new Date().toISOString()
      };
      setMessages(prev => [...prev, aiMessage]);

    } catch (error) {
      console.error('Error processing action:', error);
      setMessages(prev => [...prev, {
        type: 'error',
        message: 'An error occurred while processing your action. Please try again.',
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const rollDice = async (diceType = 'd20') => {
    try {
      const response = await api.post('/game-sessions/roll-dice', null, {
        params: { dice_type: diceType }
      });
      
      const diceMessage = {
        type: 'dice',
        message: response.data.message,
        result: response.data.result,
        critical: response.data.critical,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, diceMessage]);
    } catch (error) {
      console.error('Error rolling dice:', error);
    }
  };

  const endSession = async () => {
    if (!session?.session_id) {
      onClose();
      return;
    }
    
    try {
      await api.post(`/game-sessions/${session.session_id}/end`);
    } catch (error) {
      console.error('Error ending session:', error);
    } finally {
      onClose();
    }
  };

  const renderMessage = (msg, index) => {
    const messageClass = {
      'player': 'bg-blue-900 ml-auto',
      'narration': 'bg-gray-700',
      'dialogue': 'bg-green-900',
      'combat': 'bg-red-900',
      'observation': 'bg-purple-900',
      'movement': 'bg-yellow-900',
      'event': 'bg-orange-900',
      'dice': 'bg-indigo-900',
      'error': 'bg-red-800'
    };

    const typeLabel = {
      'player': '🎮 You',
      'narration': '📖 Narrator',
      'dialogue': '💬 Dialog',
      'combat': '⚔️ Combat',
      'observation': '👁️ Observation',
      'movement': '🚶 Movement',
      'event': '⚡ Event',
      'dice': '🎲 Dice Roll',
      'error': '❌ Error'
    };

    return (
      <div 
        key={index} 
        className={`p-3 rounded-lg mb-3 max-w-3xl ${messageClass[msg.type] || 'bg-gray-700'} ${
          msg.type === 'player' ? 'ml-auto text-right' : ''
        }`}
      >
        <div className="text-xs text-gray-400 mb-1">
          {typeLabel[msg.type] || msg.type}
          {msg.timestamp && ` • ${new Date(msg.timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}`}
        </div>
        <div className="text-white whitespace-pre-wrap">
          {msg.message}
          {msg.critical && (
            <span className={`ml-2 font-bold ${
              msg.critical === 'success' ? 'text-green-400' : 'text-red-400'
            }`}>
              {msg.critical === 'success' ? '💥 Critical Success!' : '💀 Critical Failure!'}
            </span>
          )}
        </div>
      </div>
    );
  };

  if (isStarting) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
        <div className="bg-gray-800 rounded-lg p-8">
          <div className="text-white text-xl mb-4">Starting game session...</div>
          <div className="animate-pulse flex space-x-2 justify-center">
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-gray-900 flex flex-col z-50">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 p-4 flex-shrink-0">
        <div className="container mx-auto flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold text-blue-400">
              RPG Session - {character.name}
            </h2>
            <p className="text-gray-400">
              {character.universe.replace('_', ' ')} • Level {character.level} {character.class_type || 'Adventurer'}
            </p>
          </div>
          <button
            onClick={endSession}
            className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg font-semibold transition duration-200"
          >
            End Session
          </button>
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="container mx-auto max-w-4xl">
          {messages.map((msg, index) => renderMessage(msg, index))}
          {isLoading && (
            <div className="text-center text-gray-400 italic">
              <span className="inline-block animate-pulse">Game Master is thinking...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="bg-gray-800 border-t border-gray-700 p-4 flex-shrink-0">
        <div className="container mx-auto max-w-4xl">
          {/* Dice buttons */}
          <div className="flex gap-2 mb-3 flex-wrap">
            {['d4', 'd6', 'd8', 'd10', 'd12', 'd20', 'd100'].map(dice => (
              <button
                key={dice}
                onClick={() => rollDice(dice)}
                className="bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded text-sm transition"
                disabled={isLoading}
              >
                🎲 {dice}
              </button>
            ))}
          </div>
          
          {/* Message input */}
          <form onSubmit={sendAction} className="flex gap-3">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="What do you do? (e.g., 'I look around', 'I go to the tavern', 'I attack')"
              className="flex-1 px-4 py-3 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !inputMessage.trim()}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed px-6 py-3 rounded-lg font-semibold transition duration-200"
            >
              {isLoading ? 'Sending...' : 'Send'}
            </button>
          </form>
          
          {/* Action hints */}
          <div className="mt-2 text-xs text-gray-400">
            💡 Try: "I look around the room", "I approach the bartender", "I ask about rumors", "I attack the goblin"
          </div>
        </div>
      </div>
    </div>
  );
}

export default GameSession;