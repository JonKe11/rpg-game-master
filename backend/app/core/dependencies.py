# backend/app/core/dependencies.py
from functools import lru_cache
from typing import Generator
from sqlalchemy.orm import Session
from fastapi import Depends
from app.services.session_storage import SessionStorage
from app.core.config import get_settings
from app.models.database import SessionLocal
from app.core.ai.adaptive_game_master import AdaptiveGameMaster

settings = get_settings()

# Single source of truth - jedna instancja SessionStorage
session_storage_instance = SessionStorage()

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@lru_cache()
def get_game_master() -> AdaptiveGameMaster:
    return AdaptiveGameMaster(model_name=settings.ollama_model)

# TYMCZASOWA WERSJA BEZ JWT
async def get_current_user(db: Session = Depends(get_db)):
    """Tymczasowy mock user dla testów"""
    from app.models.user import User
    mock_user = User(
        id=1, 
        username="testuser",
        email="test@example.com",
        hashed_password="hashed",
        is_active=True
    )
    return mock_user

def get_character_repository(db: Session = Depends(get_db)):
    from app.repositories.character_repository import CharacterRepository
    return CharacterRepository(db)

def get_session_repository(db: Session = Depends(get_db)):
    from app.repositories.session_repository import SessionRepository
    return SessionRepository(db)

def get_session_storage() -> SessionStorage:
    """Zwraca instancję SessionStorage - FIX: teraz zwraca instancję zamiast dict"""
    return session_storage_instance

def get_game_master_service(
    game_master: AdaptiveGameMaster = Depends(get_game_master),
    storage: SessionStorage = Depends(get_session_storage)
):
    from app.services.game_master_service import GameMasterService
    return GameMasterService(game_master, storage)