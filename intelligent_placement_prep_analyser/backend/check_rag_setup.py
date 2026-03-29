#!/usr/bin/env python
"""
Diagnostic script to verify RAG/Semantic Search setup
Run this from the backend directory: python check_rag_setup.py
"""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

print("\n" + "="*60)
print("RAG SETUP DIAGNOSTIC CHECK")
print("="*60 + "\n")

# Check 1: Environment variables
print("1. CHECKING ENVIRONMENT VARIABLES...")
print("-" * 60)

google_api_key = os.getenv("GOOGLE_API_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")
api_key = google_api_key or gemini_api_key

if google_api_key:
    print(f"✓ GOOGLE_API_KEY is set: {google_api_key[:10]}...")
elif gemini_api_key:
    print(f"✓ GEMINI_API_KEY is set: {gemini_api_key[:10]}...")
else:
    print(f"✗ NO API KEY FOUND")
    print(f"  Set either GOOGLE_API_KEY or GEMINI_API_KEY in .env file")
    sys.exit(1)

print()

# Check 2: .env file
print("2. CHECKING .ENV FILE...")
print("-" * 60)

env_file = Path(__file__).parent / ".env"
if env_file.exists():
    print(f"✓ .env file found: {env_file}")
else:
    print(f"✗ .env file NOT found: {env_file}")
    print(f"  Create .env file with settings from .env.example")

print()

# Check 3: Load settings
print("3. CHECKING SETTINGS LOADING...")
print("-" * 60)

try:
    from app.config.settings import settings
    print(f"✓ Settings loaded successfully")
    if settings.GOOGLE_API_KEY:
        print(f"✓ API key accessible from settings")
    else:
        print(f"⚠  API key not found in settings")
except Exception as e:
    print(f"✗ Failed to load settings: {e}")
    sys.exit(1)

print()

# Check 4: Required packages
print("4. CHECKING REQUIRED PACKAGES...")
print("-" * 60)

required_packages = [
    ("pdfplumber", "PDF text extraction"),
    ("langchain_community", "LangChain vector stores"),
    ("langchain_google_genai", "Google AI embeddings"),
    ("chromadb", "Vector database"),
]

all_packages_ok = True
for package, description in required_packages:
    try:
        __import__(package)
        print(f"✓ {package:<30} ({description})")
    except ImportError:
        print(f"✗ {package:<30} - MISSING")
        all_packages_ok = False

if not all_packages_ok:
    print("\nRun: pip install -r requirements.txt")

print()

# Check 5: Embeddings initialization
print("5. TESTING EMBEDDINGS INITIALIZATION...")
print("-" * 60)

try:
    from app.services.vector_service import get_embeddings
    embeddings = get_embeddings()
    print(f"✓ Embeddings initialized successfully")
    print(f"  Model: models/embedding-001")
except Exception as e:
    print(f"✗ Failed to initialize embeddings: {e}")
    print(f"\nTroubleshooting:")
    print(f"  1. Verify GOOGLE_API_KEY in .env is correct")
    print(f"  2. Check your Google API quota: https://cloud.google.com/")
    print(f"  3. Ensure the key has Generative Language API enabled")

print()

# Check 6: Vector database
print("6. CHECKING VECTOR DATABASE...")
print("-" * 60)

vector_db_path = Path(__file__).parent / "vector_db"
if vector_db_path.exists():
    print(f"✓ Vector DB directory exists: {vector_db_path}")
    # Count collections
    num_collections = len(list(vector_db_path.glob("topic_*")))
    print(f"  Current collections: {num_collections}")
else:
    print(f"ℹ  Vector DB directory will be created on first upload")

print()

# Summary
print("="*60)
print("SETUP STATUS SUMMARY")
print("="*60)

checklist = [
    ("Environment Variables", api_key is not None),
    (".env File", env_file.exists()),
    ("Settings Import", True),
    ("Required Packages", all_packages_ok),
]

all_ok = all(status for _, status in checklist)

for check, status in checklist:
    status_str = "✓" if status else "✗"
    print(f"{status_str} {check}")

print()

if all_ok:
    print("🎉 RAG setup looks good! You can now upload PDFs for semantic indexing.")
else:
    print("⚠️  Please fix the issues above before uploading PDFs.")
    sys.exit(1)

print()
