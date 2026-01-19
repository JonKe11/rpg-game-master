
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from datetime import datetime
from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.repositories.session_repository import SessionRepository
from app.repositories.character_repository import CharacterRepository
from app.services.game_master_service import GameMasterService
from app.schemas.session import StartSessionRequest, GameSessionResponse
from app.schemas.game_session import SessionActionRequest, SessionActionResponse
from app.schemas.campaign import CampaignStartRequest

router = APIRouter()

@router.post("/start", response_model=Dict)
async def start_game_session(
    request: StartSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Rozpoczyna nową sesję z Agentem AI (Stateful RAG Agent).
    Tworzy sesję w bazie i generuje wprowadzenie fabularne.
    """
    
    char_repo = CharacterRepository(db)
    character = char_repo.get(request.character_id)
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    
    session_repo = SessionRepository(db)
    session = session_repo.create(
        title=request.title or f"Przygoda: {character.name}",
        universe=character.universe,
        status="active",
        game_master_id=current_user.id,
        participants=[{
            "character_id": character.id, 
            "name": character.name,
            "race": character.race,
            "class": character.class_type
        }]
    )
    
    
    
    gm_service = GameMasterService(db)
    
    try:
        
        
        intro_prompt = (
            "[SYSTEM]: Rozpocznij nową przygodę. "
            f"Postać gracza: {character.name} (Rasa: {character.race}, Klasa: {character.class_type}). "
            "Opisz klimatyczne miejsce startowe pasujące do uniwersum i tej postaci. "
            "Zakończ pytaniem co gracz chce zrobić."
        )
        
        
        intro_response = gm_service.process_player_input(
            session_id=session.id,
            user_input=intro_prompt,
            user_name="System"
        )
        
        return {
            'session_id': session.id,
            'intro': intro_response['message'],
            'game_state': intro_response.get('game_state', {}),
            'character': {
                'id': character.id,
                'name': character.name
            }
        }
    except Exception as e:
        print(f"❌ Start Session Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")


@router.post("/start-campaign", response_model=Dict)
async def start_campaign_session(
    request: CampaignStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Uruchamia tryb kampanii. W nowej architekturze RAG Agent obsługuje
    zarówno "zwykłe" sesje jak i kampanie w ten sam, stanowy sposób.
    """
    
    session_request = StartSessionRequest(
        character_id=request.character_id,
        title=request.title,
        universe="star_wars"  
    )
    return await start_game_session(session_request, db, current_user)


@router.post("/action", response_model=SessionActionResponse)
async def process_action(
    request: SessionActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Przetwarza akcję gracza.
    """
    gm_service = GameMasterService(db)
    
    try:
        print(f"➡️ Processing action for session {request.session_id}: {request.action}") 
        
        response_data = gm_service.process_player_input(
            session_id=request.session_id,
            user_input=request.action,
            user_name=current_user.username
        )
        
        current_location = None
        game_state = response_data.get('game_state')
        if game_state and isinstance(game_state, dict):
            current_location = game_state.get('current_location')

        return SessionActionResponse(
            message=response_data['message'],
            type=response_data['type'],
            location=current_location,
            timestamp=datetime.now(), 
            narrative_style="agentic",
            choices=[],
            effects=[]
        )
        
    except ValueError as e:
        
        print(f"❌ ValueError in process_action: {e}")
        import traceback
        traceback.print_exc()
        
        if "Session not found" in str(e):
            raise HTTPException(status_code=404, detail="Session not found")
        else:
            raise HTTPException(status_code=500, detail=f"Internal Value Error: {str(e)}")
            
    except Exception as e:
        print(f"❌ Agent Action Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active", response_model=List[GameSessionResponse])
async def get_active_sessions(
    db: Session = Depends(get_db)
):
    """Pobiera listę aktywnych sesji"""
    session_repo = SessionRepository(db)
    return session_repo.get_active_sessions()


@router.post("/{session_id}/end")
async def end_session(
    session_id: int,
    db: Session = Depends(get_db)
):
    """Kończy sesję (oznacza jako completed)"""
    session_repo = SessionRepository(db)
    session_repo.update(session_id, status="completed")
    return {"message": "Session ended", "session_id": session_id}


@router.post("/roll-dice")
async def roll_dice(
    dice_type: str = "d20"
):
    """
    Pomocniczy endpoint do rzutów kośćmi (np. dla przycisku na frontendzie).
    """
    import random
    try:
        sides = int(dice_type.replace('d', ''))
        result = random.randint(1, sides)
        return {
            "dice": dice_type,
            "result": result,
            "critical": "success" if result == sides and sides == 20 else ("failure" if result == 1 and sides == 20 else None),
            "message": f"Rolled {dice_type}: {result}"
        }
    except ValueError:
         raise HTTPException(status_code=400, detail="Invalid dice type")