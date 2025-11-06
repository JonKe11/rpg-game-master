# backend/app/models/player_inventory.py
"""
Player Inventory Model

Tracks items that players have in their inventory during campaigns.
Only players (not GM) have inventory.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime

# ✅ Upewnij się, że importujesz MultiplayerCampaign, jeśli jest potrzebny do relationship
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
    
    # Relationships
    # ✅ POPRAWKA 1: Zmieniono "campaigns.id" na "multiplayer_campaigns.id" (lub na poprawną nazwę tabeli)
    campaign_id = Column(Integer, ForeignKey("multiplayer_campaigns.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    character_id = Column(Integer, ForeignKey("characters.id", ondelete="SET NULL"), nullable=True)
    
    # Item details
    item_name = Column(String(255), nullable=False)
    item_category = Column(String(50), nullable=False)  # weapons, armor, items, vehicles, droids
    item_image_url = Column(String(500), nullable=True)
    item_description = Column(String(1000), nullable=True)
    
    # Quantity and metadata
    quantity = Column(Integer, default=1, nullable=False)
    added_by_gm_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    notes = Column(String(500), nullable=True)  # GM can add notes
    
    # Relationships
    # ✅ POPRAWKA 2: Zmieniono "Campaign" na "MultiplayerCampaign"
    campaign = relationship("MultiplayerCampaign", back_populates="inventory_items")
    user = relationship("User", foreign_keys=[user_id])
    character = relationship("Character")
    added_by = relationship("User", foreign_keys=[added_by_gm_id])
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_inventory_campaign_user', 'campaign_id', 'user_id'),
        Index('idx_inventory_campaign', 'campaign_id'),
        Index('idx_inventory_user', 'user_id'),
    )
    
    def __repr__(self):
        return f"<PlayerInventory(id={self.id}, player={self.user_id}, item={self.item_name}, qty={self.quantity})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        # ... (bez zmian)