"""
Database Migration: Add RAG fields to Topic table
Add: is_indexed, embedding_chunks, last_indexed_at
"""
import sys
sys.path.insert(0, '.')

from sqlalchemy import text
from app.database.db import engine, SessionLocal
from app.database.models import Base, Topic


def migrate_add_rag_fields():
    """Add RAG-related fields to Topic table"""
    db = SessionLocal()
    
    try:
        # Get database URL to determine dialect
        db_url = str(engine.url)
        
        print("✓ Adding RAG fields to topics table...")
        
        # Check if fields already exist
        inspector_query = text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'topics' AND column_name IN ('is_indexed', 'embedding_chunks', 'last_indexed_at')
        """)
        
        existing_columns = db.execute(inspector_query).fetchall()
        
        if not existing_columns:
            # Add columns
            print("  - Adding is_indexed column...")
            db.execute(text("""
                ALTER TABLE topics ADD COLUMN is_indexed BOOLEAN DEFAULT FALSE
            """))
            
            print("  - Adding embedding_chunks column...")
            db.execute(text("""
                ALTER TABLE topics ADD COLUMN embedding_chunks INTEGER DEFAULT 0
            """))
            
            print("  - Adding last_indexed_at column...")
            db.execute(text("""
                ALTER TABLE topics ADD COLUMN last_indexed_at TIMESTAMP NULL
            """))
            
            db.commit()
            print("✓ RAG fields added successfully!")
        else:
            print("✓ RAG fields already exist")
        
    except Exception as e:
        print(f"✗ Error adding RAG fields: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def create_vector_db_directory():
    """Create vector database directory if it doesn't exist"""
    import os
    from pathlib import Path
    
    vector_db_path = Path(__file__).parent.parent.parent / "vector_db"
    vector_db_path.mkdir(parents=True, exist_ok=True)
    print(f"✓ Vector database directory: {vector_db_path}")


if __name__ == "__main__":
    print("Running RAG migration...")
    
    # Create vector DB directory
    create_vector_db_directory()
    
    # Run migrations
    migrate_add_rag_fields()
    
    print("\n✓ RAG migration complete!")
