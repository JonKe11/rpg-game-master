# backend/app/schemas/session.py
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class GameSessionBase(BaseModel):
    title: str
    universe: str
    is_public: bool = False

class GameSessionCreate(GameSessionBase):
    participants: List[int] = []  # lista ID postaci

class GameSessionUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    story_context: Optional[str] = None
    chat_history: Optional[List[Dict[str, Any]]] = None
    world_state: Optional[Dict[str, Any]] = None

class GameSessionResponse(GameSessionBase):
    id: int
    status: str
    game_master_id: int
    story_context: Optional[str]
    participants: List[int]
    created_at: datetime
    last_played: datetime
    chat_history: Optional[List[Dict]] = []
    world_state: Optional[Dict] = {}
    
    class Config:
        from_attributes = True

class StartSessionRequest(BaseModel):
    character_id: int
    title: Optional[str] = None