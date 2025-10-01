# backend/tests/integration/test_database.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, User, Character, GameSession

def test_database_connection(db_session):
    """Test database connection"""
    result = db_session.execute("SELECT 1")
    assert result.scalar() == 1

def test_create_user_with_characters(db_session):
    """Test creating user with related characters"""
    # Create user
    user = User(
        username="player",
        email="player@test.com",
        hashed_password="hash"
    )
    db_session.add(user)
    db_session.commit()
    
    # Create characters
    char1 = Character(
        name="Hero1",
        universe="star_wars",
        owner_id=user.id
    )
    char2 = Character(
        name="Hero2",
        universe="lotr",
        owner_id=user.id
    )
    db_session.add_all([char1, char2])
    db_session.commit()
    
    # Test relationship
    db_session.refresh(user)
    assert len(user.characters) == 2
    assert user.characters[0].owner.username == "player"

def test_cascade_delete(db_session):
    """Test cascade delete behavior"""
    # Create user with character
    user = User(
        username="temp",
        email="temp@test.com",
        hashed_password="hash"
    )
    db_session.add(user)
    db_session.commit()
    
    char = Character(
        name="TempHero",
        universe="star_wars",
        owner_id=user.id
    )
    db_session.add(char)
    db_session.commit()
    
    # Delete user
    db_session.delete(user)
    db_session.commit()
    
    # Character should still exist (no cascade delete by default)
    remaining = db_session.query(Character).filter_by(name="TempHero").first()
    assert remaining is not None

def test_json_fields(db_session):
    """Test JSON fields in models"""
    user = User(
        username="json_test",
        email="json@test.com",
        hashed_password="hash"
    )
    db_session.add(user)
    db_session.commit()
    
    # Create character with JSON fields
    char = Character(
        name="JsonHero",
        universe="star_wars",
        owner_id=user.id,
        stats={"strength": 10, "dexterity": 15},
        inventory=[{"name": "Sword", "quantity": 1}],
        skills=["Combat", "Stealth"]
    )
    db_session.add(char)
    db_session.commit()
    
    # Retrieve and test
    db_session.refresh(char)
    assert char.stats["strength"] == 10
    assert len(char.inventory) == 1
    assert "Combat" in char.skills