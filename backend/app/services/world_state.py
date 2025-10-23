# backend/app/services/world_state.py
"""
World State - Single Source of Truth
Persistent, validated state of the game world
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json

@dataclass
class NPC:
    """Non-Player Character data"""
    name: str
    race: str  # MUST be canon
    role: str  # "smuggler", "vendor", "guard"
    location: str
    attitude: int = 0  # -10 to +10 (hostile to friendly)
    first_met_turn: int = 0
    last_seen_turn: int = 0
    notes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class Location:
    """A specific place in the world"""
    name: str  # "Rusty Cantina", "Spaceport District"
    planet: str  # MUST be canon planet
    description: str
    visited: bool = False
    first_visit_turn: int = 0
    
    def to_dict(self) -> Dict:
        return asdict(self)

class WorldState:
    """
    Maintains consistent game world state
    Prevents AI from contradicting established facts
    """
    
    def __init__(self, universe: str, starting_planet: str, capital_city: str = None, homeworld: str = None):
        self.universe = universe
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
        
        # IMMUTABLE FACTS (set once, never change)
        self.homeworld = homeworld or starting_planet  # Origin planet (backstory)
        self.starting_planet = starting_planet  # Where campaign actually starts
        self.current_planet = starting_planet  # Can change via travel
        self.capital_city = capital_city  # e.g., "Hanna City"
        
        # DYNAMIC STATE
        self.current_location: Optional[Location] = None
        self.npcs: Dict[str, NPC] = {}  # name -> NPC
        self.locations: Dict[str, Location] = {}  # name -> Location
        
        # HISTORY & MEMORY
        self.established_facts: List[str] = []
        self.memory_traces: List[Dict] = []
        self.timeline: List[Dict] = []
        
        # PLAYER STATE
        self.player_inventory: List[str] = []
        self.player_relationships: Dict[str, int] = {}
        
        # QUEST/STORY STATE
        self.active_quests: List[str] = []
        self.completed_quests: List[str] = []
        
        # Initialize with planet facts
        if capital_city:
            self.add_established_fact(
                f"The capital city of {starting_planet} is {capital_city}",
                turn=0
            )
    
    def add_npc(
        self, 
        name: str, 
        race: str, 
        role: str, 
        location: str, 
        turn: int,
        notes: str = None
    ) -> NPC:
        """Add new NPC to world"""
        if name in self.npcs:
            return self.update_npc(name, last_seen_turn=turn)
        
        npc = NPC(
            name=name,
            race=race,
            role=role,
            location=location,
            first_met_turn=turn,
            last_seen_turn=turn,
            notes=[notes] if notes else []
        )
        
        self.npcs[name] = npc
        
        self.add_memory_trace(
            f"Met {name}, a {race} {role}",
            turn=turn
        )
        
        self.last_updated = datetime.now()
        return npc
    
    def update_npc(self, name: str, **kwargs) -> Optional[NPC]:
        """Update existing NPC"""
        if name not in self.npcs:
            return None
        
        npc = self.npcs[name]
        for key, value in kwargs.items():
            if hasattr(npc, key):
                if key == 'notes' and isinstance(value, str):
                    npc.notes.append(value)
                else:
                    setattr(npc, key, value)
        
        self.last_updated = datetime.now()
        return npc
    
    def add_location(
        self, 
        name: str, 
        description: str, 
        turn: int,
        planet: str = None
    ) -> Location:
        """Add new location to world"""
        if name in self.locations:
            return self.locations[name]
        
        location = Location(
            name=name,
            planet=planet or self.current_planet,
            description=description,
            visited=True,
            first_visit_turn=turn
        )
        
        self.locations[name] = location
        self.current_location = location
        
        self.add_memory_trace(f"Visited {name}", turn=turn)
        self.last_updated = datetime.now()
        return location
    
    def add_established_fact(self, fact: str, turn: int):
        """Add immutable fact that AI must never contradict"""
        if fact not in self.established_facts:
            self.established_facts.append(fact)
            self.add_memory_trace(f"FACT: {fact}", turn=turn, is_critical=True)
    
    def add_memory_trace(
        self, 
        description: str, 
        turn: int,
        is_critical: bool = False
    ):
        """Add important event to memory"""
        trace = {
            'turn': turn,
            'description': description,
            'is_critical': is_critical,
            'timestamp': datetime.now().isoformat()
        }
        self.memory_traces.append(trace)
        self.timeline.append(trace)
    
    def add_event(self, description: str, turn: int):
        """Add regular event to timeline"""
        event = {
            'turn': turn,
            'description': description,
            'timestamp': datetime.now().isoformat()
        }
        self.timeline.append(event)
    
    def get_recent_memory_traces(self, limit: int = 5) -> List[Dict]:
        """Get most recent important events"""
        return self.memory_traces[-limit:]
    
    def get_critical_memory_traces(self) -> List[Dict]:
        """Get all critical memories"""
        return [t for t in self.memory_traces if t.get('is_critical', False)]
    
    def get_world_context_for_prompt(self, include_timeline: bool = False) -> str:
        """Generate context string for AI prompt"""
        
        # 🆕 Add moon information if relevant
        moon_info = ""
        if self.current_planet in ['Nar Shaddaa', 'Yavin 4', 'Endor']:
            moon_relationships = {
                'Nar Shaddaa': 'a moon orbiting the planet Nal Hutta',
                'Yavin 4': 'a moon of the gas giant Yavin',
                'Endor': 'the forest moon in the Endor system'
            }
            moon_info = f"\n- Location Type: {moon_relationships.get(self.current_planet, 'planet')}"
        
        context = f"""
╔════════════════════════════════════════════╗
  WORLD STATE - SINGLE SOURCE OF TRUTH
  (DO NOT CONTRADICT ANY INFORMATION BELOW)
╚════════════════════════════════════════════╝

🌍 CURRENT LOCATION:
- Universe: {self.universe}
- Homeworld (origin): {self.homeworld} [character's birthplace - for backstory]
- Current Location: {self.current_planet} ✓ [STAY HERE - DO NOT CHANGE]{moon_info}
- Capital City: {self.capital_city if self.capital_city else '[Not specified - you can choose any location on planet]'}

👥 KNOWN NPCs (DO NOT CHANGE THEIR RACES/ROLES):
"""
        
        if self.npcs:
            for name, npc in self.npcs.items():
                context += f"- {name}: {npc.race} {npc.role} (attitude: {npc.attitude:+d})\n"
        else:
            context += "- None yet\n"
        
        context += "\n📍 VISITED LOCATIONS:\n"
        if self.locations:
            for loc_name, loc in self.locations.items():
                context += f"- {loc_name} on {loc.planet}\n"
        else:
            context += "- Only starting area\n"
        
        context += "\n⚡ ESTABLISHED FACTS (NEVER CONTRADICT):\n"
        if self.established_facts:
            for fact in self.established_facts:
                context += f"- {fact}\n"
        else:
            context += "- None yet\n"
        
        # Critical memories
        critical_memories = self.get_critical_memory_traces()
        if critical_memories:
            context += "\n🔥 CRITICAL MEMORIES:\n"
            for mem in critical_memories:
                context += f"- Turn {mem['turn']}: {mem['description']}\n"
        
        # Recent memories
        recent_memories = [m for m in self.get_recent_memory_traces(5) 
                          if not m.get('is_critical', False)]
        if recent_memories:
            context += "\n📝 RECENT EVENTS:\n"
            for mem in recent_memories:
                context += f"- Turn {mem['turn']}: {mem['description']}\n"
        
        if include_timeline:
            context += "\n📜 FULL TIMELINE:\n"
            for event in self.timeline[-10:]:
                context += f"- Turn {event['turn']}: {event['description']}\n"
        
        context += "\n╚════════════════════════════════════════════╝\n"
        
        return context
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for storage"""
        return {
            'universe': self.universe,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'homeworld': self.homeworld,
            'starting_planet': self.starting_planet,
            'current_planet': self.current_planet,
            'capital_city': self.capital_city,
            'current_location': self.current_location.to_dict() if self.current_location else None,
            'npcs': {name: npc.to_dict() for name, npc in self.npcs.items()},
            'locations': {name: loc.to_dict() for name, loc in self.locations.items()},
            'established_facts': self.established_facts,
            'memory_traces': self.memory_traces,
            'timeline': self.timeline,
            'player_inventory': self.player_inventory,
            'player_relationships': self.player_relationships,
            'active_quests': self.active_quests,
            'completed_quests': self.completed_quests
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorldState':
        """Deserialize from dict"""
        world = cls(
            universe=data['universe'],
            starting_planet=data['starting_planet'],
            capital_city=data.get('capital_city'),
            homeworld=data.get('homeworld')
        )
        
        world.created_at = datetime.fromisoformat(data['created_at'])
        world.last_updated = datetime.fromisoformat(data['last_updated'])
        world.current_planet = data['current_planet']
        
        if data.get('current_location'):
            loc_data = data['current_location']
            world.current_location = Location(**loc_data)
        
        for name, npc_data in data.get('npcs', {}).items():
            world.npcs[name] = NPC(**npc_data)
        
        for name, loc_data in data.get('locations', {}).items():
            world.locations[name] = Location(**loc_data)
        
        world.established_facts = data.get('established_facts', [])
        world.memory_traces = data.get('memory_traces', [])
        world.timeline = data.get('timeline', [])
        world.player_inventory = data.get('player_inventory', [])
        world.player_relationships = data.get('player_relationships', {})
        world.active_quests = data.get('active_quests', [])
        world.completed_quests = data.get('completed_quests', [])
        
        return world