# backend/app/models/character.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, DateTime, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class Character(Base):
    __tablename__ = "characters"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    universe = Column(String, nullable=False)
    race = Column(String)
    class_type = Column(String)
    level = Column(Integer, default=1)
    description = Column(Text)
    backstory = Column(Text)
    
    # ✅ NOWE POLA: Życie i Pancerz
    hp = Column(Integer, default=100)
    max_hp = Column(Integer, default=100)
    armor_class = Column(Integer, default=10)
    damage_reduction = Column(Integer, default=0)   # ✅ NOWE: Pancerz redukujący obrażenia
    # Star Wars specific
    homeworld = Column(String)
    born_year = Column(Integer)
    born_era = Column(String)
    gender = Column(String)
    skin_color = Column(String)
    eye_color = Column(String)
    hair_color = Column(String)
    age = Column(Integer)             # Dodano wiek
    gender = Column(String)
    height = Column(Float, nullable=True)       # Wzrost
    mass = Column(Float, nullable=True)         # Waga# Męska/Żeńska/Inna
    
    # KOTOR attributes (d20 system)
    strength = Column(Integer, default=10)
    dexterity = Column(Integer, default=10)
    constitution = Column(Integer, default=10)
    intelligence = Column(Integer, default=10)
    wisdom = Column(Integer, default=10)
    charisma = Column(Integer, default=10)
    
    # KOTOR skills (0-99 range)
    skill_computer_use = Column(Integer, default=0)
    skill_demolitions = Column(Integer, default=0)
    skill_stealth = Column(Integer, default=0)
    skill_awareness = Column(Integer, default=0)
    skill_persuade = Column(Integer, default=0)
    skill_repair = Column(Integer, default=0)
    skill_security = Column(Integer, default=0)
    skill_treat_injury = Column(Integer, default=0)
    
    # Legacy fields - może być JSON dla flexibility
    stats = Column(JSON, default={})
    inventory = Column(JSON, default=[])
    skills = Column(JSON, default=[])
    cybernetics = Column(JSON, default=[])
    affiliations = Column(JSON, default=[])
    
    # Relations
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="characters")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())