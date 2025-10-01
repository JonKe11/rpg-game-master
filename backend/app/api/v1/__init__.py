# backend/app/api/v1/__init__.py
from fastapi import APIRouter
from app.api.v1.endpoints import users, characters, game_sessions, auth, wiki

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(characters.router, prefix="/characters", tags=["characters"])
api_router.include_router(game_sessions.router, prefix="/game-sessions", tags=["game-sessions"])
api_router.include_router(wiki.router, prefix="/wiki", tags=["wiki"])