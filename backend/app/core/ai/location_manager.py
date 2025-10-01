# backend/app/core/ai/location_manager.py
from typing import Dict, Optional, List
from dataclasses import dataclass
from enum import Enum

class LocationType(Enum):
    PLANET = "planet"
    CITY = "city"
    BUILDING = "building"
    WILDERNESS = "wilderness"

@dataclass
class Location:
    name: str
    type: LocationType
    description: str = ""
    parent: Optional[str] = None

class LocationManager:
    """Zarządza lokacjami w grze"""
    
    def __init__(self):
        self.current_location: Optional[Location] = None
        self.known_locations: Dict[str, Location] = {}
        
        # Podstawowe lokacje dla uniwersów
        self.default_locations = {
            'star_wars': {
                'Tatooine': Location('Tatooine', LocationType.PLANET),
                'Mos Eisley': Location('Mos Eisley', LocationType.CITY, parent='Tatooine'),
                'Coruscant': Location('Coruscant', LocationType.PLANET),
            },
            'lotr': {
                'Shire': Location('Shire', LocationType.WILDERNESS),
                'Bree': Location('Bree', LocationType.CITY),
                'Rivendell': Location('Rivendell', LocationType.CITY),
            }
        }
    
    def set_location(self, location_name: str, universe: str = 'star_wars') -> Location:
        """Ustaw aktualną lokację"""
        if location_name in self.known_locations:
            self.current_location = self.known_locations[location_name]
        elif universe in self.default_locations and location_name in self.default_locations[universe]:
            self.current_location = self.default_locations[universe][location_name]
            self.known_locations[location_name] = self.current_location
        else:
            # Stwórz nową lokację
            self.current_location = Location(location_name, LocationType.BUILDING)
            self.known_locations[location_name] = self.current_location
        
        return self.current_location
    
    def get_current_location(self) -> Optional[Location]:
        """Zwróć aktualną lokację"""
        return self.current_location