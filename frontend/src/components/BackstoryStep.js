// frontend/src/components/BackstoryStep.js
import React, { useState } from 'react';
import api from '../api/axiosConfig';

function BackstoryStep({ characterData, onBack, onNext }) {
  const [mode, setMode] = useState('choice'); // 'choice', 'write', 'ai'
  const [backstory, setBackstory] = useState(characterData.backstory || '');
  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerate = async () => {
    setIsGenerating(true);
    setMode('ai');
    try {
      // Wewnątrz handleGenerate w BackstoryStep.js
const response = await api.post('/characters/generate-bio', {
  name: characterData.name,
  race: characterData.race,
  class_type: characterData.class_type,
  universe: characterData.universe,
  // ✅ Upewnij się, że te pola są wysyłane:
  homeworld: characterData.homeworld,
  affiliation: characterData.affiliation
});
      
      setBackstory(response.data.biography);
    } catch (error) {
      console.error("Bio Gen Error:", error);
      alert("Nie udało się wygenerować biografii. Spróbuj ponownie.");
      setMode('choice');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleComplete = () => {
    onNext({ backstory });
  };

  return (
    <div className="flex flex-col h-full">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-blue-400 mb-2">Character's history</h2>
        <p className="text-gray-400">
          Every hero has a backstory, how do you want to create yours?
        </p>
      </div>

      {/* STEP 1: Wybór trybu */}
      {mode === 'choice' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 flex-1">
          <button
            onClick={() => setMode('write')}
            className="bg-gray-800 hover:bg-gray-700 border-2 border-gray-600 hover:border-blue-500 rounded-xl p-8 flex flex-col items-center justify-center transition group"
          >
            <span className="text-4xl mb-4">✍️</span>
            <h3 className="text-xl font-bold text-white mb-2">Write it yourself</h3>
            <p className="text-gray-400 text-center text-sm">
              Do you have an idea? Write it yourself!
            </p>
          </button>

          <button
            onClick={handleGenerate}
            className="bg-gray-800 hover:bg-gray-700 border-2 border-gray-600 hover:border-purple-500 rounded-xl p-8 flex flex-col items-center justify-center transition group relative overflow-hidden"
          >
            <div className="absolute inset-0 bg-purple-600 opacity-0 group-hover:opacity-10 transition duration-500"></div>
            <span className="text-4xl mb-4">🤖</span>
            <h3 className="text-xl font-bold text-white mb-2">Ask AI for help</h3>
            <p className="text-gray-400 text-center text-sm">
              Use knowledge about {characterData.universe}, to create a unique backstory.
            </p>
          </button>
        </div>
      )}

      {/* STEP 2: Pisanie / Edycja */}
      {(mode === 'write' || mode === 'ai') && (
        <div className="flex-1 flex flex-col">
          {isGenerating ? (
            <div className="flex-1 flex flex-col items-center justify-center animate-pulse">
              <span className="text-4xl mb-4">🔮</span>
              <h3 className="text-xl text-purple-400">Consulting archives...</h3>
              <p className="text-gray-500 mt-2">AI is analizing race {characterData.race} and profession {characterData.class_type}</p>
            </div>
          ) : (
            <>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                {mode === 'ai' ? 'AI Generated Backstory (Can be edited)' : 'Your story:'}
              </label>
              <textarea
                value={backstory}
                onChange={(e) => setBackstory(e.target.value)}
                className="flex-1 w-full p-4 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none custom-scrollbar leading-relaxed"
              />
              
              {mode === 'ai' && (
                <div className="mt-2 flex justify-end">
                   <button 
                     onClick={handleGenerate}
                     className="text-sm text-purple-400 hover:text-purple-300 flex items-center gap-1"
                   >
                     🔄 Generate a different version
                   </button>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* Nawigacja */}
      <div className="flex gap-3 pt-6 mt-auto border-t border-gray-700">
        <button
          onClick={mode === 'choice' ? onBack : () => setMode('choice')}
          disabled={isGenerating}
          className="flex-1 bg-gray-600 hover:bg-gray-700 px-6 py-3 rounded-lg font-semibold transition text-white"
        >
          ← Back
        </button>
        
        <button
          onClick={handleComplete}
          disabled={isGenerating || (mode !== 'choice' && !backstory.trim())}
          className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed px-6 py-3 rounded-lg font-semibold transition text-white"
        >
          Next: Statistics →
        </button>
      </div>
    </div>
  );
}

export default BackstoryStep;