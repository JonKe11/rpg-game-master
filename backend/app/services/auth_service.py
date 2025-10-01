# backend/app/services/auth_service.py
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
import jwt  # Z PyJWT
from jwt.exceptions import InvalidTokenError

from app.core.config import get_settings
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.core.exceptions import ValidationError

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repo = user_repository
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.expire_minutes = settings.access_token_expire_minutes
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        user = self.user_repo.get_by_username(username)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user
    
    def create_access_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except InvalidTokenError:
            return None
    
    def register_user(self, username: str, email: str, password: str) -> User:
        if self.user_repo.exists(username=username, email=email):
            raise ValidationError("User with this username or email already exists")
        
        hashed_password = self.hash_password(password)
        user = self.user_repo.create(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_active=True
        )
        return user