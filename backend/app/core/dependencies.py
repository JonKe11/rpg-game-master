# backend/app/core/dependencies.py
from functools import lru_cache
from typing import Generator
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# JWT imports with fallback
try:
    import jwt
    InvalidTokenError = jwt.exceptions.InvalidTokenError
except ImportError:
    import jwt
    InvalidTokenError = jwt.InvalidTokenError

from app.core.config import get_settings
from app.models.database import SessionLocal
from app.core.ai.adaptive_game_master import AdaptiveGameMaster
from app.services.session_storage import SessionStorage

settings = get_settings()
session_storage_instance = SessionStorage()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@lru_cache()
def get_game_master() -> AdaptiveGameMaster:
    return AdaptiveGameMaster(model_name=settings.ollama_model)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Get current user from JWT token"""
    from app.repositories.user_repository import UserRepository
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, 
            settings.secret_key, 
            algorithms=[settings.algorithm]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    
    user_repo = UserRepository(db)
    user = user_repo.get_by_username(username)
    if user is None:
        raise credentials_exception
    
    return user

def get_character_repository(db: Session = Depends(get_db)):
    from app.repositories.character_repository import CharacterRepository
    return CharacterRepository(db)

def get_session_repository(db: Session = Depends(get_db)):
    from app.repositories.session_repository import SessionRepository
    return SessionRepository(db)

def get_session_storage() -> SessionStorage:
    """Return SessionStorage instance (not dict!)"""
    return session_storage_instance  # ✅ POPRAWIONE

def get_game_master_service(
    game_master: AdaptiveGameMaster = Depends(get_game_master),
    storage: SessionStorage = Depends(get_session_storage)  # ✅ POPRAWIONE
):
    from app.services.game_master_service import GameMasterService
    return GameMasterService(game_master, storage)