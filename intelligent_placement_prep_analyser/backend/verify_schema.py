#!/usr/bin/env python3
from app.database.db import engine
from sqlalchemy import inspect

inspector = inspect(engine)

# Check student_profiles table
print("=" * 60)
print("STUDENT_PROFILES TABLE SCHEMA")
print("=" * 60)
student_columns = inspector.get_columns('student_profiles')
for col in student_columns:
    print(f"  - {col['name']}: {col['type']}")

# Check topics table
print("\n" + "=" * 60)
print("TOPICS TABLE SCHEMA")
print("=" * 60)
topics_columns = inspector.get_columns('topics')
for col in topics_columns:
    print(f"  - {col['name']}: {col['type']}")

# Check departments table
print("\n" + "=" * 60)
print("DEPARTMENTS TABLE SCHEMA")
print("=" * 60)
departments_columns = inspector.get_columns('departments')
for col in departments_columns:
    print(f"  - {col['name']}: {col['type']}")

print("\n" + "=" * 60)
print("SCHEMA VERIFICATION COMPLETE")
print("=" * 60)
