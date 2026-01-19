
import React, { useState, useEffect } from 'react';
import api from '../../api/axiosConfig';

function FriendsList() {
    const [friends, setFriends] = useState([]);
    const [requests, setRequests] = useState([]);
    const [inviteName, setInviteName] = useState('');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        setLoading(true);
        try {
            const [friendsRes, requestsRes] = await Promise.all([
                api.get('/friends/'),
                api.get('/friends/requests/pending')
            ]);
            setFriends(friendsRes.data);
            setRequests(requestsRes.data);
        } catch (error) {
            console.error("Error loading friends:", error);
        } finally {
            setLoading(false);
        }
    };

    const sendRequest = async () => {
        if (!inviteName.trim()) return;
        try {
            await api.post('/friends/request', { username: inviteName });
            alert(`Friend request sent to ${inviteName}!`);
            setInviteName('');
            loadData(); 
        } catch (error) {
            alert(error.response?.data?.detail || "Failed to send request. Check username.");
        }
    };

    const handleResponse = async (userId, status) => {
        try {
            await api.post(`/friends/respond/${userId}`, { status });
            
            setRequests(prev => prev.filter(r => r.id !== userId));
            if (status === 'accepted') loadData(); 
        } catch (error) {
            console.error("Error responding:", error);
            alert("Action failed.");
        }
    };

    return (
        <div className="animate-fadeIn">
            {/* Invite Section */}
            <div className="mb-8 p-6 bg-gray-700/50 border border-gray-600 rounded-lg flex flex-col sm:flex-row gap-4 items-end">
                <div className="flex-1 w-full">
                    <label className="block text-sm font-bold text-gray-300 mb-2 uppercase tracking-wide">
                        ➕ Add Friend
                    </label>
                    <input 
                        value={inviteName}
                        onChange={(e) => setInviteName(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && sendRequest()}
                        className="w-full p-3 bg-gray-900 text-white rounded border border-gray-600 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition"
                        placeholder="Enter username (e.g. LukeSkywalker)"
                    />
                </div>
                <button 
                    onClick={sendRequest} 
                    disabled={!inviteName}
                    className={`w-full sm:w-auto px-6 py-3 rounded font-bold shadow-lg transition ${
                        inviteName ? 'bg-blue-600 hover:bg-blue-500 text-white' : 'bg-gray-600 text-gray-400 cursor-not-allowed'
                    }`}
                >
                    Send Request
                </button>
            </div>

            {/* Pending Requests */}
            {requests.length > 0 && (
                <div className="mb-8">
                    <h4 className="text-lg font-bold text-yellow-400 mb-4 flex items-center gap-2">
                        📩 Pending Requests <span className="bg-yellow-900 text-yellow-200 text-xs px-2 py-1 rounded-full">{requests.length}</span>
                    </h4>
                    <div className="grid gap-3">
                        {requests.map(req => (
                            <div key={req.id} className="bg-gray-800 p-4 rounded-lg flex justify-between items-center border-l-4 border-yellow-500 shadow-md">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 bg-gray-700 rounded-full flex items-center justify-center font-bold text-gray-300">
                                        {req.username[0].toUpperCase()}
                                    </div>
                                    <span className="font-bold text-lg">{req.username}</span>
                                </div>
                                <div className="flex gap-2">
                                    <button onClick={() => handleResponse(req.id, 'accepted')} className="bg-green-600 hover:bg-green-500 text-white px-4 py-2 rounded text-sm font-bold transition">Accept</button>
                                    <button onClick={() => handleResponse(req.id, 'rejected')} className="bg-red-600 hover:bg-red-500 text-white px-4 py-2 rounded text-sm font-bold transition">Reject</button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Friends List */}
            <div>
                <h4 className="text-xl font-bold mb-4 flex items-center gap-2">
                    👥 Your Friends <span className="text-gray-500 text-sm font-normal">({friends.length})</span>
                </h4>
                
                {loading ? (
                    <div className="text-center py-8 text-gray-500">Loading friends...</div>
                ) : friends.length === 0 ? (
                    <div className="text-center py-8 bg-gray-800/30 rounded-lg border border-dashed border-gray-700">
                        <p className="text-gray-400 mb-2">You haven't added any friends yet.</p>
                        <p className="text-sm text-gray-500">Invite someone above to get started!</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                        {friends.map(friend => (
                            <div key={friend.id} className="bg-gray-800 p-4 rounded-lg flex items-center gap-4 border border-gray-700 hover:border-gray-500 transition group">
                                <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-purple-600 rounded-full flex items-center justify-center font-bold text-xl shadow-inner">
                                    {friend.username[0].toUpperCase()}
                                </div>
                                <div>
                                    <div className="font-bold text-lg group-hover:text-blue-400 transition">{friend.username}</div>
                                    <div className="text-xs text-green-400 flex items-center gap-1">
                                        <span className="w-2 h-2 bg-green-500 rounded-full"></span> Online
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

export default FriendsList;