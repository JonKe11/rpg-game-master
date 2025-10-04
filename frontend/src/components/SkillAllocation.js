import React, { useState } from 'react';

const SKILLS = [
  { 
    key: 'skill_computer_use', 
    name: 'Computer Use', 
    description: 'Hack terminals, disable security',
    attribute: 'intelligence'
  },
  { 
    key: 'skill_demolitions', 
    name: 'Demolitions', 
    description: 'Set and disarm mines, explosives',
    attribute: 'intelligence'
  },
  { 
    key: 'skill_stealth', 
    name: 'Stealth', 
    description: 'Move silently, avoid detection',
    attribute: 'dexterity'
  },
  { 
    key: 'skill_awareness', 
    name: 'Awareness', 
    description: 'Spot hidden objects and enemies',
    attribute: 'wisdom'
  },
  { 
    key: 'skill_persuade', 
    name: 'Persuade', 
    description: 'Influence others in conversation',
    attribute: 'charisma'
  },
  { 
    key: 'skill_repair', 
    name: 'Repair', 
    description: 'Fix droids and machinery',
    attribute: 'intelligence'
  },
  { 
    key: 'skill_security', 
    name: 'Security', 
    description: 'Pick locks, disable traps',
    attribute: 'intelligence'
  },
  { 
    key: 'skill_treat_injury', 
    name: 'Treat Injury', 
    description: 'Heal wounds and cure status effects',
    attribute: 'wisdom'
  }
];

function SkillAllocation({ characterData, onBack, onComplete }) {
  const TOTAL_POINTS = 40;
  const MAX_SKILL_VALUE = 20;
  
  const [skills, setSkills] = useState({
    skill_computer_use: 0,
    skill_demolitions: 0,
    skill_stealth: 0,
    skill_awareness: 0,
    skill_persuade: 0,
    skill_repair: 0,
    skill_security: 0,
    skill_treat_injury: 0
  });
  
  const getUsedPoints = () => {
    return Object.values(skills).reduce((sum, val) => sum + val, 0);
  };
  
  const getRemainingPoints = () => {
    return TOTAL_POINTS - getUsedPoints();
  };
  
  const handleIncrease = (skillKey) => {
    if (skills[skillKey] < MAX_SKILL_VALUE && getRemainingPoints() > 0) {
      setSkills({...skills, [skillKey]: skills[skillKey] + 1});
    }
  };
  
  const handleDecrease = (skillKey) => {
    if (skills[skillKey] > 0) {
      setSkills({...skills, [skillKey]: skills[skillKey] - 1});
    }
  };
  
  const getAttributeBonus = (attributeKey) => {
    const attrValue = characterData[attributeKey] || 10;
    return Math.floor((attrValue - 10) / 2);
  };
  
  const getTotalSkillValue = (skillKey, skillObj) => {
    const attributeKey = skillObj.attribute;
    const bonus = getAttributeBonus(attributeKey);
    return skills[skillKey] + bonus;
  };
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
      <div className="bg-gray-800 rounded-lg p-6 max-w-3xl w-full mx-4 my-8">
        <h2 className="text-2xl font-bold text-blue-400 mb-2">
          Skill Allocation
        </h2>
        <p className="text-gray-400 mb-2">Step 3 of 3: Distribute your skill points</p>
        <p className="text-sm text-gray-500 mb-6">
          Distribute {TOTAL_POINTS} points among your skills. Attribute bonuses apply automatically.
        </p>
        
        <div className="bg-blue-900 border border-blue-700 p-4 rounded-lg mb-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-200">
              {getRemainingPoints()}
            </div>
            <div className="text-sm text-blue-300">Skill Points Remaining</div>
          </div>
        </div>
        
        <div className="space-y-3 mb-6 max-h-96 overflow-y-auto pr-2">
          {SKILLS.map(skill => {
            const totalValue = getTotalSkillValue(skill.key, skill);
            const bonus = getAttributeBonus(skill.attribute);
            
            return (
              <div key={skill.key} className="bg-gray-700 p-4 rounded-lg">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <h3 className="font-semibold">{skill.name}</h3>
                    <p className="text-xs text-gray-400">{skill.description}</p>
                    <p className="text-xs text-blue-400 mt-1">
                      Based on {skill.attribute} ({bonus >= 0 ? '+' : ''}{bonus} bonus)
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => handleDecrease(skill.key)}
                      disabled={skills[skill.key] === 0}
                      className="w-8 h-8 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded font-bold text-sm"
                    >
                      −
                    </button>
                    <div className="text-center min-w-[100px]">
                      <div className="text-xl font-bold">
                        {totalValue}
                        <span className="text-sm text-gray-400 ml-1">
                          ({skills[skill.key]}{bonus >= 0 ? '+' : ''}{bonus})
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={() => handleIncrease(skill.key)}
                      disabled={skills[skill.key] >= MAX_SKILL_VALUE || getRemainingPoints() === 0}
                      className="w-8 h-8 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded font-bold text-sm"
                    >
                      +
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
        
        <div className="flex gap-3">
          <button
            onClick={onBack}
            className="bg-gray-600 hover:bg-gray-700 px-6 py-3 rounded-lg font-semibold"
          >
            Back
          </button>
          <button
            onClick={() => onComplete(skills)}
            className="bg-green-600 hover:bg-green-700 px-6 py-3 rounded-lg font-semibold flex-1"
          >
            Create Character
          </button>
        </div>
      </div>
    </div>
  );
}

export default SkillAllocation;