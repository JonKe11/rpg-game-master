// frontend/src/components/multiplayer/MultiplayerLobby.js
import React, { useState } from 'react';
import CampaignList from './CampaignList';
import CreateCampaign from './CreateCampaign';
import LobbyRoom from './LobbyRoom';
import MultiplayerSession from './MultiplayerSession';

function MultiplayerLobby({ character, onClose }) {
  const [view, setView] = useState('list');
  const [selectedCampaign, setSelectedCampaign] = useState(null);

  const handleCreateCampaign = () => {
    setView('create');
  };

  const handleCampaignCreated = (campaign) => {
    setSelectedCampaign(campaign);
    setView('lobby');
  };

  const handleJoinCampaign = (campaign) => {
    setSelectedCampaign(campaign);
    setView('lobby');
  };


  const handleCampaignStarted = (freshCampaignData) => {
    console.log('🎮 Starting session with fresh data:', freshCampaignData);
    
  
    setSelectedCampaign(freshCampaignData);
    setView('session');
  };

  const handleBackToList = () => {
    setView('list');
    setSelectedCampaign(null);
  };

  return (
    <div className="fixed inset-0 bg-gray-900 z-50">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 p-4">
        <div className="container mx-auto flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold text-blue-400">
              👥 Multiplayer Mode
            </h2>
            <p className="text-gray-400 text-sm">
              Playing as: {character.name}
            </p>
          </div>
          <button
            onClick={onClose}
            className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg font-semibold transition"
          >
            Close
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="container mx-auto p-4">
        {view === 'list' && (
          <CampaignList 
            character={character}
            onCreateNew={handleCreateCampaign}
            onJoinCampaign={handleJoinCampaign}
          />
        )}

        {view === 'create' && (
          <CreateCampaign 
            character={character}
            onCampaignCreated={handleCampaignCreated}
            onCancel={handleBackToList}
          />
        )}

        {view === 'lobby' && selectedCampaign && (
          <LobbyRoom 
            campaign={selectedCampaign}
            character={character}
            onStart={handleCampaignStarted}  
            onBack={handleBackToList}
          />
        )}

        {view === 'session' && selectedCampaign && (
          <MultiplayerSession 
            campaign={selectedCampaign}  
            character={character}
            onEnd={handleBackToList}
          />
        )}
      </div>
    </div>
  );
}

export default MultiplayerLobby;