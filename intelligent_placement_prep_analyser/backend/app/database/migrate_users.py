"""
Database migration script to add missing columns to existing users table
"""
from app.database.db import engine
from sqlalchemy import text

def migrate_users_table():
    """Add missing columns to users table"""
    with engine.connect() as conn:
        # Check if password_hash column exists
        try:
            # Try to alter the users table and add missing columns
            print("Checking users table schema...")
            
            # Get current columns
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users'
            """))
            
            existing_columns = {row[0] for row in result}
            print(f"Existing columns: {existing_columns}")
            
            # List of required columns with their definitions
            required_columns = {
                'password_hash': "VARCHAR NOT NULL DEFAULT ''",
                'role': "VARCHAR NOT NULL DEFAULT 'student'",
                'is_active': "BOOLEAN NOT NULL DEFAULT true",
                'created_at': "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                'updated_at': "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            }
            
            # Add missing columns
            for column_name, column_def in required_columns.items():
                if column_name not in existing_columns:
                    print(f"Adding column {column_name}...")
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_def}"))
                    conn.commit()
                    print(f"✓ Added column {column_name}")
                else:
                    print(f"Column {column_name} already exists")
            
            print("\n✓ Users table migration completed!")
            
        except Exception as e:
            print(f"Error during migration: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    migrate_users_table()
