# backend/app/services/campaign_planner.py
from typing import Dict, List
import json
import logging
from app.core.ai.agent_game_master import AgentGameMaster
from app.models.database import SessionLocal
from app.services.postgres_cache_service import PostgresCacheService

logger = logging.getLogger(__name__)

class CampaignPlanner:
    """
    Planuje całą kampanię używając AI.
    """
    
    def __init__(self, game_master: AgentGameMaster):
        self.gm = game_master
       
        try:
            self.db = SessionLocal()
            self.pg_cache = PostgresCacheService(self.db)
        except Exception as e:
            logger.error(f"DB Error in Planner: {e}")
            self.db = None
    
    def __del__(self):
        if hasattr(self, 'db') and self.db:
            self.db.close()

    def create_campaign_outline(self, character_data: Dict, universe: str, length: str = "medium") -> Dict:
        """
        Generuje strukturę kampanii.
        """
        prompt = f"""
        Jesteś ekspertem od projektowania kampanii RPG w uniwersum {universe}.
        Stwórz zarys kampanii dla postaci:
        Imię: {character_data.get('name')}
        Rasa: {character_data.get('race')}
        Klasa: {character_data.get('class_type')}
        
        WYMAGANIA:
        Długość: {length}
        Format wyjściowy: Czysty JSON z polami: title, main_theme, antagonist, final_goal, acts (lista 3 aktów z opisami).
        """
        
   
        response = self.gm.generate(prompt)
        
        try:
         
            json_str = response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "{" not in json_str:
                raise ValueError("Brak JSON w odpowiedzi")
                
            return json.loads(json_str)
        except Exception as e:
            logger.error(f"Błąd parsowania planu kampanii: {e}")
            # Fallback
            return {
                "title": f"Przygoda {character_data.get('name')}",
                "main_theme": "Przetrwanie",
                "antagonist": "Nieznany wróg",
                "final_goal": "Przeżyć",
                "acts": []
            }