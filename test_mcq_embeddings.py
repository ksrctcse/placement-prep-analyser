#!/usr/bin/env python3 
"""
Test script to verify MCQ generation from embedded chunks
Run this to test if MCQs are being generated from vector embeddings
"""

import os
import sys
import json
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "intelligent_placement_prep_analyser" / "backend"
sys.path.insert(0, str(backend_path))

def test_vector_search():
    """Test if vector search is working for topics"""
    print("\n" + "="*60)
    print("🔍 TEST 1: Vector Search Functionality")
    print("="*60)
    
    try:
        from app.services.vector_service import search_topic
        
        print("\n✓ Successfully imported vector_service")
        
        # Try searching with a few topics
        for topic_id in [1, 2, 3]:
            print(f"\n  Testing search for topic_id={topic_id}:")
            results = search_topic(
                topic_id=topic_id,
                query="main concepts key ideas definitions",
                k=3
            )
            
            if results:
                print(f"  ✓ Found {len(results)} chunks")
                for i, result in enumerate(results, 1):
                    content_preview = result.get("content", "")[:80].replace("\n", " ")
                    print(f"    [{i}] {content_preview}...")
            else:
                print(f"  ⚠️  No results found - topic may not be indexed yet")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_topic_indexing_status():
    """Check which topics are indexed"""
    print("\n" + "="*60)
    print("📊 TEST 2: Topic Indexing Status")
    print("="*60)
    
    try:
        from app.database.db import SessionLocal
        from app.database.models import Topic
        
        db = SessionLocal()
        topics = db.query(Topic).all()
        
        if not topics:
            print("\n⚠️  No topics found in database")
            return
        
        print(f"\n📚 Found {len(topics)} total topics:\n")
        
        indexed_count = 0
        not_indexed_count = 0
        
        for topic in topics:
            status = "✓" if topic.is_indexed else "✗"
            chunks = f"{topic.embedding_chunks} chunks" if topic.embedding_chunks > 0 else "no chunks"
            print(f"  {status} [{topic.id:2d}] {topic.title:30s} | indexed={topic.is_indexed}, {chunks}")
            
            if topic.is_indexed and topic.embedding_chunks > 0:
                indexed_count += 1
            else:
                not_indexed_count += 1
        
        print(f"\n📈 Summary:")
        print(f"  ✓ Indexed topics: {indexed_count}")
        print(f"  ✗ Not indexed: {not_indexed_count}")
        
        db.close()
        
        if indexed_count == 0:
            print("\n⚠️  WARNING: No topics are indexed! MCQs will use fallback mode.")
            print("   → Have a staff member upload PDFs and wait for indexing to complete.")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_mcq_generation():
    """Test MCQ generation for an indexed topic"""
    print("\n" + "="*60)
    print("✍️  TEST 3: MCQ Generation from Embeddings")
    print("="*60)
    
    try:
        from app.database.db import SessionLocal
        from app.database.models import Topic, StudentProfile
        from app.services.mcq_agent import generate_mcqs_from_topics
        
        db = SessionLocal()
        
        # Find an indexed topic
        indexed_topic = db.query(Topic).filter(
            Topic.is_indexed == True,
            Topic.embedding_chunks > 0
        ).first()
        
        if not indexed_topic:
            print("\n⚠️  No indexed topics found!")
            print("   → Solution: Have a staff member upload PDFs to a topic first")
            print("   → Then wait for indexing to complete (is_indexed = true)")
            db.close()
            return
        
        # Find a student
        student = db.query(StudentProfile).first()
        
        if not student:
            print("\n⚠️  No students found in database!")
            print("   → Create a student account first")
            db.close()
            return
        
        print(f"\n🎯 Test Configuration:")
        print(f"  Topic: {indexed_topic.title} (ID: {indexed_topic.id})")
        print(f"  Topic chunks: {indexed_topic.embedding_chunks}")
        print(f"  Student: {student.name}")
        print(f"\n📝 Generating exactly 10 MCQs from indexed PDF content...\n")
        
        result = generate_mcqs_from_topics(
            db=db,
            topic_ids=[indexed_topic.id],
            student_id=student.id,
            num_questions=10,
            min_questions=10,  # Minimum 10 from embeddings
            max_questions=10
        )
        
        if result.get("success"):
            mcqs = result.get("mcqs", [])
            print(f"\n✅ SUCCESS: Generated {len(mcqs)} MCQs\n")
            
            # Check minimum 10 MCQs requirement
            if len(mcqs) < 10:
                print(f"⚠️  WARNING: Got {len(mcqs)} MCQs but expected minimum 10!")
            else:
                print(f"✓ Generated minimum 10 MCQs requirement met!")
            
            # Analyze sources
            embedding_count = sum(1 for mcq in mcqs if mcq.get("source") == "embeddings")
            fallback_count = sum(1 for mcq in mcqs if mcq.get("source") == "fallback")
            
            print(f"\n📊 Source Breakdown:")
            print(f"  From embeddings: {embedding_count}/{len(mcqs)}")
            print(f"  From fallback:   {fallback_count}/{len(mcqs)}")
            
            if embedding_count >= 10:
                print(f"\n✓ EXCELLENT! All 10+ MCQs are from indexed embeddings (no fallback)")
            elif embedding_count > 0:
                print(f"\n✓ Good! {embedding_count} MCQs are from indexed embeddings")
                print(f"  {fallback_count} MCQs used fallback (AI generation may have had issues)")
            else:
                print(f"\n⚠️  WARNING: All MCQs are using fallback mode")
                print(f"   → Check if topic is properly indexed with uploaded PDFs")
                print(f"   → Verify vector store has content for topic {indexed_topic.id}")
                print(f"   → Check if Gemini API is properly configured")
            
            # Show first MCQ as example
            if mcqs:
                print(f"\n📌 Example MCQ:")
                mcq = mcqs[0]
                print(f"  Q: {mcq.get('question', 'N/A')[:80]}...")
                print(f"  A) {mcq.get('option_a', 'N/A')[:60]}")
                print(f"  B) {mcq.get('option_b', 'N/A')[:60]}")
                print(f"  Correct: {mcq.get('correct_option')}")
                print(f"  Source: {mcq.get('source', 'unknown')}")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
        
        db.close()
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_vector_store_files():
    """Check if vector store directories exist"""
    print("\n" + "="*60)
    print("📁 TEST 4: Vector Store Files")
    print("="*60)
    
    vector_db_path = Path(__file__).parent / "intelligent_placement_prep_analyser" / "backend" / "vector_db"
    
    if not vector_db_path.exists():
        print(f"\n⚠️  Vector DB directory doesn't exist yet")
        print(f"   Path: {vector_db_path}")
        print(f"   → It will be created when first PDF is indexed")
        return
    
    print(f"\n📂 Vector DB Structure:")
    
    topic_dirs = sorted([d for d in vector_db_path.iterdir() if d.is_dir() and d.name.startswith("topic_")])
    
    if not topic_dirs:
        print(f"   No topic directories found in {vector_db_path}")
        return
    
    for topic_dir in topic_dirs:
        topic_id = topic_dir.name.replace("topic_", "")
        
        # Check for chroma.sqlite3
        chroma_file = topic_dir / "chroma.sqlite3"
        has_chroma = chroma_file.exists()
        
        # Count data directories
        data_dirs = len([d for d in topic_dir.iterdir() if d.is_dir() and len(d.name) > 10])
        
        status = "✓" if has_chroma else "✗"
        print(f"  {status} topic_{topic_id}/")
        print(f"     chroma.sqlite3: {'present' if has_chroma else 'missing'}")
        print(f"     data collections: {data_dirs}")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 MCQ EMBEDDING TEST SUITE")
    print("="*60)
    
    # Check environment
    print("\n🔧 Environment Check:")
    if os.getenv("GOOGLE_API_KEY"):
        print(f"  ✓ GOOGLE_API_KEY is set")
    else:
        print(f"  ✗ GOOGLE_API_KEY not set - embeddings will fail")
    
    # Run tests
    test_topic_indexing_status()
    test_vector_store_files()
    test_vector_search()
    test_mcq_generation()
    
    print("\n" + "="*60)
    print("✨ Test Suite Complete")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
