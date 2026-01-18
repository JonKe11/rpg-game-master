# backend/test_agent_standalone.py
import asyncio
from app.core.ai.agent_game_master import AgentGameMaster

async def test_agent_logic():
    agent = AgentGameMaster(model_name="llama3.1:8b")
    
    # Scenariusz 1: Pytanie o lore (Powinien użyć RAG)
    print("\n--- TEST 1: RAG Request ---")
    state = {"current_location": "Statek kosmiczny", "npcs": []}
    facts = []
    history = []
    
    response = agent.run_turn(
        user_input="Opowiedz mi o historii Mandalorians.",
        context_history=history,
        game_state=state,
        session_facts=facts,
        universe="star_wars"
    )
    
    print(f"Decyzja Agenta: {response['type']}")
    if response['type'] == 'tool_request':
        print(f"Narzędzia: {response['tool_calls']}")
    else:
        print(f"Odpowiedź: {response['content']}")

    # Scenariusz 2: Zmiana lokacji (Powinien użyć change_scene_location)
    print("\n--- TEST 2: Action Request ---")
    response = agent.run_turn(
        user_input="Lądujemy na planecie Hoth. Musimy się ukryć.",
        context_history=history,
        game_state=state,
        session_facts=facts,
        universe="star_wars"
    )
    
    print(f"Decyzja Agenta: {response['type']}")
    if response['type'] == 'tool_request':
        print(f"Narzędzia: {response['tool_calls']}")

if __name__ == "__main__":
    # Uruchomienie (symulacja asynchroniczności, choć ollama client jest sync w tym przykładzie)
    asyncio.run(test_agent_logic())