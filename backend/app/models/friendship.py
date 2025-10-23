# backend/app/models/friendship.py
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from .database import Base
import enum

class FriendshipStatus(enum.Enum):
    PENDING = "pending"    # Wysłane zaproszenie
    ACCEPTED = "accepted"  # Przyjęte
    BLOCKED = "blocked"    # Zablokowany

class Friendship(Base):
    __tablename__ = "friendships"
    
    id = Column(Integer, primary_key=True, index=True)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    friend_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    status = Column(SQLEnum(FriendshipStatus), default=FriendshipStatus.PENDING)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())