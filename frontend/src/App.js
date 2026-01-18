// frontend/src/App.js
import React, { useState, useEffect } from 'react';
import './App.css';
import api from './api/axiosConfig';
import AuthPage from './components/Auth/AuthPage';
import GameSession from './components/GameSession';
import MultiplayerLobby from './components/multiplayer/MultiplayerLobby';

// ✅ Nowe importy
import CharacterDashboard from './components/CharacterDashboard';
import ProfilePage from './components/profile/ProfilePage';

function App() {
  const [user, setUser] = useState(null);
  const [authChecked, setAuthChecked] = useState(false);
  
  // Stan nawigacji
  const [view, setView] = useState('dashboard'); // 'dashboard' | 'profile'
  
  // Stan sesji
  const [activeGameSession, setActiveGameSession] = useState(null);
  const [gameMode, setGameMode] = useState(null); // 'ai' | 'multiplayer'

  useEffect(() => {
    const token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    if (token && savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (e) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      }
    }
    setAuthChecked(true);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    setActiveGameSession(null);
    setView('dashboard');
  };

  const handleStartGameSession = (character, mode) => {
    setGameMode(mode);
    setActiveGameSession(character);
  };

  const handleCloseGameSession = () => {
    setActiveGameSession(null);
    setGameMode(null);
  };

  if (!authChecked) return <div className="min-h-screen bg-gray-900 flex items-center justify-center text-white">Loading...</div>;
  
  if (!user) return <AuthPage onAuthSuccess={setUser} />;

  // 🎮 Widok Gry (Ma priorytet)
  if (activeGameSession) {
    if (gameMode === 'ai') {
        return <GameSession character={activeGameSession} onClose={handleCloseGameSession} />;
    }
    return <MultiplayerLobby character={activeGameSession} onClose={handleCloseGameSession} />;
  }

  // 🏠 Główny Layout
  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Navbar */}
      <header className="bg-gray-800 shadow-lg sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div 
            onClick={() => setView('dashboard')}
            className="cursor-pointer flex items-center gap-2"
          >
            <h1 className="text-2xl font-bold text-blue-400 hover:text-blue-300 transition">RPG Game Master</h1>
          </div>
          
          <div className="flex items-center gap-4">
            <button 
                onClick={() => setView('profile')}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg transition ${view === 'profile' ? 'bg-gray-700' : 'hover:bg-gray-700'}`}
            >
                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center font-bold text-sm">
                    {user.username[0].toUpperCase()}
                </div>
                <span className="hidden sm:block font-medium">{user.username}</span>
            </button>
            
            <button 
                onClick={handleLogout}
                className="text-gray-400 hover:text-red-400 text-sm font-semibold transition"
            >
              Sign Out
            </button>
          </div>
        </div>
      </header>

      {/* Zawartość */}
      <main>
        {view === 'profile' ? (
            <ProfilePage onBack={() => setView('dashboard')} />
        ) : (
            <CharacterDashboard 
                user={user} 
                onStartSession={handleStartGameSession} 
            />
        )}
      </main>
    </div>
  );
}

export default App;