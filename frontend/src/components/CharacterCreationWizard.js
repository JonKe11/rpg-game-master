import React, { useState } from 'react';
import CharacterForm from './CharacterForm';
import AttributeAllocation from './AttributeAllocation';
import SkillAllocation from './SkillAllocation';
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  }
});

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
  
  return (
    <>
      {step === 1 && (
        <CharacterForm 
          onClose={onClose}
          onNext={handleBasicInfoComplete}
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
        />
      )}
    </>
  );
}

export default CharacterCreationWizard;