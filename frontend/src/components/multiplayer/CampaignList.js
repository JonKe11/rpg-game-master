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

  // ✅ DODANE: Funkcja usuwania kampanii
  const handleDeleteCampaign = async (campaignId) => {
    if (!window.confirm('Are you sure you want to delete this campaign?')) {
      return;
    }

    try {
      await api.delete(`/multiplayer/campaigns/${campaignId}`);
      await fetchCampaigns(); // Odśwież listę
    } catch (error) {
      console.error('Error deleting campaign:', error);
      alert(error.response?.data?.detail || 'Failed to delete campaign');
    }
  };

  if (loading) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-400">Loading campaigns...</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-2xl font-bold text-white">Available Campaigns</h3>
        <button
          onClick={onCreateNew}
          className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded-lg font-semibold transition"
        >
          + Create New Campaign
        </button>
      </div>

      {campaigns.length === 0 ? (
        <div className="text-center py-12 bg-gray-800 rounded-lg">
          <p className="text-gray-400 mb-4">No campaigns available</p>
          <button
            onClick={onCreateNew}
            className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg font-semibold transition"
          >
            Create First Campaign
          </button>
        </div>
      ) : (
        // ✅ SCROLLABLE CONTAINER
        <div className="max-h-[calc(100vh-250px)] overflow-y-auto pr-2">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {campaigns.map((campaign) => (
              <div
                key={campaign.id}
                className="bg-gray-800 rounded-lg p-6 hover:bg-gray-750 transition relative"
              >
                {/* ✅ DELETE BUTTON - tylko dla creatora w lobby */}
                {campaign.creator_id === currentUserId && campaign.status === 'lobby' && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteCampaign(campaign.id);
                    }}
                    className="absolute top-2 right-2 bg-red-600 hover:bg-red-700 p-2 rounded-lg transition text-sm"
                    title="Delete Campaign"
                  >
                    🗑️
                  </button>
                )}

                {/* Campaign Info */}
                <div className="mb-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-xl font-bold text-blue-400">
                      {campaign.title}
                    </h4>
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${
                      campaign.status === 'lobby' ? 'bg-yellow-600' :
                      campaign.status === 'active' ? 'bg-green-600' :
                      'bg-gray-600'
                    }`}>
                      {campaign.status}
                    </span>
                  </div>

                  <div className="space-y-1 text-sm">
                    <p className="text-gray-400">
                      Universe: <span className="text-white capitalize">
                        {campaign.universe.replace('_', ' ')}
                      </span>
                    </p>
                    <p className="text-gray-400">
                      Players: <span className="text-white">
                        {campaign.player_count}/{campaign.max_players}
                      </span>
                    </p>
                    <p className="text-gray-400">
                      GM: {campaign.has_gm ? (
                        <span className="text-green-400">✓ Assigned</span>
                      ) : (
                        <span className="text-red-400">✗ Needed</span>
                      )}
                    </p>
                  </div>
                </div>

                {/* ✅ FIXED: Action Button - umożliwia powrót do aktywnej kampanii */}
                {campaign.status === 'lobby' ? (
                  <button
                    onClick={() => handleJoin(campaign)}
                    className="w-full bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded-lg font-semibold transition"
                  >
                    Join Lobby
                  </button>
                ) : campaign.status === 'active' ? (
                  <button
                    onClick={() => handleJoin(campaign)}
                    className="w-full bg-green-600 hover:bg-green-700 px-4 py-2 rounded-lg font-semibold transition"
                  >
                    🎮 Join Game
                  </button>
                ) : (
                  <button
                    disabled
                    className="w-full bg-gray-600 px-4 py-2 rounded-lg font-semibold cursor-not-allowed"
                  >
                    {campaign.status}
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default CampaignList;