# backend/app/schemas/inventory.py
"""
Inventory Schemas

Pydantic models for player inventory validation and serialization.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class InventoryItemBase(BaseModel):
    """Base schema for inventory items"""
    item_name: str = Field(..., min_length=1, max_length=255)
    item_category: str = Field(..., pattern="^(weapons|armor|items|vehicles|droids)$")
    item_image_url: Optional[str] = Field(None, max_length=500)
    item_description: Optional[str] = Field(None, max_length=1000)
    quantity: int = Field(default=1, ge=1, le=999)
    notes: Optional[str] = Field(None, max_length=500)


class InventoryItemCreate(InventoryItemBase):
    """Schema for creating new inventory item"""
    user_id: int = Field(..., description="ID of player receiving the item")
    character_id: Optional[int] = None


class InventoryItemUpdate(BaseModel):
    """Schema for updating inventory item"""
    quantity: Optional[int] = Field(None, ge=0, le=999)
    notes: Optional[str] = Field(None, max_length=500)


class InventoryItemResponse(InventoryItemBase):
    """Schema for inventory item response"""
    id: int
    campaign_id: int
    user_id: int
    character_id: Optional[int]
    added_by_gm_id: Optional[int]
    added_at: datetime
    
    class Config:
        from_attributes = True


class PlayerInventorySummary(BaseModel):
    """Summary of player's inventory"""
    user_id: int
    username: str
    character_id: Optional[int]
    character_name: Optional[str]
    total_items: int
    items_by_category: dict[str, int]
    items: list[InventoryItemResponse]


class CampaignPlayerInfo(BaseModel):
    """Info about player in campaign for GM panel"""
    user_id: int
    username: str
    character_id: Optional[int]
    character_name: Optional[str]
    role: str
    ready: bool
    inventory_count: int


class AddItemToPlayerRequest(BaseModel):
    """Request to add item to player's inventory"""
    player_user_id: int = Field(..., description="User ID of player receiving item")
    item_name: str = Field(..., min_length=1, max_length=255)
    item_category: str = Field(..., pattern="^(weapons|armor|items|vehicles|droids)$")
    item_image_url: Optional[str] = Field(None, max_length=500)
    item_description: Optional[str] = Field(None, max_length=1000)
    quantity: int = Field(default=1, ge=1, le=999)
    notes: Optional[str] = None