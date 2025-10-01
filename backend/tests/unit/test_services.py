# backend/tests/unit/test_services.py
import pytest
from unittest.mock import Mock, MagicMock
from app.services.auth_service import AuthService
from app.services.character_service import CharacterService
from app.core.exceptions import ValidationError

def test_auth_service_hash_password():
    """Test password hashing"""
    mock_repo = Mock()
    service = AuthService(mock_repo)
    
    hashed = service.hash_password("mypassword")
    assert hashed != "mypassword"
    assert len(hashed) > 20

def test_auth_service_verify_password():
    """Test password verification"""
    mock_repo = Mock()
    service = AuthService(mock_repo)
    
    password = "testpass123"
    hashed = service.hash_password(password)
    
    assert service.verify_password(password, hashed) is True
    assert service.verify_password("wrongpass", hashed) is False

def test_auth_service_register_user_already_exists():
    """Test registration with existing user"""
    mock_repo = Mock()
    mock_repo.exists.return_value = True
    
    service = AuthService(mock_repo)
    
    with pytest.raises(ValidationError) as exc_info:
        service.register_user("john", "john@example.com", "pass123")
    
    assert "already exists" in str(exc_info.value)

def test_character_service_create_invalid_level():
    """Test character creation with invalid level"""
    mock_repo = Mock()
    service = CharacterService(mock_repo)
    
    with pytest.raises(ValidationError) as exc_info:
        service.create_character(
            owner_id=1,
            name="Hero",
            universe="star_wars",
            level=0  # Invalid
        )
    
    assert "Level must be at least 1" in str(exc_info.value)

def test_character_service_get_character_wrong_owner():
    """Test getting character with wrong owner"""
    mock_repo = Mock()
    mock_char = Mock()
    mock_char.owner_id = 2
    mock_repo.get.return_value = mock_char
    
    service = CharacterService(mock_repo)
    
    with pytest.raises(ValidationError) as exc_info:
        service.get_character_if_owner(
            character_id=1,
            user_id=1  # Different from owner_id
        )
    
    assert "don't own this character" in str(exc_info.value)