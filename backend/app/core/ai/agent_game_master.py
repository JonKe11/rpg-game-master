import json
import logging
import ollama
from typing import List, Dict, Any, Optional
from app.core.ai.tools import GM_TOOLS

logger = logging.getLogger(__name__)

class AgentGameMaster:
    """
    Agentic AI Game Master.
    Nie generuje tylko tekstu - podejmuje decyzje i używa narzędzi.
    """
    
    def __init__(self, model_name: str = "qwen2.5:7b"):
        self.client = ollama.Client()
        self.model_name = model_name
        
    def run_turn(self, 
                 user_input: str, 
                 context_history: List[Dict], 
                 game_state: Dict, 
                 session_facts: List[str],
                 universe: str) -> Dict:
        """
        Wykonuje turę: Analiza -> Wybór Narzędzia -> (Zwraca do serwisu by wykonać) -> LUB Generuje Odpowiedź.
        """
        
     
        system_prompt = self._build_system_prompt(universe, game_state, session_facts)
        
        messages = [
            {'role': 'system', 'content': system_prompt}
        ] + context_history[-10:] 
        
        if user_input:
            messages.append({'role': 'user', 'content': user_input})

       
        logger.info("🤖 Agent thinking...")
        try:
            response = self.client.chat(
                model=self.model_name,
                messages=messages,
                tools=GM_TOOLS,
            )
            
            message = response['message']
            
          
            if message.get('tool_calls'):
                logger.info(f"🛠️ Agent wants to use tools: {len(message['tool_calls'])}")
                return {
                    "type": "tool_request",
                    "tool_calls": message['tool_calls'],
                    "raw_message": message 
                }
            

            return {
                "type": "response",
                "content": message['content']
            }
            
        except Exception as e:
            logger.error(f"Agent Logic Error: {e}")
            return {"type": "error", "content": "Coś zakłóciło moje połączenie z Mocą..."}

    def continue_after_tool(self, 
                            messages_history: List[Dict], 
                            tool_results: List[Dict]) -> str:
        """
        Druga faza pętli: AI otrzymuje wynik narzędzia (np. treść z Wiki) i generuje finalny opis.
        """
     
        messages = messages_history.copy()
        for res in tool_results:
            messages.append({
                "role": "tool",
                "content": json.dumps(res['result']),
              
              
            })
            
        
        response = self.client.chat(
            model=self.model_name,
            messages=messages
        )
        return response['message']['content']
    
    
    def generate(self, prompt: str) -> str:
        """
        Prosta metoda generowania tekstu dla CampaignPlanner i innych serwisów pomocniczych.
        """
        response = self.client.generate(model=self.model_name, prompt=prompt)
        return response['response']

    def _build_system_prompt(self, universe: str, game_state: Dict, facts: List[str]) -> str:
        facts_str = "\n- ".join(facts) if facts else "Brak kluczowych wydarzeń."
        
        return f"""Jesteś Mistrzem Gry RPG w uniwersum {universe}.
        
TWOIM CELEM JEST: Prowadzić spójną, ekscytującą przygodę, dbać o kanon i reagować na graczy.

STAN GRY (PAMIĘTAJ O TYM):
- Lokacja: {game_state.get('current_location', 'Nieznana')}
- Czas: {game_state.get('time_of_day', 'Dzień')}
- Aktywni NPC: {json.dumps(game_state.get('npcs', []))}

KLUCZOWE FAKTY Z PRZESZŁOŚCI (Context):
- {facts_str}

INSTRUKCJE NARZĘDZI:
1. Jeśli gracze pytają o lore/świat -> użyj `search_knowledge_base`.
2. Jeśli gracze zmieniają miejsce -> użyj `change_scene_location`.
3. Jeśli jest walka/ryzyko -> użyj `roll_dice_check`.
4. Jeśli dajesz nagrodę -> użyj `update_inventory`.

Bądź kreatywny, ale trzymaj się faktów. Generuj w języku Angielskim"""