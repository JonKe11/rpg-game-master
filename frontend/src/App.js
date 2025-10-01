// frontend/src/App.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import GameSession from './components/GameSession';
import CharacterForm from './components/CharacterForm';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  }
});

function App() {
  const [characters, setCharacters] = useState([]);
  const [selectedCharacter, setSelectedCharacter] = useState(null);
  const [showDetails, setShowDetails] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [isEditMode, setIsEditMode] = useState(false);
  const [editedCharacter, setEditedCharacter] = useState(null);
  const [activeGameSession, setActiveGameSession] = useState(null);

  useEffect(() => {
    fetchCharacters();
  }, []);

  const fetchCharacters = async () => {
    try {
      const response = await api.get('/characters/');
      setCharacters(response.data || []);
    } catch (error) {
      console.error('Error fetching characters:', error);
      if (error.response?.status === 401) {
        console.log('Authorization required - using mock data');
        setCharacters([
          {
            id: 1,
            name: "Test Hero",
            universe: "star_wars",
            race: "Human", 
            class_type: "Warrior",
            level: 1
          }
        ]);
      }
    }
  };

  const handleShowDetails = (character) => {
    setSelectedCharacter(character);
    setEditedCharacter({...character});
    setShowDetails(true);
    setIsEditMode(false);
  };

  const handleCloseDetails = () => {
    setShowDetails(false);
    setSelectedCharacter(null);
    setIsEditMode(false);
    setEditedCharacter(null);
  };

  const handleEditToggle = () => {
    if (isEditMode) {
      setEditedCharacter({...selectedCharacter});
      setIsEditMode(false);
    } else {
      setIsEditMode(true);
    }
  };

  const handleSaveChanges = async () => {
    try {
      const updates = {};
      
      // Porównaj i dodaj tylko zmienione pola
      Object.keys(editedCharacter).forEach(key => {
        if (editedCharacter[key] !== selectedCharacter[key]) {
          updates[key] = editedCharacter[key];
        }
      });
      
      if (Object.keys(updates).length > 0) {
        const response = await api.patch(`/characters/${selectedCharacter.id}`, updates);
        setSelectedCharacter(response.data);
        setEditedCharacter(response.data);
        await fetchCharacters();
        setIsEditMode(false);
        console.log('Changes saved successfully');
      } else {
        console.log('No changes to save');
        setIsEditMode(false);
      }
    } catch (error) {
      console.error('Error saving changes:', error);
      alert('Failed to save changes. Check console for details.');
    }
  };

  const handleDeleteClick = () => {
    setShowDeleteConfirm(true);
  };

  const handleDeleteConfirm = async () => {
    if (!selectedCharacter) {
      console.error('No character selected for deletion');
      return;
    }

    try {
      await api.delete(`/characters/${selectedCharacter.id}`);
      setShowDeleteConfirm(false);
      setShowDetails(false);
      setSelectedCharacter(null);
      setIsEditMode(false);
      await fetchCharacters();
      console.log('Character deleted');
    } catch (error) {
      console.error('Error deleting character:', error);
      alert('Failed to delete character. Check console for details.');
    }
  };

  const handleDeleteCancel = () => {
    setShowDeleteConfirm(false);
  };

  const handleStartGameSession = (character) => {
    console.log('Starting game session for:', character);
    if (!character || !character.id) {
      console.error('Invalid character data:', character);
      alert('Error: Invalid character data');
      return;
    }
    setActiveGameSession(character);
    console.log('ActiveGameSession set to:', character);
  };

  const handleCloseGameSession = () => {
    setActiveGameSession(null);
  };

  const handleFormSuccess = () => {
    fetchCharacters();
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <header className="bg-gray-800 shadow-lg">
        <div className="container mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-blue-400">
            RPG Game Master
          </h1>
          <p className="text-gray-400 mt-2">
            AI-Powered RPG Session Manager
          </p>
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

        {/* Nowy formularz jako modal */}
        {showCreateForm && (
          <CharacterForm
            onClose={() => setShowCreateForm(false)}
            onSuccess={handleFormSuccess}
          />
        )}

        {/* Lista postaci */}
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
                    {character.affiliations && character.affiliations.length > 0 && (
                      <p>
                        <span className="text-gray-400">Affiliations:</span>{' '}
                        <span className="text-white">{character.affiliations.join(', ')}</span>
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
                    <button 
                      onClick={() => handleStartGameSession(character)}
                      className="bg-purple-600 hover:bg-purple-700 px-3 py-1 rounded text-sm transition duration-200"
                    >
                      Start Session
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Modal szczegółów - bez zmian, możesz zostawić jak było */}
        {showDetails && selectedCharacter && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-gray-800 rounded-lg p-6 max-w-2xl w-full mx-4 max-h-screen overflow-y-auto">
              {/* ... reszta kodu modala ... */}
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

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p><span className="text-gray-400">Universe:</span> {selectedCharacter.universe}</p>
                    <p><span className="text-gray-400">Species:</span> {selectedCharacter.race || 'Unknown'}</p>
                    <p><span className="text-gray-400">Class:</span> {selectedCharacter.class_type || 'Unknown'}</p>
                    {selectedCharacter.homeworld && (
                      <p><span className="text-gray-400">Homeworld:</span> {selectedCharacter.homeworld}</p>
                    )}
                    {selectedCharacter.gender && (
                      <p><span className="text-gray-400">Gender:</span> {selectedCharacter.gender}</p>
                    )}
                  </div>
                  <div>
                    {selectedCharacter.height && (
                      <p><span className="text-gray-400">Height:</span> {selectedCharacter.height} cm</p>
                    )}
                    {selectedCharacter.mass && (
                      <p><span className="text-gray-400">Mass:</span> {selectedCharacter.mass} kg</p>
                    )}
                    {selectedCharacter.born_year && selectedCharacter.born_era && (
                      <p><span className="text-gray-400">Born:</span> {selectedCharacter.born_year} {selectedCharacter.born_era}</p>
                    )}
                  </div>
                </div>

                {selectedCharacter.affiliations && selectedCharacter.affiliations.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-300 mb-2">Affiliations</h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedCharacter.affiliations.map((aff, idx) => (
                        <span key={idx} className="bg-blue-700 px-3 py-1 rounded-full text-sm">
                          {aff}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {selectedCharacter.description && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-300 mb-2">Description</h3>
                    <p className="text-gray-300 bg-gray-700 p-4 rounded-lg whitespace-pre-wrap">
                      {selectedCharacter.description}
                    </p>
                  </div>
                )}

                <div className="flex gap-3 pt-4 border-t border-gray-700">
                  <button 
                    onClick={() => {
                      handleStartGameSession(selectedCharacter);
                      handleCloseDetails();
                    }}
                    className="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded-lg font-semibold transition duration-200"
                  >
                    🎮 Start Session
                  </button>
                  <button 
                    onClick={handleDeleteClick}
                    className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg font-semibold transition duration-200"
                  >
                    🗑️ Delete
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

        {/* Modal usuwania */}
        {showDeleteConfirm && selectedCharacter && (
          <div 
            className="fixed inset-0 bg-black bg-opacity-95 flex items-center justify-center" 
            style={{zIndex: 100000}}
          >
            <div className="bg-red-900 rounded-lg p-6 max-w-md w-full mx-4 border-4 border-red-500 shadow-2xl">
              <h3 className="text-2xl font-bold text-red-200 mb-4">
                ⚠️ CONFIRM DELETE
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
                  🗑️ YES, DELETE
                </button>
                <button
                  onClick={handleDeleteCancel}
                  className="bg-gray-600 hover:bg-gray-500 px-6 py-3 rounded-lg font-bold text-lg flex-1"
                >
                  ✖ CANCEL
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
      
      {activeGameSession && (
        <GameSession 
          character={activeGameSession} 
          onClose={handleCloseGameSession} 
        />
      )}
    </div>
  );
}

export default App;