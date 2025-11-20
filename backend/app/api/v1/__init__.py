# backend/app/api/v1/__init__.py
from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, characters, game_sessions, wiki
from app.api.v1.endpoints import inventory
from app.api.v1.endpoints import multiplayer
from app.api.v1.endpoints import friends # ✅ NOWY IMPOR
api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(characters.router, prefix="/characters", tags=["characters"])
api_router.include_router(game_sessions.router, prefix="/game-sessions", tags=["game-sessions"])
api_router.include_router(wiki.router, prefix="/wiki", tags=["wiki"])
api_router.include_router(multiplayer.router, prefix="/multiplayer", tags=["multiplayer"])
# ✅ POPRAWKA: Zmieniono prefix, aby uniknąć konfliktu
api_router.include_router(
    inventory.router,
    prefix="/multiplayer/inventory",  # <-- Dodano /inventory
    tags=["multiplayer-inventory"]     # Zmieniono tag dla jasności
)
api_router.include_router(friends.router, prefix="/friends", tags=["friends"])


