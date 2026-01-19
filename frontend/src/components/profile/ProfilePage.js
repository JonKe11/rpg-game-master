
import React, { useState, useEffect } from 'react';
import api from '../../api/axiosConfig';
import FriendsList from './FriendsList';

function ProfilePage({ onBack }) {
    const [profile, setProfile] = useState(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('overview'); 

    useEffect(() => {
        fetchProfile();
    }, []);

    const fetchProfile = async () => {
        try {
            const response = await api.get('/users/profile/me');
            setProfile(response.data);
        } catch (error) {
            console.error("Failed to load profile:", error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="text-white text-center p-8">Loading profile...</div>;
    if (!profile) return <div className="text-red-400 text-center p-8">Failed to load profile</div>;

    return (
        <div className="container mx-auto p-6 text-white">
            <div className="flex justify-between items-center mb-8">
                <h2 className="text-3xl font-bold">👤 My Profile</h2>
                <button onClick={onBack} className="bg-gray-600 px-4 py-2 rounded hover:bg-gray-700">
                    ← Back to Dashboard
                </button>
            </div>

            {/* User Card */}
            <div className="bg-gray-800 rounded-lg p-6 mb-8 flex items-center gap-6 shadow-lg">
                <div className="w-20 h-20 bg-blue-600 rounded-full flex items-center justify-center text-3xl font-bold">
                    {profile.user.username[0].toUpperCase()}
                </div>
                <div>
                    <h3 className="text-2xl font-bold">{profile.user.username}</h3>
                    <p className="text-gray-400">{profile.user.email}</p>
                    <div className="flex gap-4 mt-3 text-sm">
                        <span className="bg-gray-700 px-3 py-1 rounded">Characters: {profile.stats.characters_count}</span>
                        <span className="bg-gray-700 px-3 py-1 rounded">Campaigns: {profile.stats.campaigns_count}</span>
                        <span className="bg-gray-700 px-3 py-1 rounded">Friends: {profile.stats.friends_count}</span>
                    </div>
                </div>
            </div>

            {/* Tabs */}
            <div className="flex gap-4 mb-6 border-b border-gray-700 pb-1">
                {['overview', 'campaigns', 'friends'].map(tab => (
                    <button
                        key={tab}
                        onClick={() => setActiveTab(tab)}
                        className={`px-4 py-2 font-semibold capitalize ${
                            activeTab === tab ? 'text-blue-400 border-b-2 border-blue-400' : 'text-gray-400 hover:text-white'
                        }`}
                    >
                        {tab}
                    </button>
                ))}
            </div>

            {/* Content */}
            <div className="bg-gray-800 rounded-lg p-6 min-h-[400px]">
                {activeTab === 'overview' && (
                    <div>
                        <h4 className="text-xl font-bold mb-4">My Characters</h4>
                        {profile.characters.length === 0 ? <p className="text-gray-500">No characters yet.</p> : (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {profile.characters.map(char => (
                                    <div key={char.id} className="bg-gray-700 p-4 rounded flex justify-between">
                                        <div>
                                            <div className="font-bold">{char.name}</div>
                                            <div className="text-sm text-gray-400">{char.race} {char.class}</div>
                                        </div>
                                        <div className="text-blue-300 font-mono">Lvl {char.level}</div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'campaigns' && (
                    <div>
                        <h4 className="text-xl font-bold mb-4">My Campaigns History</h4>
                        {profile.campaigns.length === 0 ? <p className="text-gray-500">No campaigns yet.</p> : (
                            <div className="space-y-3">
                                {profile.campaigns.map(camp => (
                                    <div key={camp.id} className="bg-gray-700 p-4 rounded flex justify-between items-center">
                                        <div>
                                            <div className="font-bold text-lg">{camp.title}</div>
                                            <div className="text-sm text-gray-400">Role: {camp.role}</div>
                                        </div>
                                        <span className={`px-2 py-1 rounded text-xs uppercase font-bold ${
                                            camp.status === 'active' ? 'bg-green-600' : 'bg-gray-600'
                                        }`}>
                                            {camp.status}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'friends' && <FriendsList />}
            </div>
        </div>
    );
}

export default ProfilePage;