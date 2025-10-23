# backend/app/models/campaign.py
from sqlalchemy import Column, Integer, String, JSON, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base
import enum

class CampaignStatus(enum.Enum):
    LOBBY = "lobby"           # Czeka na graczy
    ACTIVE = "active"         # Gra trwa
    PAUSED = "paused"         # Zapauzowana
    COMPLETED = "completed"   # Zakończona

class ParticipantRole(enum.Enum):
    GAME_MASTER = "gm"
    PLAYER = "player"

class MultiplayerCampaign(Base):
    __tablename__ = "multiplayer_campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    universe = Column(String, nullable=False)  # star_wars, lotr, etc.
    
    # Status
    status = Column(SQLEnum(CampaignStatus), default=CampaignStatus.LOBBY)
    
    # Creator & GM
    creator_id = Column(Integer, nullable=False)  # Kto utworzył
    game_master_id = Column(Integer, nullable=True)  # Kto jest GM (assigned in lobby)
    
    # Settings
    max_players = Column(Integer, default=7)
    is_public = Column(Boolean, default=True)  # Public vs Friends-only
    
    # Game State
    current_location = Column(String, nullable=True)  # "Tatooine"
    location_image_url = Column(String, nullable=True)
    
    # Participants: [{user_id, character_id, role, joined_at}]
    participants = Column(JSON, default=[])
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    messages = relationship("CampaignMessage", back_populates="campaign", cascade="all, delete-orphan")