
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    
    characters = relationship("Character", back_populates="owner")
    game_sessions = relationship("GameSession", back_populates="game_master")
    
    
    sent_friend_requests = relationship(
        "Friendship",
        foreign_keys="Friendship.sender_id",
        back_populates="sender",
        cascade="all, delete-orphan"
    )
    received_friend_requests = relationship(
        "Friendship",
        foreign_keys="Friendship.receiver_id",
        back_populates="receiver",
        cascade="all, delete-orphan"
    )