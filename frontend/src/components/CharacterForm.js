// frontend/src/components/CharacterForm.js

import React, { useState, useEffect, useCallback } from 'react';
import api from '../api/axiosConfig';
import AutocompleteField from './AutocompleteField';

function CharacterForm({ onClose, onNext }) {
    const [formData, setFormData] = useState({
        name: '',
        universe: 'star_wars',
        species: '',
        homeworld: '',
        affiliation: '',
        race: '',
        class_type: '',
        level: 1,
        description: '',
        backstory: ''
    });

    const [canonData, setCanonData] = useState({
        species: [],
        planets: [],
        organizations: []
    });

    const [loading, setLoading] = useState(true);

    // ✅ FIX: useCallback dla loadCanonData
    const loadCanonData = useCallback(async () => {
        setLoading(true);
        try {
            const response = await api.get('/wiki/canon/all', {
                params: { universe: formData.universe }
            });
            
            setCanonData({
                species: response.data.data.species || [],
                planets: response.data.data.planets || [],
                organizations: response.data.data.organizations || []
            });
            
            console.log('✅ Loaded canon data:');
            console.log(`   Species: ${response.data.data.species?.length || 0}`);
            console.log(`   Planets: ${response.data.data.planets?.length || 0}`);
            console.log(`   Organizations: ${response.data.data.organizations?.length || 0}`);
            
        } catch (error) {
            console.error('❌ Error loading canon data:', error);
            
            setCanonData({
                species: [],
                planets: [],
                organizations: []
            });
            
            alert('Failed to load canon data. Please refresh the page.');
        } finally {
            setLoading(false);
        }
    }, [formData.universe]); // ✅ FIX: dodaj formData.universe

    useEffect(() => {
        loadCanonData();
    }, [loadCanonData]); // ✅ FIX: dodaj loadCanonData

    const updateFormData = (updates) => {
        setFormData(prev => ({ ...prev, ...updates }));
    };

    const handleUniverseChange = (universe) => {
        updateFormData({ universe });
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        
        if (!formData.name?.trim()) {
            alert('Please enter character name');
            return;
        }
        if (!formData.species?.trim()) {
            alert('Please select species');
            return;
        }
        if (!formData.homeworld?.trim()) {
            alert('Please select homeworld');
            return;
        }
        
        onNext(formData);
    };

    if (loading) {
        return (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div className="bg-gray-800 rounded-lg p-8 max-w-2xl w-full mx-4">
                    <div className="text-center">
                        <div className="text-xl text-white mb-2">Loading canon database...</div>
                        <div className="text-sm text-gray-400">
                            {formData.universe === 'star_wars' ? 'Star Wars' : 'Lord of the Rings'} Universe
                        </div>
                        <div className="mt-4">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-gray-800 rounded-lg p-8 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
                <div className="flex justify-between items-center mb-6">
                    <h2 className="text-2xl font-bold text-white">Create New Character</h2>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-white text-2xl"
                    >
                        ×
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                    {/* Progress Indicator */}
                    <div className="flex items-center justify-center mb-6">
                        <div className="flex items-center">
                            <div className="flex items-center">
                                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold">
                                    1
                                </div>
                                <span className="ml-2 text-white font-semibold">Basic Info</span>
                            </div>
                            <div className="w-12 h-1 bg-gray-600 mx-2"></div>
                            <div className="flex items-center">
                                <div className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center text-gray-400">
                                    2
                                </div>
                                <span className="ml-2 text-gray-400">Attributes</span>
                            </div>
                            <div className="w-12 h-1 bg-gray-600 mx-2"></div>
                            <div className="flex items-center">
                                <div className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center text-gray-400">
                                    3
                                </div>
                                <span className="ml-2 text-gray-400">Skills</span>
                            </div>
                        </div>
                    </div>

                    {/* Universe Selection */}
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            Universe *
                        </label>
                        <select
                            value={formData.universe}
                            onChange={(e) => handleUniverseChange(e.target.value)}
                            className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="star_wars">Star Wars</option>
                            <option value="lotr">Lord of the Rings</option>
                        </select>
                    </div>

                    {/* Character Name */}
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            Character Name *
                        </label>
                        <input
                            type="text"
                            value={formData.name}
                            onChange={(e) => updateFormData({ name: e.target.value })}
                            placeholder="Enter character name"
                            className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            required
                        />
                    </div>

                    {/* Species Autocomplete */}
                    <AutocompleteField
                        label="Species *"
                        value={formData.species}
                        onChange={(value) => updateFormData({ species: value })}
                        suggestions={canonData.species}
                        placeholder="Search species... (e.g., Human, Twi'lek, Wookiee)"
                    />

                    {/* Homeworld Autocomplete */}
                    <AutocompleteField
                        label="Homeworld *"
                        value={formData.homeworld}
                        onChange={(value) => updateFormData({ homeworld: value })}
                        suggestions={canonData.planets}
                        placeholder="Search planet... (e.g., Tatooine, Coruscant)"
                    />

                    {/* Affiliation Autocomplete */}
                    <AutocompleteField
                        label="Affiliation"
                        value={formData.affiliation}
                        onChange={(value) => updateFormData({ affiliation: value })}
                        suggestions={canonData.organizations}
                        placeholder="Search organization... (e.g., Jedi Order, Rebel Alliance)"
                    />

                    {/* Class Type */}
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            Class
                        </label>
                        <input
                            type="text"
                            value={formData.class_type}
                            onChange={(e) => updateFormData({ class_type: e.target.value })}
                            placeholder="e.g., Jedi, Smuggler, Bounty Hunter"
                            className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>

                    {/* Level */}
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            Level
                        </label>
                        <input
                            type="number"
                            min="1"
                            value={formData.level}
                            onChange={(e) => updateFormData({ level: parseInt(e.target.value) })}
                            className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>

                    {/* Description */}
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            Description
                        </label>
                        <textarea
                            value={formData.description}
                            onChange={(e) => updateFormData({ description: e.target.value })}
                            rows="3"
                            placeholder="Brief physical description..."
                            className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>

                    {/* Backstory */}
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            Backstory
                        </label>
                        <textarea
                            value={formData.backstory}
                            onChange={(e) => updateFormData({ backstory: e.target.value })}
                            rows="4"
                            placeholder="Character's history and background..."
                            className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>

                    {/* Buttons */}
                    <div className="flex gap-3 pt-4">
                        <button
                            type="button"
                            onClick={onClose}
                            className="flex-1 bg-gray-600 hover:bg-gray-700 px-6 py-3 rounded-lg font-semibold transition"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            className="flex-1 bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg font-semibold transition"
                        >
                            Next: Attributes →
                        </button>
                    </div>

                    {/* Data Stats */}
                    <div className="pt-4 text-xs text-gray-500 text-center">
                        Loaded: {canonData.species.length} species, {canonData.planets.length} planets, {canonData.organizations.length} organizations
                    </div>
                </form>
            </div>
        </div>
    );
}

export default CharacterForm;