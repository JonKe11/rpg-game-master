// frontend/src/components/CharacterDetails.js
import React from 'react';

function CharacterDetails({ character, onClose, onEdit, onDelete, onStartSession }) {
  const renderStarWarsDetails = () => (
    <>
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="space-y-2">
          <DetailRow label="Species" value={character.race} />
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
          <DetailRow label="Homeland" value={character.homeworld} />
          <DetailRow label="Age/Era" value={character.born_era} />
        </div>
        <div className="space-y-2">
          <DetailRow label="Gender" value={character.gender} />
          <DetailRow label="Height" value={character.height} />
          <DetailRow label="Hair Color" value={character.hair_color} />
          <DetailRow label="Eye Color" value={character.eye_color} />
        </div>
      </div>

      {character.skills && character.skills.length > 0 && (
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-gray-300 mb-2">Known As</h3>
          <div className="flex flex-wrap gap-2">
            {character.skills.map((alias, idx) => (
              <span key={idx} className="bg-gray-700 px-3 py-1 rounded-full text-sm">
                {alias}
              </span>
            ))}
          </div>
        </div>
      )}
    </>
  );

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 max-w-3xl w-full mx-4 max-h-screen overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-start mb-6">
          <div>
            <h2 className="text-3xl font-bold text-blue-400 mb-2">
              {character.name}
            </h2>
            <div className="flex items-center gap-3">
              <span className="bg-blue-600 px-3 py-1 rounded text-sm">
                Level {character.level}
              </span>
              <span className="bg-gray-700 px-3 py-1 rounded text-sm capitalize">
                {character.universe.replace('_', ' ')}
              </span>
              {character.class_type && (
                <span className="bg-purple-700 px-3 py-1 rounded text-sm">
                  {character.class_type}
                </span>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-2xl"
          >
            ×
          </button>
        </div>

        {/* Universe-specific details */}
        {character.universe === 'star_wars' && renderStarWarsDetails()}
        {character.universe === 'lotr' && renderLOTRDetails()}

        {/* Affiliations */}
        {character.affiliations && character.affiliations.length > 0 && (
          <div className="mb-4">
            <h3 className="text-lg font-semibold text-gray-300 mb-2">Affiliations</h3>
            <div className="flex flex-wrap gap-2">
              {character.affiliations.map((aff, idx) => (
                <span key={idx} className="bg-blue-700 px-3 py-1 rounded-full text-sm">
                  {aff}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Description */}
        {character.description && (
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-300 mb-2">Description</h3>
            <p className="text-gray-300 bg-gray-700 p-4 rounded-lg whitespace-pre-wrap">
              {character.description}
            </p>
          </div>
        )}

        {/* Metadata */}
        <div className="border-t border-gray-700 pt-4 mb-4">
          <h3 className="text-lg font-semibold text-gray-300 mb-2">Character Info</h3>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <DetailRow label="Character ID" value={`#${character.id}`} />
            {character.created_at && (
              <DetailRow 
                label="Created" 
                value={new Date(character.created_at).toLocaleDateString('en-US')} 
              />
            )}
            {character.updated_at && (
              <DetailRow 
                label="Last Modified" 
                value={new Date(character.updated_at).toLocaleDateString('en-US')} 
              />
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3">
          <button
            onClick={onStartSession}
            className="bg-purple-600 hover:bg-purple-700 px-6 py-3 rounded-lg font-semibold transition duration-200 flex-1"
          >
            🎮 Start Session
          </button>
          <button
            onClick={onEdit}
            className="bg-green-600 hover:bg-green-700 px-6 py-3 rounded-lg font-semibold transition duration-200"
          >
            ✏️ Edit
          </button>
          <button
            onClick={onDelete}
            className="bg-red-600 hover:bg-red-700 px-6 py-3 rounded-lg font-semibold transition duration-200"
          >
            🗑️ Delete
          </button>
        </div>
      </div>
    </div>
  );
}

// Helper component for consistent detail rows
function DetailRow({ label, value }) {
  if (!value) return null;
  
  return (
    <p className="text-sm">
      <span className="text-gray-400">{label}:</span>{' '}
      <span className="text-white">{value}</span>
    </p>
  );
}

export default CharacterDetails;