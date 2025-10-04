# backend/app/schemas/character.py
from pydantic import BaseModel, field_validator
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
    
    # Star Wars fields
    homeworld: Optional[str] = None
    born_year: Optional[int] = None
    born_era: Optional[str] = "BBY"
    gender: Optional[str] = None
    height: Optional[float] = None
    mass: Optional[float] = None
    skin_color: Optional[str] = None
    eye_color: Optional[str] = None
    hair_color: Optional[str] = None
    
    # KOTOR attributes
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10
    
    # KOTOR skills
    skill_computer_use: int = 0
    skill_demolitions: int = 0
    skill_stealth: int = 0
    skill_awareness: int = 0
    skill_persuade: int = 0
    skill_repair: int = 0
    skill_security: int = 0
    skill_treat_injury: int = 0
    
    # Legacy
    cybernetics: Optional[List[str]] = None
    affiliations: Optional[List[str]] = None

class CharacterCreate(CharacterBase):
    pass

class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    race: Optional[str] = None
    class_type: Optional[str] = None
    level: Optional[int] = None
    description: Optional[str] = None
    backstory: Optional[str] = None
    homeworld: Optional[str] = None
    born_year: Optional[int] = None
    born_era: Optional[str] = None
    gender: Optional[str] = None
    height: Optional[float] = None
    mass: Optional[float] = None
    skin_color: Optional[str] = None
    eye_color: Optional[str] = None
    hair_color: Optional[str] = None
    
    strength: Optional[int] = None
    dexterity: Optional[int] = None
    constitution: Optional[int] = None
    intelligence: Optional[int] = None
    wisdom: Optional[int] = None
    charisma: Optional[int] = None
    
    skill_computer_use: Optional[int] = None
    skill_demolitions: Optional[int] = None
    skill_stealth: Optional[int] = None
    skill_awareness: Optional[int] = None
    skill_persuade: Optional[int] = None
    skill_repair: Optional[int] = None
    skill_security: Optional[int] = None
    skill_treat_injury: Optional[int] = None
    
    cybernetics: Optional[List[str]] = None
    affiliations: Optional[List[str]] = None
    stats: Optional[Dict[str, Any]] = None
    inventory: Optional[List[Dict[str, Any]]] = None
    skills: Optional[List[str]] = None

class CharacterResponse(CharacterBase):
    id: int
    owner_id: int
    stats: Dict[str, Any] = {}
    inventory: List[Dict[str, Any]] = []
    skills: List[str] = []
    created_at: datetime
    
    @field_validator('cybernetics', 'affiliations', 'skills', mode='before')
    @classmethod
    def convert_none_to_list(cls, v):
        return v if v is not None else []
    
    @field_validator('stats', 'inventory', mode='before')
    @classmethod
    def convert_none_to_dict_or_list(cls, v, info):
        if v is None:
            return {} if info.field_name == 'stats' else []
        return v
    
    class Config:
        from_attributes = True