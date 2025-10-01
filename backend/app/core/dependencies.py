# # backend/app/core/dependencies.py
# from functools import lru_cache
# from typing import Generator, Optional
# from sqlalchemy.orm import Session
# from fastapi import Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer

# # ZMIEŃ importy JWT
# import jwt  # Z PyJWT
# from jwt.exceptions import InvalidTokenError

# from app.core.config import get_settings
# from app.models.database import SessionLocal
# from app.core.ai.adaptive_game_master import AdaptiveGameMaster

# settings = get_settings()
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# def get_db() -> Generator[Session, None, None]:
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# session_storage = {}

# def get_session_storage():
#     return session_storage

# @lru_cache()
# def get_game_master() -> AdaptiveGameMaster:
#     return AdaptiveGameMaster(model_name=settings.ollama_model)

# async def get_current_user(
#     token: str = Depends(oauth2_scheme),
#     db: Session = Depends(get_db)
# ):
#     """Get current user from JWT token"""
#     from app.repositories.user_repository import UserRepository
    
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
    
#     try:
#         payload = jwt.decode(
#             token, 
#             settings.secret_key, 
#             algorithms=[settings.algorithm]
#         )
#         username: str = payload.get("sub")
#         if username is None:
#             raise credentials_exception
#     except InvalidTokenError:  # Zmienione z JWTError
#         raise credentials_exception
    
#     user_repo = UserRepository(db)
#     user = user_repo.get_by_username(username)
#     if user is None:
#         raise credentials_exception
    
#     return user

# def get_character_repository(db: Session = Depends(get_db)):
#     from app.repositories.character_repository import CharacterRepository
#     return CharacterRepository(db)

# def get_session_repository(db: Session = Depends(get_db)):
#     from app.repositories.session_repository import SessionRepository
#     return SessionRepository(db)

# def get_game_master_service(
#     game_master: AdaptiveGameMaster = Depends(get_game_master),
#     storage: dict = Depends(get_session_storage)
# ):
#     from app.services.game_master_service import GameMasterService
#     return GameMasterService(game_master, storage)

# backend/app/core/dependencies.py
from functools import lru_cache
from typing import Generator, Optional
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from app.services.session_storage import SessionStorage
from app.core.config import get_settings
from app.models.database import SessionLocal
from app.core.ai.adaptive_game_master import AdaptiveGameMaster

settings = get_settings()
session_storage_instance = SessionStorage()
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

session_storage = {}




@lru_cache()
def get_game_master() -> AdaptiveGameMaster:
    return AdaptiveGameMaster(model_name=settings.ollama_model)

# TYMCZASOWA WERSJA BEZ JWT
async def get_current_user(db: Session = Depends(get_db)):
    """Tymczasowy mock user dla testów"""
    from app.models.user import User
    # Zwróć mockowego usera
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

def get_session_storage():
    return session_storage

def get_game_master_service(
    game_master: AdaptiveGameMaster = Depends(get_game_master),
    storage: SessionStorage = Depends(lambda: session_storage_instance)
):
    from app.services.game_master_service import GameMasterService
    return GameMasterService(game_master, storage)