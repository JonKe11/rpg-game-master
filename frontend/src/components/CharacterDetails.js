// frontend/src/components/CharacterDetails.js
import React from 'react';

function CharacterDetails({ character, onClose, onEdit, onDelete, onStartSession }) {
  
  const renderStarWarsDetails = () => (
    <>
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="space-y-2">
          <DetailRow label="Species" value={character.race} />
          {/* ✅ Dodano wyświetlanie Wieku */}
          <DetailRow label="Age" value={character.age} /> 
          <DetailRow label="Homeworld" value={character.homeworld} />
          {character.born_year && character.born_era && (
            <DetailRow 
              label="Born" 
              value={`${character.born_year} ${character.born_era}`} 
            />
          )}
          <DetailRow label="Gender" value={character.gender} />
        </div>
        <div className="space-y-2">
          {character.height && (
            <DetailRow label="Height" value={`${character.height} cm`} />
          )}
          {character.mass && (
            <DetailRow label="Mass" value={`${character.mass} kg`} />
          )}
          <DetailRow label="Skin Color" value={character.skin_color} />
          <DetailRow label="Eye Color" value={character.eye_color} />
          <DetailRow label="Hair Color" value={character.hair_color} />
        </div>
      </div>

      {character.cybernetics && character.cybernetics.length > 0 && (
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-gray-300 mb-2">Cybernetics</h3>
          <div className="flex flex-wrap gap-2">
            {character.cybernetics.map((item, idx) => (
              <span key={idx} className="bg-gray-700 px-3 py-1 rounded-full text-sm">
                {item}
              </span>
            ))}
          </div>
        </div>
      )}
    </>
  );

  const renderLOTRDetails = () => (
    <>
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="space-y-2">
          <DetailRow label="Race" value={character.race} />
          <DetailRow label="Age" value={character.age} />
          <DetailRow label="Homeland" value={character.homeworld} />
          <DetailRow label="Era" value={character.born_era} />
        </div>
        <div className="space-y-2">
          <DetailRow label="Gender" value={character.gender} />
          <DetailRow label="Height" value={character.height} />
          <DetailRow label="Hair Color" value={character.hair_color} />
          <DetailRow label="Eye Color" value={character.eye_color} />
        </div>
      </div>
    </>
  );

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg p-6 max-w-3xl w-full mx-4 max-h-[90vh] overflow-y-auto custom-scrollbar shadow-2xl border border-gray-700">
        
        {/* Header */}
        <div className="flex justify-between items-start mb-6 border-b border-gray-700 pb-4">
          <div>
            <h2 className="text-3xl font-bold text-white mb-2">
              {character.name}
            </h2>
            <div className="flex items-center gap-3">
              <span className="bg-blue-600 px-3 py-1 rounded text-sm font-bold text-white shadow">
                Level {character.level}
              </span>
              <span className="bg-gray-700 px-3 py-1 rounded text-sm capitalize text-gray-300 border border-gray-600">
                {character.universe.replace('_', ' ')}
              </span>
              {character.class_type && (
                <span className="bg-purple-600/50 px-3 py-1 rounded text-sm text-purple-200 border border-purple-500/50">
                  {character.class_type}
                </span>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-3xl leading-none transition"
          >
            ×
          </button>
        </div>

        {/* Universe-specific details */}
        <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-700 mb-6">
            {character.universe === 'star_wars' && renderStarWarsDetails()}
            {character.universe === 'lotr' && renderLOTRDetails()}
            {/* Fallback dla innych uniwersów */}
            {!['star_wars', 'lotr'].includes(character.universe) && (
                 <div className="grid grid-cols-2 gap-4">
                    <DetailRow label="Race" value={character.race} />
                    <DetailRow label="Class" value={character.class_type} />
                    <DetailRow label="Age" value={character.age} />
                    <DetailRow label="Gender" value={character.gender} />
                 </div>
            )}
        </div>

        {/* Affiliations */}
        {character.affiliations && character.affiliations.length > 0 && (
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-300 mb-2">Affiliations</h3>
            <div className="flex flex-wrap gap-2">
              {character.affiliations.map((aff, idx) => (
                <span key={idx} className="bg-blue-900/50 text-blue-200 border border-blue-700 px-3 py-1 rounded-full text-sm">
                  {aff}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* ✅ SEKCJA BIOGRAFII (AI Generated) */}
        {character.backstory && (
          <div className="mb-6">
            <h3 className="text-xl font-bold text-blue-400 mb-3 flex items-center gap-2">
              📜 Biography 
              <span className="text-[10px] uppercase bg-blue-900 text-blue-200 px-2 py-0.5 rounded border border-blue-700 tracking-wider">
                AI Generated
              </span>
            </h3>
            <div className="text-gray-300 bg-gray-900/50 p-5 rounded-lg whitespace-pre-wrap border-l-4 border-blue-500 italic shadow-inner leading-relaxed">
              {character.backstory}
            </div>
          </div>
        )}

        {/* Description (Manual) */}
        {character.description && (
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-300 mb-2">Short Description</h3>
            <p className="text-gray-400 bg-gray-700/30 p-4 rounded-lg whitespace-pre-wrap border border-gray-700">
              {character.description}
            </p>
          </div>
        )}

        {/* Metadata */}
        <div className="border-t border-gray-700 pt-4 mb-6">
          <div className="grid grid-cols-2 gap-2 text-xs text-gray-500">
            <DetailRow label="Character ID" value={`#${character.id}`} />
            {character.created_at && (
              <DetailRow 
                label="Created" 
                value={new Date(character.created_at).toLocaleDateString('en-US')} 
              />
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3 pt-2">
          <button
            onClick={onStartSession}
            className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white px-6 py-3 rounded-lg font-bold transition duration-200 flex-1 shadow-lg"
          >
            🎮 Start Session
          </button>
          
          <button
            onClick={onDelete}
            className="bg-red-900/50 hover:bg-red-800/80 text-red-200 border border-red-800 px-6 py-3 rounded-lg font-semibold transition duration-200"
          >
            🗑️ Delete
          </button>
        </div>
      </div>
    </div>
  );
}


function DetailRow({ label, value }) {
  if (!value) return null;
  
  return (
    <p className="text-sm flex justify-between border-b border-gray-700/50 pb-1 last:border-0">
      <span className="text-gray-400">{label}:</span>{' '}
      <span className="text-white font-medium text-right ml-4">{value}</span>
    </p>
  );
}

export default CharacterDetails;