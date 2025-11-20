# backend/app/api/v1/endpoints/friends.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.friendship import Friendship, FriendshipStatus
from app.schemas.friend import FriendRequestCreate, FriendResponse, FriendshipUpdate

router = APIRouter()

@router.get("/", response_model=List[FriendResponse])
async def get_friends(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Pobierz listę znajomych (status ACCEPTED)"""
    friendships = db.query(Friendship).filter(
        or_(Friendship.sender_id == current_user.id, Friendship.receiver_id == current_user.id),
        Friendship.status == FriendshipStatus.ACCEPTED
    ).all()
    
    friends = []
    for f in friendships:
        friend_user = f.receiver if f.sender_id == current_user.id else f.sender
        friends.append({
            "id": friend_user.id,
            "username": friend_user.username,
            "status": "accepted"
        })
    return friends

@router.get("/requests/pending", response_model=List[FriendResponse])
async def get_pending_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Pobierz oczekujące zaproszenia (otrzymane)"""
    requests = db.query(Friendship).filter(
        Friendship.receiver_id == current_user.id,
        Friendship.status == FriendshipStatus.PENDING
    ).all()
    
    return [{
        "id": req.sender.id,
        "username": req.sender.username,
        "status": "pending"
    } for req in requests]

@router.post("/request")
async def send_friend_request(
    request: FriendRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Wyślij zaproszenie do znajomych"""
    target_user = db.query(User).filter(User.username == request.username).first()
    if not target_user:
        raise HTTPException(404, "User not found")
    if target_user.id == current_user.id:
        raise HTTPException(400, "Cannot add yourself")
        
    # Sprawdź czy relacja już istnieje
    existing = db.query(Friendship).filter(
        or_(
            and_(Friendship.sender_id == current_user.id, Friendship.receiver_id == target_user.id),
            and_(Friendship.sender_id == target_user.id, Friendship.receiver_id == current_user.id)
        )
    ).first()
    
    if existing:
        if existing.status == FriendshipStatus.ACCEPTED:
            raise HTTPException(400, "Already friends")
        if existing.status == FriendshipStatus.PENDING:
            raise HTTPException(400, "Request already pending")
            
    new_friendship = Friendship(
        sender_id=current_user.id,
        receiver_id=target_user.id,
        status=FriendshipStatus.PENDING
    )
    db.add(new_friendship)
    db.commit()
    return {"message": "Friend request sent"}

@router.post("/respond/{user_id}")
async def respond_to_request(
    user_id: int,
    update: FriendshipUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Zaakceptuj lub odrzuć zaproszenie"""
    friendship = db.query(Friendship).filter(
        Friendship.sender_id == user_id,
        Friendship.receiver_id == current_user.id,
        Friendship.status == FriendshipStatus.PENDING
    ).first()
    
    if not friendship:
        raise HTTPException(404, "Friend request not found")
        
    if update.status == "accepted":
        friendship.status = FriendshipStatus.ACCEPTED
        db.commit()
        return {"message": "Friend request accepted"}
    elif update.status == "rejected":
        db.delete(friendship)
        db.commit()
        return {"message": "Friend request rejected"}
    
    raise HTTPException(400, "Invalid status")