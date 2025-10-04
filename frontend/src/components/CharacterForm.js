// frontend/src/components/CharacterForm.js
import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import WikiImportButton from './WikiImportButton';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  }
});

function CharacterForm({ onClose, onNext }) {
  const [universe, setUniverse] = useState('star_wars');
  const [formData, setFormData] = useState({
    name: '',
    universe: 'star_wars',
    race: '',
    class_type: '',
    level: 1,
    description: '',
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

  const [categories, setCategories] = useState({
    races: [],
    planets: [],
    organizations: [],
    colors: [],
    genders: []
  });

  const [loadingCategories, setLoadingCategories] = useState(true);
  const [categoriesError, setCategoriesError] = useState(null);
  const [showRaceSuggestions, setShowRaceSuggestions] = useState(false);
  const [showPlanetSuggestions, setShowPlanetSuggestions] = useState(false);

  const universeOptions = [
    { value: 'star_wars', label: 'Star Wars' },
    { value: 'lotr', label: 'Lord of the Rings' },
    { value: 'dnd', label: 'Dungeons & Dragons' },
    { value: 'cyberpunk', label: 'Cyberpunk' }
  ];

  const fetchCategories = useCallback(async () => {
    setLoadingCategories(true);
    setCategoriesError(null);
    
    try {
      const [speciesRes, planetsRes, orgsRes, canonRes] = await Promise.all([
        api.get(`/wiki/categories/${universe}/species?limit=100`),
        api.get(`/wiki/categories/${universe}/planets?limit=100`),
        api.get(`/wiki/categories/${universe}/organizations?limit=50`),
        api.get(`/wiki/canon/${universe}`)
      ]);

      setCategories({
        races: speciesRes.data.items || [],
        planets: planetsRes.data.items || [],
        organizations: orgsRes.data.items || [],
        colors: canonRes.data.colors || [],
        genders: canonRes.data.genders || []
      });
    } catch (error) {
      console.error('Error fetching categories:', error);
      setCategoriesError('Failed to load universe data. Please try again.');
    } finally {
      setLoadingCategories(false);
    }
  }, [universe]);

  useEffect(() => {
    fetchCategories();
  }, [fetchCategories]);

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
    setFormData({ ...formData, [name]: value });
  };

  const handleAffiliationToggle = (affiliation) => {
    const current = formData.affiliations || [];
    const updated = current.includes(affiliation)
      ? current.filter(a => a !== affiliation)
      : [...current, affiliation];
    setFormData({ ...formData, affiliations: updated });
  };

  const getFilteredRaces = () => {
    if (!formData.race) return categories.races;
    return categories.races.filter(race => 
      race.toLowerCase().includes(formData.race.toLowerCase())
    );
  };

  const getFilteredPlanets = () => {
    if (!formData.homeworld) return categories.planets;
    return categories.planets.filter(planet => 
      planet.toLowerCase().includes(formData.homeworld.toLowerCase())
    );
  };

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

  const handleNext = (e) => {
    e.preventDefault();
    
    const processedData = {
      ...formData,
      level: parseInt(formData.level) || 1,
      height: formData.height ? parseFloat(formData.height) : null,
      mass: formData.mass ? parseFloat(formData.mass) : null,
      born_year: formData.born_year ? parseInt(formData.born_year) : null,
      cybernetics: formData.cybernetics 
        ? formData.cybernetics.split(',').map(s => s.trim()).filter(s => s)
        : [],
      affiliations: formData.affiliations || [],
    };
    
    onNext(processedData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
      <div className="bg-gray-800 rounded-lg p-6 max-w-4xl w-full mx-4 my-8">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-2xl font-bold text-blue-400">Create New Character</h2>
            <p className="text-sm text-gray-400 mt-1">Step 1 of 3: Basic Information</p>
          </div>
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

        {loadingCategories && (
          <div className="bg-blue-900 border border-blue-700 text-blue-200 px-4 py-3 rounded mb-4">
            Loading universe data...
          </div>
        )}

        {categoriesError && (
          <div className="bg-red-900 border border-red-700 text-red-200 px-4 py-3 rounded mb-4 flex items-center justify-between">
            <span>{categoriesError}</span>
            <button
              onClick={fetchCategories}
              className="bg-red-700 hover:bg-red-600 px-3 py-1 rounded text-sm transition"
            >
              Retry
            </button>
          </div>
        )}

        <form onSubmit={handleNext} className="space-y-6">
          {/* Universe selector */}
          <div>
            <label className="block text-sm font-medium mb-2">Universe *</label>
            <select
              value={universe}
              onChange={(e) => handleUniverseChange(e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {universeOptions.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          {/* Name and Level */}
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

          {universe === 'star_wars' && (
            <>
              {/* Species */}
              <div className="relative">
                <label className="block text-sm font-medium mb-2">
                  Species {categories.races.length > 0 && `(${categories.races.length} available)`}
                </label>
                <input
                  type="text"
                  name="race"
                  value={formData.race}
                  onChange={handleInputChange}
                  onFocus={() => setShowRaceSuggestions(true)}
                  onBlur={() => setTimeout(() => setShowRaceSuggestions(false), 200)}
                  placeholder="Type to search or enter manually..."
                  className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                {showRaceSuggestions && getFilteredRaces().length > 0 && (
                  <div className="absolute z-10 w-full mt-1 bg-gray-700 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                    {getFilteredRaces().slice(0, 20).map(race => (
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

              {/* Homeworld */}
              <div className="relative">
                <label className="block text-sm font-medium mb-2">
                  Homeworld {categories.planets.length > 0 && `(${categories.planets.length} available)`}
                </label>
                <input
                  type="text"
                  name="homeworld"
                  value={formData.homeworld}
                  onChange={handleInputChange}
                  onFocus={() => setShowPlanetSuggestions(true)}
                  onBlur={() => setTimeout(() => setShowPlanetSuggestions(false), 200)}
                  placeholder="Type to search or enter manually..."
                  className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                {showPlanetSuggestions && getFilteredPlanets().length > 0 && (
                  <div className="absolute z-10 w-full mt-1 bg-gray-700 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                    {getFilteredPlanets().slice(0, 20).map(planet => (
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

              {/* Birth Year and Era */}
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
                    {categories.genders.map(gender => (
                      <option key={gender} value={gender}>{gender}</option>
                    ))}
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

              {/* Height and Mass */}
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

              {/* Colors */}
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Skin Color</label>
                  <input
                    type="text"
                    name="skin_color"
                    value={formData.skin_color}
                    onChange={handleInputChange}
                    list="skin-colors"
                    placeholder="Enter or select..."
                    className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <datalist id="skin-colors">
                    {categories.colors.map(color => (
                      <option key={color} value={color} />
                    ))}
                  </datalist>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Eye Color</label>
                  <input
                    type="text"
                    name="eye_color"
                    value={formData.eye_color}
                    onChange={handleInputChange}
                    list="eye-colors"
                    placeholder="Enter or select..."
                    className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <datalist id="eye-colors">
                    {categories.colors.map(color => (
                      <option key={color} value={color} />
                    ))}
                  </datalist>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Hair Color</label>
                  <input
                    type="text"
                    name="hair_color"
                    value={formData.hair_color}
                    onChange={handleInputChange}
                    list="hair-colors"
                    placeholder="Enter or select..."
                    className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <datalist id="hair-colors">
                    {categories.colors.map(color => (
                      <option key={color} value={color} />
                    ))}
                  </datalist>
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
                  placeholder="None or describe (comma separated)"
                  className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Affiliations */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  Affiliations {categories.organizations.length > 0 && `(${categories.organizations.length} available)`}
                </label>
                <div className="bg-gray-700 rounded-lg p-4 max-h-48 overflow-y-auto">
                  {categories.organizations.length === 0 ? (
                    <p className="text-gray-400 text-sm">
                      {loadingCategories ? 'Loading organizations...' : 'No organizations loaded.'}
                    </p>
                  ) : (
                    <div className="grid grid-cols-2 gap-2">
                      {categories.organizations.map(affiliation => (
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
                  )}
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

          {/* Buttons */}
          <div className="flex gap-3 pt-4 border-t border-gray-700">
            <button
              type="button"
              onClick={onClose}
              className="bg-gray-600 hover:bg-gray-700 px-6 py-3 rounded-lg font-semibold transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg font-semibold transition flex-1"
            >
              Next: Attributes
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default CharacterForm;