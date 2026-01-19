
from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    
    database_url: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:rpg11!@localhost:5432/rpg_gamemaster"
    )
    
    
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    ollama_timeout: int = 30
    
    
    use_redis: bool = False  
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    
    app_name: str = "RPG Game Master"
    version: str = "0.1.0"
    debug: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()