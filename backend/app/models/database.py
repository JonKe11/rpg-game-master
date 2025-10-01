from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator
from app.core.config import get_settings  # DODAJ!

settings = get_settings()  # DODAJ!

# Tu później dodasz prawdziwy DATABASE_URL z .env
DATABASE_URL = settings.database_url  # POPRAW!
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()