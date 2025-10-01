from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class GameSession(Base):
    __tablename__ = "game_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    universe = Column(String, nullable=False)
    status = Column(String, default="active")  # active, paused, completed
    
    # Historia i stan gry
    story_context = Column(Text)  # kontekst fabularny
    chat_history = Column(JSON, default=[])  # historia rozmów
    world_state = Column(JSON, default={})  # stan świata gry
    
    # Relacje
    game_master_id = Column(Integer, ForeignKey("users.id"))
    game_master = relationship("User", back_populates="game_sessions")
    
    # Uczestnicy sesji (jako JSON z ID postaci)
    participants = Column(JSON, default=[])
    
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_played = Column(DateTime(timezone=True), server_default=func.now())