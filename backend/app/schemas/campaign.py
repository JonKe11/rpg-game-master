# backend/app/schemas/campaign.py
"""
Pydantic schemas dla Campaign API
"""
from pydantic import BaseModel
from typing import Optional

class CampaignStartRequest(BaseModel):
    """Request do rozpoczęcia kampanii"""
    character_id: int
    title: Optional[str] = None
    campaign_length: str = "medium"  # short, medium, long
    
    class Config:
        schema_extra = {
            "example": {
                "character_id": 1,
                "title": "The Hero's Journey",
                "campaign_length": "medium"
            }
        }

class CampaignProgressResponse(BaseModel):
    """Response z progresem kampanii"""
    progress_percent: float
    current_beat: Optional[str]
    act: str
    turns_taken: int
    turns_total: int
    near_end: bool
    completed: bool