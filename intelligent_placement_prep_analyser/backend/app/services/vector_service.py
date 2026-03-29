
from langchain_community.vectorstores import FAISS, Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
import json
from pathlib import Path

# Lazy initialization of vector store
_embeddings = None
_vector_stores = {}  # Store per topic for isolation
VECTOR_DB_PATH = os.path.join(os.path.dirname(__file__), '../../vector_db')

def get_embeddings():
    """Get or initialize embeddings using Google Generative AI"""
    global _embeddings
    if _embeddings is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY environment variable not set. "
                "Please set the API key in your .env file or environment variables."
            )
        try:
            # Pass API key explicitly to ensure it's used
            # Use gemini-embedding-001 - the stable embedding model available in Google Generative AI
            _embeddings = GoogleGenerativeAIEmbeddings(
                model="models/gemini-embedding-001",
                google_api_key=api_key
            )
            print(f"✓ Embeddings initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize embeddings: {e}")
            raise
    return _embeddings

def create_text_splitter():
    """Create a text splitter for PDF chunks"""
    return RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " ", ""]
    )

def create_topic_vector_store(topic_id: int):
    """Create and return a vector store for a specific topic"""
    embeddings = get_embeddings()
    topic_path = os.path.join(VECTOR_DB_PATH, f"topic_{topic_id}")
    os.makedirs(topic_path, exist_ok=True)
    
    vector_store = Chroma(
        collection_name=f"topic_{topic_id}",
        embedding_function=embeddings,
        persist_directory=topic_path
    )
    return vector_store

def get_vector_store(topic_id: int):
    """Get or initialize vector store for a specific topic"""
    if topic_id not in _vector_stores:
        _vector_stores[topic_id] = create_topic_vector_store(topic_id)
    return _vector_stores[topic_id]

def add_text_chunks(topic_id: int, texts: list, metadatas: list = None):
    """Add text chunks to vector store with metadata"""
    if not texts:
        print(f"⚠️  No texts to add for topic {topic_id}")
        return 0
    
    print(f"🔄 Adding {len(texts)} chunks to vector store for topic {topic_id}...")
    
    try:
        # Get embeddings function first to test API connection
        embeddings = get_embeddings()
        print(f"✓ Embeddings initialized")
        
        vector_store = get_vector_store(topic_id)
        print(f"✓ Vector store created/loaded for topic {topic_id}")
        
        # Add texts with metadata (e.g., page numbers, source)
        if metadatas is None:
            metadatas = [{"topic_id": topic_id} for _ in texts]
        else:
            for meta in metadatas:
                meta["topic_id"] = topic_id
        
        # Add to vector store
        ids = vector_store.add_texts(texts, metadatas=metadatas)
        print(f"✓ Added {len(ids)} text chunks to vector store")
        
        vector_store.persist()
        print(f"✓ Vector store persisted to disk")
        
        return len(texts)
    except ValueError as e:
        print(f"❌ Configuration error for topic {topic_id}: {e}")
        print(f"   Make sure GOOGLE_API_KEY environment variable is set")
        raise
    except Exception as e:
        print(f"❌ Error adding chunks for topic {topic_id}: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise

def search_topic(topic_id: int, query: str, k: int = 5):
    """Search similar content within a specific topic"""
    if not query or not query.strip():
        return []
    
    try:
        vector_store = get_vector_store(topic_id)
        results = vector_store.similarity_search(query, k=k)
        return [
            {
                "content": doc.page_content,
                "page": doc.metadata.get("page", "N/A"),
                "score": doc.metadata.get("score", 0)
            }
            for doc in results
        ]
    except Exception as e:
        print(f"Error searching topic {topic_id}: {e}")
        return []

def search_resume(query: str = ""):
    """Legacy function for resume search (kept for backward compatibility)"""
    if not query:
        return []
    # This can be expanded for cross-topic search if needed
    return []

def delete_topic_store(topic_id: int):
    """Delete vector store for a topic (when topic is deleted)"""
    if topic_id in _vector_stores:
        del _vector_stores[topic_id]
    
    topic_path = os.path.join(VECTOR_DB_PATH, f"topic_{topic_id}")
    if os.path.exists(topic_path):
        import shutil
        shutil.rmtree(topic_path, ignore_errors=True)


# Backward compatibility function for legacy resume service
def add_chunks(chunks):
    """Legacy function for backward compatibility with resume_service"""
    # Resume processing - store in a generic collection
    if not chunks:
        return 0
    
    embeddings = get_embeddings()
    resume_store_path = os.path.join(VECTOR_DB_PATH, "resumes")
    os.makedirs(resume_store_path, exist_ok=True)
    
    try:
        vector_store = Chroma(
            collection_name="resumes",
            embedding_function=embeddings,
            persist_directory=resume_store_path
        )
        vector_store.add_texts(chunks)
        vector_store.persist()
        return len(chunks)
    except Exception as e:
        print(f"Error adding resume chunks: {e}")
        return 0
