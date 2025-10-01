// frontend/src/components/WikiImportButton.js
import React, { useState } from 'react';
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  }
});

function WikiImportButton({ universe, onImport }) {
  const [showModal, setShowModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [characterData, setCharacterData] = useState(null);
  const [error, setError] = useState(null);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setSearching(true);
    setError(null);
    setCharacterData(null);

    try {
      // Wyszukaj postać
      const searchResponse = await api.get(`/wiki/search/${searchQuery}`, {
        params: { universe }
      });

      if (!searchResponse.data.url) {
        setError('Character not found in wiki');
        setSearching(false);
        return;
      }

      // Pobierz pełne dane
      const dataResponse = await api.get(`/wiki/data/${searchQuery}`, {
        params: { universe }
      });

      setCharacterData(dataResponse.data);
    } catch (err) {
      console.error('Wiki import error:', err);
      setError(err.response?.data?.detail || 'Failed to import from wiki');
    } finally {
      setSearching(false);
    }
  };

  const handleImport = () => {
    if (characterData) {
      // Mapuj dane z wiki na formularz
      const mappedData = mapWikiToForm(characterData);
      onImport(mappedData);
      setShowModal(false);
      setSearchQuery('');
      setCharacterData(null);
    }
  };

  const mapWikiToForm = (wikiData) => {
    const infoBox = wikiData.info || {};
    
    return {
      name: wikiData.name,
      race: infoBox.species || infoBox.race || '',
      description: wikiData.description || '',
      homeworld: infoBox.homeworld || '',
      born: infoBox.born || '',
      gender: infoBox.gender || '',
      height: parseHeight(infoBox.height),
      mass: parseMass(infoBox.mass),
      skin_color: infoBox.skin_color || infoBox.skin || '',
      eye_color: infoBox.eye_color || infoBox.eyes || '',
      hair_color: infoBox.hair_color || infoBox.hair || '',
      cybernetics: extractCybernetics(infoBox),
      affiliations: wikiData.affiliations || [],
      abilities: wikiData.abilities || []
    };
  };

  const parseHeight = (heightStr) => {
    if (!heightStr) return '';
    // Parse "1.83 meters" or "183 centimeters"
    const match = heightStr.match(/(\d+\.?\d*)/);
    if (!match) return '';
    const value = parseFloat(match[1]);
    if (heightStr.toLowerCase().includes('meter')) {
      return (value * 100).toString(); // Convert to cm
    }
    return value.toString();
  };

  const parseMass = (massStr) => {
    if (!massStr) return '';
    // Parse "77 kilograms"
    const match = massStr.match(/(\d+\.?\d*)/);
    return match ? match[1] : '';
  };

  const extractCybernetics = (infoBox) => {
    // Check common fields for cybernetics
    const cyberFields = ['cybernetics', 'prosthetics', 'implants'];
    for (const field of cyberFields) {
      if (infoBox[field]) {
        return Array.isArray(infoBox[field]) ? infoBox[field] : [infoBox[field]];
      }
    }
    return [];
  };

  return (
    <>
      <button
        type="button"
        onClick={() => setShowModal(true)}
        className="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded-lg font-semibold transition duration-200 flex items-center gap-2"
      >
        📥 Import from Wiki
      </button>

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-[60]">
          <div className="bg-gray-800 rounded-lg p-6 max-w-2xl w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-2xl font-bold text-blue-400">
                Import Character from Wiki
              </h3>
              <button
                onClick={() => {
                  setShowModal(false);
                  setSearchQuery('');
                  setCharacterData(null);
                  setError(null);
                }}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>

            <p className="text-gray-400 mb-4">
              Search for a character in {universe.replace('_', ' ')} wiki to auto-fill the form.
            </p>

            {/* Search input */}
            <div className="flex gap-2 mb-4">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleSearch();
                  }
                }}
                placeholder="e.g., Luke Skywalker, Darth Vader..."
                className="flex-1 px-4 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={handleSearch}
                disabled={searching || !searchQuery.trim()}
                className="bg-blue-600 hover:bg-blue-700 px-6 py-2 rounded-lg font-semibold transition duration-200 disabled:opacity-50"
              >
                {searching ? 'Searching...' : 'Search'}
              </button>
            </div>

            {error && (
              <div className="bg-red-900 border border-red-700 text-red-200 px-4 py-3 rounded mb-4">
                {error}
              </div>
            )}

            {/* Preview */}
            {characterData && (
              <div className="bg-gray-700 rounded-lg p-4 mb-4 max-h-96 overflow-y-auto">
                <h4 className="text-xl font-bold text-blue-400 mb-3">
                  {characterData.name}
                </h4>

                {characterData.image_url && (
                  <img
                    src={characterData.image_url}
                    alt={characterData.name}
                    className="w-32 h-32 object-cover rounded-lg mb-3"
                    onError={(e) => {e.target.style.display = 'none'}}
                  />
                )}

                <div className="space-y-2 text-sm">
                  <p className="text-gray-300">{characterData.description}</p>
                  
                  {characterData.info && (
                    <div className="grid grid-cols-2 gap-2 mt-3">
                      {Object.entries(characterData.info).slice(0, 8).map(([key, value]) => (
                        <div key={key}>
                          <span className="text-gray-400 capitalize">
                            {key.replace(/_/g, ' ')}:
                          </span>{' '}
                          <span className="text-white">{value}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {characterData.affiliations && characterData.affiliations.length > 0 && (
                    <div className="mt-3">
                      <span className="text-gray-400">Affiliations:</span>
                      <div className="flex flex-wrap gap-2 mt-1">
                        {characterData.affiliations.map((aff, idx) => (
                          <span key={idx} className="bg-blue-700 px-2 py-1 rounded text-xs">
                            {aff}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {characterData.abilities && characterData.abilities.length > 0 && (
                    <div className="mt-3">
                      <span className="text-gray-400">Abilities:</span>
                      <ul className="list-disc list-inside mt-1">
                        {characterData.abilities.slice(0, 5).map((ability, idx) => (
                          <li key={idx} className="text-sm">{ability}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                <div className="flex gap-3 mt-4 pt-4 border-t border-gray-600">
                  <button
                    onClick={handleImport}
                    className="bg-green-600 hover:bg-green-700 px-6 py-2 rounded-lg font-semibold transition duration-200 flex-1"
                  >
                    ✓ Import This Character
                  </button>
                  <button
                    onClick={() => {
                      setCharacterData(null);
                      setSearchQuery('');
                    }}
                    className="bg-gray-600 hover:bg-gray-700 px-6 py-2 rounded-lg font-semibold transition duration-200"
                  >
                    Search Again
                  </button>
                </div>
              </div>
            )}

            {!characterData && !searching && (
              <div className="text-center text-gray-400 py-8">
                <p>💡 Try searching for:</p>
                <div className="flex flex-wrap gap-2 justify-center mt-2">
                  {['Luke Skywalker', 'Darth Vader', 'Yoda', 'Leia Organa'].map(name => (
                    <button
                      key={name}
                      onClick={() => {
                        setSearchQuery(name);
                        // Auto-search after a moment
                        setTimeout(() => handleSearch(), 100);
                      }}
                      className="bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded text-sm transition"
                    >
                      {name}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}

export default WikiImportButton;