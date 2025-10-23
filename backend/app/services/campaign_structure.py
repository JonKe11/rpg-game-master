# backend/app/services/campaign_structure.py
"""
Modele dla Story Arc System
Campaign, Acts, Story Beats
"""
from typing import List, Dict, Optional
from pydantic import BaseModel
from enum import Enum
from datetime import datetime

class StoryAct(str, Enum):
    """Akty fabularne (3-act structure)"""
    ACT_1_SETUP = "act_1_setup"
    ACT_2_CONFRONTATION = "act_2_confrontation"
    ACT_3_RESOLUTION = "act_3_resolution"
    EPILOGUE = "epilogue"

class BeatType(str, Enum):
    """Typy story beats (inspirowane Blake Snyder's Beat Sheet)"""
    OPENING_IMAGE = "opening_image"
    CATALYST = "catalyst"
    DEBATE = "debate"
    BREAK_INTO_TWO = "break_into_two"
    B_STORY = "b_story"
    FUN_AND_GAMES = "fun_and_games"
    MIDPOINT = "midpoint"
    BAD_GUYS_CLOSE_IN = "bad_guys_close_in"
    ALL_IS_LOST = "all_is_lost"
    DARK_NIGHT = "dark_night_of_soul"
    BREAK_INTO_THREE = "break_into_three"
    FINALE = "finale"
    FINAL_IMAGE = "final_image"

class StoryBeat(BaseModel):
    """Pojedynczy moment fabularny"""
    id: str
    beat_type: BeatType
    act: StoryAct
    title: str
    description: str
    estimated_turns: int
    
    # Status tracking
    status: str = "pending"  # pending, active, completed, skipped
    actual_turns_taken: int = 0
    
    # Trigger conditions (optional)
    required_location: Optional[str] = None
    required_npc: Optional[str] = None
    trigger_keyword: Optional[str] = None

class CampaignArc(BaseModel):
    """Pełna struktura kampanii RPG"""
    campaign_id: str
    title: str
    universe: str
    
    # Story elements
    main_theme: str  # revenge, discovery, redemption, survival
    main_antagonist: str
    final_goal: str
    
    # Structure
    total_estimated_turns: int
    current_turn: int = 0
    current_beat_id: Optional[str] = None
    current_act: StoryAct = StoryAct.ACT_1_SETUP
    
    # Story beats (15-25 kluczowych momentów)
    beats: List[StoryBeat] = []
    
    # Tracking
    completed_beats: List[str] = []
    
    # Player choices (wpływają na fabułę)
    major_choices_made: List[Dict] = []
    
    # Meta
    created_at: datetime = datetime.now()
    last_updated: datetime = datetime.now()
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def get_progress_percentage(self) -> float:
        """Progress w %"""
        if not self.total_estimated_turns:
            return 0.0
        return min(100.0, (self.current_turn / self.total_estimated_turns) * 100)
    
    def get_current_beat(self) -> Optional[StoryBeat]:
        """Pobierz aktualny beat"""
        if not self.current_beat_id:
            return None
        return next((b for b in self.beats if b.id == self.current_beat_id), None)
    
    def get_next_beat(self) -> Optional[StoryBeat]:
        """Pobierz następny pending beat"""
        pending = [b for b in self.beats if b.status == "pending"]
        return pending[0] if pending else None
    
    def advance_beat(self):
        """Przejdź do następnego beatu"""
        current = self.get_current_beat()
        if current:
            current.status = "completed"
            self.completed_beats.append(current.id)
        
        next_beat = self.get_next_beat()
        if next_beat:
            next_beat.status = "active"
            self.current_beat_id = next_beat.id
            self.current_act = next_beat.act
            print(f"📖 Advanced to: {next_beat.title}")
    
    def is_near_end(self) -> bool:
        """Czy kampania bliska końca (ostatnie 20%)"""
        return self.get_progress_percentage() > 80
    
    def is_completed(self) -> bool:
        """Czy kampania zakończona"""
        return len(self.completed_beats) >= len(self.beats)