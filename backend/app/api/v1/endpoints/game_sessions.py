# backend/app/api/v1/endpoints/game_sessions.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List

from app.core.dependencies import get_db, get_game_master, get_session_storage
from app.repositories.session_repository import SessionRepository
from app.repositories.character_repository import CharacterRepository
from app.schemas.session import StartSessionRequest
from app.schemas.game_session import (
    SessionActionRequest,
    SessionActionResponse,
)
from app.schemas.campaign import CampaignStartRequest  # 🆕 NOWY
from app.schemas.session import GameSessionResponse
from app.services.game_master_service import GameMasterService
from app.services.story_aware_game_master import StoryAwareGameMaster  # 🆕 NOWY
from app.core.ai.adaptive_game_master import AdaptiveGameMaster
from app.services.session_storage import SessionStorage

router = APIRouter()

@router.post("/start", response_model=Dict)
async def start_game_session(
    request: StartSessionRequest,
    db: Session = Depends(get_db),
    game_master: AdaptiveGameMaster = Depends(get_game_master),
    storage: SessionStorage = Depends(get_session_storage)
):
    """
    Start new game session (legacy - without campaign structure)
    Use /start-campaign for full story arc experience
    """
    # Get character
    char_repo = CharacterRepository(db)
    character = char_repo.get(request.character_id)
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Create session in database
    session_repo = SessionRepository(db)
    session = session_repo.create(
        title=request.title or f"Adventure of {character.name}",
        universe=character.universe,
        status="active",
        game_master_id=1,
        participants=[character.id]
    )
    
    # Prepare character data
    character_data = {
        'id': character.id,
        'name': character.name,
        'universe': character.universe,
        'race': character.race,
        'class_type': character.class_type,
        'level': character.level,
        'homeworld': getattr(character, 'homeworld', None),
        'session_id': session.id
    }
    
    # Start with basic Game Master (no campaign)
    gm_service = GameMasterService(game_master, storage)
    intro = gm_service.start_session(
        session.id,
        character_data,
        character.universe
    )
    
    return {
        'session_id': session.id,
        'character': character_data,
        'intro': intro
    }

@router.post("/start-campaign", response_model=Dict)
async def start_campaign_session(
    request: CampaignStartRequest,
    db: Session = Depends(get_db),
    game_master: AdaptiveGameMaster = Depends(get_game_master),
    storage: SessionStorage = Depends(get_session_storage)
):
    """
    🆕 Start new CAMPAIGN with full story arc
    - AI plans campaign structure
    - Story beats tracking
    - RAG with wiki knowledge
    - Canon validation
    """
    # Get character
    char_repo = CharacterRepository(db)
    character = char_repo.get(request.character_id)
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Create session in database
    session_repo = SessionRepository(db)
    session = session_repo.create(
        title=request.title or f"Campaign: {character.name}",
        universe=character.universe,
        status="active",
        game_master_id=1,
        participants=[character.id]
    )
    
    # Prepare character data
    character_data = {
        'id': character.id,
        'name': character.name,
        'universe': character.universe,
        'race': character.race,
        'class_type': character.class_type,
        'level': character.level,
        'description': character.description,
        'homeworld': getattr(character, 'homeworld', None),
        'session_id': session.id
    }
    
    # Start with Story-Aware Game Master
    story_gm = StoryAwareGameMaster(game_master, storage)
    
    # Check if session already has intro (for consistency)
    existing_intro = storage.get_intro(session.id)
    existing_campaign = storage.get_campaign(session.id)
    
    if existing_intro and existing_campaign:
        print(f"♻️ Reusing existing campaign for session {session.id}")
        return {
            'session_id': session.id,
            'character': character_data,
            'intro': existing_intro['message'],
            'campaign': {
                'title': existing_campaign.title,
                'theme': existing_campaign.main_theme,
                'progress': existing_campaign.get_progress_percentage(),
                'current_beat': existing_campaign.get_current_beat().title if existing_campaign.get_current_beat() else None,
                'estimated_turns': existing_campaign.total_estimated_turns
            },
            'type': 'campaign'
        }
    
    # Generate NEW campaign
    try:
        result = story_gm.start_campaign(
            session.id,
            character_data,
            character.universe,
            campaign_length=request.campaign_length
        )
        
        return {
            'session_id': session.id,
            'character': character_data,
            'intro': result['message'],
            'campaign': result.get('campaign', {}),
            'type': 'campaign'
        }
    except Exception as e:
        print(f"❌ Campaign start error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to start campaign: {str(e)}")

@router.post("/action", response_model=SessionActionResponse)
async def process_action(
    request: SessionActionRequest,
    db: Session = Depends(get_db),
    game_master: AdaptiveGameMaster = Depends(get_game_master),
    storage: SessionStorage = Depends(get_session_storage)
):
    """
    Process player action
    Automatically uses story-aware GM if campaign exists
    """
    # Check if this is a campaign session
    campaign = storage.get_campaign(request.session_id)
    
    if campaign:
        # Use story-aware GM
        story_gm = StoryAwareGameMaster(game_master, storage)
        
        try:
            response = story_gm.process_action_with_story(
                request.session_id,
                request.action
            )
            
            # Update session in DB
            session_repo = SessionRepository(db)
            session_repo.update_last_played(request.session_id)
            
            return SessionActionResponse(**response)
        except Exception as e:
            print(f"❌ Story action error: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))
    else:
        # Use basic GM (legacy)
        gm_service = GameMasterService(game_master, storage)
        
        try:
            response = gm_service.process_action(
                request.session_id,
                request.action
            )
            
            session_repo = SessionRepository(db)
            session_repo.update_last_played(request.session_id)
            
            return SessionActionResponse(**response)
        except Exception as e:
            print(f"❌ Action error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

@router.get("/active", response_model=List[GameSessionResponse])
async def get_active_sessions(
    db: Session = Depends(get_db)
):
    """Get active game sessions"""
    session_repo = SessionRepository(db)
    return session_repo.get_active_sessions()

@router.post("/{session_id}/end")
async def end_session(
    session_id: int,
    db: Session = Depends(get_db),
    storage: SessionStorage = Depends(get_session_storage)
):
    """End game session and cleanup"""
    session_repo = SessionRepository(db)
    session_repo.update(session_id, status="completed")
    
    # Cleanup storage
    storage.delete_context(session_id)
    storage.delete_campaign(session_id)
    
    return {"message": "Session ended", "session_id": session_id}

@router.get("/{session_id}/campaign")
async def get_campaign_status(
    session_id: int,
    storage: SessionStorage = Depends(get_session_storage)
):
    """🆕 Get campaign progress and status"""
    campaign = storage.get_campaign(session_id)
    
    if not campaign:
        raise HTTPException(status_code=404, detail="No campaign found for this session")
    
    current_beat = campaign.get_current_beat()
    
    return {
        'title': campaign.title,
        'theme': campaign.main_theme,
        'antagonist': campaign.main_antagonist,
        'goal': campaign.final_goal,
        'progress': {
            'percent': round(campaign.get_progress_percentage(), 1),
            'turn': campaign.current_turn,
            'total_turns': campaign.total_estimated_turns,
            'act': campaign.current_act,
            'near_end': campaign.is_near_end()
        },
        'current_beat': {
            'title': current_beat.title if current_beat else None,
            'description': current_beat.description if current_beat else None,
            'progress': f"{current_beat.actual_turns_taken}/{current_beat.estimated_turns}" if current_beat else None
        },
        'completed_beats': len(campaign.completed_beats),
        'total_beats': len(campaign.beats)
    }

@router.post("/roll-dice")
async def roll_dice(
    dice_type: str = "d20"
):
    """Roll dice"""
    from app.core.ai.adaptive_game_master import AdaptiveGameMaster
    gm = AdaptiveGameMaster()
    result = gm.generate_dice_roll(dice_type)
    return result