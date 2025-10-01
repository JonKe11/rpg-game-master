# backend/app/core/ai/base.py
from abc import ABC, abstractmethod
from typing import Dict, Optional

class BaseGameMaster(ABC):
    """Abstract base class for Game Master implementations"""
    
    @abstractmethod
    def start_session(self, character: Dict, universe: str = None) -> Dict:
        """Start new game session"""
        pass
    
    @abstractmethod
    def process_action(self, action: str, context: Dict) -> Dict:
        """Process player action"""
        pass
    
    @abstractmethod
    def generate_dice_roll(self, dice_type: str = 'd20') -> Dict:
        """Generate dice roll"""
        pass