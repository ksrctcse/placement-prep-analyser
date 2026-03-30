#!/usr/bin/env python3
"""
Diagnostic script to debug MCQ generation failure
Checks: Topic status, Vector store, Content retrieval, Gemini generation
"""

import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "intelligent_placement_prep_analyser" / "backend"
sys.path.insert(0, str(backend_path))

def check_topic_status():
    """Check if topic is indexed and has chunks"""
    print("\n" + "="*70)
    print("🔍 STEP 1: Check Topic Indexing Status")
    print("="*70)
    
    try:
        from app.database.db import SessionLocal
        from app.database.models import Topic
        
        db = SessionLocal()
        topic = db.query(Topic).filter(Topic.id == 1).first()
        
        if not topic:
            print("❌ Topic ID 1 not found in database")
            return False
        
        print(f"\nTopic: {topic.title}")
        print(f"  ID: {topic.id}")
        print(f"  is_indexed: {topic.is_indexed}")
        print(f"  embedding_chunks: {topic.embedding_chunks}")
        print(f"  file_path: {topic.file_path}")
        print(f"  file_size: {topic.file_size}")
        
        if not topic.is_indexed:
            print("\n❌ PROBLEM: Topic is NOT indexed")
            print("   → Staff member needs to upload a PDF for this topic first")
            print("   → Or PDF upload failed silently")
            return False
        
        if topic.embedding_chunks == 0:
            print("\n❌ PROBLEM: Topic has 0 embedding chunks")
            print("   → PDF was uploaded but not processed")
            print("   → Check if PDF extraction failed")
            return False
        
        print(f"\n✓ Topic is indexed with {topic.embedding_chunks} chunks")
        db.close()
        return True
    
    except Exception as e:
        print(f"❌ Error checking topic: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_vector_store():
    """Check if vector store directory and files exist"""
    print("\n" + "="*70)
    print("🔍 STEP 2: Check Vector Store Files")
    print("="*70)
    
    try:
        vector_db_path = Path(__file__).parent / "intelligent_placement_prep_analyser" / "backend" / "vector_db"
        topic_path = vector_db_path / "topic_1"
        
        print(f"\nVector DB path: {vector_db_path}")
        print(f"Topic path: {topic_path}")
        
        if not vector_db_path.exists():
            print("❌ Vector DB directory doesn't exist")
            return False
        
        print(f"✓ Vector DB directory exists")
        
        if not topic_path.exists():
            print("❌ Topic directory doesn't exist")
            return False
        
        print(f"✓ Topic directory exists")
        
        # Check for chroma.sqlite3
        chroma_file = topic_path / "chroma.sqlite3"
        if not chroma_file.exists():
            print("❌ chroma.sqlite3 database file not found")
            return False
        
        print(f"✓ Chroma database exists")
        
        # List contents
        print(f"\n📁 Contents of {topic_path.name}/:")
        for item in topic_path.iterdir():
            if item.is_file():
                size_mb = item.stat().st_size / (1024 * 1024)
                print(f"   📄 {item.name} ({size_mb:.2f} MB)")
            else:
                content_count = len(list(item.iterdir()))
                print(f"   📁 {item.name}/ ({content_count} items)")
        
        return True
    
    except Exception as e:
        print(f"❌ Error checking vector store: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_vector_search():
    """Test if vector search returns content"""
    print("\n" + "="*70)
    print("🔍 STEP 3: Test Vector Search")
    print("="*70)
    
    try:
        from app.services.vector_service import search_topic
        
        print(f"\nSearching vector store for topic 1...")
        
        search_query = "main concepts key topics definitions"
        print(f"Query: '{search_query}'")
        
        results = search_topic(topic_id=1, query=search_query, k=5)
        
        if not results:
            print("❌ Vector search returned NO results")
            print("   → Possible causes:")
            print("      1. Vector store is empty (PDF wasn't indexed)")
            print("      2. Chroma database is corrupted")
            print("      3. Google Embeddings API is not working")
            return False
        
        print(f"✓ Vector search returned {len(results)} results")
        
        for i, result in enumerate(results, 1):
            content = result.get("content", "")
            preview = content[:100].replace("\n", " ")
            page = result.get("page", "?")
            print(f"\n  [{i}] Page {page}")
            print(f"      {preview}...")
            if len(content) > 100:
                print(f"      (Total: {len(content)} characters)")
        
        return True
    
    except Exception as e:
        print(f"❌ Error in vector search: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_content_retrieval():
    """Check what content is passed to MCQ generator"""
    print("\n" + "="*70)
    print("🔍 STEP 4: Check Content Retrieval Pipeline")
    print("="*70)
    
    try:
        from app.database.db import SessionLocal
        from app.database.models import Topic
        from app.services.mcq_agent import _retrieve_topic_content
        
        db = SessionLocal()
        topic = db.query(Topic).filter(Topic.id == 1).first()
        
        if not topic:
            print("❌ Topic not found")
            return False
        
        print(f"\nRetrieving content for topic: {topic.title}")
        print(f"Topic is_indexed: {topic.is_indexed}")
        print(f"Topic chunks: {topic.embedding_chunks}")
        
        content = _retrieve_topic_content(topic)
        
        print(f"\nContent retrieved: {len(content)} characters")
        
        if not content or content.strip() == "":
            print("❌ PROBLEM: Content is empty!")
            print("   → This is why fallback MCQs are being used")
            print("   → Check vector search and topic indexing")
            return False
        
        # Check if it's just basic content
        if "Topic:" in content and "Description:" in content:
            print("⚠️  Content appears to be BASIC (fallback) format")
            print("   Not real PDF content")
            return False
        
        print(f"✓ Content retrieved successfully")
        print(f"\nContent preview (first 300 chars):")
        print(f"{'='*70}")
        print(content[:300])
        print(f"{'='*70}")
        
        db.close()
        return True
    
    except Exception as e:
        print(f"❌ Error in content retrieval: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_gemini_api():
    """Test if Gemini API is accessible"""
    print("\n" + "="*70)
    print("🔍 STEP 5: Test Gemini API")
    print("="*70)
    
    try:
        import google.generativeai as genai
        from app.config.settings import settings
        
        api_key = os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            print("❌ GOOGLE_API_KEY environment variable not set")
            return False
        
        print(f"✓ GOOGLE_API_KEY is set ({len(api_key)} chars)")
        
        genai.configure(api_key=api_key)
        # Use gemini-1.5-flash (most stable, widely available, and blazingly fast)
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Try a simple test
        print(f"\nTesting Gemini API with simple prompt...")
        
        test_response = model.generate_content(
            "Generate 1 MCQ question about Python in JSON format: ["
        )
        
        if test_response.text:
            print(f"✓ Gemini API is working")
            print(f"Response preview: {test_response.text[:100]}")
            return True
        else:
            print(f"❌ Gemini API returned empty response")
            return False
    
    except Exception as e:
        print(f"❌ Error testing Gemini API: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_pdf_file():
    """Check if PDF file exists and is valid"""
    print("\n" + "="*70)
    print("🔍 STEP 6: Check PDF File")
    print("="*70)
    
    try:
        from app.database.db import SessionLocal
        from app.database.models import Topic
        
        db = SessionLocal()
        topic = db.query(Topic).filter(Topic.id == 1).first()
        
        if not topic:
            print("❌ Topic not found")
            return False
        
        print(f"\nTopic file_path: {topic.file_path}")
        
        if not topic.file_path:
            print("❌ Topic has no file_path")
            print("   → PDF was never uploaded")
            return False
        
        if not os.path.exists(topic.file_path):
            print(f"❌ PDF file does not exist at: {topic.file_path}")
            print("   → File was deleted or moved")
            return False
        
        file_size = os.path.getsize(topic.file_path)
        print(f"✓ PDF file exists")
        print(f"  Size: {file_size / 1024:.2f} KB")
        
        db.close()
        return True
    
    except Exception as e:
        print(f"❌ Error checking PDF file: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all diagnostic checks"""
    print("\n" + "="*70)
    print("MCQ GENERATION DIAGNOSTIC SUITE")
    print("Checking why MCQs use fallback instead of PDF content")
    print("="*70)
    
    # Environment check
    print("\n🔧 Environment Check:")
    if os.getenv("GOOGLE_API_KEY"):
        print("  ✓ GOOGLE_API_KEY is set")
    else:
        print("  ✗ GOOGLE_API_KEY not set")
    
    # Run all checks
    results = {
        "PDF file exists": check_pdf_file(),
        "Topic indexed": check_topic_status(),
        "Vector store files": check_vector_store(),
        "Vector search works": check_vector_search(),
        "Content retrieval": check_content_retrieval(),
        "Gemini API": test_gemini_api(),
    }
    
    # Summary
    print("\n" + "="*70)
    print("📊 DIAGNOSTIC SUMMARY")
    print("="*70)
    
    for check_name, passed in results.items():
        status = "✓" if passed else "❌"
        print(f"{status} {check_name}")
    
    all_passed = all(results.values())
    
    print(f"\n{'='*70}")
    if all_passed:
        print("✅ ALL CHECKS PASSED!")
        print("   System should be generating MCQs from PDF content")
        print("   If still getting fallback: There's a logic issue in mcq_agent.py")
    else:
        print("❌ SOME CHECKS FAILED!")
        print("\nFix the issues in order:")
        for check_name, passed in results.items():
            if not passed:
                print(f"  1. {check_name}")
                print(f"     → See detailed error message above")
    
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
