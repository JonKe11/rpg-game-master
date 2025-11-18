# backend/app/models/campaign_message.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base
import enum

class MessageType(enum.Enum):
    # GM Messages
    GM_NARRATION = "gm_narration"
    GM_EVENT = "gm_event"
    GM_CHOICE = "gm_choice"
    
    # Player Messages
    PLAYER_ACTION = "player_action"
    PLAYER_SPEECH = "player_speech"
    
    # System
    DICE_ROLL = "dice_roll"
    SYSTEM = "system"
    
    # ✨ DODANE - GM Tools!
    LOCATION_CHANGE = "location_change"  # ✨ NOWE!
    ITEM_ADDED = "item_added"            # ✨ NOWE!


    NPC_SPAWN = "npc_spawn"
    DICE_ROLL_RESULT = "dice_roll_result" # Wynik rzutu (systemowy)
class CampaignMessage(Base):
    __tablename__ = "campaign_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("multiplayer_campaigns.id"), nullable=False)
    
    user_id = Column(Integer, nullable=False)
    character_id = Column(Integer, nullable=True)
    
    message_type = Column(SQLEnum(MessageType), nullable=False)
    content = Column(Text, nullable=False)
    
    # 🔧 POPRAWIONE: metadata → message_metadata
    message_metadata = Column(JSON, default={})
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    campaign = relationship("MultiplayerCampaign", back_populates="messages")