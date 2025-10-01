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

  // Auto-scroll do końca czatu
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Rozpocznij sesję przy montowaniu komponentu
  useEffect(() => {
    startSession();
  }, []);

  const startSession = async () => {
    try {
      setIsStarting(true);
      const response = await api.post('/game-sessions/start', {
        character_id: character.id || 1,
        title: `Przygoda ${character.name}`
      });
      
      // Popraw na:
if (response.data.intro) {
  setMessages([{
    type: 'narration',
    message: response.data.intro.message || response.data.intro,
    timestamp: response.data.intro.timestamp || new Date().toISOString()
  }]);
} else {
  // Fallback
  setMessages([{
    type: 'narration',
    message: "Rozpoczynacie przygodę...",
    timestamp: new Date().toISOString()
  }]);
}
      
      setIsStarting(false);
    } catch (error) {
      console.error('Błąd podczas rozpoczynania sesji:', error);
      setIsStarting(false);
    }
  };

  const sendAction = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || !session) return;

    // Dodaj wiadomość gracza do czatu
    const playerMessage = {
      type: 'player',
      message: inputMessage,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, playerMessage]);
    
    // Wyczyść input
    const action = inputMessage;
    setInputMessage('');
    setIsLoading(true);

    try {
      // Wyślij akcję do AI
      const response = await api.post('/game-sessions/action', {
        action: action,
        session_id: session.session_id
      });

      // Dodaj odpowiedź AI do czatu
      const aiMessage = {
        type: response.data.type,
        message: response.data.message,
        timestamp: response.data.timestamp
      };
      setMessages(prev => [...prev, aiMessage]);

    } catch (error) {
      console.error('Błąd podczas wysyłania akcji:', error);
      setMessages(prev => [...prev, {
        type: 'error',
        message: 'Wystąpił błąd podczas przetwarzania akcji.',
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
      
      // Dodaj wynik rzutu do czatu
      const diceMessage = {
        type: 'dice',
        message: response.data.message,
        result: response.data.result,
        critical: response.data.critical,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, diceMessage]);
    } catch (error) {
      console.error('Błąd podczas rzutu kością:', error);
    }
  };

  const endSession = async () => {
    if (!session) return;
    
    try {
      await api.post(`/game-sessions/${session.session_id}/end`);
      onClose();
    } catch (error) {
      console.error('Błąd podczas kończenia sesji:', error);
    }
  };

  // Funkcja do renderowania wiadomości w zależności od typu
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
      'player': '🎮 Ty',
      'narration': '📖 Narrator',
      'dialogue': '💬 Dialog',
      'combat': '⚔️ Walka',
      'observation': '👁️ Obserwacja',
      'movement': '🚶 Ruch',
      'event': '⚡ Wydarzenie',
      'dice': '🎲 Rzut kością',
      'error': '❌ Błąd'
    };

    return (
      <div 
        key={index} 
        className={`p-3 rounded-lg mb-3 max-w-3xl ${messageClass[msg.type] || 'bg-gray-700'} ${
          msg.type === 'player' ? 'text-right' : ''
        }`}
      >
        <div className="text-xs text-gray-400 mb-1">
          {typeLabel[msg.type] || msg.type}
          {msg.timestamp && ` • ${new Date(msg.timestamp).toLocaleTimeString('pl-PL')}`}
        </div>
        <div className="text-white">
          {msg.message}
          {msg.critical && (
            <span className={`ml-2 font-bold ${
              msg.critical === 'success' ? 'text-green-400' : 'text-red-400'
            }`}>
              {msg.critical === 'success' ? '💥 Krytyczny sukces!' : '💀 Krytyczna porażka!'}
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
          <div className="text-white text-xl">Rozpoczynam sesję...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-gray-900 flex flex-col z-50">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 p-4">
        <div className="container mx-auto flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold text-blue-400">
              Sesja RPG - {character.name}
            </h2>
            <p className="text-gray-400">
              {character.universe.replace('_', ' ')} • Level {character.level} {character.class_type}
            </p>
          </div>
          <button
            onClick={endSession}
            className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg font-semibold transition duration-200"
          >
            Zakończ Sesję
          </button>
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="container mx-auto max-w-4xl">
          {messages.map((msg, index) => renderMessage(msg, index))}
          {isLoading && (
            <div className="text-center text-gray-400 italic">
              Mistrz Gry myśli...
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="bg-gray-800 border-t border-gray-700 p-4">
        <div className="container mx-auto max-w-4xl">
          {/* Przyciski kości */}
          <div className="flex gap-2 mb-3">
            <button
              onClick={() => rollDice('d4')}
              className="bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded text-sm transition"
            >
              🎲 d4
            </button>
            <button
              onClick={() => rollDice('d6')}
              className="bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded text-sm transition"
            >
              🎲 d6
            </button>
            <button
              onClick={() => rollDice('d8')}
              className="bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded text-sm transition"
            >
              🎲 d8
            </button>
            <button
              onClick={() => rollDice('d10')}
              className="bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded text-sm transition"
            >
              🎲 d10
            </button>
            <button
              onClick={() => rollDice('d12')}
              className="bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded text-sm transition"
            >
              🎲 d12
            </button>
            <button
              onClick={() => rollDice('d20')}
              className="bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded text-sm transition"
            >
              🎲 d20
            </button>
            <button
              onClick={() => rollDice('d100')}
              className="bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded text-sm transition"
            >
              🎲 d100
            </button>
          </div>
          
          {/* Formularz wiadomości */}
          <form onSubmit={sendAction} className="flex gap-3">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Co robisz? (np. 'rozglądam się', 'idę do karczmy', 'rozmawiam z NPC')"
              className="flex-1 px-4 py-3 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !inputMessage.trim()}
              className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg font-semibold transition duration-200 disabled:opacity-50"
            >
              Wyślij
            </button>
          </form>
          
          {/* Podpowiedzi */}
          <div className="mt-2 text-xs text-gray-400">
            Przykładowe akcje: "rozglądam się po pomieszczeniu", "idę do tawerny", "pytam o plotki", "atakuję goblina"
          </div>
        </div>
      </div>
    </div>
  );
}

export default GameSession;