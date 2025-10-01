from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime

class CharacterBase(BaseModel):
    name: str
    universe: str
    race: Optional[str] = None
    class_type: Optional[str] = None
    level: int = 1
    description: Optional[str] = None
    backstory: Optional[str] = None

class CharacterCreate(CharacterBase):
    pass

class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    race: Optional[str] = None
    class_type: Optional[str] = None
    level: Optional[int] = None
    description: Optional[str] = None
    backstory: Optional[str] = None
    stats: Optional[Dict[str, Any]] = None
    inventory: Optional[List[Dict[str, Any]]] = None
    skills: Optional[List[str]] = None

class CharacterResponse(CharacterBase):
    id: int
    owner_id: int
    stats: Dict[str, Any]
    inventory: List[Dict[str, Any]]
    skills: List[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
