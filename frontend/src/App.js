// frontend/src/App.js
import React, { useState, useEffect } from 'react';
import api from './api/axiosConfig';
import './App.css';
import GameSession from './components/GameSession';
import CharacterCreationWizard from './components/CharacterCreationWizard';
import MultiplayerLobby from './components/multiplayer/MultiplayerLobby';
import AuthPage from './components/Auth/AuthPage.js';



function App() {
  // 🆕 Auth state
  const [user, setUser] = useState(null);
  const [authChecked, setAuthChecked] = useState(false);

  // Existing state
  const [characters, setCharacters] = useState([]);
  const [selectedCharacter, setSelectedCharacter] = useState(null);
  const [showDetails, setShowDetails] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [activeGameSession, setActiveGameSession] = useState(null);
  const [gameMode, setGameMode] = useState(null);

  // 🆕 Check if user is already logged in
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

  // Fetch characters when user logs in
  // Fetch characters when user logs in
useEffect(() => {
  if (user) {
    fetchCharacters();
  }
  // eslint-disable-next-line react-hooks/exhaustive-deps
}, [user]);

  const fetchCharacters = async () => {
    try {
      const response = await api.get('/characters/');
      setCharacters(response.data || []);
    } catch (error) {
      console.error('Error fetching characters:', error);
      if (error.response?.status === 401) {
        handleLogout();
      }
    }
  };

  // 🆕 Logout function
  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    setCharacters([]);
    setSelectedCharacter(null);
    setShowDetails(false);
    setActiveGameSession(null);
  };

  const handleShowDetails = (character) => {
    setSelectedCharacter(character);
    setShowDetails(true);
  };

  const handleCloseDetails = () => {
    setShowDetails(false);
    setSelectedCharacter(null);
  };

  const handleDeleteClick = () => {
    setShowDeleteConfirm(true);
  };

  const handleDeleteConfirm = async () => {
    if (!selectedCharacter) return;

    try {
      await api.delete(`/characters/${selectedCharacter.id}`);
      setShowDeleteConfirm(false);
      setShowDetails(false);
      setSelectedCharacter(null);
      await fetchCharacters();
    } catch (error) {
      console.error('Error deleting character:', error);
      alert('Failed to delete character.');
    }
  };

  const handleDeleteCancel = () => {
    setShowDeleteConfirm(false);
  };

  const handleStartGameSession = (character, mode = 'ai') => {
    console.log('Starting game session for:', character, 'Mode:', mode);
    if (!character || !character.id) {
      console.error('Invalid character data:', character);
      alert('Error: Invalid character data');
      return;
    }
    setGameMode(mode);
    setActiveGameSession(character);
  };

  const handleCloseGameSession = () => {
    setActiveGameSession(null);
    setGameMode(null);
  };

  const handleFormSuccess = () => {
    fetchCharacters();
  };

  // 🆕 Show loading while checking auth
  if (!authChecked) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  // 🆕 Show auth page if not logged in
  if (!user) {
    return <AuthPage onAuthSuccess={setUser} />;
  }

  // Main app (only shown when logged in)
  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <header className="bg-gray-800 shadow-lg">
        <div className="container mx-auto px-4 py-6 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-blue-400">
              RPG Game Master
            </h1>
            <p className="text-gray-400 mt-2">
              AI-Powered RPG Session Manager
            </p>
          </div>
          {/* 🆕 User info & Logout */}
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-white font-semibold">{user.username}</p>
              <p className="text-gray-400 text-sm">{user.email}</p>
            </div>
            <button
              onClick={handleLogout}
              className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg font-semibold transition"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <button
            onClick={() => setShowCreateForm(true)}
            className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg font-semibold transition duration-200"
          >
            + New Character
          </button>
        </div>

        {showCreateForm && (
          <CharacterCreationWizard
            onClose={() => setShowCreateForm(false)}
            onSuccess={handleFormSuccess}
          />
        )}

        <div>
          <h2 className="text-2xl font-bold mb-4">Your Characters</h2>
          
          {characters.length === 0 ? (
            <div className="bg-gray-800 rounded-lg p-8 text-center">
              <p className="text-gray-400">You don't have any characters yet.</p>
              <p className="text-gray-400 mt-2">Click "New Character" to create your first!</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {characters.map((character) => (
                <div key={character.id} className="bg-gray-800 rounded-lg p-6 hover:shadow-xl transition duration-200">
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="text-xl font-bold text-blue-400">
                      {character.name}
                    </h3>
                    <span className="bg-blue-600 px-2 py-1 rounded text-sm">
                      Lvl {character.level}
                    </span>
                  </div>
                  
                  <div className="space-y-2 text-sm">
                    <p>
                      <span className="text-gray-400">Universe:</span>{' '}
                      <span className="text-white capitalize">
                        {character.universe.replace('_', ' ')}
                      </span>
                    </p>
                    {character.race && (
                      <p>
                        <span className="text-gray-400">Species:</span>{' '}
                        <span className="text-white">{character.race}</span>
                      </p>
                    )}
                    {character.homeworld && (
                      <p>
                        <span className="text-gray-400">Homeworld:</span>{' '}
                        <span className="text-white">{character.homeworld}</span>
                      </p>
                    )}
                    {character.class_type && (
                      <p>
                        <span className="text-gray-400">Class:</span>{' '}
                        <span className="text-white">{character.class_type}</span>
                      </p>
                    )}
                  </div>

                  {character.description && (
                    <p className="mt-4 text-gray-300 text-sm line-clamp-3">
                      {character.description}
                    </p>
                  )}

                  <div className="mt-4 flex gap-2">
                    <button 
                      onClick={() => handleShowDetails(character)}
                      className="bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded text-sm transition duration-200"
                    >
                      Details
                    </button>

                    <div className="relative group">
                      <button 
                        className="bg-purple-600 hover:bg-purple-700 px-3 py-1 rounded text-sm transition duration-200"
                      >
                        🎮 Start Session ▼
                      </button>
                      
                      <div className="hidden group-hover:block absolute left-0 mt-1 w-48 bg-gray-800 rounded-lg shadow-xl z-10 border border-gray-700">
                        <button
                          onClick={() => handleStartGameSession(character, 'ai')}
                          className="w-full text-left px-4 py-2 hover:bg-gray-700 rounded-t-lg transition text-sm"
                        >
                          🤖 AI Game Master
                        </button>
                        <button
                          onClick={() => handleStartGameSession(character, 'multiplayer')}
                          className="w-full text-left px-4 py-2 hover:bg-gray-700 rounded-b-lg transition text-sm"
                        >
                          👥 Multiplayer
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {showDetails && selectedCharacter && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
            <div className="bg-gray-800 rounded-lg p-6 max-w-4xl w-full mx-4 my-8 max-h-screen overflow-y-auto">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h2 className="text-3xl font-bold text-blue-400">
                    {selectedCharacter.name}
                  </h2>
                  <span className="bg-blue-600 px-3 py-1 rounded text-sm mt-2 inline-block">
                    Level {selectedCharacter.level}
                  </span>
                </div>
                <button
                  onClick={handleCloseDetails}
                  className="text-gray-400 hover:text-white text-2xl"
                >
                  ×
                </button>
              </div>

              <div className="space-y-6">
                {/* Basic Info */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-300 mb-3 border-b border-gray-700 pb-2">
                    Basic Information
                  </h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <p><span className="text-gray-400">Universe:</span> <span className="capitalize">{selectedCharacter.universe.replace('_', ' ')}</span></p>
                      <p><span className="text-gray-400">Species:</span> {selectedCharacter.race || 'Unknown'}</p>
                      <p><span className="text-gray-400">Class:</span> {selectedCharacter.class_type || 'Unknown'}</p>
                      {selectedCharacter.homeworld && (
                        <p><span className="text-gray-400">Homeworld:</span> {selectedCharacter.homeworld}</p>
                      )}
                      {selectedCharacter.gender && (
                        <p><span className="text-gray-400">Gender:</span> {selectedCharacter.gender}</p>
                      )}
                    </div>
                    <div className="space-y-2">
                      {selectedCharacter.height && (
                        <p><span className="text-gray-400">Height:</span> {selectedCharacter.height} cm</p>
                      )}
                      {selectedCharacter.mass && (
                        <p><span className="text-gray-400">Mass:</span> {selectedCharacter.mass} kg</p>
                      )}
                      {selectedCharacter.born_year && selectedCharacter.born_era && (
                        <p><span className="text-gray-400">Born:</span> {selectedCharacter.born_year} {selectedCharacter.born_era}</p>
                      )}
                      {selectedCharacter.skin_color && (
                        <p><span className="text-gray-400">Skin:</span> {selectedCharacter.skin_color}</p>
                      )}
                      {selectedCharacter.eye_color && (
                        <p><span className="text-gray-400">Eyes:</span> {selectedCharacter.eye_color}</p>
                      )}
                      {selectedCharacter.hair_color && (
                        <p><span className="text-gray-400">Hair:</span> {selectedCharacter.hair_color}</p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Attributes */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-300 mb-3 border-b border-gray-700 pb-2">
                    Attributes
                  </h3>
                  <div className="grid grid-cols-3 gap-3">
                    {[
                      { key: 'strength', name: 'Strength', abbr: 'STR' },
                      { key: 'dexterity', name: 'Dexterity', abbr: 'DEX' },
                      { key: 'constitution', name: 'Constitution', abbr: 'CON' },
                      { key: 'intelligence', name: 'Intelligence', abbr: 'INT' },
                      { key: 'wisdom', name: 'Wisdom', abbr: 'WIS' },
                      { key: 'charisma', name: 'Charisma', abbr: 'CHA' }
                    ].map(attr => {
                      const value = selectedCharacter[attr.key] || 10;
                      const modifier = Math.floor((value - 10) / 2);
                      return (
                        <div key={attr.key} className="bg-gray-700 p-3 rounded-lg text-center">
                          <div className="text-xs text-gray-400 mb-1">{attr.abbr}</div>
                          <div className="text-2xl font-bold">{value}</div>
                          <div className="text-sm text-blue-400">
                            {modifier >= 0 ? '+' : ''}{modifier}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Skills */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-300 mb-3 border-b border-gray-700 pb-2">
                    Skills
                  </h3>
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { key: 'skill_computer_use', name: 'Computer Use' },
                      { key: 'skill_demolitions', name: 'Demolitions' },
                      { key: 'skill_stealth', name: 'Stealth' },
                      { key: 'skill_awareness', name: 'Awareness' },
                      { key: 'skill_persuade', name: 'Persuade' },
                      { key: 'skill_repair', name: 'Repair' },
                      { key: 'skill_security', name: 'Security' },
                      { key: 'skill_treat_injury', name: 'Treat Injury' }
                    ].map(skill => {
                      const value = selectedCharacter[skill.key] || 0;
                      return (
                        <div key={skill.key} className="bg-gray-700 p-2 rounded flex justify-between items-center">
                          <span className="text-sm">{skill.name}</span>
                          <span className="font-bold text-blue-400">{value}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Affiliations */}
                {selectedCharacter.affiliations?.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-300 mb-3 border-b border-gray-700 pb-2">
                      Affiliations
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedCharacter.affiliations.map((aff, idx) => (
                        <span key={idx} className="bg-blue-700 px-3 py-1 rounded-full text-sm">
                          {aff}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Cybernetics */}
                {selectedCharacter.cybernetics?.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-300 mb-3 border-b border-gray-700 pb-2">
                      Cybernetics
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedCharacter.cybernetics.map((cyber, idx) => (
                        <span key={idx} className="bg-purple-700 px-3 py-1 rounded-full text-sm">
                          {cyber}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Description */}
                {selectedCharacter.description && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-300 mb-3 border-b border-gray-700 pb-2">
                      Description
                    </h3>
                    <p className="text-gray-300 bg-gray-700 p-4 rounded-lg whitespace-pre-wrap">
                      {selectedCharacter.description}
                    </p>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex gap-3 pt-4 border-t border-gray-700">
                  <div className="relative group">
                    <button 
                      className="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded-lg font-semibold transition duration-200"
                    >
                      🎮 Start Session ▼
                    </button>
                    
                    <div className="hidden group-hover:block absolute left-0 bottom-full mb-1 w-48 bg-gray-800 rounded-lg shadow-xl z-10 border border-gray-700">
                      <button
                        onClick={() => {
                          handleStartGameSession(selectedCharacter, 'ai');
                          handleCloseDetails();
                        }}
                        className="w-full text-left px-4 py-2 hover:bg-gray-700 rounded-t-lg transition"
                      >
                        🤖 AI Game Master
                      </button>
                      <button
                        onClick={() => {
                          handleStartGameSession(selectedCharacter, 'multiplayer');
                          handleCloseDetails();
                        }}
                        className="w-full text-left px-4 py-2 hover:bg-gray-700 rounded-b-lg transition"
                      >
                        👥 Multiplayer
                      </button>
                    </div>
                  </div>

                  <button 
                    onClick={handleDeleteClick}
                    className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg font-semibold transition duration-200"
                  >
                    Delete
                  </button>
                  <button
                    onClick={handleCloseDetails}
                    className="bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded-lg font-semibold transition duration-200 ml-auto"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {showDeleteConfirm && selectedCharacter && (
          <div 
            className="fixed inset-0 bg-black bg-opacity-95 flex items-center justify-center" 
            style={{zIndex: 100000}}
          >
            <div className="bg-red-900 rounded-lg p-6 max-w-md w-full mx-4 border-4 border-red-500 shadow-2xl">
              <h3 className="text-2xl font-bold text-red-200 mb-4">
                CONFIRM DELETE
              </h3>
              <p className="text-red-100 mb-6 text-lg">
                Are you sure you want to delete <strong className="text-white text-xl">
                  {selectedCharacter?.name}
                </strong>?
                <br />
                <span className="text-red-300 font-bold">THIS CANNOT BE UNDONE!</span>
              </p>
              <div className="flex gap-4">
                <button
                  onClick={handleDeleteConfirm}
                  className="bg-red-600 hover:bg-red-500 px-6 py-3 rounded-lg font-bold text-lg flex-1"
                >
                  YES, DELETE
                </button>
                <button
                  onClick={handleDeleteCancel}
                  className="bg-gray-600 hover:bg-gray-500 px-6 py-3 rounded-lg font-bold text-lg flex-1"
                >
                  CANCEL
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
      
      {/* Game Sessions */}
      {activeGameSession && gameMode === 'ai' && (
        <GameSession 
          character={activeGameSession}
          onClose={handleCloseGameSession} 
        />
      )}

      {activeGameSession && gameMode === 'multiplayer' && (
        <MultiplayerLobby 
          character={activeGameSession}
          onClose={handleCloseGameSession} 
        />
      )}
    </div>
  );
}

export default App;