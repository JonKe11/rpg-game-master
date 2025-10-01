// frontend/src/components/CharacterForm.js
import React, { useState } from 'react';
import axios from 'axios';
import WikiImportButton from './WikiImportButton';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  }
});

function CharacterForm({ onClose, onSuccess }) {
  const [universe, setUniverse] = useState('star_wars');
  const [formData, setFormData] = useState({
    name: '',
    universe: 'star_wars',
    race: '',
    class_type: '',
    level: 1,
    description: '',
    // Star Wars specific fields
    homeworld: '',
    born_year: '',
    born_era: 'BBY',
    gender: '',
    height: '',
    mass: '',
    skin_color: '',
    eye_color: '',
    hair_color: '',
    cybernetics: '',
    affiliations: []
  });

  const [isLoading, setIsLoading] = useState(false);
  const [showRaceSuggestions, setShowRaceSuggestions] = useState(false);
  const [showPlanetSuggestions, setShowPlanetSuggestions] = useState(false);

  // Universe options
  const universeOptions = [
    { value: 'star_wars', label: 'Star Wars' },
    { value: 'lotr', label: 'Lord of the Rings' },
    { value: 'dnd', label: 'Dungeons & Dragons' },
    { value: 'cyberpunk', label: 'Cyberpunk' }
  ];

  // Wiki data (hardcoded for now, later from API)
  const starWarsRaces = [
    'Human', 'Twi\'lek', 'Wookiee', 'Rodian', 'Zabrak', 'Duros', 
    'Mon Calamari', 'Bothan', 'Sullustan', 'Trandoshan', 'Togruta',
    'Nautolan', 'Mirialan', 'Chiss', 'Kel Dor', 'Cerean', 'Iktotchi'
  ];

  const starWarsPlanets = [
    'Tatooine', 'Coruscant', 'Naboo', 'Alderaan', 'Hoth', 'Endor',
    'Dagobah', 'Bespin', 'Mustafar', 'Kashyyyk', 'Kamino', 'Geonosis',
    'Mandalore', 'Corellia', 'Dantooine', 'Ryloth', 'Mon Cala'
  ];

  const starWarsAffiliations = [
    'Jedi Order', 'Sith', 'Galactic Republic', 'Galactic Empire',
    'Rebel Alliance', 'New Republic', 'First Order', 'Resistance',
    'Mandalorians', 'Bounty Hunters Guild', 'Hutt Cartel',
    'Trade Federation', 'Separatists', 'Republic Senate'
  ];

  const handleUniverseChange = (newUniverse) => {
    setUniverse(newUniverse);
    setFormData({
      ...formData,
      universe: newUniverse,
      race: '',
      homeworld: '',
      affiliations: []
    });
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  const handleAffiliationToggle = (affiliation) => {
    const currentAffiliations = formData.affiliations || [];
    if (currentAffiliations.includes(affiliation)) {
      setFormData({
        ...formData,
        affiliations: currentAffiliations.filter(a => a !== affiliation)
      });
    } else {
      setFormData({
        ...formData,
        affiliations: [...currentAffiliations, affiliation]
      });
    }
  };

  const getFilteredRaces = () => {
    if (!formData.race) return starWarsRaces;
    return starWarsRaces.filter(race => 
      race.toLowerCase().includes(formData.race.toLowerCase())
    );
  };

  const getFilteredPlanets = () => {
    if (!formData.homeworld) return starWarsPlanets;
    return starWarsPlanets.filter(planet => 
      planet.toLowerCase().includes(formData.homeworld.toLowerCase())
    );
  };

  // Handle Wiki Import
  const handleImport = (wikiData) => {
    setFormData({
      ...formData,
      name: wikiData.name || formData.name,
      race: wikiData.race || formData.race,
      description: wikiData.description || formData.description,
      homeworld: wikiData.homeworld || formData.homeworld,
      gender: wikiData.gender || formData.gender,
      height: wikiData.height || formData.height,
      mass: wikiData.mass || formData.mass,
      skin_color: wikiData.skin_color || formData.skin_color,
      eye_color: wikiData.eye_color || formData.eye_color,
      hair_color: wikiData.hair_color || formData.hair_color,
      cybernetics: wikiData.cybernetics || formData.cybernetics,
      affiliations: wikiData.affiliations || formData.affiliations,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const submitData = {
        ...formData,
        level: parseInt(formData.level) || 1,
        height: formData.height ? parseInt(formData.height) : null,
        mass: formData.mass ? parseInt(formData.mass) : null,
        born_year: formData.born_year ? parseInt(formData.born_year) : null,
      };

      await api.post('/characters/', submitData);
      onSuccess();
      onClose();
    } catch (error) {
      console.error('Error creating character:', error);
      alert('Failed to create character. Check console for details.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
      <div className="bg-gray-800 rounded-lg p-6 max-w-4xl w-full mx-4 my-8">
        {/* Header with Import button */}
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-blue-400">Create New Character</h2>
          <div className="flex gap-2 items-center">
            <WikiImportButton 
              universe={universe}
              onImport={handleImport}
            />
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white text-2xl ml-4"
            >
              ×
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Universe Selection */}
          <div>
            <label className="block text-sm font-medium mb-2">Universe *</label>
            <select
              value={universe}
              onChange={(e) => handleUniverseChange(e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {universeOptions.map(opt => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Basic Fields */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Name *</label>
              <input
                type="text"
                name="name"
                required
                value={formData.name}
                onChange={handleInputChange}
                className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Level</label>
              <input
                type="number"
                name="level"
                min="1"
                value={formData.level}
                onChange={handleInputChange}
                className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Star Wars Specific Fields */}
          {universe === 'star_wars' && (
            <>
              {/* Species with autocomplete */}
              <div className="relative">
                <label className="block text-sm font-medium mb-2">Species</label>
                <input
                  type="text"
                  name="race"
                  value={formData.race}
                  onChange={handleInputChange}
                  onFocus={() => setShowRaceSuggestions(true)}
                  onBlur={() => setTimeout(() => setShowRaceSuggestions(false), 200)}
                  placeholder="Type to search..."
                  className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                {showRaceSuggestions && getFilteredRaces().length > 0 && (
                  <div className="absolute z-10 w-full mt-1 bg-gray-700 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                    {getFilteredRaces().map(race => (
                      <div
                        key={race}
                        onClick={() => {
                          setFormData({...formData, race});
                          setShowRaceSuggestions(false);
                        }}
                        className="px-3 py-2 hover:bg-gray-600 cursor-pointer"
                      >
                        {race}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Homeworld with autocomplete */}
              <div className="relative">
                <label className="block text-sm font-medium mb-2">Homeworld</label>
                <input
                  type="text"
                  name="homeworld"
                  value={formData.homeworld}
                  onChange={handleInputChange}
                  onFocus={() => setShowPlanetSuggestions(true)}
                  onBlur={() => setTimeout(() => setShowPlanetSuggestions(false), 200)}
                  placeholder="Type to search..."
                  className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                {showPlanetSuggestions && getFilteredPlanets().length > 0 && (
                  <div className="absolute z-10 w-full mt-1 bg-gray-700 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                    {getFilteredPlanets().map(planet => (
                      <div
                        key={planet}
                        onClick={() => {
                          setFormData({...formData, homeworld: planet});
                          setShowPlanetSuggestions(false);
                        }}
                        className="px-3 py-2 hover:bg-gray-600 cursor-pointer"
                      >
                        {planet}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Birth Year */}
              <div className="grid grid-cols-3 gap-4">
                <div className="col-span-2">
                  <label className="block text-sm font-medium mb-2">Birth Year</label>
                  <input
                    type="number"
                    name="born_year"
                    value={formData.born_year}
                    onChange={handleInputChange}
                    placeholder="e.g. 19"
                    className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Era</label>
                  <select
                    name="born_era"
                    value={formData.born_era}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="BBY">BBY</option>
                    <option value="ABY">ABY</option>
                  </select>
                </div>
              </div>

              {/* Gender and Class */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Gender</label>
                  <select
                    name="gender"
                    value={formData.gender}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select...</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Class/Occupation</label>
                  <input
                    type="text"
                    name="class_type"
                    value={formData.class_type}
                    onChange={handleInputChange}
                    placeholder="e.g. Jedi, Smuggler, Pilot"
                    className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              {/* Physical Attributes */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Height (cm)</label>
                  <input
                    type="number"
                    name="height"
                    value={formData.height}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Mass (kg)</label>
                  <input
                    type="number"
                    name="mass"
                    value={formData.mass}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Skin Color</label>
                  <input
                    type="text"
                    name="skin_color"
                    value={formData.skin_color}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Eye Color</label>
                  <input
                    type="text"
                    name="eye_color"
                    value={formData.eye_color}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Hair Color</label>
                  <input
                    type="text"
                    name="hair_color"
                    value={formData.hair_color}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              {/* Cybernetics */}
              <div>
                <label className="block text-sm font-medium mb-2">Cybernetics</label>
                <input
                  type="text"
                  name="cybernetics"
                  value={formData.cybernetics}
                  onChange={handleInputChange}
                  placeholder="None or describe"
                  className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Affiliations */}
              <div>
                <label className="block text-sm font-medium mb-2">Affiliations</label>
                <div className="bg-gray-700 rounded-lg p-4 max-h-48 overflow-y-auto">
                  <div className="grid grid-cols-2 gap-2">
                    {starWarsAffiliations.map(affiliation => (
                      <label key={affiliation} className="flex items-center space-x-2 cursor-pointer hover:bg-gray-600 p-2 rounded">
                        <input
                          type="checkbox"
                          checked={formData.affiliations.includes(affiliation)}
                          onChange={() => handleAffiliationToggle(affiliation)}
                          className="form-checkbox h-4 w-4 text-blue-600"
                        />
                        <span className="text-sm">{affiliation}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            </>
          )}

          {/* Description */}
          <div>
            <label className="block text-sm font-medium mb-2">Description / Backstory</label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              rows="6"
              placeholder="Describe your character's appearance, personality, and backstory..."
              className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Submit Buttons */}
          <div className="flex gap-3 pt-4 border-t border-gray-700">
            <button
              type="submit"
              disabled={isLoading}
              className="bg-green-600 hover:bg-green-700 px-6 py-3 rounded-lg font-semibold transition duration-200 disabled:opacity-50"
            >
              {isLoading ? 'Creating...' : 'Create Character'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="bg-gray-600 hover:bg-gray-700 px-6 py-3 rounded-lg font-semibold transition duration-200"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default CharacterForm;