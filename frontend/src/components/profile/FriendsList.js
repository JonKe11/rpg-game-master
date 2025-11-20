// frontend/src/components/profile/FriendsList.js
import React, { useState, useEffect } from 'react';
import api from '../../api/axiosConfig';

function FriendsList() {
    const [friends, setFriends] = useState([]);
    const [requests, setRequests] = useState([]);
    const [inviteName, setInviteName] = useState('');

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [friendsRes, requestsRes] = await Promise.all([
                api.get('/friends/'),
                api.get('/friends/requests/pending')
            ]);
            setFriends(friendsRes.data);
            setRequests(requestsRes.data);
        } catch (error) {
            console.error("Error loading friends:", error);
        }
    };

    const sendRequest = async () => {
        if (!inviteName) return;
        try {
            await api.post('/friends/request', { username: inviteName });
            alert('Friend request sent!');
            setInviteName('');
        } catch (error) {
            alert(error.response?.data?.detail || "Failed to send request");
        }
    };

    const handleResponse = async (userId, status) => {
        try {
            await api.post(`/friends/respond/${userId}`, { status });
            loadData(); // Odśwież
        } catch (error) {
            console.error("Error responding:", error);
        }
    };

    return (
        <div>
            {/* Invite Section */}
            <div className="mb-8 p-4 bg-gray-700 rounded-lg flex gap-4 items-end">
                <div className="flex-1">
                    <label className="block text-sm text-gray-300 mb-1">Add Friend by Username</label>
                    <input 
                        value={inviteName}
                        onChange={(e) => setInviteName(e.target.value)}
                        className="w-full p-2 bg-gray-600 text-white rounded border border-gray-500 focus:border-blue-500 outline-none"
                        placeholder="Enter username..."
                    />
                </div>
                <button onClick={sendRequest} className="bg-green-600 hover:bg-green-700 px-6 py-2 rounded font-bold h-10">
                    Send Request
                </button>
            </div>

            {/* Pending Requests */}
            {requests.length > 0 && (
                <div className="mb-8">
                    <h4 className="text-lg font-bold text-yellow-400 mb-3">Pending Requests</h4>
                    <div className="space-y-2">
                        {requests.map(req => (
                            <div key={req.id} className="bg-gray-700 p-3 rounded flex justify-between items-center border-l-4 border-yellow-500">
                                <span className="font-bold">{req.username}</span>
                                <div className="flex gap-2">
                                    <button onClick={() => handleResponse(req.id, 'accepted')} className="bg-blue-600 px-3 py-1 rounded text-sm hover:bg-blue-500">Accept</button>
                                    <button onClick={() => handleResponse(req.id, 'rejected')} className="bg-gray-600 px-3 py-1 rounded text-sm hover:bg-gray-500">Ignore</button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Friends List */}
            <h4 className="text-lg font-bold mb-3">Your Friends ({friends.length})</h4>
            {friends.length === 0 ? (
                <p className="text-gray-500 italic">No friends yet.</p>
            ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                    {friends.map(friend => (
                        <div key={friend.id} className="bg-gray-700 p-3 rounded flex items-center gap-3">
                            <div className="w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center font-bold">
                                {friend.username[0].toUpperCase()}
                            </div>
                            <div className="font-semibold">{friend.username}</div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default FriendsList;