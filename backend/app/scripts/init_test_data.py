# backend/scripts/init_test_data.py
from app.models import Base, engine
from app.models.character import Character
from app.models.user import User
from sqlalchemy.orm import Session

# Stwórz tabele
Base.metadata.create_all(bind=engine)

# Stwórz sesję
db = Session(engine)

# Stwórz testowego usera (ID=1 jak w mock)
test_user = User(
    id=1,
    username="testuser",
    email="test@example.com",
    hashed_password="hashed",
    is_active=True
)
db.merge(test_user)

# Stwórz testowe postacie
test_character = Character(
    name="Luke Skywalker",
    universe="star_wars",
    race="Human",
    class_type="Jedi",
    level=5,
    description="A young Jedi Knight",
    backstory="Farm boy from Tatooine who became a hero",
    owner_id=1
)
db.add(test_character)

db.commit()
print("Test data created!")