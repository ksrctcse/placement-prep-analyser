
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os

# Lazy initialization of vector store
_vector_store = None
_embeddings = None

def get_embeddings():
    """Get or initialize embeddings"""
    global _embeddings
    if _embeddings is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        _embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    return _embeddings

def get_vector_store():
    """Get or initialize vector store"""
    global _vector_store
    if _vector_store is None:
        embeddings = get_embeddings()
        _vector_store = FAISS.from_texts(["init"], embeddings)
    return _vector_store

def add_chunks(chunks):
    """Add text chunks to vector store"""
    if not chunks:
        return
    vector_store = get_vector_store()
    vector_store.add_texts(chunks)

def search_resume(query):
    """Search for relevant documents"""
    if not query:
        return []
    vector_store = get_vector_store()
    return vector_store.similarity_search(query)
