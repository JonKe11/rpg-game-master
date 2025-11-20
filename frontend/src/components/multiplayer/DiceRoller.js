import React from 'react';
import api from '../../api/axiosConfig';

const DIES = [4, 6, 8, 10, 12, 20, 100];

function DiceRoller({ campaignId, characterId }) {
    const rollDice = async (sides) => {
        try {
            console.log(`🎲 Rolling d${sides}...`); // Log dla debugowania
            await api.post(`/multiplayer/campaigns/${campaignId}/messages`, {
                message_type: 'dice_roll', // Ważne: to musi być dokładnie ten string
                content: '', // Puste, bo backend to wypełni
                character_id: characterId,
                // Parametry dla backendu:
                dice_type: sides,
                dice_count: 1,
                modifier: 0 
            });
        } catch (error) {
            console.error('Roll failed:', error);
            alert('Failed to roll dice. Check console.');
        }
    };

    return (
        <div className="bg-gray-800 p-2 rounded-lg flex gap-2 overflow-x-auto mb-2 border border-gray-700">
            <span className="text-gray-400 text-sm self-center mr-2">Roll:</span>
            {DIES.map(sides => (
                <button
                    key={sides}
                    onClick={() => rollDice(sides)}
                    className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-1 px-3 rounded text-sm transition whitespace-nowrap shadow-md"
                >
                    d{sides}
                </button>
            ))}
        </div>
    );
}

export default DiceRoller;