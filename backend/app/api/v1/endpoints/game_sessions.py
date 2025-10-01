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
from app.schemas.session import GameSessionResponse
from app.services.game_master_service import GameMasterService
from app.core.ai.adaptive_game_master import AdaptiveGameMaster

router = APIRouter()

@router.post("/start", response_model=Dict)
async def start_game_session(
    request: StartSessionRequest,
    db: Session = Depends(get_db),
    game_master: AdaptiveGameMaster = Depends(get_game_master),
    storage: dict = Depends(get_session_storage)
):
    """Start new game session"""
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
        game_master_id=1,  # TODO: from current user
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
        'session_id': session.id
    }
    
    # Start with Game Master
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

@router.post("/action", response_model=SessionActionResponse)
async def process_action(
    request: SessionActionRequest,
    db: Session = Depends(get_db),
    game_master: AdaptiveGameMaster = Depends(get_game_master),
    storage: dict = Depends(get_session_storage)
):
    """Process player action"""
    gm_service = GameMasterService(game_master, storage)
    
    try:
        response = gm_service.process_action(
            request.session_id,
            request.action
        )
        
        # Update session in DB
        session_repo = SessionRepository(db)
        session_repo.update_last_played(request.session_id)
        
        return SessionActionResponse(**response)
    except Exception as e:
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
    db: Session = Depends(get_db)
):
    """End game session"""
    session_repo = SessionRepository(db)
    session_repo.update(session_id, status="completed")
    
    return {"message": "Session ended", "session_id": session_id}


@router.post("/roll-dice")
async def roll_dice(
    dice_type: str = "d20"
):
    """Roll dice"""
    from app.core.ai.adaptive_game_master import AdaptiveGameMaster
    gm = AdaptiveGameMaster()
    result = gm.generate_dice_roll(dice_type)
    return result