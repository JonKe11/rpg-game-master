# backend/app/services/game_master_service.py
from typing import Dict, Optional, TYPE_CHECKING # ✅ Dodano TYPE_CHECKING
from datetime import datetime
# ⛔️ USUNIĘTO: from app.core.ai.adaptive_game_master import AdaptiveGameMaster
from app.services.session_storage import SessionStorage
from app.core.exceptions import AIError
import logging # ✅ Dodano logger

# ✅ NOWY BLOK: Importuj tylko dla type-checkera, aby przerwać cykl
if TYPE_CHECKING:
    from app.core.ai.adaptive_game_master import AdaptiveGameMaster

logger = logging.getLogger(__name__)

class GameMasterService:
    # ✅ POPRAWKA: Użyj stringa ("") dla type hinta, aby uniknąć importu w czasie działania
    def __init__(self, game_master: "AdaptiveGameMaster", storage):
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
                # Sprawdź, czy SessionContext istnieje przed importem
                try:
                    from app.schemas.game_session import SessionContext
                    ctx = SessionContext(**context)
                    self.storage.save_context(session_id, ctx)
                except ImportError:
                    logger.warning("SessionContext schema not found, saving raw dict.")
                    self.storage.save_context(session_id, context)
            
            return intro_response
            
        except Exception as e:
            logger.error(f"AI Error in start_session: {e}", exc_info=True)
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
                # Jeśli context jest obiektem Pydantic, użyj .dict()
                context_dict = context.dict() if hasattr(context, 'dict') else context
                response = self.game_master.process_action(action, context_dict)
            else:
                # Fallback bez kontekstu
                logger.warning(f"No context found for session_id: {session_id}. Using fallback response.")
                response = {
                    'message': f"Wykonujesz akcję: {action}",
                    'type': 'event',
                    'timestamp': datetime.now().isoformat()
                }
            
            return response
            
        except Exception as e:
            logger.error(f"Process action error: {e}", exc_info=True)
            return {
                'message': f"Akcja wykonana: {action}",
                'type': 'event',
                'timestamp': datetime.now().isoformat()
            }