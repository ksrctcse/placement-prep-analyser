
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Lazy initialization - only create when first needed
embeddings = None
vector_store = None

def get_embeddings():
    """Get or create embeddings instance (lazy loading)"""
    global embeddings
    if embeddings is None:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-004")
    return embeddings

def get_vector_store():
    """Get or create vector store instance (lazy loading)"""
    global vector_store
    if vector_store is None:
        vector_store = FAISS.from_texts(["init"], get_embeddings())
    return vector_store

def add_chunks(chunks):
    """Add text chunks to vector store"""
    if chunks:
        get_vector_store().add_texts(chunks)

def search_resume(query):
    """Search vector store for similar resume content"""
    return get_vector_store().similarity_search(query)
