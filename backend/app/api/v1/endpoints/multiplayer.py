
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.orm.attributes import flag_modified
import random
from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.campaign import MultiplayerCampaign, CampaignStatus, ParticipantRole
from app.models.campaign_message import CampaignMessage, MessageType
from app.websocket import manager
from app.models.friendship import Friendship, FriendshipStatus
router = APIRouter()





class CampaignCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None  
    universe: str
    is_public: bool = True


class JoinCampaignRequest(BaseModel):
    character_id: int


class SendMessageRequest(BaseModel):
    message_type: str
    content: str = ""
    
    character_id: Optional[int] = None 
    metadata: Dict[str, Any] = {}
    dice_type: Optional[int] = None
    dice_count: int = 1
    modifier: int = 0

class UpdateMessageRequest(BaseModel):
    """Request do aktualizacji wiadomości (np. stanu walki)"""
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    




@router.post("/campaigns/create")
async def create_campaign(
    request: CampaignCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Tworzy nową kampanię (lobby)"""
    
    campaign = MultiplayerCampaign(
        title=request.title,
        description=request.description,
        universe=request.universe,
        creator_id=current_user.id,
        is_public=request.is_public,
        status=CampaignStatus.LOBBY,
        participants=[],
        spawned_npcs=[]  
    )
    
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    
    return {
        "campaign_id": campaign.id,
        "title": campaign.title,
        "description": campaign.description,
        "status": campaign.status.value,
        "universe": campaign.universe
    }


@router.get("/campaigns/")
async def list_campaigns(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Zwraca kampanie:
    1. Publiczne
    2. Prywatne, których jestem twórcą
    3. Prywatne, stworzone przez moich znajomych
    """
    from app.models.friendship import Friendship, FriendshipStatus
    from sqlalchemy import or_, and_

    
    friends_ships = db.query(Friendship).filter(
        or_(Friendship.sender_id == current_user.id, Friendship.receiver_id == current_user.id),
        Friendship.status == FriendshipStatus.ACCEPTED
    ).all()
    
    friend_ids = []
    for f in friends_ships:
        fid = f.receiver_id if f.sender_id == current_user.id else f.sender_id
        friend_ids.append(fid)
    
    
    campaigns = db.query(MultiplayerCampaign).filter(
        or_(
            MultiplayerCampaign.is_public == True,                 
            MultiplayerCampaign.creator_id == current_user.id,     
            MultiplayerCampaign.creator_id.in_(friend_ids)         
        )
    ).filter(
        MultiplayerCampaign.status.in_([CampaignStatus.LOBBY, CampaignStatus.ACTIVE, CampaignStatus.PAUSED])
    ).all()
    
    return [
        {
            "id": c.id,
            "title": c.title,
            "description": c.description,
            "universe": c.universe,
            "status": c.status.value,
            "player_count": len(c.participants or []),
            "max_players": c.max_players,
            "has_gm": c.game_master_id is not None,
            "created_at": c.created_at.isoformat(),
            "participant_ids": [p.get("user_id") for p in (c.participants or [])],
            "creator_id": c.creator_id,
            "is_friend_campaign": c.creator_id in friend_ids,
            "is_public": c.is_public
        }
        for c in campaigns
    ]


@router.get("/campaigns/{campaign_id}")
async def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Pobiera szczegóły kampanii"""
    
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
        "participants": campaign.participants or [],
        "current_location": campaign.current_location,
        "location_image_url": campaign.location_image_url,
        "max_players": campaign.max_players,
        "created_at": campaign.created_at.isoformat(),
        
        "spawned_npcs": campaign.spawned_npcs or []
    }


@router.post("/campaigns/{campaign_id}/join")
async def join_campaign(
    campaign_id: int,
    request: JoinCampaignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dołącz do lobby lub wznów sesję"""
    
    campaign = db.query(MultiplayerCampaign).filter(
        MultiplayerCampaign.id == campaign_id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    participants = campaign.participants or []
    participant = next((p for p in participants if p.get("user_id") == current_user.id), None)

    
    if campaign.status == CampaignStatus.LOBBY:
        if participant:
            return {"message": "Already in lobby", "status": "joined"}
        
        if len(participants) >= campaign.max_players:
            raise HTTPException(status_code=400, detail="Campaign is full")
        
        
        participants.append({
            "user_id": current_user.id,
            "username": current_user.username,
            "character_id": request.character_id,
            "role": ParticipantRole.PLAYER.value,
            "ready": False,
            "joined_at": datetime.now().isoformat()
        })
        campaign.participants = participants
        flag_modified(campaign, "participants")
        
        await manager.broadcast(campaign_id, {
            "type": "system",
            "content": f"{current_user.username} joined the lobby"
        })

    
    elif campaign.status in [CampaignStatus.ACTIVE, CampaignStatus.PAUSED]:
        if not participant:
            raise HTTPException(status_code=403, detail="Campaign is in progress and you are not a participant")
        
        
        if participant.get("character_id") != request.character_id:
            raise HTTPException(status_code=403, detail="You must join with the same character you started with")
        
        
        if campaign.status == CampaignStatus.PAUSED and campaign.game_master_id == current_user.id:
            campaign.status = CampaignStatus.LOBBY
            await manager.broadcast(campaign_id, {
                "type": "system",
                "content": "The Game Master has returned. Session is resuming in lobby..."
            })

    db.commit()
    db.refresh(campaign)
    
    return {
        "message": "Joined successfully",
        "status": campaign.status.value
    }


@router.post("/campaigns/{campaign_id}/toggle-ready")
async def toggle_ready(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    campaign = db.query(MultiplayerCampaign).filter(MultiplayerCampaign.id == campaign_id).first()
    if not campaign: raise HTTPException(404, "Campaign not found")
    if campaign.status != CampaignStatus.LOBBY: raise HTTPException(400, "Campaign already started")
    
    participant = next((p for p in (campaign.participants or []) if p["user_id"] == current_user.id), None)
    if not participant: raise HTTPException(404, "Not in campaign")
    if participant.get("role") == ParticipantRole.GAME_MASTER.value: raise HTTPException(403, "Game Master is always ready")
    
    participant["ready"] = not participant.get("ready", False)
    flag_modified(campaign, "participants")
    db.commit()
    
    await manager.broadcast(campaign_id, {"type": "system", "content": f"{current_user.username} is {'ready' if participant['ready'] else 'not ready'}"})
    return {"ready": participant["ready"]}


@router.post("/campaigns/{campaign_id}/assign-gm")
async def assign_game_master(
    campaign_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    campaign = db.query(MultiplayerCampaign).filter(MultiplayerCampaign.id == campaign_id).first()
    if not campaign: raise HTTPException(404, "Campaign not found")
    if campaign.creator_id != current_user.id: raise HTTPException(403, "Only creator can assign GM")
    if campaign.status != CampaignStatus.LOBBY: raise HTTPException(400, "Can only assign GM in lobby")
    
    participant = next((p for p in (campaign.participants or []) if p["user_id"] == user_id), None)
    if not participant: raise HTTPException(404, "User not in campaign")
    
    campaign.game_master_id = user_id
    participant["role"] = ParticipantRole.GAME_MASTER.value
    participant["ready"] = True
    flag_modified(campaign, "participants")
    db.commit()
    
    await manager.broadcast(campaign_id, {"type": "system", "content": f"{participant['username']} is now the Game Master"})
    return {"message": "GM assigned"}


@router.post("/campaigns/{campaign_id}/start")
async def start_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Startuje z LOBBY lub PAUSED"""
    campaign = db.query(MultiplayerCampaign).filter(MultiplayerCampaign.id == campaign_id).first()
    if not campaign: raise HTTPException(404, "Campaign not found")
    if campaign.game_master_id != current_user.id: raise HTTPException(403, "Only GM can start campaign")
    
    if campaign.status not in [CampaignStatus.LOBBY, CampaignStatus.PAUSED]:
        raise HTTPException(status_code=400, detail=f"Campaign already {campaign.status.value}")
    
    if not campaign.game_master_id: raise HTTPException(400, "No GM assigned")
    
    players = [p for p in (campaign.participants or []) if p.get("role") != ParticipantRole.GAME_MASTER.value]
    
    
    if campaign.status == CampaignStatus.LOBBY:
        if not players: raise HTTPException(400, "Need at least one player to start")
        all_ready = all(p.get("ready", False) for p in players)
        if not all_ready:
            not_ready = [p["username"] for p in players if not p.get("ready", False)]
            raise HTTPException(400, f"Waiting for: {', '.join(not_ready)}")
    
    campaign.status = CampaignStatus.ACTIVE
    campaign.started_at = datetime.now()
    db.commit()
    
    await manager.broadcast(campaign_id, {"type": "system", "content": "Campaign has started! 🎲"})
    return {"message": "Campaign started"}


@router.post("/campaigns/{campaign_id}/pause")
async def pause_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Pauzuje sesję (tylko GM)"""
    campaign = db.query(MultiplayerCampaign).filter(MultiplayerCampaign.id == campaign_id).first()
    if not campaign: raise HTTPException(404, "Campaign not found")
    if campaign.game_master_id != current_user.id: raise HTTPException(403, "Only GM can pause campaign")
    
    campaign.status = CampaignStatus.PAUSED
    campaign.last_activity = datetime.now()
    db.commit()
    
    
    await manager.broadcast(campaign_id, {
        "type": "session_paused",
        "content": "The Game Master has paused the session. Returning to lobby..."
    })
    
    return {"message": "Campaign paused"}


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
    
    if campaign.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only creator can delete campaign")
    
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
    """
    Send message to campaign.
    Handles dice rolls and special types like npc_spawn.
    """
    print(f"📩 Otrzymano wiadomość typu: {request.message_type}")  
    
    final_content = request.content
    final_metadata = request.metadata or {}
    
    
    try:
        final_type = MessageType(request.message_type)
    except ValueError:
        
        final_type = MessageType.PLAYER_ACTION

    
    
    
    if request.message_type == 'npc_spawn':
        print("👤 Wykryto spawnowanie NPC! (Logic executing...)")
        
        
        
        final_type = MessageType.GM_EVENT 
        final_metadata['original_type'] = 'npc_spawn'
        
        campaign = db.query(MultiplayerCampaign).filter(MultiplayerCampaign.id == campaign_id).first()
        if campaign and 'npc' in final_metadata:
            spawned_npc = final_metadata['npc']
            print(f"📝 Zapisywanie NPC: {spawned_npc.get('name')}")
            
            if 'id' not in spawned_npc:
                spawned_npc['id'] = f"npc_{int(datetime.now().timestamp())}_{random.randint(100,999)}"
            
            
            current_npcs = list(campaign.spawned_npcs or [])
            current_npcs.append(spawned_npc)
            campaign.spawned_npcs = current_npcs
            flag_modified(campaign, "spawned_npcs")
            db.commit()
            print("✅ NPC zapisany w bazie.")

    elif request.message_type == 'combat_update':
        final_type = MessageType.GM_EVENT
        final_metadata['original_type'] = 'combat_update'

    
    if request.message_type == "dice_roll":
        if not request.dice_type:
            raise HTTPException(status_code=400, detail="Dice type required")
        rolls = [random.randint(1, request.dice_type) for _ in range(request.dice_count)]
        total = sum(rolls) + request.modifier
        
        
        try:
            final_type = MessageType.DICE_ROLL_RESULT
        except (ValueError, AttributeError):
            final_type = MessageType.SYSTEM 
        
        reason = request.metadata.get("reason", "")
        reason_str = f" ({reason})" if reason else ""
        roll_str = ", ".join(map(str, rolls))
        mod_str = f"+{request.modifier}" if request.modifier > 0 else (str(request.modifier) if request.modifier < 0 else "")
        final_content = f"rolled {request.dice_count}d{request.dice_type}{mod_str}{reason_str}: [{roll_str}] = {total}"
        final_metadata.update({"rolls": rolls, "total": total, "modifier": request.modifier, "dice_type": request.dice_type})

    
    message = CampaignMessage(
        campaign_id=campaign_id,
        user_id=current_user.id,
        character_id=request.character_id,
        message_type=final_type,
        content=final_content,
        message_metadata=final_metadata
    )
    
    db.add(message)
    db.commit()
    db.refresh(message)
    
    
    broadcast_type = request.message_type if request.message_type in ['npc_spawn', 'combat_update'] else message.message_type.value

    await manager.broadcast(campaign_id, {
        "id": message.id,
        "type": broadcast_type,
        "content": message.content,
        "user_id": current_user.id,
        "username": current_user.username,
        "character_id": request.character_id,
        "message_metadata": message.message_metadata,
        "timestamp": message.timestamp.isoformat()
    })
    
    return {"message_id": message.id}


@router.put("/campaigns/{campaign_id}/messages/{message_id}")
async def update_message(
    campaign_id: int,
    message_id: int,
    request: UpdateMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ✅ NOWY ENDPOINT: Aktualizuje wiadomość (np. zmianę tury w walce).
    Tylko GM może edytować wiadomości systemowe/eventowe.
    """
    message = db.query(CampaignMessage).filter(
        CampaignMessage.id == message_id,
        CampaignMessage.campaign_id == campaign_id
    ).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
        
    campaign = db.query(MultiplayerCampaign).filter(MultiplayerCampaign.id == campaign_id).first()
    
    
    
    is_combat_update = message.message_metadata and message.message_metadata.get('original_type') == 'combat_update'
    
    if campaign.game_master_id != current_user.id and not is_combat_update:
        raise HTTPException(status_code=403, detail="Only GM can update campaign messages")

    
    if request.content is not None:
        message.content = request.content
    if request.metadata is not None:
        message.message_metadata = request.metadata
        flag_modified(message, "message_metadata")
        
    db.commit()
    
    
    
    original_type = message.message_metadata.get('original_type') or message.message_type.value
    
    await manager.broadcast(campaign_id, {
        "type": "message_update",
        "id": message.id,
        "original_type": original_type,
        "content": message.content,
        "message_metadata": message.message_metadata,
        "timestamp": datetime.now().isoformat()
    })
    
    return {"success": True}






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
    
    if campaign.game_master_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only GM can change location")
    
    
    campaign.current_location = location_name
    if location_image_url:
        campaign.location_image_url = location_image_url
    
    db.commit()
    db.refresh(campaign)
    
    print(f"📍 Location changed to: {location_name}")
    
    
    await manager.broadcast(campaign_id, {
        "type": "location_change",
        "location": location_name,
        "location_image_url": location_image_url,
        "timestamp": datetime.now().isoformat()
    })
    
    
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