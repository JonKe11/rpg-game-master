# backend/app/services/session_storage.py
from typing import Dict, Optional
import json
from datetime import datetime, timedelta
from app.schemas.game_session import SessionContext

class SessionStorage:
    """In-memory session storage (alternative to Redis)"""
    
    def __init__(self):
        self.sessions: Dict[int, Dict] = {}
        self.expiry_times: Dict[int, datetime] = {}
        self.ttl_hours = 24
    
    def save_context(self, session_id: int, context: SessionContext):
        """Save session context"""
        self.sessions[session_id] = context.dict()
        self.expiry_times[session_id] = datetime.now() + timedelta(hours=self.ttl_hours)
        self._cleanup_expired()
    
    def get_context(self, session_id: int) -> Optional[SessionContext]:
        """Get session context"""
        self._cleanup_expired()
        
        if session_id in self.sessions:
            return SessionContext(**self.sessions[session_id])
        return None
    
    def delete_context(self, session_id: int):
        """Delete session context"""
        if session_id in self.sessions:
            del self.sessions[session_id]
        if session_id in self.expiry_times:
            del self.expiry_times[session_id]
    
    def exists(self, session_id: int) -> bool:
        """Check if session exists"""
        self._cleanup_expired()
        return session_id in self.sessions
    
    def _cleanup_expired(self):
        """Remove expired sessions"""
        now = datetime.now()
        expired = [
            sid for sid, exp_time in self.expiry_times.items()
            if exp_time < now
        ]
        for sid in expired:
            self.delete_context(sid)
    
    def get_all_sessions(self) -> Dict[int, Dict]:
        """Get all active sessions (for debugging)"""
        self._cleanup_expired()
        return self.sessions.copy()