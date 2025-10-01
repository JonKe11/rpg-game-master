// frontend/src/components/CharacterEditModal.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import AutocompleteField from './AutocompleteField';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  }
});

function CharacterEditModal({ character, onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    name: character.name || '',
    race: character.race || '',
    class_type: character.class_type || '',
    level: character.level || 1,
    description: character.description || '',
    homeworld: character.homeworld || '',
    born_year: character.born_year || '',
    born_era: character.born_era || 'BBY',
    gender: character.gender || '',
    height: character.height || '',
    mass: character.mass || '',
    skin_color: character.skin_color || '',
    eye_color: character.eye_color || '',
    hair_color: character.hair_color || '',
    cybernetics: character.cybernetics || [],
    affiliations: character.affiliations || []
  });

  const [categories, setCategories] = useState({
    species: [],
    planets: [],
    organizations: [],
    colors: [],
    genders: ['Male', 'Female', 'Other', 'None']
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchCanonElements();
  }, [character.universe]);

  const fetchCanonElements = async () => {
    try {
      const response = await api.get(`/wiki/canon/${character.universe}`);
      const data = response.data;
      
      setCategories({
        species: data.popular_species || [],
        planets: data.popular_planets || [],
        organizations: data.popular_affiliations || [],
        colors: data.colors || [],
        genders: data.genders || ['Male', 'Female', 'Other', 'None']
      });
    } catch (error) {
      console.error('Error fetching canon elements:', error);
    }
  };

  const searchCategory = async (category, query) => {
    if (!query || query.length < 2) {
      return categories[category] || [];
    }

    try {
      const response = await api.get(
        `/wiki/categories/${character.universe}/${category}?search=${query}`
      );
      return response.data.items || [];
    } catch (error) {
      console.error(`Error searching ${category}:`, error);
      return [];
    }
  };

  const handleChange = (field, value) => {
    setFormData({
      ...formData,
      [field]: value
    });
  };

  const handleArrayAdd = (field, value) => {
    if (value && !formData[field].includes(value)) {
      setFormData({
        ...formData,
        [field]: [...formData[field], value]
      });
    }
  };

  const handleArrayRemove = (field, value) => {
    setFormData({
      ...formData,
      [field]: formData[field].filter(item => item !== value)
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Przygotuj tylko zmienione pola
      const updates = {};
      Object.keys(formData).forEach(key => {
        if (formData[key] !== character[key]) {
          // Konwertuj typy
          if (key === 'level' || key === 'born_year') {
            updates[key] = formData[key] ? parseInt(formData[key]) : null;
          } else if (key === 'height' || key === 'mass') {
            updates[key] = formData[key] ? parseFloat(formData[key]) : null;
          } else {
            updates[key] = formData[key];
          }
        }
      });

      if (Object.keys(updates).length > 0) {
        await api.patch(`/characters/${character.id}`, updates);
        onSuccess();
        onClose();
      } else {
        onClose();
      }
    } catch (error) {
      console.error('Error updating character:', error);
      setError(error.response?.data?.detail || 'Failed to update character');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 overflow-y-auto">
      <div className="bg-gray-800 rounded-lg p-8 max-w-4xl w-full mx-4 my-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-3xl font-bold text-blue-400">Edit Character</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-2xl"
          >
            ×
          </button>
        </div>

        {error && (
          <div className="bg-red-900 border border-red-700 text-red-200 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Podstawowe pola */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                Name *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => handleChange('name', e.target.value)}
                className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Level
              </label>
              <input
                type="number"
                min="1"
                value={formData.level}
                onChange={(e) => handleChange('level', e.target.value)}
                className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Star Wars pola */}
          {character.universe === 'star_wars' && (
            <>
              <div className="grid grid-cols-2 gap-4">
                <AutocompleteField
                  label="Species/Race *"
                  value={formData.race}
                  onChange={(value) => handleChange('race', value)}
                  suggestions={categories.species}
                  onSearch={(query) => searchCategory('species', query)}
                  placeholder="e.g., Human, Twi'lek"
                  required
                />

                <AutocompleteField
                  label="Homeworld"
                  value={formData.homeworld}
                  onChange={(value) => handleChange('homeworld', value)}
                  suggestions={categories.planets}
                  onSearch={(query) => searchCategory('planets', query)}
                  placeholder="e.g., Tatooine"
                />
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Born Year
                  </label>
                  <input
                    type="number"
                    value={formData.born_year}
                    onChange={(e) => handleChange('born_year', e.target.value)}
                    className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., 19"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Era
                  </label>
                  <select
                    value={formData.born_era}
                    onChange={(e) => handleChange('born_era', e.target.value)}
                    className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="BBY">BBY</option>
                    <option value="ABY">ABY</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Gender
                  </label>
                  <select
                    value={formData.gender}
                    onChange={(e) => handleChange('gender', e.target.value)}
                    className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select...</option>
                    {categories.genders.map(gender => (
                      <option key={gender} value={gender}>{gender}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Height (cm)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={formData.height}
                    onChange={(e) => handleChange('height', e.target.value)}
                    className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Mass (kg)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={formData.mass}
                    onChange={(e) => handleChange('mass', e.target.value)}
                    className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <AutocompleteField
                  label="Skin Color"
                  value={formData.skin_color}
                  onChange={(value) => handleChange('skin_color', value)}
                  suggestions={categories.colors}
                  placeholder="e.g., Fair"
                />

                <AutocompleteField
                  label="Eye Color"
                  value={formData.eye_color}
                  onChange={(value) => handleChange('eye_color', value)}
                  suggestions={categories.colors}
                  placeholder="e.g., Blue"
                />

                <AutocompleteField
                  label="Hair Color"
                  value={formData.hair_color}
                  onChange={(value) => handleChange('hair_color', value)}
                  suggestions={categories.colors}
                  placeholder="e.g., Brown"
                />
              </div>

              {/* Cybernetics */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  Cybernetics
                </label>
                <div className="flex gap-2 mb-2">
                  <input
                    type="text"
                    id="edit-cybernetics-input"
                    className="flex-1 px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Add cybernetic enhancement"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        const input = e.target;
                        handleArrayAdd('cybernetics', input.value);
                        input.value = '';
                      }
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => {
                      const input = document.getElementById('edit-cybernetics-input');
                      handleArrayAdd('cybernetics', input.value);
                      input.value = '';
                    }}
                    className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg"
                  >
                    Add
                  </button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {formData.cybernetics.map((item, index) => (
                    <span
                      key={index}
                      className="bg-gray-700 px-3 py-1 rounded-full text-sm flex items-center gap-2"
                    >
                      {item}
                      <button
                        type="button"
                        onClick={() => handleArrayRemove('cybernetics', item)}
                        className="text-red-400 hover:text-red-300"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              </div>

              {/* Affiliations */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  Affiliation(s)
                </label>
                <AutocompleteField
                  value=""
                  onChange={(value) => {
                    handleArrayAdd('affiliations', value);
                  }}
                  suggestions={categories.organizations}
                  onSearch={(query) => searchCategory('organizations', query)}
                  placeholder="Add organization"
                  clearOnSelect
                />
                <div className="flex flex-wrap gap-2 mt-2">
                  {formData.affiliations.map((item, index) => (
                    <span
                      key={index}
                      className="bg-blue-700 px-3 py-1 rounded-full text-sm flex items-center gap-2"
                    >
                      {item}
                      <button
                        type="button"
                        onClick={() => handleArrayRemove('affiliations', item)}
                        className="text-red-400 hover:text-red-300"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* Class */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Class/Role
            </label>
            <input
              type="text"
              value={formData.class_type}
              onChange={(e) => handleChange('class_type', e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Description / Backstory
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => handleChange('description', e.target.value)}
              rows="6"
              className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Buttons */}
          <div className="flex gap-4 pt-4">
            <button
              type="submit"
              disabled={loading}
              className="bg-green-600 hover:bg-green-700 px-6 py-3 rounded-lg font-semibold transition duration-200 disabled:opacity-50 flex-1"
            >
              {loading ? 'Saving...' : 'Save Changes'}
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

export default CharacterEditModal;