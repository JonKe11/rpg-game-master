// frontend/src/components/CampaignProgress.js
import React from 'react';

function CampaignProgress({ campaign }) {
  if (!campaign) return null;

  const getActColor = (act) => {
    const colors = {
      'act_1_setup': 'text-green-400',
      'act_2_confrontation': 'text-yellow-400',
      'act_3_resolution': 'text-red-400',
      'epilogue': 'text-purple-400'
    };
    return colors[act] || 'text-gray-400';
  };

  const getActLabel = (act) => {
    const labels = {
      'act_1_setup': 'Act I: Setup',
      'act_2_confrontation': 'Act II: Confrontation',
      'act_3_resolution': 'Act III: Resolution',
      'epilogue': 'Epilogue'
    };
    return labels[act] || act;
  };

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 mb-4">
      {/* Campaign Title */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-lg font-bold text-blue-400">
            📖 {campaign.title || 'Campaign'}
          </h3>
          {campaign.theme && (
            <p className="text-xs text-gray-400 capitalize">
              Theme: {campaign.theme}
            </p>
          )}
        </div>
        {campaign.progress_percent !== undefined && (
          <div className="text-right">
            <div className="text-2xl font-bold text-blue-400">
              {Math.round(campaign.progress_percent)}%
            </div>
            <div className="text-xs text-gray-400">Complete</div>
          </div>
        )}
      </div>

      {/* Progress Bar */}
      {campaign.progress_percent !== undefined && (
        <div className="mb-3">
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div
              className="bg-blue-500 h-2 rounded-full transition-all duration-500"
              style={{ width: `${campaign.progress_percent}%` }}
            ></div>
          </div>
        </div>
      )}

      {/* Current Status */}
      <div className="grid grid-cols-2 gap-3 text-sm">
        {campaign.current_beat && (
          <div className="bg-gray-700 p-2 rounded">
            <div className="text-xs text-gray-400">Current Beat</div>
            <div className="font-semibold text-white truncate">
              {campaign.current_beat}
            </div>
          </div>
        )}
        
        {campaign.act && (
          <div className="bg-gray-700 p-2 rounded">
            <div className="text-xs text-gray-400">Act</div>
            <div className={`font-semibold ${getActColor(campaign.act)}`}>
              {getActLabel(campaign.act)}
            </div>
          </div>
        )}
        
        {campaign.turns_taken !== undefined && campaign.turns_total && (
          <div className="bg-gray-700 p-2 rounded">
            <div className="text-xs text-gray-400">Progress</div>
            <div className="font-semibold text-white">
              Turn {campaign.turns_taken}/{campaign.turns_total}
            </div>
          </div>
        )}

        {campaign.near_end && (
          <div className="bg-red-900 bg-opacity-30 border border-red-700 p-2 rounded col-span-2 text-center">
            <div className="text-xs font-bold text-red-400">
              ⚠️ Approaching Finale
            </div>
          </div>
        )}

        {campaign.completed && (
          <div className="bg-green-900 bg-opacity-30 border border-green-700 p-2 rounded col-span-2 text-center">
            <div className="text-xs font-bold text-green-400">
              ✅ Campaign Completed!
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default CampaignProgress;