// frontend/src/components/multiplayer/CampaignList.js
import React, { useState, useEffect } from 'react';
import api from '../../api/axiosConfig';

function CampaignList({ character, onCreateNew, onJoinCampaign }) {
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentUserId, setCurrentUserId] = useState(null);

  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (userData) {
      const user = JSON.parse(userData);
      setCurrentUserId(user.id);
    }
    
    fetchCampaigns();
    const interval = setInterval(fetchCampaigns, 3000);
    return () => clearInterval(interval);
    
  }, []);

  const fetchCampaigns = async () => {
    try {
      const response = await api.get('/multiplayer/campaigns/');
      setCampaigns(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching campaigns:', error);
      setLoading(false);
    }
  };

  const handleJoin = async (campaign) => {
    try {
      await api.post(`/multiplayer/campaigns/${campaign.id}/join`, {
        character_id: character.id
      });
      onJoinCampaign(campaign);
    } catch (error) {
      console.error('Error joining campaign:', error);
      alert(error.response?.data?.detail || 'Failed to join campaign');
    }
  };

  const handleDeleteCampaign = async (campaignId) => {
    if (!window.confirm('Are you sure you want to delete this campaign?')) return;
    try {
      await api.delete(`/multiplayer/campaigns/${campaignId}`);
      await fetchCampaigns();
    } catch (error) {
      console.error('Error deleting campaign:', error);
      alert(error.response?.data?.detail || 'Failed to delete campaign');
    }
  };

  const renderJoinButton = (campaign) => {
    const isParticipant = campaign.participant_ids && campaign.participant_ids.includes(currentUserId);
    
    if (campaign.status === 'lobby') {
      return (
        <button
          onClick={() => handleJoin(campaign)}
          className="w-full bg-purple-600 hover:bg-purple-500 px-4 py-2 rounded-lg font-bold transition shadow-lg border border-purple-500"
        >
          {isParticipant ? "Enter Lobby" : "Join Lobby"}
        </button>
      );
    }
    
    if (campaign.status === 'active' || campaign.status === 'paused') {
      if (isParticipant) {
        return (
          <button
            onClick={() => handleJoin(campaign)}
            className="w-full bg-green-600 hover:bg-green-500 px-4 py-2 rounded-lg font-bold transition shadow-lg border border-green-500"
          >
            🎮 Resume Game
          </button>
        );
      } else {
        return (
          <button
            disabled
            className="w-full bg-gray-700 text-gray-400 px-4 py-2 rounded-lg font-semibold cursor-not-allowed border border-gray-600"
          >
            🔒 In Progress
          </button>
        );
      }
    }
    
    return (
      <button disabled className="w-full bg-gray-700 px-4 py-2 rounded-lg cursor-not-allowed">
        {campaign.status}
      </button>
    );
  };

  if (loading) {
    return (
        <div className="flex justify-center items-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8 border-b border-gray-700 pb-4">
        <div>
            <h3 className="text-3xl font-bold text-white">Campaigns</h3>
            <p className="text-gray-400 text-sm mt-1">Find a game or start your own adventure.</p>
        </div>
        <button 
            onClick={onCreateNew} 
            className="bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white px-6 py-3 rounded-lg font-bold transition shadow-lg flex items-center gap-2"
        >
          <span>➕</span> Create Campaign
        </button>
      </div>

      {campaigns.length === 0 ? (
        <div className="text-center py-16 bg-gray-800/50 rounded-xl border border-gray-700 border-dashed">
          <p className="text-gray-300 text-lg mb-2">No campaigns found.</p>
          <p className="text-gray-500 mb-6">Be the first to start an adventure!</p>
          <button onClick={onCreateNew} className="bg-blue-600 hover:bg-blue-700 px-6 py-2 rounded-lg font-semibold transition">
            Start New Campaign
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 overflow-y-auto max-h-[calc(100vh-250px)] pr-2 custom-scrollbar">
            {campaigns.map((campaign) => (
              <div 
                key={campaign.id} 
                className="bg-gray-800 rounded-xl p-5 hover:bg-gray-750 transition duration-200 border border-gray-700 flex flex-col relative group shadow-lg"
              >
                {/* Delete Button (Only for Creator in Lobby) */}
                {campaign.creator_id === currentUserId && campaign.status === 'lobby' && (
                  <button
                    onClick={(e) => { e.stopPropagation(); handleDeleteCampaign(campaign.id); }}
                    className="absolute top-4 right-4 text-gray-500 hover:text-red-400 p-1 rounded transition opacity-0 group-hover:opacity-100"
                    title="Delete Campaign"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                )}

                <div className="mb-4">
                  <div className="flex justify-between items-start">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider mb-2 inline-block ${
                        campaign.status === 'lobby' ? 'bg-yellow-900 text-yellow-200 border border-yellow-700' :
                        campaign.status === 'active' ? 'bg-green-900 text-green-200 border border-green-700' :
                        'bg-gray-700 text-gray-300'
                      }`}>
                        {campaign.status}
                      </span>
                      {campaign.is_friend_campaign && (
                          <span className="text-xs text-blue-400 font-semibold flex items-center gap-1">
                              👥 Friends
                          </span>
                      )}
                  </div>

                  <h4 className="text-xl font-bold text-white mb-1 truncate">{campaign.title}</h4>
                  
                  {/* ✅ Wyświetlanie opisu */}
                  <p className="text-gray-400 text-sm h-10 line-clamp-2 leading-relaxed">
                      {campaign.description || <span className="italic opacity-50">No description provided.</span>}
                  </p>
                </div>

                <div className="space-y-2 mb-6 text-sm bg-gray-900/50 p-3 rounded-lg">
                    <div className="flex justify-between">
                        <span className="text-gray-500">Universe</span>
                        <span className="text-gray-300 capitalize font-medium">{campaign.universe.replace('_', ' ')}</span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-gray-500">Players</span>
                        <span className={`font-mono font-bold ${campaign.player_count >= campaign.max_players ? 'text-red-400' : 'text-white'}`}>
                            {campaign.player_count} / {campaign.max_players}
                        </span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-gray-500">Game Master</span>
                        {campaign.has_gm ? (
                            <span className="text-green-400 text-xs font-bold bg-green-900/30 px-2 py-0.5 rounded">ASSIGNED</span>
                        ) : (
                            <span className="text-red-400 text-xs font-bold bg-red-900/30 px-2 py-0.5 rounded">NEEDED</span>
                        )}
                    </div>
                </div>

                <div className="mt-auto">
                    {renderJoinButton(campaign)}
                </div>
                
              </div>
            ))}
        </div>
      )}
    </div>
  );
}

export default CampaignList;