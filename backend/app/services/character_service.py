# backend/app/services/character_service.py
from typing import List, Optional, Dict
from app.repositories.character_repository import CharacterRepository
from app.models.character import Character
from app.core.scraper.wiki_scraper import WikiScraper
from app.core.exceptions import NotFoundError, ValidationError

class CharacterService:
    """Service handling character operations"""
    
    def __init__(self, character_repository: CharacterRepository):
        self.char_repo = character_repository
        self.wiki_scraper = WikiScraper()
    
    def create_character(self, owner_id: int, **character_data) -> Character:
        """Create new character for user"""
        # Validate level
        if character_data.get('level', 1) < 1:
            raise ValidationError("Level must be at least 1")
        
        # Create character
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
        """Enhance character with data from wiki"""
        character = self.get_character_if_owner(character_id, user_id)
        
        # Search wiki
        url = self.wiki_scraper.search_character(
            character.name, 
            character.universe
        )
        
        if url:
            wiki_data = self.wiki_scraper.scrape_character_data(url)
            
            # Update character with wiki data
            updates = {}
            if wiki_data.get('description') and not character.description:
                updates['description'] = wiki_data['description']
            if wiki_data.get('biography') and not character.backstory:
                updates['backstory'] = wiki_data['biography'][:2000]
            if wiki_data.get('abilities'):
                updates['skills'] = wiki_data['abilities'][:10]
            
            if updates:
                character = self.char_repo.update(character_id, **updates)
        
        return character
    
    def update_character(
        self, 
        character_id: int, 
        user_id: int, 
        **updates
    ) -> Character:
        """Update character if user is owner"""
        character = self.get_character_if_owner(character_id, user_id)
        
        # Remove None values
        updates = {k: v for k, v in updates.items() if v is not None}
        
        if updates:
            character = self.char_repo.update(character_id, **updates)
        
        return character
    
    def delete_character(self, character_id: int, user_id: int) -> bool:
        """Delete character if user is owner"""
        character = self.get_character_if_owner(character_id, user_id)
        return self.char_repo.delete(character_id)