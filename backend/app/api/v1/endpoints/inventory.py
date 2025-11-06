# backend/app/api/v1/inventory.py
"""
Inventory API Endpoints

Manages player inventory in multiplayer campaigns.
Only GM can add/remove items. Players can view their own inventory.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.campaign import MultiplayerCampaign
from app.models.player_inventory import PlayerInventory
from app.models.character import Character
from app.schemas.inventory import (
    InventoryItemResponse,
    InventoryItemCreate,
    InventoryItemUpdate,
    PlayerInventorySummary,
    CampaignPlayerInfo,
    AddItemToPlayerRequest
)

router = APIRouter()


def get_campaign_or_404(campaign_id: int, db: Session) -> MultiplayerCampaign:
    """Get campaign or raise 404"""
    campaign = db.query(MultiplayerCampaign).filter(
        MultiplayerCampaign.id == campaign_id
    ).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    return campaign


def check_is_gm(campaign: MultiplayerCampaign, user: User):
    """Check if user is GM, raise 403 if not"""
    if campaign.game_master_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only GM can perform this action"
        )


def check_is_participant(campaign: MultiplayerCampaign, user_id: int):
    """Check if user is participant in campaign"""
    participants = campaign.participants or []
    is_participant = any(p.get('user_id') == user_id for p in participants)
    
    if not is_participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a participant in this campaign"
        )


@router.get("/campaigns/{campaign_id}/players", response_model=List[CampaignPlayerInfo])
async def get_campaign_players(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of players in campaign with inventory counts.
    
    Available to all participants (GM and players).
    """
    campaign = get_campaign_or_404(campaign_id, db)
    check_is_participant(campaign, current_user.id)
    
    participants = campaign.participants or []
    players_info = []
    
    for participant in participants:
        user_id = participant.get('user_id')
        character_id = participant.get('character_id')
        
        # Get user info
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            continue
        
        # Get character info if exists
        character_name = None
        if character_id:
            character = db.query(Character).filter(Character.id == character_id).first()
            if character:
                character_name = character.name
        
        # Count inventory items
        inventory_count = db.query(PlayerInventory).filter(
            PlayerInventory.campaign_id == campaign_id,
            PlayerInventory.user_id == user_id
        ).count()
        
        players_info.append(CampaignPlayerInfo(
            user_id=user_id,
            username=user.username,
            character_id=character_id,
            character_name=character_name,
            role=participant.get('role', 'player'),
            ready=participant.get('ready', False),
            inventory_count=inventory_count
        ))
    
    return players_info


@router.get("/campaigns/{campaign_id}/inventory/{user_id}", response_model=PlayerInventorySummary)
async def get_player_inventory(
    campaign_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get player's inventory.
    
    Players can view their own inventory.
    GM can view any player's inventory.
    """
    campaign = get_campaign_or_404(campaign_id, db)
    check_is_participant(campaign, current_user.id)
    
    # Check permissions
    is_gm = campaign.game_master_id == current_user.id
    is_own_inventory = user_id == current_user.id
    
    if not (is_gm or is_own_inventory):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own inventory (or you must be GM)"
        )
    
    # Get player info
    player = db.query(User).filter(User.id == user_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    
    # Get character info
    participants = campaign.participants or []
    participant = next((p for p in participants if p.get('user_id') == user_id), None)
    
    character_id = None
    character_name = None
    if participant and participant.get('character_id'):
        character_id = participant['character_id']
        character = db.query(Character).filter(Character.id == character_id).first()
        if character:
            character_name = character.name
    
    # Get inventory items
    items = db.query(PlayerInventory).filter(
        PlayerInventory.campaign_id == campaign_id,
        PlayerInventory.user_id == user_id
    ).order_by(PlayerInventory.added_at.desc()).all()
    
    # Calculate stats
    total_items = sum(item.quantity for item in items)
    items_by_category = {}
    for item in items:
        category = item.item_category
        items_by_category[category] = items_by_category.get(category, 0) + item.quantity
    
    return PlayerInventorySummary(
        user_id=user_id,
        username=player.username,
        character_id=character_id,
        character_name=character_name,
        total_items=total_items,
        items_by_category=items_by_category,
        items=[InventoryItemResponse.from_orm(item) for item in items]
    )


@router.post("/campaigns/{campaign_id}/inventory", response_model=InventoryItemResponse)
async def add_item_to_player(
    campaign_id: int,
    request: AddItemToPlayerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add item to player's inventory.
    
    Only GM can add items.
    """
    campaign = get_campaign_or_404(campaign_id, db)
    check_is_gm(campaign, current_user)
    
    # Verify player is in campaign
    check_is_participant(campaign, request.player_user_id)
    
    # Get player's character_id from participants
    participants = campaign.participants or []
    participant = next((p for p in participants if p.get('user_id') == request.player_user_id), None)
    character_id = participant.get('character_id') if participant else None
    
    # Check if item already exists (to update quantity instead of creating duplicate)
    existing_item = db.query(PlayerInventory).filter(
        PlayerInventory.campaign_id == campaign_id,
        PlayerInventory.user_id == request.player_user_id,
        PlayerInventory.item_name == request.item_name
    ).first()
    
    if existing_item:
        # Update quantity
        existing_item.quantity += request.quantity
        db.commit()
        db.refresh(existing_item)
        return InventoryItemResponse.from_orm(existing_item)
    
    # Create new item
    new_item = PlayerInventory(
        campaign_id=campaign_id,
        user_id=request.player_user_id,
        character_id=character_id,
        item_name=request.item_name,
        item_category=request.item_category,
        item_image_url=request.item_image_url,
        item_description=request.item_description,
        quantity=request.quantity,
        added_by_gm_id=current_user.id,
        notes=request.notes
    )
    
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    
    return InventoryItemResponse.from_orm(new_item)


@router.patch("/campaigns/{campaign_id}/inventory/{item_id}", response_model=InventoryItemResponse)
async def update_inventory_item(
    campaign_id: int,
    item_id: int,
    update_data: InventoryItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update inventory item (quantity or notes).
    
    Only GM can update items.
    """
    campaign = get_campaign_or_404(campaign_id, db)
    check_is_gm(campaign, current_user)
    
    item = db.query(PlayerInventory).filter(
        PlayerInventory.id == item_id,
        PlayerInventory.campaign_id == campaign_id
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found"
        )
    
    # Update fields
    if update_data.quantity is not None:
        if update_data.quantity == 0:
            # If quantity is 0, delete the item
            db.delete(item)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail="Item removed (quantity = 0)"
            )
        item.quantity = update_data.quantity
    
    if update_data.notes is not None:
        item.notes = update_data.notes
    
    db.commit()
    db.refresh(item)
    
    return InventoryItemResponse.from_orm(item)


@router.delete("/campaigns/{campaign_id}/inventory/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inventory_item(
    campaign_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete inventory item.
    
    Only GM can delete items.
    """
    campaign = get_campaign_or_404(campaign_id, db)
    check_is_gm(campaign, current_user)
    
    item = db.query(PlayerInventory).filter(
        PlayerInventory.id == item_id,
        PlayerInventory.campaign_id == campaign_id
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found"
        )
    
    db.delete(item)
    db.commit()
    
    return None


@router.get("/campaigns/{campaign_id}/player/{user_id}/character")
async def get_player_character(
    campaign_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get player's character sheet.
    
    GM can view any player's character.
    Players can view their own character.
    """
    campaign = get_campaign_or_404(campaign_id, db)
    check_is_participant(campaign, current_user.id)
    
    # Check permissions
    is_gm = campaign.game_master_id == current_user.id
    is_own_character = user_id == current_user.id
    
    if not (is_gm or is_own_character):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only GM can view other players' characters"
        )
    
    # Get character_id from participants
    participants = campaign.participants or []
    participant = next((p for p in participants if p.get('user_id') == user_id), None)
    
    if not participant or not participant.get('character_id'):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player has no character assigned"
        )
    
    character_id = participant['character_id']
    character = db.query(Character).filter(Character.id == character_id).first()
    
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )
    
    # Return character data (adjust based on your Character model)
    return {
        'id': character.id,
        'name': character.name,
        'race': character.race,
        'class_type': character.class_type,
        'level': getattr(character, 'level', 1),
        'background': getattr(character, 'background', ''),
        'attributes': {
            'strength': getattr(character, 'strength', 10),
            'dexterity': getattr(character, 'dexterity', 10),
            'constitution': getattr(character, 'constitution', 10),
            'intelligence': getattr(character, 'intelligence', 10),
            'wisdom': getattr(character, 'wisdom', 10),
            'charisma': getattr(character, 'charisma', 10),
        },
        'skills': {
            'computer_use': getattr(character, 'computer_use', 0),
            'demolitions': getattr(character, 'demolitions', 0),
            'stealth': getattr(character, 'stealth', 0),
            'awareness': getattr(character, 'awareness', 0),
            'persuade': getattr(character, 'persuade', 0),
            'repair': getattr(character, 'repair', 0),
            'security': getattr(character, 'security', 0),
            'treat_injury': getattr(character, 'treat_injury', 0),
        },
        'homeworld': getattr(character, 'homeworld', None),
        'universe': getattr(character, 'universe', 'star_wars'),
    }