#!/usr/bin/env python
"""
Script to populate the departments table with default values
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.database.db import SessionLocal, engine
from app.database.models import DepartmentModel

print("Connecting to database...")
session = SessionLocal()

try:
    # Check existing departments
    existing_count = session.query(DepartmentModel).count()
    print(f"Current departments in DB: {existing_count}")
    
    # If empty, add default departments
    if existing_count == 0:
        print("\nAdding default departments...")
        departments = ["CSE", "IT", "EEE", "ECE", "MECH", "CIVIL"]
        
        dept_objects = []
        for dept_name in departments:
            dept = DepartmentModel(name=dept_name)
            dept_objects.append(dept)
            session.add(dept)
            print(f"  Added to session: {dept_name}")
        
        print(f"\nCommitting {len(dept_objects)} departments...")
        session.commit()
        print(f"✓ Successfully inserted {len(departments)} departments")
    else:
        print("✓ Departments already exist, skipping insertion")
    
    # Verify
    all_depts = session.query(DepartmentModel).all()
    print(f"\nVerification - Total departments in DB: {len(all_depts)}")
    for dept in all_depts:
        print(f"  - ID: {dept.id}, Name: {dept.name}")
    
    if len(all_depts) == 0:
        print("WARNING: No departments found in database!")
    
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    session.rollback()
finally:
    session.close()
    print("\nDone")
