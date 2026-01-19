// frontend/src/components/CharacterForm.js
import React, { useState } from 'react';
import AutocompleteField from './AutocompleteField'; 

function CharacterForm({ onClose, onNext, onSearchWiki }) {
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

        age: '',
        gender: '',
        eye_color: '',
        skin_color: ''
    });

    const updateFormData = (updates) => {
        setFormData(prev => ({ ...prev, ...updates }));
    };

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

    const handleSubmit = (e) => {
        e.preventDefault();
        const dataToSubmit = {
            ...formData,
   
            race: formData.species || formData.race,
  
            age: formData.age ? parseInt(formData.age) : null
        };
        onNext(dataToSubmit);
    };

    return (
        <div className="flex flex-col h-full">
            <div className="mb-6">
                <h2 className="text-2xl font-bold text-blue-400 mb-2">Basic information</h2>
                <p className="text-gray-400">Craft your character.</p>
            </div>

            <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
                <form id="char-form" onSubmit={handleSubmit} className="space-y-6">
                    
                    {/* --- Sekcja 1: Tożsamość --- */}
                    <div className="bg-gray-700/30 p-4 rounded-lg border border-gray-700">
                        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                            👤 Identity
                        </h3>
                        
                        {/* Name */}
                        <div className="mb-4">
                            <label className="block text-sm font-medium text-gray-300 mb-1">Name *</label>
                            <input
                                type="text"
                                value={formData.name}
                                onChange={(e) => updateFormData({ name: e.target.value })}
                                required
                                placeholder="e.g. Luke Skywalker"
                                className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg focus:ring-2 focus:ring-blue-500 outline-none border border-gray-600 focus:border-transparent transition"
                            />
                        </div>

                        {/* Universe Selection */}
                        <div className="mb-4">
                            <label className="block text-sm font-medium text-gray-300 mb-2">Universe</label>
                            <div className="grid grid-cols-3 gap-2">
                                {['star_wars', 'dnd', 'dune'].map(u => (
                                    <button
                                        key={u}
                                        type="button"
                                        onClick={() => handleUniverseChange(u)}
                                        className={`px-3 py-2 rounded-lg text-sm font-medium capitalize transition border ${
                                            formData.universe === u 
                                                ? 'bg-blue-600 text-white border-blue-500 shadow-lg' 
                                                : 'bg-gray-800 text-gray-400 border-gray-600 hover:bg-gray-700 hover:border-gray-500'
                                        }`}
                                    >
                                        {u.replace('_', ' ')}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* --- Sekcja 2: Cechy Fizyczne --- */}
                    <div className="bg-gray-700/30 p-4 rounded-lg border border-gray-700">
                        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                            🧬 Physical Traits
                        </h3>
                        <div className="grid grid-cols-2 gap-4">
                            {/* Age */}
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">Age</label>
                                <input
                                    type="number"
                                    min="1"
                                    max="999"
                                    value={formData.age}
                                    onChange={(e) => updateFormData({ age: e.target.value })}
                                    placeholder="e.g. 25"
                                    className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg focus:ring-2 focus:ring-blue-500 outline-none border border-gray-600"
                                />
                            </div>

                            {/* Gender */}
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">Gender</label>
                                <select
                                    value={formData.gender}
                                    onChange={(e) => updateFormData({ gender: e.target.value })}
                                    className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg focus:ring-2 focus:ring-blue-500 outline-none border border-gray-600"
                                >
                                    <option value="">Select...</option>
                                    <option value="Male">Male</option>
                                    <option value="Female">Female</option>
                                    <option value="Non-binary">Non-binary</option>
                                    <option value="Droid">Droid / Other</option>
                                </select>
                            </div>

                            {/* Eye Color */}
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">Eye Color</label>
                                <input
                                    type="text"
                                    value={formData.eye_color}
                                    onChange={(e) => updateFormData({ eye_color: e.target.value })}
                                    placeholder="e.g. Blue"
                                    className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg focus:ring-2 focus:ring-blue-500 outline-none border border-gray-600"
                                />
                            </div>

                            {/* Skin Color */}
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">Skin Color</label>
                                <input
                                    type="text"
                                    value={formData.skin_color}
                                    onChange={(e) => updateFormData({ skin_color: e.target.value })}
                                    placeholder="e.g. Fair, Green"
                                    className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg focus:ring-2 focus:ring-blue-500 outline-none border border-gray-600"
                                />
                            </div>
                        </div>
                    </div>

                    {/* --- Sekcja 3: Tło i Profesja (Wiki Integration) --- */}
                    <div className="bg-gray-700/30 p-4 rounded-lg border border-gray-700">
                        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                            📜 Background
                        </h3>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <AutocompleteField
                                label={formData.universe === 'star_wars' ? "Species *" : "Race *"}
                                value={formData.universe === 'star_wars' ? formData.species : formData.race}
                                onChange={(val) => handleFormValueChange(formData.universe === 'star_wars' ? 'species' : 'race', val)}
                                onSearch={(q) => onSearchWiki(formData.universe, 'species', q)}
                                placeholder="e.g. Twi'lek"
                                required
                            />

                            <AutocompleteField
                                label="Class / Profession *"
                                value={formData.class_type}
                                onChange={(val) => handleFormValueChange('class_type', val)}
                                onSearch={(q) => onSearchWiki(formData.universe, 'classes', q)}
                                placeholder="e.g. Smuggler"
                                required
                            />

                            <AutocompleteField
                                label="Homeworld / Origin"
                                value={formData.homeworld}
                                onChange={(val) => handleFormValueChange('homeworld', val)}
                                onSearch={(q) => onSearchWiki(formData.universe, 'planets', q)}
                                placeholder="e.g. Tatooine"
                            />

                            <AutocompleteField
                                label="Affiliation"
                                value={formData.affiliation}
                                onChange={(val) => handleFormValueChange('affiliation', val)}
                                onSearch={(q) => onSearchWiki(formData.universe, 'organizations', q)}
                                placeholder="e.g. Rebel Alliance"
                            />
                        </div>
                    </div>

                    {/* --- Sekcja 4: Detale --- */}
                    <div className="grid grid-cols-4 gap-4">
                        <div className="col-span-1">
                            <label className="block text-sm font-medium text-gray-300 mb-1">Level</label>
                            <input
                                type="number"
                                min="1"
                                max="20"
                                value={formData.level}
                                onChange={(e) => updateFormData({ level: parseInt(e.target.value) || 1 })}
                                className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-center border border-gray-600"
                            />
                        </div>
                        <div className="col-span-3">
                            <label className="block text-sm font-medium text-gray-300 mb-1">Short Description</label>
                            <input
                                type="text"
                                value={formData.description}
                                onChange={(e) => updateFormData({ description: e.target.value })}
                                placeholder="A brief summary..."
                                className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg focus:ring-2 focus:ring-blue-500 outline-none border border-gray-600"
                            />
                        </div>
                    </div>
                </form>
            </div>

            {/* Buttons */}
            <div className="flex gap-3 pt-4 mt-auto border-t border-gray-700">
                <button type="button" onClick={onClose} className="flex-1 bg-gray-600 hover:bg-gray-700 px-6 py-3 rounded-lg font-semibold transition text-white">
                    Cancel
                </button>
                <button 
                    type="submit" 
                    form="char-form"
                    className="flex-1 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 px-6 py-3 rounded-lg font-semibold transition text-white shadow-lg"
                >
                    Next: Backstory →
                </button>
            </div>
        </div>
    );
}

export default CharacterForm;