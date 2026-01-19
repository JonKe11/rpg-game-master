
"""
Player Inventory Model

Tracks items that players have in their inventory during campaigns.
Only players (not GM) have inventory.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, JSON 

from app.models.database import Base
from app.models.campaign import MultiplayerCampaign 
from app.models.user import User
from app.models.character import Character


class PlayerInventory(Base):
    """
    Player inventory item.
    
    Each row represents one item in a player's inventory.
    Tied to both campaign and player for multi-campaign support.
    """
    __tablename__ = "player_inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    
    
    
    campaign_id = Column(Integer, ForeignKey("multiplayer_campaigns.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    character_id = Column(Integer, ForeignKey("characters.id", ondelete="SET NULL"), nullable=True)
    
    
    item_name = Column(String(255), nullable=False)
    item_category = Column(String(50), nullable=False)  
    item_image_url = Column(String(500), nullable=True)
    item_description = Column(String(1000), nullable=True)
    
    item_rarity = Column(String, default="common")
    
    quantity = Column(Integer, default=1, nullable=False)
    
    stat_modifiers = Column(JSON, default={}, nullable=True)
    added_by_gm_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    notes = Column(String(500), nullable=True)  
    
    is_equipped = Column(Boolean, default=False)
    slot = Column(String(50), default="item") 
    dice_config = Column(JSON, nullable=True) 
    
    armor_value = Column(Integer, default=0)
    
    
    campaign = relationship("MultiplayerCampaign", back_populates="inventory_items")
    user = relationship("User", foreign_keys=[user_id])
    character = relationship("Character")
    added_by = relationship("User", foreign_keys=[added_by_gm_id])
    
    
    __table_args__ = (
        Index('idx_inventory_campaign_user', 'campaign_id', 'user_id'),
        Index('idx_inventory_campaign', 'campaign_id'),
        Index('idx_inventory_user', 'user_id'),
    )
    
    def __repr__(self):
        return f"<PlayerInventory(id={self.id}, player={self.user_id}, item={self.item_name}, qty={self.quantity})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        