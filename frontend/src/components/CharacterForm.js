// frontend/src/components/CharacterForm.js
// ✅ WERSJA 3.2 - Odbiera onSearchWiki i naprawia handleFormValueChange

import React, { useState } from 'react';
// ⛔️ Usunięto 'api' - nie jest już tu potrzebne
import AutocompleteField from './AutocompleteField'; 

// ✅ Zaktualizowano propsy: dodano onSearchWiki
function CharacterForm({ onClose, onNext, onSearchWiki }) {
    const [formData, setFormData] = useState({
        name: '',
        universe: 'star_wars',
        species: '',
        homeworld: '',
        affiliation: '',
        race: '', // Utrzymane dla kompatybilności
        class_type: '',
        level: 1,
        description: '',
        backstory: ''
    });

    // ⛔️ Usunięto 'searchWiki' - teraz przychodzi z propsów

    const updateFormData = (updates) => {
        setFormData(prev => ({ ...prev, ...updates }));
    };

    // ✅ NOWA funkcja pomocnicza
    const handleFormValueChange = (field, value) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };
    
    const handleUniverseChange = (universe) => {
        updateFormData({ 
            universe,
            species: '',
            race: '',
            homeworld: '',
            affiliation: ''
        });
    };

    const handleSpeciesChange = (value) => {
        updateFormData({ species: value, race: value });
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        
        if (!formData.name?.trim()) {
            alert('Name is required.');
            return;
        }
        if (!formData.species?.trim()) {
            alert('Species is required.');
            return;
        }
        if (!formData.homeworld?.trim()) {
            alert('Homeworld is required.');
            return;
        }
        
        onNext(formData);
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-gray-800 rounded-lg p-8 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
                <div className="flex justify-between items-center mb-6">
                    <h2 className="text-2xl font-bold text-white">Create New Character</h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-white text-2xl">×</button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                    {/* Progress Indicator (bez zmian) */}
                    <div className="flex items-center justify-center mb-6">
                        <div className="flex items-center">
                            <div className="flex items-center"><div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold">1</div><span className="ml-2 text-white font-semibold">Basic Info</span></div>
                            <div className="w-12 h-1 bg-gray-600 mx-2"></div>
                            <div className="flex items-center"><div className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center text-gray-400">2</div><span className="ml-2 text-gray-400">Attributes</span></div>
                            <div className="w-12 h-1 bg-gray-600 mx-2"></div>
                            <div className="flex items-center"><div className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center text-gray-400">3</div><span className="ml-2 text-gray-400">Skills</span></div>
                        </div>
                    </div>

                    {/* Universe Selection (bez zmian) */}
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">Universe *</label>
                        <select
                            value={formData.universe}
                            onChange={(e) => handleUniverseChange(e.target.value)}
                            className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg"
                        >
                            <option value="star_wars">Star Wars</option>
                            <option value="lotr">Lord of the Rings</option>
                        </select>
                    </div>

                    {/* Character Name (bez zmian) */}
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">Character Name *</label>
                        <input
                            type="text"
                            value={formData.name}
                            onChange={(e) => updateFormData({ name: e.target.value })}
                            placeholder="Enter character name"
                            className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg"
                            required
                        />
                    </div>

                    {/* ✅ ZMODYFIKOWANE Pola Autocomplete */}
                    <AutocompleteField
                        label="Species *"
                        value={formData.species}
                        onChange={handleSpeciesChange}
                        // ✅ Używamy funkcji z propsów, przekazując kategorię
                        onSearch={(query) => onSearchWiki(formData.universe, 'species', query)} 
                        placeholder="Search species... (e.g., Human, Twi'lek)"
                        required
                    />
                    <AutocompleteField
                        label="Homeworld *"
                        value={formData.homeworld}
                        onChange={(value) => handleFormValueChange('homeworld', value)}
                         // ✅ Używamy funkcji z propsów, przekazując kategorię
                        onSearch={(query) => onSearchWiki(formData.universe, 'planets', query)}
                        placeholder="Search planet... (e.g., Tatooine)"
                        required
                    />
                    <AutocompleteField
                        label="Affiliation"
                        value={formData.affiliation}
                        onChange={(value) => handleFormValueChange('affiliation', value)}
                         // ✅ Używamy funkcji z propsów, przekazując kategorię
                        onSearch={(query) => onSearchWiki(formData.universe, 'organizations', query)}
                        placeholder="Search organization... (e.g., Jedi Order)"
                    />
                    
                    {/* Reszta formularza */}
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">Class</label>
                        <input
                            type="text"
                            value={formData.class_type}
                            onChange={(e) => updateFormData({ class_type: e.target.value })}
                            placeholder="e.g., Jedi, Smuggler, Bounty Hunter"
                            className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">Level</label>
                        <input
                            type="number"
                            min="1"
                            value={formData.level}
                            onChange={(e) => updateFormData({ level: parseInt(e.target.value) })}
                            className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">Description</label>
                        <textarea
                            value={formData.description}
                            onChange={(e) => updateFormData({ description: e.target.value })}
                            rows="3"
                            placeholder="Brief physical description..."
                            className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">Backstory</label>
                        <textarea
                            value={formData.backstory}
                            onChange={(e) => updateFormData({ backstory: e.target.value })}
                            rows="4"
                            placeholder="Character's history and background..."
                            className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg"
                        />
                    </div>

                    {/* Buttons */}
                    <div className="flex gap-3 pt-4">
                        <button type="button" onClick={onClose} className="flex-1 bg-gray-600 hover:bg-gray-700 px-6 py-3 rounded-lg font-semibold transition">
                            Cancel
                        </button>
                        <button type="submit" className="flex-1 bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg font-semibold transition">
                            Next: Attributes →
                        </button>
                    </div>
                    
                    {/* ⛔️ Usunięto 'Data Stats' */}
                </form>
            </div>
        </div>
    );
}

export default CharacterForm;