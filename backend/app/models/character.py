from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class Character(Base):
    __tablename__ = "characters"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    universe = Column(String, nullable=False)  # np. "star_wars", "lotr", "dnd"
    race = Column(String)
    class_type = Column(String)  # klasa postaci
    level = Column(Integer, default=1)
    description = Column(Text)
    backstory = Column(Text)
    
    # Statystyki jako JSON dla elastyczności różnych systemów
    stats = Column(JSON, default={})
    inventory = Column(JSON, default=[])
    skills = Column(JSON, default=[])
    
    # Relacje
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="characters")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())