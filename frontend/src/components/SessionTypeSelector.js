// frontend/src/components/SessionTypeSelector.js
import React, { useState } from 'react';

function SessionTypeSelector({ character, onSelect, onCancel }) {
  const [sessionType, setSessionType] = useState(null);
  const [campaignLength, setCampaignLength] = useState('medium');

  const handleContinue = () => {
    if (sessionType === 'campaign') {
      onSelect({ type: 'campaign', length: campaignLength });
    } else {
      onSelect({ type: 'basic' });
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-8 max-w-2xl w-full mx-4">
        <h2 className="text-3xl font-bold text-blue-400 mb-4">
          Start Game Session
        </h2>
        <p className="text-gray-400 mb-6">
          Choose how you want to play with <span className="text-white font-semibold">{character.name}</span>
        </p>

        {/* Session Type Selection */}
        <div className="space-y-4 mb-6">
          {/* Campaign Option */}
          <div
            onClick={() => setSessionType('campaign')}
            className={`border-2 rounded-lg p-6 cursor-pointer transition ${
              sessionType === 'campaign'
                ? 'border-blue-500 bg-blue-900 bg-opacity-30'
                : 'border-gray-700 hover:border-gray-600'
            }`}
          >
            <div className="flex items-start gap-4">
              <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center mt-1 ${
                sessionType === 'campaign' ? 'border-blue-500' : 'border-gray-600'
              }`}>
                {sessionType === 'campaign' && (
                  <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                )}
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-bold text-white mb-2">
                  📖 Story Campaign (Recommended)
                </h3>
                <p className="text-gray-400 text-sm mb-3">
                  AI plans a complete story arc with beginning, middle, and end. 
                  Features story beats, character development, and meaningful progression.
                </p>
                <div className="bg-gray-900 bg-opacity-50 p-3 rounded">
                  <p className="text-xs text-gray-300 mb-2">✨ Features:</p>
                  <ul className="text-xs text-gray-400 space-y-1">
                    <li>• AI-planned campaign structure (3-act story)</li>
                    <li>• Story beats tracking & progression</li>
                    <li>• Canon wiki knowledge integration</li>
                    <li>• Meaningful choices & consequences</li>
                    <li>• Dynamic pacing & tension</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          {/* Basic Option */}
          <div
            onClick={() => setSessionType('basic')}
            className={`border-2 rounded-lg p-6 cursor-pointer transition ${
              sessionType === 'basic'
                ? 'border-blue-500 bg-blue-900 bg-opacity-30'
                : 'border-gray-700 hover:border-gray-600'
            }`}
          >
            <div className="flex items-start gap-4">
              <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center mt-1 ${
                sessionType === 'basic' ? 'border-blue-500' : 'border-gray-600'
              }`}>
                {sessionType === 'basic' && (
                  <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                )}
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-bold text-white mb-2">
                  🎲 Quick Session
                </h3>
                <p className="text-gray-400 text-sm">
                  Freeform session without structured campaign. Perfect for quick adventures 
                  or testing characters.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Campaign Length Selection */}
        {sessionType === 'campaign' && (
          <div className="mb-6 p-4 bg-gray-700 rounded-lg">
            <h4 className="font-semibold text-white mb-3">Campaign Length</h4>
            <div className="grid grid-cols-3 gap-3">
              {[
                { value: 'short', label: 'Short', turns: '15-20 turns', time: '~30 min' },
                { value: 'medium', label: 'Medium', turns: '30-40 turns', time: '~1 hour' },
                { value: 'long', label: 'Long', turns: '50-70 turns', time: '~2 hours' }
              ].map(option => (
                <button
                  key={option.value}
                  onClick={() => setCampaignLength(option.value)}
                  className={`p-4 rounded-lg border-2 transition ${
                    campaignLength === option.value
                      ? 'border-blue-500 bg-blue-900 bg-opacity-30'
                      : 'border-gray-600 hover:border-gray-500'
                  }`}
                >
                  <div className="font-bold text-white mb-1">{option.label}</div>
                  <div className="text-xs text-gray-400">{option.turns}</div>
                  <div className="text-xs text-gray-500">{option.time}</div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3">
          <button
            onClick={onCancel}
            className="bg-gray-600 hover:bg-gray-700 px-6 py-3 rounded-lg font-semibold transition"
          >
            Cancel
          </button>
          <button
            onClick={handleContinue}
            disabled={!sessionType}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed px-6 py-3 rounded-lg font-semibold transition flex-1"
          >
            {sessionType === 'campaign' ? '📖 Start Campaign' : '🎲 Start Session'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default SessionTypeSelector;