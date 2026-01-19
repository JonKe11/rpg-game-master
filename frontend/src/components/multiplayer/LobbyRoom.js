// frontend/src/components/multiplayer/LobbyRoom.js
import React, { useState, useEffect } from 'react';
import api from '../../api/axiosConfig';

function LobbyRoom({ campaign, character, onStart, onBack }) {
  const [campaignData, setCampaignData] = useState({ ...campaign, participants: campaign.participants || [] });
  const [isCreator, setIsCreator] = useState(false);
  const [currentUserId, setCurrentUserId] = useState(null);
  const [myReadyStatus, setMyReadyStatus] = useState(false);

  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (userData) {
      const user = JSON.parse(userData);
      setCurrentUserId(user.id);
      setIsCreator(campaign.creator_id === user.id);
    }

    const interval = setInterval(refreshCampaign, 2000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (currentUserId && campaignData.participants) {
      const me = campaignData.participants.find(p => p.user_id === currentUserId);
      if (me) {
        setMyReadyStatus(me.ready || false);
      }
    }
  }, [campaignData, currentUserId]);

  const refreshCampaign = async () => {
    try {
      const response = await api.get(`/multiplayer/campaigns/${campaign.id}`);
      const freshData = { ...response.data, participants: response.data.participants || [] };
      setCampaignData(freshData);
      
      if (freshData.status === 'active') {
        console.log('🎮 Campaign is active! Starting game...');
        setTimeout(() => {
          onStart(freshData);
        }, 500);
      }
    } catch (error) {
      console.error('Error refreshing campaign:', error);
    }
  };

  const handleAssignGM = async (userId) => {
    try {
      await api.post(`/multiplayer/campaigns/${campaign.id}/assign-gm`, null, { params: { user_id: userId } });
      await refreshCampaign();
    } catch (error) {
      console.error('Error assigning GM:', error);
      alert(error.response?.data?.detail || 'Failed to assign GM');
    }
  };

  const handleToggleReady = async () => {
    try {
      const response = await api.post(`/multiplayer/campaigns/${campaign.id}/toggle-ready`);
      setMyReadyStatus(response.data.ready);
      await refreshCampaign();
    } catch (error) {
      console.error('Error toggling ready:', error);
      alert(error.response?.data?.detail || 'Failed to toggle ready');
    }
  };

  const handleStart = async () => {
    try {
      console.log('🎲 Starting/Resuming campaign...');
      await api.post(`/multiplayer/campaigns/${campaign.id}/start`);
      console.log('✅ Campaign start/resume triggered!');
      await refreshCampaign();
    } catch (error) {
      console.error('Error starting campaign:', error);
      alert(error.response?.data?.detail || 'Failed to start campaign');
    }
  };

  const isGM = campaignData.game_master_id === currentUserId;
  const isPaused = campaignData.status === 'paused';
  const players = (campaignData.participants || []).filter(p => p.role !== 'gm');
  
  
  const canStart = () => {
    if (!campaignData.game_master_id) return false;
    if (campaignData.status === 'lobby') {
      const allReady = players.length > 0 ? players.every(p => p.ready) : false;
      return allReady;
    }
    if (campaignData.status === 'paused') {
      return true; 
    }
    return false;
  };
  
  const getStartButtonText = () => {
    if (isPaused) return "🚀 Resume Campaign";
    if (!campaignData.game_master_id) return "Need GM";
    if (players.length === 0) return "Need players";
    if (players.every(p => p.ready)) return "🎲 Start Campaign";
    return "⧗ Waiting for players...";
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h3 className="text-2xl font-bold text-white">{campaignData.title}</h3>
          <p className="text-gray-400">
            {campaignData.status === 'lobby' ? 'Lobby - Waiting for players...' : 
             campaignData.status === 'paused' ? 'Paused - Ready to resume' : 'Loading...'}
          </p>
        </div>
        <button onClick={onBack} className="bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded-lg transition">
          ← Back
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Players List */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h4 className="text-xl font-bold text-white mb-4">
            Players ({(campaignData.participants || []).length}/{campaignData.max_players})
          </h4>
          <div className="space-y-3">
            {(campaignData.participants || []).map((participant, index) => (
              <div key={index} className="bg-gray-700 rounded-lg p-4 flex justify-between items-center">
                 <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${
                    participant.role === 'gm' || participant.ready ? 'bg-green-500' : 'bg-gray-500'
                  }`} title={participant.role === 'gm' ? 'Game Master' : participant.ready ? 'Ready' : 'Not ready'} />
                  <div>
                    <p className="text-white font-semibold">
                      {participant.username}
                      {participant.role === 'gm' && ' 👑'}
                    </p>
                    {/* ✅ Poprawka: Wyświetlaj character_name, a nie ID */}
                    <p className="text-gray-400 text-sm">
                      {participant.character_name || `Char ID: ${participant.character_id}`}
                    </p>
                  </div>
                </div>
                {isCreator && participant.role !== 'gm' && !campaignData.game_master_id && campaignData.status === 'lobby' && (
                  <button onClick={() => handleAssignGM(participant.user_id)} className="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-sm transition">
                    Make GM
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Campaign Info */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h4 className="text-xl font-bold text-white mb-4">Campaign Info</h4>
           <div className="space-y-3">
             {/* ... (Reszta info bez zmian) ... */}
           </div>

          {/* Player Action */}
          {!isGM && campaignData.status === 'lobby' && (
            <div className="mt-6 pt-6 border-t border-gray-700">
              <button onClick={handleToggleReady} className={`w-full px-6 py-3 rounded-lg font-bold text-lg transition ${myReadyStatus ? 'bg-green-600 hover:bg-green-700' : 'bg-gray-600 hover:bg-gray-700'}`}>
                {myReadyStatus ? '✓ Ready!' : 'Click when Ready'}
              </button>
            </div>
          )}

          {/* GM Action */}
          {isGM && (campaignData.status === 'lobby' || isPaused) && (
            <div className="mt-6 pt-6 border-t border-gray-700">
              <button
                onClick={handleStart}
                disabled={!canStart()}
                className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed px-6 py-3 rounded-lg font-bold text-lg transition"
              >
                {getStartButtonText()}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default LobbyRoom;