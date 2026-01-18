from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class GameSession(Base):
    __tablename__ = "game_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    universe = Column(String, nullable=False)
    status = Column(String, default="active")
    
    # --- NOWE POLA DLA AGENTA ---
    # Kontener na ustrukturyzowany stan (Lokacja, NPC, Questy)
    # Przykład: {"current_location": "Tatooine", "npcs": [{"name": "Watto", "attitude": "hostile"}]}
    game_state = Column(JSON, default={}) 
    
    # Lista kluczowych faktów (Pamięć długotrwała/Skompresowana historia)
    # Przykład: ["Gracze ukradli statek.", "Imperium szuka Jedi na Tatooine."]
    session_facts = Column(JSON, default=[])
    
    # Surowa historia czatu (Pamięć krótkotrwała - bufor)
    chat_history = Column(JSON, default=[]) 
    
    # --- RESZTA BEZ ZMIAN ---
    game_master_id = Column(Integer, ForeignKey("users.id"))
    game_master = relationship("User", back_populates="game_sessions")
    participants = Column(JSON, default=[])
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_played = Column(DateTime(timezone=True), server_default=func.now())