// frontend/src/components/CharacterCreationWizard.js
import React, { useState } from 'react';
import CharacterForm from './CharacterForm';
import BackstoryStep from './BackstoryStep';
import AttributeAllocation from './AttributeAllocation';
import SkillAllocation from './SkillAllocation';
import api from '../api/axiosConfig';

function CharacterCreationWizard({ onClose, onSuccess }) {
  const [step, setStep] = useState(1);
  const [characterData, setCharacterData] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  

  const handleBasicInfoComplete = (data) => {
    setCharacterData(prev => ({ ...prev, ...data }));
    setStep(2);
  };
  

  const handleBackstoryComplete = (data) => {
    setCharacterData(prev => ({ ...prev, ...data }));
    setStep(3);
  };


  const handleAttributesComplete = (attributes) => {
    setCharacterData(prev => ({ ...prev, ...attributes }));
    setStep(4);
  };
  

  const handleSkillsComplete = async (skills) => {
    const finalData = { ...characterData, ...skills };
    setIsSubmitting(true);
    
    try {
      console.log("Saving character:", finalData);
      await api.post('/characters/', finalData);
      onSuccess();
      onClose();
    } catch (error) {
      console.error('Error creating character:', error);
      alert('Failed to create character.');
    } finally {
      setIsSubmitting(false);
    }
  };


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
          limit: 10
        }
      });
      return response.data.items ? response.data.items.map(item => item.name) : [];
    } catch (error) {
      console.error(`Error searching ${category}:`, error);
      return [];
    }
  };
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-xl w-full max-w-4xl h-[85vh] flex flex-col shadow-2xl border border-gray-700 overflow-hidden">
        
        {/* Progress Bar */}
        <div className="bg-gray-900 h-2 w-full flex">
            <div className={`h-full bg-blue-600 transition-all duration-500 ${step >= 1 ? 'w-1/4' : 'w-0'}`}></div>
            <div className={`h-full bg-purple-600 transition-all duration-500 ${step >= 2 ? 'w-1/4' : 'w-0'}`}></div>
            <div className={`h-full bg-green-600 transition-all duration-500 ${step >= 3 ? 'w-1/4' : 'w-0'}`}></div>
            <div className={`h-full bg-yellow-600 transition-all duration-500 ${step >= 4 ? 'w-1/4' : 'w-0'}`}></div>
        </div>

        <div className="flex-1 p-8 overflow-hidden">
            {step === 1 && (
                <CharacterForm 
                onClose={onClose}
                onNext={handleBasicInfoComplete}
                onSearchWiki={searchWiki} 
                />
            )}
            
            {step === 2 && (
                <BackstoryStep
                characterData={characterData}
                onBack={() => setStep(1)}
                onNext={handleBackstoryComplete}
                />
            )}

            {step === 3 && (
                <AttributeAllocation
                characterData={characterData}
                onBack={() => setStep(2)}
                onNext={handleAttributesComplete}
                />
            )}
            
            {step === 4 && (
                <SkillAllocation
                characterData={characterData}
                onBack={() => setStep(3)}
         
                onComplete={handleSkillsComplete}
                isSubmitting={isSubmitting}
                />
            )}
        </div>
      </div>
    </div>
  );
}

export default CharacterCreationWizard;