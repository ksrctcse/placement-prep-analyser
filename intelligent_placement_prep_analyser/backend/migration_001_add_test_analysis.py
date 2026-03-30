"""
Database Migration - Add Test Analysis and Topic Performance tables
Run this script to create the new tables for test analysis features
"""

import sys
sys.path.insert(0, '/Users/arunkumaraswamy/Documents/Study/projects/placement-prep-analyser/intelligent_placement_prep_analyser/backend')

from app.database.db import engine, Base
from app.database.models import TestAttemptDetail, TestAnalysis, TopicPerformance
import os

def run_migration():
    """Create all new tables"""
    print("Starting database migration...")
    
    try:
        # Create all tables defined in the models
        Base.metadata.create_all(bind=engine)
        print("✓ Database migration completed successfully!")
        print("\nTables created/updated:")
        print("  - test_attempt_details")
        print("  - test_analyses")
        print("  - topic_performance")
        return True
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
