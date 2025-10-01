# backend/app/repositories/user_repository.py
from typing import Optional
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.user import User

class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(User, db)
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Znajdź użytkownika po nazwie"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Znajdź użytkownika po emailu"""
        return self.db.query(User).filter(User.email == email).first()
    
    def exists(self, username: str = None, email: str = None) -> bool:
        """Sprawdź czy użytkownik istnieje"""
        query = self.db.query(User)
        if username and email:
            return query.filter(
                (User.username == username) | (User.email == email)
            ).first() is not None
        elif username:
            return query.filter(User.username == username).first() is not None
        elif email:
            return query.filter(User.email == email).first() is not None
        return False