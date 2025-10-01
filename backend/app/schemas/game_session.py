# backend/app/schemas/game_session.py
from typing import List, Dict, Optional, TypedDict
from pydantic import BaseModel
from datetime import datetime

class NPCData(TypedDict):
    name: str
    race: str
    occupation: str
    personality: str
    motivation: str
    relationship: int

class SessionContext(BaseModel):
    """Strongly typed session context"""
    session_id: int
    universe: str
    character: Dict
    location: Optional[str]
    history: List[Dict]
    narrative_style: str = "adaptive"
    story_threads: List[str] = []
    active_npcs: Dict[str, NPCData] = {}

class SessionActionRequest(BaseModel):
    action: str
    session_id: int

class SessionActionResponse(BaseModel):
    message: str
    type: str
    timestamp: datetime
    location: Optional[str] = None
    narrative_style: Optional[str] = None
    choices: Optional[List[str]] = None
    effects: Optional[List[str]] = None
    wiki_sources: Optional[List[str]] = None