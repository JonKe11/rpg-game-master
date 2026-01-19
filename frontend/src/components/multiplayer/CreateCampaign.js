
import React, { useState } from 'react';
import api from '../../api/axiosConfig';

function CreateCampaign({ character, onCampaignCreated, onCancel }) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState(''); 
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
      
      console.log('🔄 Creating campaign:', { title, description, universe, isPublic });
      const response = await api.post('/multiplayer/campaigns/create', {
        title: title,
        description: description, 
        universe: universe,
        is_public: isPublic
      });
      console.log('✅ Campaign created:', response.data);

      
      try {
        await api.post(
          `/multiplayer/campaigns/${response.data.campaign_id}/join`,
          { character_id: character.id }
        );
      } catch (joinError) {
        console.error('❌ Join error:', joinError);
        
      }

      
      const campaignData = await api.get(`/multiplayer/campaigns/${response.data.campaign_id}`);
      onCampaignCreated(campaignData.data);

    } catch (error) {
      console.error('❌ Create error:', error);
      alert(`Failed to create campaign: ${error.response?.data?.detail || error.message}`);
      setCreating(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h3 className="text-2xl font-bold text-white mb-6">Create New Campaign</h3>

      <form onSubmit={handleCreate} className="bg-gray-800 rounded-lg p-6 space-y-4 shadow-xl border border-gray-700">
        
        {/* Title */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Campaign Title
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 border border-gray-600"
            required
            maxLength={60}
          />
        </div>

        {/* ✅ Description Field */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Brief Description (Optional)
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows="3"
            className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 border border-gray-600 resize-none"
            maxLength={200}
          />
          <p className="text-xs text-gray-500 text-right mt-1">{description.length}/200</p>
        </div>

        {/* Universe */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Universe
          </label>
          <select
            value={universe}
            onChange={(e) => setUniverse(e.target.value)}
            className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 border border-gray-600"
          >
            <option value="star_wars">Star Wars</option>
            <option value="lotr">Lord of the Rings</option>
            <option value="dnd">Dungeons & Dragons</option>
            <option value="cyberpunk">Cyberpunk</option>
          </select>
        </div>

        {/* Visibility */}
        <div className="flex items-center bg-gray-700/30 p-3 rounded-lg border border-gray-600">
          <input
            type="checkbox"
            id="isPublic"
            checked={isPublic}
            onChange={(e) => setIsPublic(e.target.checked)}
            className="w-5 h-5 text-blue-600 bg-gray-700 border-gray-500 rounded focus:ring-blue-500 cursor-pointer"
          />
          <label htmlFor="isPublic" className="ml-3 text-sm text-gray-200 cursor-pointer select-none">
            <span className="font-bold block">Public Campaign</span>
            <span className="text-gray-400 text-xs">Anyone on the server can see and join this lobby.</span>
          </label>
        </div>

        {/* Buttons */}
        <div className="pt-4 flex gap-3">
          <button
            type="submit"
            disabled={creating}
            className="flex-1 bg-gradient-to-r from-green-600 to-green-500 hover:from-green-500 hover:to-green-400 disabled:from-gray-600 disabled:to-gray-600 text-white px-6 py-3 rounded-lg font-bold transition shadow-lg"
          >
            {creating ? 'Creating Lobby...' : '🚀 Create & Join'}
          </button>
          <button
            type="button"
            onClick={onCancel}
            disabled={creating}
            className="bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 text-gray-300 px-6 py-3 rounded-lg font-semibold transition border border-gray-600"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

export default CreateCampaign;