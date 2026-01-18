# backend/app/services/character_service.py
from typing import List, Optional, Dict
import logging
from app.repositories.character_repository import CharacterRepository
from app.models.character import Character

from app.core.exceptions import NotFoundError, ValidationError


from app.models.database import SessionLocal
from app.services.postgres_cache_service import PostgresCacheService

logger = logging.getLogger(__name__)

class CharacterService:
    """Service handling character operations"""
    
    def __init__(self, character_repository: CharacterRepository):
        self.char_repo = character_repository
        
    
        try:
            self.db = SessionLocal()
            self.pg_cache = PostgresCacheService(self.db)
            logger.info("✅ CharacterService połączony z PostgresCacheService")
        except Exception as e:
            logger.error(f"❌ CharacterService nie mógł połączyć się z DB: {e}")
            self.db = None
            self.pg_cache = None

    def __del__(self):
      
        if self.db:
            self.db.close()
    
    def create_character(self, owner_id: int, **character_data) -> Character:
        """Create new character for user"""
        if character_data.get('level', 1) < 1:
            raise ValidationError("Level must be at least 1")
        
        character = self.char_repo.create(
            owner_id=owner_id,
            **character_data
        )
        return character
    
    def get_user_characters(self, user_id: int) -> List[Character]:
        """Get all characters for user"""
        return self.char_repo.get_by_owner(user_id)
    
    def get_character_if_owner(self, character_id: int, user_id: int) -> Character:
        """Get character only if user is owner"""
        character = self.char_repo.get(character_id)
        if not character:
            raise NotFoundError("Character", character_id)
        if character.owner_id != user_id:
            raise ValidationError("You don't own this character")
        return character
    
    def enhance_with_wiki(self, character_id: int, user_id: int) -> Character:
       
        character = self.get_character_if_owner(character_id, user_id)
        
        if not self.pg_cache:
            logger.warning(f"⚠️ Nie można wzbogacić {character.name}: brak połączenia z pg_cache")
            return character

        try:
        
            article = self.pg_cache.get_article_by_title(
                character.name,
                character.universe
            )
            
            if article and article.content:
                updates = {}
                
              
                wiki_description = article.content.get('description')
                
                if wiki_description:
                    if not character.description:
                        updates['description'] = wiki_description[:500]
                    if not character.backstory:
                        updates['backstory'] = wiki_description[:2000]
                
              
                if updates:
                    character = self.char_repo.update(character_id, **updates)
                    logger.info(f"✅ Wzbogacono {character.name} o dane z Wiki")
                else:
                    logger.info(f"ℹ️ {character.name} posiada już kompletne dane")
            else:
                logger.warning(f"⚠️ Nie znaleziono danych Wiki dla {character.name}")
        
        except Exception as e:
            logger.error(f"⚠️ Błąd wzbogacania Wiki dla {character.name}: {e}")
            
        
        return character
    
    def update_character(
        self, 
        character_id: int, 
        user_id: int, 
        **updates
    ) -> Character:
        """Update character if user is owner"""
        character = self.get_character_if_owner(character_id, user_id)
        
        updates = {k: v for k, v in updates.items() if v is not None}
        
        if updates:
            character = self.char_repo.update(character_id, **updates)
        
        return character
    
    def delete_character(self, character_id: int, user_id: int) -> bool:
        """Delete character if user is owner"""
        character = self.get_character_if_owner(character_id, user_id)
        return self.char_repo.delete(character_id)