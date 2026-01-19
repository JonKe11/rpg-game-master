
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.dependencies import get_db, get_current_user
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserResponse
from app.models.user import User
from app.models.campaign import MultiplayerCampaign
from app.models.character import Character
from app.models.friendship import Friendship, FriendshipStatus
from sqlalchemy import or_

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/profile/me")
async def get_my_profile_full(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Pobiera pełne dane do profilu użytkownika"""
    
    
    characters = db.query(Character).filter(Character.owner_id == current_user.id).all()
    
    
    
    campaigns = db.query(MultiplayerCampaign).all()
    my_campaigns = []
    for c in campaigns:
        is_gm = c.game_master_id == current_user.id
        is_player = False
        if c.participants:
            for p in c.participants:
                if p.get('user_id') == current_user.id:
                    is_player = True
                    break
        
        if is_gm or is_player or c.creator_id == current_user.id:
            my_campaigns.append({
                "id": c.id,
                "title": c.title,
                "role": "GM" if is_gm else ("Creator" if c.creator_id == current_user.id else "Player"),
                "status": c.status.value
            })

    
    friends_count = db.query(Friendship).filter(
        or_(Friendship.sender_id == current_user.id, Friendship.receiver_id == current_user.id),
        Friendship.status == FriendshipStatus.ACCEPTED
    ).count()

    return {
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "joined_at": current_user.created_at
        },
        "stats": {
            "characters_count": len(characters),
            "campaigns_count": len(my_campaigns),
            "friends_count": friends_count
        },
        "characters": [{"id": c.id, "name": c.name, "level": c.level, "class": c.class_type, "race": c.race} for c in characters],
        "campaigns": my_campaigns
    }