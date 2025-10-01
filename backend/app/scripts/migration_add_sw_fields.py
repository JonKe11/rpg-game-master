# backend/scripts/migration_add_sw_fields.py
"""
Migracja dodająca pola specyficzne dla Star Wars do tabeli characters
"""
from sqlalchemy import text
from app.models.database import engine

def upgrade():
    """Dodaje nowe kolumny do tabeli characters"""
    
    migrations = [
        # Star Wars specyficzne pola
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS homeworld VARCHAR",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS born_year INTEGER",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS born_era VARCHAR(3)",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS gender VARCHAR(20)",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS height FLOAT",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS mass FLOAT",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS skin_color VARCHAR(50)",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS eye_color VARCHAR(50)",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS hair_color VARCHAR(50)",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS cybernetics JSON",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS affiliations JSON",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS wiki_data JSON",
    ]
    
    with engine.connect() as conn:
        for migration in migrations:
            try:
                conn.execute(text(migration))
                print(f"✓ Executed: {migration[:50]}...")
            except Exception as e:
                print(f"✗ Failed: {migration[:50]}... - {e}")
        
        conn.commit()
    
    print("\n✅ Migration completed successfully!")

def downgrade():
    """Usuwa nowe kolumny (rollback)"""
    
    rollbacks = [
        "ALTER TABLE characters DROP COLUMN IF EXISTS homeworld",
        "ALTER TABLE characters DROP COLUMN IF EXISTS born_year",
        "ALTER TABLE characters DROP COLUMN IF EXISTS born_era",
        "ALTER TABLE characters DROP COLUMN IF EXISTS gender",
        "ALTER TABLE characters DROP COLUMN IF EXISTS height",
        "ALTER TABLE characters DROP COLUMN IF EXISTS mass",
        "ALTER TABLE characters DROP COLUMN IF EXISTS skin_color",
        "ALTER TABLE characters DROP COLUMN IF EXISTS eye_color",
        "ALTER TABLE characters DROP COLUMN IF EXISTS hair_color",
        "ALTER TABLE characters DROP COLUMN IF EXISTS cybernetics",
        "ALTER TABLE characters DROP COLUMN IF EXISTS affiliations",
        "ALTER TABLE characters DROP COLUMN IF EXISTS wiki_data",
    ]
    
    with engine.connect() as conn:
        for rollback in rollbacks:
            try:
                conn.execute(text(rollback))
                print(f"✓ Executed: {rollback[:50]}...")
            except Exception as e:
                print(f"✗ Failed: {rollback[:50]}... - {e}")
        
        conn.commit()
    
    print("\n✅ Rollback completed successfully!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'downgrade':
        downgrade()
    else:
        upgrade()