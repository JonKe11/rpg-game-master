// frontend/src/components/CharacterCreationWizard.js
// ✅ WERSJA 2.0 - Dodano logikę wyszukiwania i przekazano ją do CharacterForm

import React, { useState } from 'react';
import CharacterForm from './CharacterForm';
import AttributeAllocation from './AttributeAllocation';
import SkillAllocation from './SkillAllocation';
import api from '../api/axiosConfig'; // Potrzebne do wyszukiwania

function CharacterCreationWizard({ onClose, onSuccess }) {
  const [step, setStep] = useState(1);
  const [characterData, setCharacterData] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const handleBasicInfoComplete = (data) => {
    setCharacterData(data);
    setStep(2);
  };
  
  const handleAttributesComplete = (attributes) => {
    setCharacterData({...characterData, ...attributes});
    setStep(3);
  };
  
  const handleSkillsComplete = async (skills) => {
    const finalData = {...characterData, ...skills};
    setIsSubmitting(true);
    
    try {
      await api.post('/characters/', finalData);
      onSuccess();
      onClose();
    } catch (error) {
      console.error('Error creating character:', error);
      alert('Failed to create character. Check console for details.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // ✅ NOWA FUNKCJA WYSZUKIWANIA
  // Ta funkcja zostanie przekazana do CharacterForm, a następnie do AutocompleteField
  const searchWiki = async (universe, category, query) => {
    if (!query || query.length < 2) {
      return [];
    }
    try {
      const response = await api.get('/wiki/search', {
        params: {
          universe: universe,
          category: category,
          q: query,
          limit: 10 // Wystarczy 10 sugestii
        }
      });
      return response.data.items.map(item => item.name);
    } catch (error) {
      console.error(`Error searching ${category}:`, error);
      return [];
    }
  };
  
  return (
    <>
      {step === 1 && (
        <CharacterForm 
          onClose={onClose}
          onNext={handleBasicInfoComplete}
          // ✅ Przekazujemy funkcję wyszukiwania do CharacterForm
          onSearchWiki={searchWiki} 
        />
      )}
      {step === 2 && (
        <AttributeAllocation
          characterData={characterData}
          onBack={() => setStep(1)}
          onNext={handleAttributesComplete}
        />
      )}
      {step === 3 && (
        <SkillAllocation
          characterData={characterData}
          onBack={() => setStep(2)}
          onComplete={handleSkillsComplete}
          isSubmitting={isSubmitting}
        />
      )}
    </>
  );
}

export default CharacterCreationWizard;