# backend/app/core/ai/tools.py

GM_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Przeszukuje bazę wiedzy (Wiki) w poszukiwaniu informacji o świecie, rasach, planetach lub technologii.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Hasło do wyszukania"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "change_scene_location",
            "description": "Zmienia lokację w grze i obraz tła.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location_name": {"type": "string", "description": "Nazwa nowej lokacji"},
                    "image_search_query": {"type": "string", "description": "Angielski opis do wyszukania obrazka"}
                },
                "required": ["location_name", "image_search_query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "spawn_npc",
            "description": "Tworzy wizualną kartę NPC na czacie. Użyj tego, gdy wprowadzasz nową postać lub wroga.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Imię NPC"},
                    "race": {"type": "string", "description": "Rasa NPC"},
                    "description": {"type": "string", "description": "Krótki opis wyglądu"},
                    "attitude": {"type": "string", "enum": ["Hostile", "Neutral", "Friendly"], "description": "Nastawienie do graczy"},
                    "is_enemy": {"type": "boolean", "description": "Czy to przeciwnik w walce?"}
                },
                "required": ["name", "race", "attitude"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "start_combat",
            "description": "Rozpoczyna tryb walki (Combat Tracker). Użyj, gdy negocjacje zawiodą i zaczyna się bitwa.",
            "parameters": {
                "type": "object",
                "properties": {
                    "enemies": {
                        "type": "array", 
                        "items": {"type": "string"},
                        "description": "Lista imion wrogów biorących udział w walce"
                    }
                },
                "required": ["enemies"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "roll_dice_check",
            "description": "Wykonuje rzut kością (test umiejętności lub atak).",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string", "description": "Powód rzutu"},
                    "dice_type": {"type": "integer", "default": 20},
                    "modifier": {"type": "integer", "default": 0}
                },
                "required": ["reason"]
            }
        }
    }
]