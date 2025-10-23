# backend/app/api/v1/endpoints/multiplayer.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.orm.attributes import flag_modified

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.campaign import MultiplayerCampaign, CampaignStatus, ParticipantRole
from app.models.campaign_message import CampaignMessage, MessageType
from app.websocket import manager

router = APIRouter()

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class CampaignCreateRequest(BaseModel):
    title: str
    universe: str
    is_public: bool = True

class JoinCampaignRequest(BaseModel):
    character_id: int

class SendMessageRequest(BaseModel):
    message_type: str
    content: str
    character_id: int = None
    metadata: Dict = {}

# ============================================================================
# CAMPAIGN MANAGEMENT
# ============================================================================

@router.post("/campaigns/create")
async def create_campaign(
    request: CampaignCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new multiplayer campaign (lobby)"""
    
    campaign = MultiplayerCampaign(
        title=request.title,
        universe=request.universe,
        creator_id=current_user.id,
        is_public=request.is_public,
        status=CampaignStatus.LOBBY,
        participants=[]
    )
    
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    
    return {
        "campaign_id": campaign.id,
        "title": campaign.title,
        "status": campaign.status.value,
        "universe": campaign.universe
    }

@router.get("/campaigns/")
async def list_campaigns(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List available campaigns"""
    
    campaigns = db.query(MultiplayerCampaign).filter(
        (MultiplayerCampaign.is_public == True) | 
        (MultiplayerCampaign.creator_id == current_user.id)
    ).filter(
        MultiplayerCampaign.status.in_([CampaignStatus.LOBBY, CampaignStatus.ACTIVE, CampaignStatus.PAUSED])
    ).all()
    
    return [
        {
            "id": c.id,
            "title": c.title,
            "universe": c.universe,
            "status": c.status.value,
            "player_count": len(c.participants),
            "max_players": c.max_players,
            "has_gm": c.game_master_id is not None,
            "created_at": c.created_at.isoformat()
        }
        for c in campaigns
    ]

@router.get("/campaigns/{campaign_id}")
async def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get campaign details"""
    
    campaign = db.query(MultiplayerCampaign).filter(
        MultiplayerCampaign.id == campaign_id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return {
        "id": campaign.id,
        "title": campaign.title,
        "universe": campaign.universe,
        "status": campaign.status.value,
        "creator_id": campaign.creator_id,
        "game_master_id": campaign.game_master_id,
        "participants": campaign.participants,
        "current_location": campaign.current_location,
        "location_image_url": campaign.location_image_url,
        "max_players": campaign.max_players,
        "created_at": campaign.created_at.isoformat()
    }

@router.post("/campaigns/{campaign_id}/join")
async def join_campaign(
    campaign_id: int,
    request: JoinCampaignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Join campaign lobby"""
    
    campaign = db.query(MultiplayerCampaign).filter(
        MultiplayerCampaign.id == campaign_id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign.status != CampaignStatus.LOBBY:
        raise HTTPException(status_code=400, detail="Campaign already started")
    
    if len(campaign.participants) >= campaign.max_players:
        raise HTTPException(status_code=400, detail="Campaign is full")
    
    # Check if already joined - if yes, just return success
    if any(p["user_id"] == current_user.id for p in campaign.participants):
        return {"message": "Already in campaign"}
    
    # Add participant
    campaign.participants.append({
        "user_id": current_user.id,
        "username": current_user.username,
        "character_id": request.character_id,
        "role": ParticipantRole.PLAYER.value,
        "ready": False,
        "joined_at": datetime.now().isoformat()
    })
    
    flag_modified(campaign, "participants")
    
    db.commit()
    db.refresh(campaign)
    
    print(f"✅ User {current_user.username} joined campaign {campaign_id}")
    print(f"   Participants count: {len(campaign.participants)}")
    
    # Notify via WebSocket
    await manager.broadcast(campaign_id, {
        "type": "system",
        "content": f"{current_user.username} joined the campaign"
    })
    
    return {
        "message": "Joined successfully",
        "participants_count": len(campaign.participants)
    }

@router.post("/campaigns/{campaign_id}/toggle-ready")
async def toggle_ready(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Toggle ready status for current player"""
    
    campaign = db.query(MultiplayerCampaign).filter(
        MultiplayerCampaign.id == campaign_id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign.status != CampaignStatus.LOBBY:
        raise HTTPException(status_code=400, detail="Campaign already started")
    
    # Find participant
    participant = next((p for p in campaign.participants if p["user_id"] == current_user.id), None)
    if not participant:
        raise HTTPException(status_code=404, detail="Not in campaign")
    
    # ✅ DODANE: GM nie może toggle ready
    if participant.get("role") == ParticipantRole.GAME_MASTER.value:
        raise HTTPException(status_code=403, detail="Game Master is always ready")
    
    # Toggle ready
    participant["ready"] = not participant.get("ready", False)
    
    flag_modified(campaign, "participants")
    db.commit()
    db.refresh(campaign)
    
    # Check if all non-GM players ready
    players = [p for p in campaign.participants if p.get("role") != ParticipantRole.GAME_MASTER.value]
    all_ready = all(p.get("ready", False) for p in players) if players else False
    
    print(f"✅ User {current_user.username} ready status: {participant['ready']}")
    print(f"   All players ready: {all_ready}")
    
    # Broadcast via WebSocket
    status_text = "ready" if participant["ready"] else "not ready"
    await manager.broadcast(campaign_id, {
        "type": "system",
        "content": f"{current_user.username} is {status_text}"
    })
    
    return {
        "ready": participant["ready"],
        "all_ready": all_ready
    }

@router.post("/campaigns/{campaign_id}/assign-gm")
async def assign_game_master(
    campaign_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign Game Master role (only creator can do this)"""
    
    campaign = db.query(MultiplayerCampaign).filter(
        MultiplayerCampaign.id == campaign_id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only creator can assign GM")
    
    if campaign.status != CampaignStatus.LOBBY:
        raise HTTPException(status_code=400, detail="Can only assign GM in lobby")
    
    participant = next((p for p in campaign.participants if p["user_id"] == user_id), None)
    if not participant:
        raise HTTPException(status_code=404, detail="User not in campaign")
    
    campaign.game_master_id = user_id
    participant["role"] = ParticipantRole.GAME_MASTER.value
    participant["ready"] = True  # ✅ GM jest zawsze ready
    
    flag_modified(campaign, "participants")
    
    db.commit()
    db.refresh(campaign)
    
    print(f"✅ {participant['username']} assigned as GM (auto-ready)")
    
    await manager.broadcast(campaign_id, {
        "type": "system",
        "content": f"{participant['username']} is now the Game Master"
    })
    
    return {"message": "GM assigned"}

@router.post("/campaigns/{campaign_id}/start")
async def start_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start campaign (only GM can start)"""
    
    campaign = db.query(MultiplayerCampaign).filter(
        MultiplayerCampaign.id == campaign_id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign.game_master_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only GM can start campaign")
    
    if campaign.status != CampaignStatus.LOBBY:
        raise HTTPException(status_code=400, detail="Campaign already started")
    
    if not campaign.game_master_id:
        raise HTTPException(status_code=400, detail="No GM assigned")
    
    # ✅ Check if all non-GM players are ready
    if campaign.participants:
        players = [p for p in campaign.participants if p.get("role") != ParticipantRole.GAME_MASTER.value]
        if players:
            all_ready = all(p.get("ready", False) for p in players)
            if not all_ready:
                not_ready = [p["username"] for p in players if not p.get("ready", False)]
                raise HTTPException(
                    status_code=400, 
                    detail=f"Not all players ready. Waiting for: {', '.join(not_ready)}"
                )
    
    campaign.status = CampaignStatus.ACTIVE
    campaign.started_at = datetime.now()
    
    db.commit()
    
    await manager.broadcast(campaign_id, {
        "type": "system",
        "content": "Campaign has started! 🎲"
    })
    
    return {"message": "Campaign started"}

# ============================================================================
# MESSAGES
# ============================================================================

@router.get("/campaigns/{campaign_id}/messages")
async def get_messages(
    campaign_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get campaign message history"""
    
    messages = db.query(CampaignMessage).filter(
        CampaignMessage.campaign_id == campaign_id
    ).order_by(CampaignMessage.timestamp.desc()).limit(limit).all()
    
    return [
        {
            "id": m.id,
            "user_id": m.user_id,
            "character_id": m.character_id,
            "message_type": m.message_type.value,
            "content": m.content,
            "message_metadata": m.message_metadata,
            "timestamp": m.timestamp.isoformat()
        }
        for m in reversed(messages)
    ]

@router.delete("/campaigns/{campaign_id}")
async def delete_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete campaign (only creator can delete)"""
    
    campaign = db.query(MultiplayerCampaign).filter(
        MultiplayerCampaign.id == campaign_id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Only creator can delete
    if campaign.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only creator can delete campaign")
    
    # Only delete if in lobby
    if campaign.status != CampaignStatus.LOBBY:
        raise HTTPException(status_code=400, detail="Cannot delete active campaign")
    
    db.delete(campaign)
    db.commit()
    
    return {"message": "Campaign deleted", "campaign_id": campaign_id}

@router.post("/campaigns/{campaign_id}/messages")
async def send_message(
    campaign_id: int,
    request: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send message to campaign"""
    
    message = CampaignMessage(
        campaign_id=campaign_id,
        user_id=current_user.id,
        character_id=request.character_id,
        message_type=MessageType(request.message_type),
        content=request.content,
        message_metadata=request.metadata
    )
    
    db.add(message)
    db.commit()
    db.refresh(message)
    
    await manager.broadcast(campaign_id, {
        "type": request.message_type,
        "content": request.content,
        "user_id": current_user.id,
        "username": current_user.username,
        "character_id": request.character_id,
        "message_metadata": request.metadata,
        "timestamp": message.timestamp.isoformat()
    })
    
    return {"message_id": message.id}


# ============================================================================
# LOCATION SYSTEM
# ============================================================================

@router.post("/campaigns/{campaign_id}/location")
async def change_location(
    campaign_id: int,
    location_name: str,
    location_image_url: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Change campaign location (only GM can do this)"""
    
    campaign = db.query(MultiplayerCampaign).filter(
        MultiplayerCampaign.id == campaign_id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Only GM can change location
    if campaign.game_master_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only GM can change location")
    
    # Update location
    campaign.current_location = location_name
    if location_image_url:
        campaign.location_image_url = location_image_url
    
    db.commit()
    db.refresh(campaign)
    
    print(f"📍 Location changed to: {location_name}")
    
    # Broadcast to all players
    await manager.broadcast(campaign_id, {
        "type": "location_change",
        "location": location_name,
        "location_image_url": location_image_url,
        "timestamp": datetime.now().isoformat()
    })
    
    # Also send as system message
    await manager.broadcast(campaign_id, {
        "type": "system",
        "content": f"📍 Location changed to: {location_name}",
        "timestamp": datetime.now().isoformat()
    })
    
    return {
        "message": "Location changed",
        "location": location_name,
        "location_image_url": location_image_url
    }

@router.get("/campaigns/{campaign_id}/location")
async def get_current_location(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current campaign location"""
    
    campaign = db.query(MultiplayerCampaign).filter(
        MultiplayerCampaign.id == campaign_id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return {
        "location": campaign.current_location,
        "location_image_url": campaign.location_image_url
    }