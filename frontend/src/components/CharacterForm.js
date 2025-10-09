// frontend/src/components/CharacterForm.js
import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import WikiImportButton from './WikiImportButton';
import AutocompleteField from './AutocompleteField';

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
        api.get(`/wiki/categories/${universe}/species?limit=20000`),
        api.get(`/wiki/categories/${universe}/planets?limit=20000`),
        api.get(`/wiki/categories/${universe}/organizations?limit=20000`),
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
      setCategoriesError('Failed to load universe data. Using fallback data.');
      
      // Fallback data
      setCategories({
        races: ['Human', "Twi'lek", 'Wookiee', 'Rodian', 'Zabrak'],
        planets: ['Tatooine', 'Coruscant', 'Naboo', 'Endor', 'Hoth'],
        organizations: ['Jedi Order', 'Sith', 'Galactic Empire', 'Rebel Alliance'],
        colors: ['Blue', 'Green', 'Brown', 'Black', 'Blonde', 'Red', 'White', 'Gray'],
        genders: ['Male', 'Female', 'Other', 'None']
      });
    } finally {
      setLoadingCategories(false);
    }
  }, [universe]);

  useEffect(() => {
    fetchCategories();
  }, [universe]);

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

  const handleAddAffiliation = (affiliation) => {
    if (affiliation && !formData.affiliations.includes(affiliation)) {
      setFormData({
        ...formData,
        affiliations: [...formData.affiliations, affiliation]
      });
    }
  };

  const handleRemoveAffiliation = (affiliation) => {
    setFormData({
      ...formData,
      affiliations: formData.affiliations.filter(a => a !== affiliation)
    });
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
      <div className="bg-gray-800 rounded-lg p-6 max-w-4xl w-full mx-4 my-8 max-h-[90vh] overflow-y-auto">
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
          <div className="bg-yellow-900 border border-yellow-700 text-yellow-200 px-4 py-3 rounded mb-4 flex items-center justify-between">
            <span>{categoriesError}</span>
            <button
              onClick={fetchCategories}
              className="bg-yellow-700 hover:bg-yellow-600 px-3 py-1 rounded text-sm transition"
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
              <AutocompleteField
                label={`Species ${categories.races.length > 0 ? `(${categories.races.length} available)` : ''}`}
                value={formData.race}
                onChange={(value) => setFormData({...formData, race: value})}
                suggestions={categories.races}
                placeholder="Type to search or enter manually..."
              />

              {/* Homeworld */}
              <AutocompleteField
                label={`Homeworld ${categories.planets.length > 0 ? `(${categories.planets.length} available)` : ''}`}
                value={formData.homeworld}
                onChange={(value) => setFormData({...formData, homeworld: value})}
                suggestions={categories.planets}
                placeholder="Type to search or enter manually..."
              />

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
                    placeholder="e.g. 172"
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
                    placeholder="e.g. 77"
                    className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              {/* Colors */}
              <div className="grid grid-cols-3 gap-4">
                <AutocompleteField
                  label="Skin Color"
                  value={formData.skin_color}
                  onChange={(value) => setFormData({...formData, skin_color: value})}
                  suggestions={categories.colors}
                  placeholder="Enter or select..."
                />
                <AutocompleteField
                  label="Eye Color"
                  value={formData.eye_color}
                  onChange={(value) => setFormData({...formData, eye_color: value})}
                  suggestions={categories.colors}
                  placeholder="Enter or select..."
                />
                <AutocompleteField
                  label="Hair Color"
                  value={formData.hair_color}
                  onChange={(value) => setFormData({...formData, hair_color: value})}
                  suggestions={categories.colors}
                  placeholder="Enter or select..."
                />
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
                <p className="text-xs text-gray-400 mt-1">
                  Example: Cybernetic hand, Neural implant, Prosthetic leg
                </p>
              </div>

              {/* Affiliations - FIXED: Autocomplete instead of 7851 checkboxes! */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  Affiliations {categories.organizations.length > 0 && `(${categories.organizations.length} available)`}
                </label>
                <AutocompleteField
                  label=""
                  value=""
                  onChange={handleAddAffiliation}
                  suggestions={categories.organizations}
                  placeholder="Type to search and add organizations..."
                  clearOnSelect={true}
                />
                
                {/* Display selected affiliations */}
                {formData.affiliations.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {formData.affiliations.map((affiliation, idx) => (
                      <span
                        key={idx}
                        className="bg-blue-700 px-3 py-1 rounded-full text-sm flex items-center gap-2"
                      >
                        {affiliation}
                        <button
                          type="button"
                          onClick={() => handleRemoveAffiliation(affiliation)}
                          className="text-red-400 hover:text-red-300 font-bold"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}
                
                <p className="text-xs text-gray-400 mt-2">
                  💡 Popular: Jedi Order, Galactic Empire, Rebel Alliance, Mandalorians
                </p>
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
              Next: Attributes →
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default CharacterForm;