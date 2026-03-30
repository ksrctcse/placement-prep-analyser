"""
Database Migration - Add attempt_count column to test_attempts table
Run this script to add the attempt_count column for tracking multiple test attempts
"""

import sys
sys.path.insert(0, '/Users/arunkumaraswamy/Documents/Study/projects/placement-prep-analyser/intelligent_placement_prep_analyser/backend')

from app.database.db import engine
from sqlalchemy import text, inspect

def run_migration():
    """Add attempt_count column to test_attempts table"""
    print("Starting database migration: Add attempt_count to test_attempts...")
    
    try:
        # Check if column already exists
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('test_attempts')]
        
        if 'attempt_count' in columns:
            print("✓ Column 'attempt_count' already exists in test_attempts table")
            return True
        
        # Add the column
        with engine.connect() as connection:
            connection.execute(text(
                "ALTER TABLE test_attempts ADD COLUMN attempt_count INTEGER DEFAULT 1"
            ))
            connection.commit()
        
        print("✓ Successfully added 'attempt_count' column to test_attempts table")
        print("  - Default value: 1")
        return True
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
