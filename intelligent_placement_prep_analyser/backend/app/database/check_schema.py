"""
Check database schema for all auth tables
"""
from app.database.db import engine
from sqlalchemy import text, inspect

def check_schema():
    """Check the schema of all tables"""
    inspector = inspect(engine)
    
    tables = ['users', 'staff_profiles', 'student_profiles', 'departments']
    
    for table_name in tables:
        print(f"\n=== Table: {table_name} ===")
        try:
            columns = inspector.get_columns(table_name)
            for col in columns:
                print(f"  {col['name']}: {col['type']}")
        except Exception as e:
            print(f"  Error: {str(e)}")

if __name__ == "__main__":
    check_schema()
