import React, { useState } from 'react';

const ATTRIBUTES = [
  { key: 'strength', name: 'Strength', description: 'Physical power, melee damage' },
  { key: 'dexterity', name: 'Dexterity', description: 'Agility, ranged accuracy, defense' },
  { key: 'constitution', name: 'Constitution', description: 'Health points, fortitude' },
  { key: 'intelligence', name: 'Intelligence', description: 'Skills, tech abilities' },
  { key: 'wisdom', name: 'Wisdom', description: 'Force powers, awareness' },
  { key: 'charisma', name: 'Charisma', description: 'Persuasion, leadership' }
];

function AttributeAllocation({ characterData, onBack, onNext }) {
  const TOTAL_POINTS = 30;
  const MIN_VALUE = 8;
  const MAX_VALUE = 18;
  
  const [attributes, setAttributes] = useState({
    strength: 10,
    dexterity: 10,
    constitution: 10,
    intelligence: 10,
    wisdom: 10,
    charisma: 10
  });
  
  const getUsedPoints = () => {
    return Object.values(attributes).reduce((sum, val) => sum + (val - 8), 0);
  };
  
  const getRemainingPoints = () => {
    return TOTAL_POINTS - getUsedPoints();
  };
  
  const handleIncrease = (attr) => {
    if (attributes[attr] < MAX_VALUE && getRemainingPoints() > 0) {
      setAttributes({...attributes, [attr]: attributes[attr] + 1});
    }
  };
  
  const handleDecrease = (attr) => {
    if (attributes[attr] > MIN_VALUE) {
      setAttributes({...attributes, [attr]: attributes[attr] - 1});
    }
  };
  
  const getModifier = (value) => {
    return Math.floor((value - 10) / 2);
  };
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 max-w-2xl w-full mx-4 max-h-screen overflow-y-auto">
        <h2 className="text-2xl font-bold text-blue-400 mb-2">
          Attribute Allocation
        </h2>
        <p className="text-gray-400 mb-2">Step 2 of 3: Distribute your attribute points</p>
        <p className="text-sm text-gray-500 mb-6">
          Distribute {TOTAL_POINTS} points among your attributes (8-18 range)
        </p>
        
        <div className="bg-blue-900 border border-blue-700 p-4 rounded-lg mb-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-200">
              {getRemainingPoints()}
            </div>
            <div className="text-sm text-blue-300">Points Remaining</div>
          </div>
        </div>
        
        <div className="space-y-4 mb-6">
          {ATTRIBUTES.map(attr => (
            <div key={attr.key} className="bg-gray-700 p-4 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <div className="flex-1">
                  <h3 className="font-semibold text-lg">{attr.name}</h3>
                  <p className="text-sm text-gray-400">{attr.description}</p>
                </div>
                <div className="flex items-center gap-4">
                  <button
                    onClick={() => handleDecrease(attr.key)}
                    disabled={attributes[attr.key] <= MIN_VALUE}
                    className="w-8 h-8 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded font-bold"
                  >
                    −
                  </button>
                  <div className="text-center min-w-[80px]">
                    <div className="text-2xl font-bold">{attributes[attr.key]}</div>
                    <div className="text-xs text-gray-400">
                      {getModifier(attributes[attr.key]) >= 0 ? '+' : ''}
                      {getModifier(attributes[attr.key])}
                    </div>
                  </div>
                  <button
                    onClick={() => handleIncrease(attr.key)}
                    disabled={attributes[attr.key] >= MAX_VALUE || getRemainingPoints() === 0}
                    className="w-8 h-8 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded font-bold"
                  >
                    +
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
        
        <div className="flex gap-3">
          <button
            onClick={onBack}
            className="bg-gray-600 hover:bg-gray-700 px-6 py-3 rounded-lg font-semibold"
          >
            Back
          </button>
          <button
            onClick={() => onNext(attributes)}
            disabled={getRemainingPoints() !== 0}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed px-6 py-3 rounded-lg font-semibold flex-1"
          >
            {getRemainingPoints() === 0 ? 'Next: Skills' : `Spend ${getRemainingPoints()} more points`}
          </button>
        </div>
      </div>
    </div>
  );
}

export default AttributeAllocation;