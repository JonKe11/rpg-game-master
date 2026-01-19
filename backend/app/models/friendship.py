
from sqlalchemy import Column, Integer, ForeignKey, String, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from .database import Base
import enum

class FriendshipStatus(enum.Enum):
    PENDING = "pending"   
    ACCEPTED = "accepted" 
    BLOCKED = "blocked"   

class Friendship(Base):
    __tablename__ = "friendships"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(SQLEnum(FriendshipStatus), default=FriendshipStatus.PENDING)

    
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_friend_requests")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_friend_requests")

    __table_args__ = (
        UniqueConstraint('sender_id', 'receiver_id', name='unique_friendship'),
    )