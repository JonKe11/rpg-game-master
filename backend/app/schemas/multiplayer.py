# backend/app/schemas/multiplayer.py
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

# ============================================================================
# CAMPAIGN SCHEMAS
# ============================================================================

class CampaignCreate(BaseModel):
    title: str
    universe: str
    is_public: bool = True

class CampaignJoin(BaseModel):
    character_id: int

class ParticipantInfo(BaseModel):
    user_id: int
    username: str
    character_id: int
    role: str  # "gm" or "player"
    joined_at: str

class CampaignResponse(BaseModel):
    id: int
    title: str
    universe: str
    status: str
    creator_id: int
    game_master_id: Optional[int]
    participants: List[Dict[str, Any]]
    current_location: Optional[str]
    location_image_url: Optional[str]
    max_players: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class CampaignListItem(BaseModel):
    id: int
    title: str
    universe: str
    status: str
    player_count: int
    max_players: int
    has_gm: bool
    created_at: datetime

# ============================================================================
# MESSAGE SCHEMAS
# ============================================================================

class MessageSend(BaseModel):
    message_type: str  # "gm_narration", "player_action", etc.
    content: str
    character_id: Optional[int] = None
    message_metadata: Dict[str, Any] = {}  # ✅ NOWE

class MessageResponse(BaseModel):
    id: int
    user_id: int
    character_id: Optional[int]
    message_type: str
    content: str
    message_metadata: Dict[str, Any]  # ✅ NOWE
    timestamp: datetime
    
    class Config:
        from_attributes = True

# ============================================================================
# WEBSOCKET MESSAGE SCHEMAS
# ============================================================================

class WSMessage(BaseModel):
    """WebSocket message format"""
    type: str  # "message", "system", "dice_roll", etc.
    content: str
    user_id: Optional[int] = None
    username: Optional[str] = None
    character_id: Optional[int] = None
    message_metadata: Dict[str, Any] = {}  # ✅ NOWE
    timestamp: Optional[str] = None