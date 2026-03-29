#!/usr/bin/env python
"""
RAG System Verification Test
"""
import sys
sys.path.insert(0, '.')

def test_imports():
    """Test all RAG system imports"""
    print('Testing RAG system imports...\n')
    
    try:
        # Test vector service
        from app.services.vector_service import get_embeddings, create_text_splitter
        print('✓ Vector service imported')
        
        # Test PDF service
        from app.services.pdf_service import process_pdf_for_rag
        print('✓ PDF service imported')
        
        # Test models
        from app.database.models import Topic
        print('✓ Topic model imported')
        
        # Test embeddings
        embeddings = get_embeddings()
        print(f'✓ Embeddings initialized: {type(embeddings).__name__}')
        
        # Test text splitter
        splitter = create_text_splitter()
        print(f'✓ Text splitter created (chunk_size={splitter.chunk_size})')
        
        print('\n✓✓✓ All RAG imports successful! ✓✓✓\n')
        return True
        
    except Exception as e:
        print(f'✗ Error: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_imports()
    sys.exit(0 if success else 1)
