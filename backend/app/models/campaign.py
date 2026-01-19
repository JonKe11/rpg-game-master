
from sqlalchemy import Column, Integer, String, JSON, DateTime, Boolean, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base
import enum

class CampaignStatus(enum.Enum):
    LOBBY = "lobby"           
    ACTIVE = "active"        
    PAUSED = "paused"         
    COMPLETED = "completed"   

class ParticipantRole(enum.Enum):
    GAME_MASTER = "gm"
    PLAYER = "player"

class MultiplayerCampaign(Base):
    __tablename__ = "multiplayer_campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    universe = Column(String, nullable=False)  
    description = Column(Text, nullable=True)  
    
   
    status = Column(SQLEnum(CampaignStatus), default=CampaignStatus.LOBBY)
    
  
    creator_id = Column(Integer, nullable=False)  
    game_master_id = Column(Integer, nullable=True)  
    
  
    max_players = Column(Integer, default=7)
    is_public = Column(Boolean, default=True)  
    
 
    current_location = Column(String, nullable=True)  
    location_image_url = Column(String, nullable=True)
    

    participants = Column(JSON, default=[])
    

  
    spawned_npcs = Column(JSON, default=[])
    
   
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
 
    messages = relationship("CampaignMessage", back_populates="campaign", cascade="all, delete-orphan")
    inventory_items = relationship("PlayerInventory", back_populates="campaign", cascade="all, delete-orphan")