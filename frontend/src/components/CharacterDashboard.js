// frontend/src/pages/CharacterDashboard.js
import React, { useState, useEffect } from 'react';
import api from '../api/axiosConfig';
import CharacterCreationWizard from '../components/CharacterCreationWizard';
import CharacterDetails from '../components/CharacterDetails'; 
// import CharacterEditModal from '../components/CharacterEditModal'; 

function CharacterDashboard({ user, onStartSession }) {
  const [characters, setCharacters] = useState([]);
  const [selectedCharacter, setSelectedCharacter] = useState(null);
  const [showDetails, setShowDetails] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);

  useEffect(() => {
    fetchCharacters();
  }, []);

  const fetchCharacters = async () => {
    try {
      const response = await api.get('/characters/');
      setCharacters(response.data || []);
    } catch (error) {
      console.error('Error fetching characters:', error);
    }
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

  return (
    <div className="container mx-auto px-4 py-8">
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
          onSuccess={() => {
            setShowCreateForm(false);
            fetchCharacters();
          }}
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
        <h3 className="text-xl font-bold text-blue-400">{character.name}</h3>
        <span className="bg-blue-600 px-2 py-1 rounded text-sm">Lvl {character.level}</span>
      </div>
      
      <div className="space-y-2 text-sm text-gray-300">
        <p>Universe: <span className="capitalize">{character.universe.replace('_', ' ')}</span></p>
        <p>Race: {character.race}</p>
        <p>Class: {character.class_type}</p>
      </div>

      <div className="mt-4 flex gap-2">
        <button 
          onClick={() => handleShowDetails(character)}
          className="bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded text-sm transition duration-200"
        >
          Details
        </button>

   
        <div className="relative group">
          <button className="bg-purple-600 hover:bg-purple-700 px-3 py-1 rounded text-sm transition duration-200">
            🎮 Start Session ▼
          </button>
          
      
          <div className="hidden group-hover:block absolute left-0 top-full pt-1 w-48 z-50">
          
            <div className="bg-gray-800 rounded-lg shadow-xl border border-gray-700 overflow-hidden">
              <button
                onClick={() => onStartSession(character, 'ai')}
                className="w-full text-left px-4 py-2 hover:bg-gray-700 transition text-sm border-b border-gray-700"
              >
                🤖 AI Game Master
              </button>
              <button
                onClick={() => onStartSession(character, 'multiplayer')}
                className="w-full text-left px-4 py-2 hover:bg-gray-700 transition text-sm"
              >
                👥 Multiplayer
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  ))}
</div>
        )}
      </div>

      {/* Modals */}
      {showDetails && selectedCharacter && (
        <CharacterDetails 
            character={selectedCharacter} 
            onClose={handleCloseDetails}
            onDelete={handleDeleteClick}
            onStartSession={() => onStartSession(selectedCharacter, 'multiplayer')}
      
        />
      )}

      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-95 flex items-center justify-center" style={{zIndex: 100000}}>
            <div className="bg-red-900 rounded-lg p-6 max-w-md w-full mx-4 border-4 border-red-500">
                <h3 className="text-2xl font-bold text-red-200 mb-4">CONFIRM DELETE</h3>
                <p className="text-red-100 mb-6">Are you sure? This cannot be undone.</p>
                <div className="flex gap-4">
                    <button onClick={handleDeleteConfirm} className="bg-red-600 hover:bg-red-500 px-6 py-3 rounded-lg font-bold flex-1">YES, DELETE</button>
                    <button onClick={() => setShowDeleteConfirm(false)} className="bg-gray-600 hover:bg-gray-500 px-6 py-3 rounded-lg font-bold flex-1">CANCEL</button>
                </div>
            </div>
        </div>
      )}
    </div>
  );
}

export default CharacterDashboard;