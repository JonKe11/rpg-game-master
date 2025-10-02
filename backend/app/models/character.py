# backend/app/models/character.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, DateTime, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class Character(Base):
    __tablename__ = "characters"
    
    # Podstawowe pola
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    universe = Column(String, nullable=False)
    race = Column(String)
    class_type = Column(String)
    level = Column(Integer, default=1)
    description = Column(Text)
    backstory = Column(Text)
    
    # Star Wars specyficzne pola
    homeworld = Column(String)
    born_year = Column(Integer)
    born_era = Column(String)  # BBY lub ABY
    gender = Column(String)
    height = Column(Float)  # w cm
    mass = Column(Float)  # w kg
    skin_color = Column(String)
    eye_color = Column(String)
    hair_color = Column(String)
    
    # JSON fields
    stats = Column(JSON, default={})
    inventory = Column(JSON, default=[])
    skills = Column(JSON, default=[])
    cybernetics = Column(JSON, default=[])
    affiliations = Column(JSON, default=[])
    wiki_data = Column(JSON, default={})
    
    # Relacje
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="characters")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())