# backend/tests/unit/test_game_master.py
import pytest
from unittest.mock import Mock, patch
from app.core.ai.adaptive_game_master import AdaptiveGameMaster, ActionType

def test_parse_action_move():
    """Test parsing movement action"""
    gm = AdaptiveGameMaster()
    action_type, entities = gm._parse_action("Idź do kantyny")
    
    assert action_type == ActionType.MOVE
    assert "kantyny" in str(entities).lower()

def test_parse_action_combat():
    """Test parsing combat action"""
    gm = AdaptiveGameMaster()
    action_type, entities = gm._parse_action("Atakuję goblina")
    
    assert action_type == ActionType.COMBAT

def test_parse_action_examine():
    """Test parsing examine action"""
    gm = AdaptiveGameMaster()
    action_type, entities = gm._parse_action("Sprawdzam skrzynię")
    
    assert action_type == ActionType.EXAMINE

@patch('app.core.ai.adaptive_game_master.ollama.Client')
def test_start_session(mock_ollama):
    """Test starting game session"""
    gm = AdaptiveGameMaster()
    gm._check_ollama_connection = Mock(return_value=False)
    
    character = {
        'name': 'Test Hero',
        'race': 'Human',
        'class_type': 'Warrior',
        'level': 1
    }
    
    result = gm.start_session(character, 'star_wars')
    
    assert 'message' in result
    assert 'type' in result
    assert result['type'] == 'narration'

def test_create_npc():
    """Test NPC creation"""
    gm = AdaptiveGameMaster()
    npc = gm._create_npc('star_wars', 'merchant')
    
    assert 'name' in npc
    assert 'race' in npc
    assert 'occupation' in npc
    assert npc['occupation'] == 'merchant'
    assert 'personality' in npc
    assert 'motivation' in npc