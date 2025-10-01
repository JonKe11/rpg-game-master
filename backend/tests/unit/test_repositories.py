# backend/tests/unit/test_repositories.py
import pytest
from app.repositories.character_repository import CharacterRepository
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.models.character import Character

def test_user_repository_create(db_session):
    """Test creating user"""
    repo = UserRepository(db_session)
    
    user = repo.create(
        username="john",
        email="john@example.com",
        hashed_password="hashedpass",
        is_active=True
    )
    
    assert user.id is not None
    assert user.username == "john"
    assert user.email == "john@example.com"

def test_user_repository_get_by_username(db_session):
    """Test finding user by username"""
    repo = UserRepository(db_session)
    
    # Create user
    repo.create(
        username="jane",
        email="jane@example.com",
        hashed_password="hashedpass"
    )
    
    # Find user
    user = repo.get_by_username("jane")
    assert user is not None
    assert user.username == "jane"
    
    # Non-existent user
    user = repo.get_by_username("nonexistent")
    assert user is None

def test_character_repository_get_by_owner(db_session):
    """Test getting characters by owner"""
    # Create user first
    user_repo = UserRepository(db_session)
    user = user_repo.create(
        username="player",
        email="player@example.com",
        hashed_password="hash"
    )
    
    # Create characters
    char_repo = CharacterRepository(db_session)
    char1 = char_repo.create(
        name="Hero1",
        universe="star_wars",
        owner_id=user.id
    )
    char2 = char_repo.create(
        name="Hero2",
        universe="lotr",
        owner_id=user.id
    )
    
    # Get by owner
    characters = char_repo.get_by_owner(user.id)
    assert len(characters) == 2
    assert characters[0].name == "Hero1"
    assert characters[1].name == "Hero2"

def test_character_repository_update(db_session):
    """Test updating character"""
    user_repo = UserRepository(db_session)
    user = user_repo.create(
        username="player",
        email="player@example.com",
        hashed_password="hash"
    )
    
    char_repo = CharacterRepository(db_session)
    char = char_repo.create(
        name="Hero",
        universe="star_wars",
        level=1,
        owner_id=user.id
    )
    
    # Update level
    updated = char_repo.update(char.id, level=5, race="Jedi")
    assert updated.level == 5
    assert updated.race == "Jedi"
    assert updated.name == "Hero"  # Unchanged