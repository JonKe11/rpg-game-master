# backend/app/services/game_master_service.py
from typing import Dict, Optional
from datetime import datetime
from app.core.ai.adaptive_game_master import AdaptiveGameMaster
from app.services.session_storage import SessionStorage
from app.core.exceptions import AIError

class GameMasterService:
    def __init__(self, game_master: AdaptiveGameMaster, storage):
        self.game_master = game_master
        # Akceptuj różne typy storage
        if isinstance(storage, dict):
            from app.services.session_storage import SessionStorage
            self.storage = SessionStorage()
        else:
            self.storage = storage
        
    def start_session(self, session_id: int, character_data: Dict, universe: str) -> Dict:
        """Start new game session"""
        try:
            # Spróbuj z AI
            intro_response = self.game_master.start_session(character_data, universe)
            
            # Zapisz w storage
            context = {
                'session_id': session_id,
                'universe': universe,
                'character': character_data,
                'location': intro_response.get('location'),
                'history': [intro_response]
            }
            
            # Zapisz kontekst
            if hasattr(self.storage, 'save_context'):
                from app.schemas.game_session import SessionContext
                ctx = SessionContext(**context)
                self.storage.save_context(session_id, ctx)
            
            return intro_response
            
        except Exception as e:
            print(f"AI Error: {e}")
            # Fallback response
            return {
                'message': f"Witaj, {character_data.get('name', 'bohaterze')}! Rozpoczynasz swoją przygodę w świecie {universe}. Rozglądasz się dookoła...",
                'type': 'narration',
                'timestamp': datetime.now().isoformat()
            }
    
    def process_action(self, session_id: int, action: str) -> Dict:
        """Process player action"""
        try:
            # Pobierz kontekst
            context = None
            if hasattr(self.storage, 'get_context'):
                context = self.storage.get_context(session_id)
            
            if context:
                response = self.game_master.process_action(action, context.dict())
            else:
                # Fallback bez kontekstu
                response = {
                    'message': f"Wykonujesz akcję: {action}",
                    'type': 'event',
                    'timestamp': datetime.now().isoformat()
                }
            
            return response
            
        except Exception as e:
            print(f"Process action error: {e}")
            return {
                'message': f"Akcja wykonana: {action}",
                'type': 'event',
                'timestamp': datetime.now().isoformat()
            }