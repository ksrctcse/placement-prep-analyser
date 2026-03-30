"""
Database Migration - Add roll_number column to student_profiles table
Run this script to add the roll_number column for storing student roll numbers
"""

import sys
sys.path.insert(0, '/Users/arunkumaraswamy/Documents/Study/projects/placement-prep-analyser/intelligent_placement_prep_analyser/backend')

from app.database.db import engine
from sqlalchemy import text, inspect

def run_migration():
    """Add roll_number column to student_profiles table"""
    print("Starting database migration: Add roll_number to student_profiles...")
    
    try:
        # Check if column already exists
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('student_profiles')]
        
        if 'roll_number' in columns:
            print("✓ Column 'roll_number' already exists in student_profiles table")
            return True
        
        # Add the column
        with engine.connect() as connection:
            connection.execute(text(
                "ALTER TABLE student_profiles ADD COLUMN roll_number VARCHAR(50) DEFAULT NULL"
            ))
            connection.commit()
        
        print("✓ Successfully added 'roll_number' column to student_profiles table")
        print("  - Column type: VARCHAR(50)")
        print("  - Nullable: Yes (existing students won't have a roll number)")
        return True
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
