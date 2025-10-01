# backend/app/api/v1/endpoints/characters.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
# Dodaj na początku pliku:
from typing import List, Dict  # <-- Dodaj Dict!

from app.core.dependencies import (
    get_character_repository,
    get_current_user
)
from app.core.exceptions import NotFoundError
from app.repositories.character_repository import CharacterRepository
from app.schemas.character import (
    CharacterCreate,
    CharacterUpdate,
    CharacterResponse
)
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[CharacterResponse])
async def list_characters(
    skip: int = 0,
    limit: int = 100,
    repo: CharacterRepository = Depends(get_character_repository),
    current_user: User = Depends(get_current_user)
):
    """List user's characters"""
    return repo.get_by_owner(current_user.id)

@router.post("/", response_model=CharacterResponse)
async def create_character(
    character: CharacterCreate,
    repo: CharacterRepository = Depends(get_character_repository),
    current_user: User = Depends(get_current_user)
):
    """Create new character"""
    return repo.create(
        **character.dict(),
        owner_id=current_user.id
    )

@router.get("/{character_id}", response_model=CharacterResponse)
async def get_character(
    character_id: int,
    repo: CharacterRepository = Depends(get_character_repository),
    current_user: User = Depends(get_current_user)
):
    """Get character details"""
    character = repo.get(character_id)
    
    if not character:
        raise NotFoundError("Character", character_id)
    
    if character.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return character

@router.patch("/{character_id}", response_model=CharacterResponse)
async def update_character(
    character_id: int,
    updates: CharacterUpdate,
    repo: CharacterRepository = Depends(get_character_repository),
    current_user: User = Depends(get_current_user)
):
    """Update character"""
    character = repo.get(character_id)
    
    if not character:
        raise NotFoundError("Character", character_id)
    
    if character.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return repo.update(character_id, **updates.dict(exclude_unset=True))

@router.delete("/{character_id}", response_model=Dict)
async def delete_character(
    character_id: int,
    repo: CharacterRepository = Depends(get_character_repository),
    current_user: User = Depends(get_current_user)
):
    """Delete character"""
    character = repo.get(character_id)
    
    if not character:
        raise NotFoundError("Character", character_id)
    
    if character.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    success = repo.delete(character_id)
    
    return {
        "success": success,
        "message": f"Character {character.name} deleted"
    }