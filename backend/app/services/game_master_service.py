# backend/app/services/game_master_service.py
from typing import Dict, List, Any
import json
import random
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.ai.agent_game_master import AgentGameMaster
from app.services.postgres_cache_service import PostgresCacheService
from app.models.session import GameSession

logger = logging.getLogger(__name__)

class GameMasterService:
    def __init__(self, db: Session):
        self.db = db
        self.agent = AgentGameMaster() 
        self.wiki_service = PostgresCacheService(db)
        
    def process_player_input(self, session_id: int, user_input: str, user_name: str) -> Dict:
        """Główna pętla obsługi tury"""
        
        session = self.db.query(GameSession).filter(GameSession.id == session_id).first()
        if not session:
            raise ValueError("Session not found")

        game_state = session.game_state or {}
        facts = session.session_facts or []
        
        
        self._append_history(session, "user", f"{user_name}: {user_input}")
        
        
        decision = self.agent.run_turn(
            user_input=user_input, 
            context_history=session.chat_history, 
            game_state=game_state, 
            session_facts=facts, 
            universe=session.universe
        )
        
        final_response = ""
        
       
        if decision['type'] == 'tool_request':
            tool_results = []
            
            for tool_call in decision['tool_calls']:
                fn_name = tool_call['function']['name']
                args = tool_call['function']['arguments']
                
                
                try:
                    result = self._execute_tool(fn_name, args, session)
                    tool_results.append({"name": fn_name, "result": str(result)})
                except Exception as e:
                    logger.error(f"❌ Tool execution failed ({fn_name}): {e}")
                    tool_results.append({"name": fn_name, "result": "Tool failed to execute."})
                
          
            final_response = self.agent.continue_after_tool(session.chat_history, tool_results)
            
        else:
            final_response = decision['content']
            
       
        self._append_history(session, "assistant", final_response)
        
        session.last_played = datetime.now()
        self.db.commit()
        self.db.refresh(session)
        
        return {
            "message": final_response,
            "type": "narration",
            "game_state": session.game_state
        }

    def _execute_tool(self, name: str, args: Dict, session: GameSession) -> Any:
        """Router narzędzi - generuje eventy dla frontendu"""
        logger.info(f"🛠️ Executing tool: {name} with args: {args}")
        
        if name == "spawn_npc":
            
            npc_data = {
                "id": f"npc_{random.randint(1000,9999)}",
                "name": args.get('name', 'Unknown'),
                "race": args.get('race', 'Unknown'),
                "attitude": args.get('attitude', 'Neutral'),
                
                "hp": random.randint(30, 80),
                "max_hp": random.randint(30, 80),
                "armor_class": random.randint(10, 16),
                "damage_reduction": random.randint(0, 3),
                "damage_dice": "1d8+2",
                "image_url": None 
            }
            
            
            state = session.game_state or {}
            npcs = state.get('npcs', [])
            npcs.append(npc_data)
            state['npcs'] = npcs
            session.game_state = state
            
            
            self._append_rich_message(
                session, 
                type="npc_spawn", 
                content=f"Spawned {npc_data['name']}", 
                metadata={"npc": npc_data, "original_type": "npc_spawn"}
            )
            return f"NPC {args['name']} pojawił się w grze."

        elif name == "start_combat":
            
            state = session.game_state or {}
            npcs = state.get('npcs', [])
            
            combatants = []
           
            for npc in npcs:
                combatants.append({
                    **npc,
                    "type": "npc",
                    "active": False,
                    "initiative": random.randint(1, 20)
                })
            
            combat_data = {
                "round": 1,
                "turn_text": "Combat Started!",
                "combatants": combatants,
                "ended": False
            }
            
            
            self._append_rich_message(
                session,
                type="gm_event", 
                content=json.dumps(combat_data),
                metadata={"original_type": "combat_update"}
            )
            return "Rozpoczęto tryb walki."

        elif name == "change_scene_location":
            state = session.game_state or {}
            state['current_location'] = args['location_name']
            session.game_state = state
            
           
            self._append_rich_message(
                session,
                type="location_change",
                content=args['location_name'],
                metadata={}
            )
            return f"Lokacja zmieniona na {args['location_name']}."

        elif name == "search_knowledge_base":
           
            results = self.wiki_service.search_articles_paginated(
                universe=session.universe, 
                category=None,  
                query=args['query'], 
                limit=1
            )
            if results and results['items']:
                art = results['items'][0]
                return f"Wiki: {art.title} - {art.content.get('summary', 'Brak opisu')}"
            return "Brak danych w wiki."

        elif name == "roll_dice_check":
            roll = random.randint(1, args.get('dice_type', 20)) + args.get('modifier', 0)
            result_msg = f"🎲 Rzut ({args['reason']}): {roll}"
            
           
            self._append_rich_message(
                session,
                type="dice_roll_result",
                content=f"{args['reason']}={roll}",
                metadata={"reason": args['reason']}
            )
            return result_msg

        return "Narzędzie wykonane."

    def _append_history(self, session, role, content):
        """Dodaje zwykłą wiadomość tekstową"""
        history = list(session.chat_history or [])
        history.append({
            "role": role, 
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        session.chat_history = history

    def _append_rich_message(self, session, type, content, metadata):
        
        history = list(session.chat_history or [])
     
        history.append({
            "role": "system", 
            "message_type": type, 
            "content": content,
            "message_metadata": metadata,
            "timestamp": datetime.now().isoformat()
        })
        session.chat_history = history