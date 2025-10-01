from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.character import Character

class CharacterRepository(BaseRepository[Character]):
    def __init__(self, db: Session):
        super().__init__(Character, db)
    
    def get_by_owner(self, owner_id: int) -> List[Character]:
        return self.db.query(Character).filter(
            Character.owner_id == owner_id
        ).all()
    
    def get_by_universe(self, universe: str) -> List[Character]:
        return self.db.query(Character).filter(
            Character.universe == universe
        ).all()