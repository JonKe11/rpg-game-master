// frontend/src/components/WikiImportButton.js
import React, { useState } from 'react';
import api from '../api/axiosConfig';

function WikiImportButton({ universe, onImport }) {
  const [showModal, setShowModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [characterData, setCharacterData] = useState(null);
  const [error, setError] = useState(null);

  // ✅ NOWA FUNKCJA: Wyszukiwanie
  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setSearching(true);
    setError(null);
    setCharacterData(null);
    setSearchResults([]);

    try {
      // ✅ NOWY ENDPOINT: /wiki/{universe}/search
      const searchResponse = await api.get(`/wiki/${universe}/search`, {
        params: { 
          q: searchQuery,
          limit: 10,
          category: 'characters'  // Szukaj tylko postaci
        }
      });

      if (!searchResponse.data.results?.length) {
        setError('Character not found in wiki');
        setSearching(false);
        return;
      }

      setSearchResults(searchResponse.data.results);
      
      // Jeśli tylko 1 wynik - od razu go pobierz
      if (searchResponse.data.results.length === 1) {
        await fetchCharacterDetails(searchResponse.data.results[0]);
      }
      
    } catch (err) {
      console.error('Wiki search error:', err);
      setError(err.response?.data?.detail || 'Failed to search wiki');
    } finally {
      setSearching(false);
    }
  };

  // ✅ NOWA FUNKCJA: Pobierz szczegóły postaci
  const fetchCharacterDetails = async (result) => {
    try {
      // ✅ NOWY ENDPOINT: /wiki/{universe}/{category}/{title}
      const response = await api.get(
        `/wiki/${universe}/${result.category}/${result.title}`
      );

      // ✅ MAPOWANIE: Backend → Frontend format
      const mappedData = {
        name: response.data.title,
        description: response.data.content.description || '',
        image_url: response.data.image_url,
        info: {
          species: response.data.content.species || '',
          homeworld: response.data.content.homeworld || '',
          born: response.data.content.born || '',
          gender: response.data.content.gender || '',
          height: response.data.content.height || '',
          mass: response.data.content.mass || '',
          skin_color: response.data.content.skin_color || '',
          eye_color: response.data.content.eye_color || '',
          hair_color: response.data.content.hair_color || '',
        },
        affiliations: response.data.content.affiliations || [],
        abilities: response.data.content.abilities || []
      };

      setCharacterData(mappedData);
      setSearchResults([]);  // Ukryj listę wyników
      
    } catch (err) {
      console.error('Wiki fetch error:', err);
      setError(err.response?.data?.detail || 'Failed to fetch character data');
    }
  };

  const handleImport = () => {
    if (characterData) {
      const formData = mapWikiToForm(characterData);
      onImport(formData);
      handleClose();
    }
  };

  const handleClose = () => {
    setShowModal(false);
    setSearchQuery('');
    setCharacterData(null);
    setSearchResults([]);
    setError(null);
  };

  const mapWikiToForm = (wikiData) => {
    const infoBox = wikiData.info || {};
    
    return {
      name: wikiData.name,
      race: infoBox.species || '',
      description: wikiData.description || '',
      homeworld: infoBox.homeworld || '',
      born: infoBox.born || '',
      gender: infoBox.gender || '',
      height: parseHeight(infoBox.height),
      mass: parseMass(infoBox.mass),
      skin_color: infoBox.skin_color || '',
      eye_color: infoBox.eye_color || '',
      hair_color: infoBox.hair_color || '',
      affiliations: wikiData.affiliations || [],
      abilities: wikiData.abilities || []
    };
  };

  const parseHeight = (heightStr) => {
    if (!heightStr) return '';
    const match = heightStr.match(/(\d+\.?\d*)/);
    if (!match) return '';
    const value = parseFloat(match[1]);
    if (heightStr.toLowerCase().includes('meter')) {
      return (value * 100).toString();
    }
    return value.toString();
  };

  const parseMass = (massStr) => {
    if (!massStr) return '';
    const match = massStr.match(/(\d+\.?\d*)/);
    return match ? match[1] : '';
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
          <div className="bg-gray-800 rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-2xl font-bold text-blue-400">
                Import Character from Wiki
              </h3>
              <button
                onClick={handleClose}
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

            {/* ✅ NOWE: Lista wyników wyszukiwania */}
            {searchResults.length > 0 && (
              <div className="mb-4">
                <h4 className="text-lg font-semibold mb-2">Search Results:</h4>
                <div className="space-y-2">
                  {searchResults.map((result, idx) => (
                    <button
                      key={idx}
                      onClick={() => fetchCharacterDetails(result)}
                      className="w-full bg-gray-700 hover:bg-gray-600 p-3 rounded-lg text-left transition"
                    >
                      <div className="font-semibold">{result.title}</div>
                      <div className="text-sm text-gray-400">
                        Category: {result.category}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Preview (unchanged) */}
            {characterData && (
              <div className="bg-gray-700 rounded-lg p-4 mb-4">
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
                      {Object.entries(characterData.info)
                        .filter(([_, value]) => value)
                        .slice(0, 8)
                        .map(([key, value]) => (
                          <div key={key}>
                            <span className="text-gray-400 capitalize">
                              {key.replace(/_/g, ' ')}:
                            </span>{' '}
                            <span className="text-white">{value}</span>
                          </div>
                        ))}
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

            {!characterData && !searching && searchResults.length === 0 && (
              <div className="text-center text-gray-400 py-8">
                <p>💡 Try searching for:</p>
                <div className="flex flex-wrap gap-2 justify-center mt-2">
                  {['Luke Skywalker', 'Darth Vader', 'Yoda', 'Leia Organa'].map(name => (
                    <button
                      key={name}
                      onClick={() => {
                        setSearchQuery(name);
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