# backend/app/repositories/session_repository.py
from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.session import GameSession

class SessionRepository(BaseRepository[GameSession]):
    def __init__(self, db: Session):
        super().__init__(GameSession, db)
    
    def get_active_sessions(self, user_id: int = None) -> List[GameSession]:
        """Pobierz aktywne sesje (opcjonalnie dla konkretnego użytkownika)"""
        query = self.db.query(GameSession).filter(GameSession.status == "active")
        if user_id:
            query = query.filter(GameSession.game_master_id == user_id)
        return query.order_by(GameSession.last_played.desc()).all()
    
    def get_by_participant(self, character_id: int) -> List[GameSession]:
        """Pobierz sesje w których uczestniczy postać"""
        # JSON contains sprawdza czy character_id jest w tablicy participants
        return self.db.query(GameSession).filter(
            GameSession.participants.contains([character_id])
        ).all()
    
    def update_last_played(self, session_id: int):
        """Aktualizuj czas ostatniej gry"""
        from datetime import datetime
        session = self.get(session_id)
        if session:
            session.last_played = datetime.now()
            self.db.commit()