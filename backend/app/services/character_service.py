# backend/app/services/character_service.py
from typing import List, Optional, Dict
from app.repositories.character_repository import CharacterRepository
from app.models.character import Character
from app.services.wiki_fetcher_service import WikiFetcherService
from app.core.exceptions import NotFoundError, ValidationError

class CharacterService:
    """Service handling character operations"""
    
    def __init__(self, character_repository: CharacterRepository):
        self.char_repo = character_repository
        self.wiki_fetcher = WikiFetcherService()  # ✅ NOWY: Wiki Fetcher
    
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
        """
        Enhance character with data from wiki.
        
        ✅ UPDATED: Uses new WikiFetcherService with FANDOM API.
        
        Args:
            character_id: Character ID
            user_id: User ID (for ownership check)
            
        Returns:
            Updated character
        """
        character = self.get_character_if_owner(character_id, user_id)
        
        try:
            # Fetch from wiki using new API
            wiki_data = self.wiki_fetcher.fetch_article(
                character.name,
                character.universe
            )
            
            if wiki_data:
                # Update character with wiki data
                updates = {}
                
                # Description (if empty)
                if wiki_data.get('description') and not character.description:
                    # Limit to reasonable length
                    description = wiki_data['description'][:500]
                    updates['description'] = description
                
                # Backstory (use description as backstory if empty)
                if wiki_data.get('description') and not character.backstory:
                    backstory = wiki_data['description'][:2000]
                    updates['backstory'] = backstory
                
                # Apply updates
                if updates:
                    character = self.char_repo.update(character_id, **updates)
                    print(f"✅ Enhanced {character.name} with wiki data")
                else:
                    print(f"ℹ️ {character.name} already has complete data")
            else:
                print(f"⚠️ No wiki data found for {character.name}")
        
        except Exception as e:
            print(f"⚠️ Wiki enhancement failed for {character.name}: {e}")
            # Don't raise - enhancement is optional
        
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