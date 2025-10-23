// frontend/src/components/multiplayer/CreateCampaign.js
import React, { useState } from 'react';
import api from '../../api/axiosConfig';

function CreateCampaign({ character, onCampaignCreated, onCancel }) {
  const [title, setTitle] = useState('');
  const [universe, setUniverse] = useState(character.universe || 'star_wars');
  const [isPublic, setIsPublic] = useState(true);
  const [creating, setCreating] = useState(false);

  const handleCreate = async (e) => {
    e.preventDefault();
    
    if (!title.trim()) {
      alert('Please enter a campaign title');
      return;
    }

    setCreating(true);

    try {
      // 1. Create campaign
      console.log('🔄 Creating campaign:', { title, universe, isPublic });
      const response = await api.post('/multiplayer/campaigns/create', {
        title: title,
        universe: universe,
        is_public: isPublic
      });
      console.log('✅ Campaign created:', response.data);

      // 2. Join own campaign
      try {
        console.log('🔄 Joining campaign:', response.data.campaign_id, 'with character:', character.id);
        const joinResponse = await api.post(
          `/multiplayer/campaigns/${response.data.campaign_id}/join`,
          { character_id: character.id }
        );
        console.log('✅ Joined campaign:', joinResponse.data);
      } catch (joinError) {
        console.error('❌ Join error:', joinError.response?.data || joinError);
        alert(`Campaign created but failed to join: ${joinError.response?.data?.detail || joinError.message}`);
        setCreating(false);
        return; // Don't continue if join failed
      }

      // 3. Fetch full campaign data
      console.log('🔄 Fetching campaign data...');
      const campaignData = await api.get(`/multiplayer/campaigns/${response.data.campaign_id}`);
      console.log('✅ Campaign data:', campaignData.data);
      
      onCampaignCreated(campaignData.data);
    } catch (error) {
      console.error('❌ Create error:', error.response?.data || error);
      alert(`Failed to create campaign: ${error.response?.data?.detail || error.message}`);
      setCreating(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h3 className="text-2xl font-bold text-white mb-6">Create New Campaign</h3>

      <form onSubmit={handleCreate} className="bg-gray-800 rounded-lg p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Campaign Title
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g., The Tatooine Heist"
            className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Universe
          </label>
          <select
            value={universe}
            onChange={(e) => setUniverse(e.target.value)}
            className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="star_wars">Star Wars</option>
            <option value="lotr">Lord of the Rings</option>
            <option value="dnd">Dungeons & Dragons</option>
            <option value="cyberpunk">Cyberpunk</option>
          </select>
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            id="isPublic"
            checked={isPublic}
            onChange={(e) => setIsPublic(e.target.checked)}
            className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500"
          />
          <label htmlFor="isPublic" className="ml-2 text-sm text-gray-300">
            Public (anyone can join)
          </label>
        </div>

        <div className="pt-4 flex gap-3">
          <button
            type="submit"
            disabled={creating}
            className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 px-6 py-3 rounded-lg font-semibold transition"
          >
            {creating ? 'Creating...' : 'Create Campaign'}
          </button>
          <button
            type="button"
            onClick={onCancel}
            disabled={creating}
            className="bg-gray-600 hover:bg-gray-700 disabled:bg-gray-500 px-6 py-3 rounded-lg font-semibold transition"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

export default CreateCampaign;