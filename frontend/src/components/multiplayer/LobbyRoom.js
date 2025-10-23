// frontend/src/components/multiplayer/LobbyRoom.js
import React, { useState, useEffect } from 'react';
import api from '../../api/axiosConfig';

function LobbyRoom({ campaign, character, onStart, onBack }) {
  // ✅ Zawsze zapewnij że participants jest array
  const [campaignData, setCampaignData] = useState({
    ...campaign,
    participants: campaign.participants || []
  });
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
      
      // ✅ Zawsze upewnij się że participants jest array
      const freshData = {
        ...response.data,
        participants: response.data.participants || []
      };
      
      setCampaignData(freshData);
      
      if (freshData.status === 'active') {
        console.log('🎮 Campaign is active! Starting game with fresh data...');
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
      await api.post(`/multiplayer/campaigns/${campaign.id}/assign-gm`, null, {
        params: { user_id: userId }
      });
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
      console.log('🎲 Starting campaign...');
      await api.post(`/multiplayer/campaigns/${campaign.id}/start`);
      console.log('✅ Campaign started!');
      await refreshCampaign();
    } catch (error) {
      console.error('Error starting campaign:', error);
      alert(error.response?.data?.detail || 'Failed to start campaign');
    }
  };

  const isGM = campaignData.game_master_id === currentUserId;
  const players = (campaignData.participants || []).filter(p => p.role !== 'gm');
  const allReady = players.length > 0 ? players.every(p => p.ready) : false;
  const canStart = campaignData.game_master_id && allReady && players.length >= 1;

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h3 className="text-2xl font-bold text-white">{campaignData.title}</h3>
          <p className="text-gray-400">
            {campaignData.status === 'active' ? '🎮 Game in progress...' : 'Lobby - Waiting for players...'}
          </p>
        </div>
        <button
          onClick={onBack}
          className="bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded-lg transition"
        >
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
                  }`} title={
                    participant.role === 'gm' ? 'Game Master (always ready)' : 
                    participant.ready ? 'Ready' : 'Not ready'
                  } />
                  
                  <div>
                    <p className="text-white font-semibold">
                      {participant.username}
                      {participant.role === 'gm' && ' 👑'}
                    </p>
                    <p className="text-gray-400 text-sm">
                      Character ID: {participant.character_id}
                    </p>
                  </div>
                </div>

                {isCreator && participant.role !== 'gm' && !campaignData.game_master_id && campaignData.status === 'lobby' && (
                  <button
                    onClick={() => handleAssignGM(participant.user_id)}
                    className="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-sm transition"
                  >
                    Make GM
                  </button>
                )}
              </div>
            ))}

            {(!campaignData.participants || campaignData.participants.length === 0) && (
              <p className="text-gray-400 text-center py-4">No players yet</p>
            )}
          </div>
        </div>

        {/* Campaign Info */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h4 className="text-xl font-bold text-white mb-4">Campaign Info</h4>

          <div className="space-y-3">
            <div>
              <p className="text-gray-400 text-sm">Universe</p>
              <p className="text-white capitalize">{campaignData.universe.replace('_', ' ')}</p>
            </div>

            <div>
              <p className="text-gray-400 text-sm">Status</p>
              <span className={`inline-block px-3 py-1 rounded text-sm ${
                campaignData.status === 'lobby' ? 'bg-yellow-600' : 
                campaignData.status === 'active' ? 'bg-green-600' : 'bg-gray-600'
              }`}>
                {campaignData.status}
              </span>
            </div>

            <div>
              <p className="text-gray-400 text-sm">Game Master</p>
              <p className="text-white">
                {campaignData.game_master_id ? '✓ Assigned' : '✗ Not assigned'}
              </p>
            </div>

            <div>
              <p className="text-gray-400 text-sm">Ready Status</p>
              <p className={`font-semibold ${allReady ? 'text-green-400' : 'text-yellow-400'}`}>
                {allReady ? '✓ All players ready!' : 
                 players.length > 0 ? `⧗ ${players.filter(p => !p.ready).length} player(s) not ready` :
                 '⧗ Waiting for players...'}
              </p>
            </div>
          </div>

          {!isGM && campaignData.status === 'lobby' && (
            <div className="mt-6 pt-6 border-t border-gray-700">
              <button
                onClick={handleToggleReady}
                className={`w-full px-6 py-3 rounded-lg font-bold text-lg transition ${
                  myReadyStatus 
                    ? 'bg-green-600 hover:bg-green-700' 
                    : 'bg-gray-600 hover:bg-gray-700'
                }`}
              >
                {myReadyStatus ? '✓ Ready!' : 'Click when Ready'}
              </button>
              <p className="text-gray-400 text-sm text-center mt-2">
                Waiting for GM to start...
              </p>
            </div>
          )}

          {isGM && campaignData.status === 'lobby' && (
            <div className="mt-6 pt-6 border-t border-gray-700">
              <button
                onClick={handleStart}
                disabled={!canStart}
                className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed px-6 py-3 rounded-lg font-bold text-lg transition"
              >
                {!campaignData.game_master_id ? 'Need GM' :
                 !allReady ? '⧗ Waiting for all ready...' :
                 players.length < 1 ? 'Need at least 1 player' :
                 '🎲 Start Campaign'}
              </button>
              {!allReady && players.length > 0 && (
                <p className="text-yellow-400 text-sm text-center mt-2">
                  {players.filter(p => !p.ready).length} player(s) not ready
                </p>
              )}
            </div>
          )}

          {campaignData.status === 'active' && (
            <div className="mt-6 pt-6 border-t border-gray-700">
              <p className="text-green-400 text-center font-semibold">
                🎮 Campaign is running!
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default LobbyRoom;