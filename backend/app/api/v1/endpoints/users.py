# backend/app/api/v1/endpoints/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserResponse
from app.models.user import User

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user info"""
    return current_user

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get user by ID"""
    user_repo = UserRepository(db)
    user = user_repo.get(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user