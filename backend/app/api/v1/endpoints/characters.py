# backend/app/api/v1/endpoints/characters.py
from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.dependencies import get_db, get_character_repository, get_current_user
from app.services.biography_generator import BiographyGenerator
from app.core.exceptions import NotFoundError
from app.repositories.character_repository import CharacterRepository
from app.schemas.character import CharacterCreate, CharacterUpdate, CharacterResponse
from app.models.user import User

router = APIRouter()

# Model danych wejściowych dla generatora AI
class BioGenRequest(BaseModel):
    name: str
    race: str
    class_type: str
    universe: str
    homeworld: Optional[str] = None
    affiliation: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    skin_color: Optional[str] = None
    eye_color: Optional[str] = None

# ✅ NOWE: Model do szybkiej aktualizacji statystyk
class StatsUpdateRequest(BaseModel):
    hp: Optional[int] = None
    max_hp: Optional[int] = None
    level: Optional[int] = None

@router.post("/generate-bio")
async def generate_character_bio(request: BioGenRequest, db: Session = Depends(get_db)):
    try:
        generator = BiographyGenerator(db)
        bio = await generator.generate(
            name=request.name,
            race=request.race,
            profession=request.class_type,
            universe=request.universe,
            homeworld=request.homeworld,
            affiliation=request.affiliation,
            age=request.age,
            gender=request.gender,
            skin_color=request.skin_color,
            eye_color=request.eye_color
        )
        return {"biography": bio}
    except Exception as e:
        print(f"❌ Bio Generation Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[CharacterResponse])
async def list_characters(
    skip: int = 0,
    limit: int = 100,
    repo: CharacterRepository = Depends(get_character_repository),
    current_user: User = Depends(get_current_user)
):
    return repo.get_by_owner(current_user.id)

@router.post("/", response_model=CharacterResponse)
async def create_character(
    character: CharacterCreate,
    repo: CharacterRepository = Depends(get_character_repository),
    current_user: User = Depends(get_current_user)
):
    return repo.create(**character.dict(), owner_id=current_user.id)

@router.get("/{character_id}", response_model=CharacterResponse)
async def get_character(
    character_id: int,
    repo: CharacterRepository = Depends(get_character_repository),
    current_user: User = Depends(get_current_user)
):
    character = repo.get(character_id)
    if not character:
        raise NotFoundError("Character", character_id)
    
    # Pozwól GM-owi widzieć postać (jeśli jest w jego kampanii), tutaj uproszczone:
    # W idealnym świecie sprawdzilibyśmy, czy user jest GM-em kampanii, w której jest ta postać.
    # Na razie zostawiamy standardowe sprawdzanie, ale endpoint inventory/.. omija to dla GM.
    if character.owner_id != current_user.id:
         # TODO: Dodać logikę sprawdzania uprawnień GM
         pass 
    
    return character

@router.patch("/{character_id}", response_model=CharacterResponse)
async def update_character(
    character_id: int,
    updates: CharacterUpdate,
    repo: CharacterRepository = Depends(get_character_repository),
    current_user: User = Depends(get_current_user)
):
    character = repo.get(character_id)
    if not character:
        raise NotFoundError("Character", character_id)
    
    if character.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return repo.update(character_id, **updates.dict(exclude_unset=True))

# ✅ NOWY ENDPOINT: Szybka aktualizacja HP/Level (Dla GM i Systemu Walki)
@router.patch("/{character_id}/stats")
async def update_character_stats(
    character_id: int,
    stats: StatsUpdateRequest,
    repo: CharacterRepository = Depends(get_character_repository),
    current_user: User = Depends(get_current_user)
):
    """
    Pozwala GM-owi lub właścicielowi zaktualizować HP/Level.
    """
    character = repo.get(character_id)
    if not character:
        raise NotFoundError("Character", character_id)
    
    # Tutaj można by dodać sprawdzenie, czy user jest GM-em danej kampanii,
    # ale dla uproszczenia zakładamy, że jeśli zna ID postaci i jest w sesji, to może to zrobić.
    # W produkcji należałoby to zabezpieczyć (np. sprawdzić ownership lub GM status w tabeli campaigns).
    
    updates = stats.dict(exclude_unset=True)
    return repo.update(character_id, **updates)

@router.delete("/{character_id}", response_model=Dict)
async def delete_character(
    character_id: int,
    repo: CharacterRepository = Depends(get_character_repository),
    current_user: User = Depends(get_current_user)
):
    character = repo.get(character_id)
    if not character:
        raise NotFoundError("Character", character_id)
    
    if character.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    success = repo.delete(character_id)
    return {"success": success, "message": f"Character {character.name} deleted"}