# backend/app/services/session_storage.py
"""
Session storage z obsługą Campaign Arc
Trzyma: session context + campaign structure
"""
from typing import Dict, Optional
import json
from datetime import datetime, timedelta
from pathlib import Path
from app.services.campaign_structure import CampaignArc
from app.services.world_state import WorldState

class SessionStorage:
    """
    In-memory + file storage dla:
    - Session context (lokacja, NPC, historia)
    - Campaign arc (story beats, progres)
    - World State (single source of truth)
    """
    
    def __init__(self, storage_dir: str = 'session_storage'):
        self.sessions: Dict[int, Dict] = {}
        self.campaigns: Dict[int, CampaignArc] = {}
        self.expiry_times: Dict[int, datetime] = {}
        self.ttl_hours = 72  # 3 dni
        
        # File storage dla persistence
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    # ========================================================================
    # Session Context Methods (existing)
    # ========================================================================
    
    def save_context(self, session_id: int, context: Dict):
        """Save session context (lokacja, NPC, historia)"""
        self.sessions[session_id] = context
        self.expiry_times[session_id] = datetime.now() + timedelta(hours=self.ttl_hours)
        self._cleanup_expired()
        
        # Save to file
        self._save_to_file(session_id, 'context')
    
    def get_context(self, session_id: int) -> Optional[Dict]:
        """Get session context"""
        self._cleanup_expired()
        
        if session_id in self.sessions:
            return self.sessions[session_id]
        
        # Try loading from file
        return self._load_from_file(session_id, 'context')
    
    def delete_context(self, session_id: int):
        """Delete session context"""
        if session_id in self.sessions:
            del self.sessions[session_id]
        if session_id in self.expiry_times:
            del self.expiry_times[session_id]
        
        # Delete file
        context_file = self.storage_dir / f"session_{session_id}_context.json"
        if context_file.exists():
            context_file.unlink()
    
    # ========================================================================
    # Campaign Arc Methods
    # ========================================================================
    
    def save_campaign(self, session_id: int, campaign: CampaignArc):
        """Save campaign arc"""
        self.campaigns[session_id] = campaign
        self.expiry_times[session_id] = datetime.now() + timedelta(hours=self.ttl_hours)
        
        # Save to file
        self._save_to_file(session_id, 'campaign', campaign.dict())
    
    def get_campaign(self, session_id: int) -> Optional[CampaignArc]:
        """Get campaign arc"""
        self._cleanup_expired()
        
        # Check memory
        if session_id in self.campaigns:
            return self.campaigns[session_id]
        
        # Try loading from file
        data = self._load_from_file(session_id, 'campaign')
        if data:
            campaign = CampaignArc(**data)
            self.campaigns[session_id] = campaign
            return campaign
        
        return None
    
    def delete_campaign(self, session_id: int):
        """Delete campaign"""
        if session_id in self.campaigns:
            del self.campaigns[session_id]
        
        campaign_file = self.storage_dir / f"session_{session_id}_campaign.json"
        if campaign_file.exists():
            campaign_file.unlink()
    
    # ========================================================================
    # Intro Methods
    # ========================================================================
    
    def save_intro(self, session_id: int, intro_message: Dict):
        """
        Save intro message permanently
        Ensures consistent intro even after refresh
        """
        intro_file = self.storage_dir / f"session_{session_id}_intro.json"
        
        try:
            with open(intro_file, 'w', encoding='utf-8') as f:
                json.dump(intro_message, f, indent=2, ensure_ascii=False, default=str)
            print(f"✅ Intro saved to file: {intro_file.name}")
        except Exception as e:
            print(f"⚠️ Failed to save intro: {e}")

    def get_intro(self, session_id: int) -> Optional[Dict]:
        """Get saved intro message"""
        intro_file = self.storage_dir / f"session_{session_id}_intro.json"
        
        if not intro_file.exists():
            return None
        
        try:
            with open(intro_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ Loaded intro from file: {intro_file.name}")
            return data
        except Exception as e:
            print(f"⚠️ Failed to load intro: {e}")
            return None
    def save_intro(self, session_id: int, intro_data: Dict):
        """Save intro separately from context (for caching)"""
        intro_key = f"intro_{session_id}"
        self.sessions[intro_key] = intro_data
        self.expiry_times[intro_key] = datetime.now() + timedelta(hours=self.ttl_hours)
        print(f"💾 Intro cached for session {session_id}")
    # ========================================================================
    # World State Methods
    # ========================================================================
    
    def save_world_state(self, session_id: int, world_state: WorldState):
        """Save world state to disk"""
        world_file = self.storage_dir / f"session_{session_id}_world.json"
        
        try:
            with open(world_file, 'w', encoding='utf-8') as f:
                json.dump(world_state.to_dict(), f, indent=2, ensure_ascii=False)
            print(f"💾 World state saved: {world_file.name}")
        except Exception as e:
            print(f"⚠️ Failed to save world state: {e}")
            import traceback
            traceback.print_exc()
    
    def get_world_state(self, session_id: int) -> Optional[WorldState]:
        """Load world state from disk"""
        world_file = self.storage_dir / f"session_{session_id}_world.json"
        
        if not world_file.exists():
            print(f"⚠️ World state file not found: {world_file.name}")
            return None
        
        try:
            with open(world_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            world = WorldState.from_dict(data)
            print(f"✅ World state loaded: {world_file.name}")
            return world
        except Exception as e:
            print(f"⚠️ Failed to load world state: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def delete_world_state(self, session_id: int):
        """Delete world state file"""
        world_file = self.storage_dir / f"session_{session_id}_world.json"
        if world_file.exists():
            world_file.unlink()
            print(f"🗑️ World state deleted: {world_file.name}")
    
    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    def exists(self, session_id: int) -> bool:
        """Check if session exists"""
        self._cleanup_expired()
        return session_id in self.sessions or session_id in self.campaigns
    
    def get_all_sessions(self) -> Dict[int, Dict]:
        """Get all active sessions (debugging)"""
        self._cleanup_expired()
        return {
            'contexts': self.sessions.copy(),
            'campaigns': {
                sid: camp.dict() for sid, camp in self.campaigns.items()
            }
        }
    
    def _cleanup_expired(self):
        """Remove expired sessions"""
        now = datetime.now()
        expired = [
            sid for sid, exp_time in self.expiry_times.items()
            if exp_time < now
        ]
        for sid in expired:
            self.delete_context(sid)
            self.delete_campaign(sid)
    
    def _save_to_file(self, session_id: int, file_type: str, data: Optional[Dict] = None):
        """Save to JSON file for persistence"""
        if data is None:
            data = self.sessions.get(session_id, {})
        
        filename = f"session_{session_id}_{file_type}.json"
        filepath = self.storage_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            print(f"⚠️ Failed to save {file_type} to file: {e}")
    
    def _load_from_file(self, session_id: int, file_type: str) -> Optional[Dict]:
        """Load from JSON file"""
        filename = f"session_{session_id}_{file_type}.json"
        filepath = self.storage_dir / filename
        
        if not filepath.exists():
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Failed to load {file_type} from file: {e}")
            return None