# backend/app/websocket/campaign_ws.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
from datetime import datetime

class ConnectionManager:
    """Manages WebSocket connections for campaigns"""
    
    def __init__(self):
        # campaign_id -> [websockets]
        self.active_connections: Dict[int, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, campaign_id: int):
        """Connect client to campaign room"""
        await websocket.accept()
        
        if campaign_id not in self.active_connections:
            self.active_connections[campaign_id] = []
        
        self.active_connections[campaign_id].append(websocket)
        print(f"✅ Client connected to campaign {campaign_id}")
    
    def disconnect(self, websocket: WebSocket, campaign_id: int):
        """Disconnect client from campaign room"""
        if campaign_id in self.active_connections:
            self.active_connections[campaign_id].remove(websocket)
            
            # Clean up empty rooms
            if not self.active_connections[campaign_id]:
                del self.active_connections[campaign_id]
        
        print(f"❌ Client disconnected from campaign {campaign_id}")
    
    async def broadcast(self, campaign_id: int, message: dict):
        """Broadcast message to all clients in campaign"""
        if campaign_id not in self.active_connections:
            return
        
        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()
        
        # Send to all connected clients
        disconnected = []
        for connection in self.active_connections[campaign_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error sending to client: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn, campaign_id)
    
    async def send_personal(self, websocket: WebSocket, message: dict):
        """Send message to specific client"""
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()
        
        await websocket.send_json(message)

# Global manager instance
manager = ConnectionManager()