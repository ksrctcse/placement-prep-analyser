#!/usr/bin/env python3
"""
Migration script to add department_id and section columns to topics table
"""
from sqlalchemy import text
from app.database.db import engine
from sqlalchemy import inspect

print("=" * 60)
print("TOPICS TABLE MIGRATION")
print("=" * 60)

print("\nAdding new columns to topics table...")

with engine.connect() as connection:
    try:
        connection.execute(text('ALTER TABLE topics ADD COLUMN IF NOT EXISTS department_id INTEGER'))
        print("✓ Added department_id column")
    except Exception as e:
        print(f"  Note on department_id: {type(e).__name__}")
    
    try:
        connection.execute(text("ALTER TABLE topics ADD COLUMN IF NOT EXISTS section VARCHAR(1)"))
        print("✓ Added section column")
    except Exception as e:
        print(f"  Note on section: {type(e).__name__}")
    
    try:
        connection.execute(text(
            'ALTER TABLE topics ADD CONSTRAINT fk_topics_department_id '
            'FOREIGN KEY (department_id) REFERENCES departments(id)'
        ))
        print("✓ Added foreign key constraint for department_id")
    except Exception as e:
        print(f"  Note on FK: {type(e).__name__} (may already exist)")
    
    try:
        connection.execute(text('CREATE INDEX IF NOT EXISTS idx_topics_department_id ON topics(department_id)'))
        print("✓ Added index on department_id")
    except Exception as e:
        print(f"  Note on index: {type(e).__name__}")
    
    connection.commit()

# Verify the table structure
print("\nVerifying table structure...")
inspector = inspect(engine)
topics_columns = inspector.get_columns('topics')
print(f"\nTopics table now has {len(topics_columns)} columns:")
for col in topics_columns:
    print(f"  - {col['name']}: {col['type']}")

print("\n" + "=" * 60)
print("MIGRATION COMPLETE")
print("=" * 60)
