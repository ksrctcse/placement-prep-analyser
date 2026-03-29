from typing import List, Optional, Dict, Any
from pathlib import Path
import os
from app.config.settings import settings
import json
from datetime import datetime

class VectorStoreService:
    """
    Service for managing vector embeddings of resumes.
    Supports both ChromaDB and FAISS as backends.
    """
    
    def __init__(self):
        self.store_type = settings.VECTOR_STORE_TYPE
        self.store_path = settings.VECTOR_STORE_PATH
        
        # Create vector store directory if it doesn't exist
        Path(self.store_path).mkdir(parents=True, exist_ok=True)
        
        self._initialize_store()
    
    def _initialize_store(self):
        """Initialize the vector store based on configured type."""
        if self.store_type == "chromadb":
            self._init_chromadb()
        elif self.store_type == "faiss":
            self._init_faiss()
        else:
            raise ValueError(f"Unsupported vector store type: {self.store_type}")
    
    def _init_chromadb(self):
        """Initialize ChromaDB vector store."""
        try:
            import chromadb
            self.client = chromadb.PersistentClient(path=self.store_path)
            self.collection = self.client.get_or_create_collection(
                name="resumes",
                metadata={"hnsw:space": "cosine"}
            )
        except ImportError:
            raise ImportError("chromadb not installed. Install it with: pip install chromadb")
    
    def _init_faiss(self):
        """Initialize FAISS vector store."""
        try:
            import faiss
            import numpy as np
            self.faiss = faiss
            self.np = np
            
            # Initialize metadata store
            self.metadata_file = os.path.join(self.store_path, "metadata.json")
            self.embeddings_file = os.path.join(self.store_path, "embeddings.faiss")
            
            # Load or create index
            if os.path.exists(self.embeddings_file):
                self.index = faiss.read_index(self.embeddings_file)
                self._load_metadata()
            else:
                # Initialize FAISS index (768-dimensional vectors for embeddings)
                self.index = faiss.IndexFlatL2(768)
                self.metadata = {}
            
        except ImportError:
            raise ImportError("faiss not installed. Install it with: pip install faiss-cpu")
    
    def _load_metadata(self):
        """Load metadata from file."""
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {}
    
    def _save_metadata(self):
        """Save metadata to file."""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, default=str)
    
    async def add_resume(self, user_id: int, resume_content: str, file_name: str) -> str:
        """
        Add a resume to the vector store using embeddings.
        
        Args:
            user_id: User ID
            resume_content: Extracted text content from resume
            file_name: Original file name
        
        Returns:
            Vector store ID
        """
        # Generate embeddings (using a simple approach - in production use proper embedding model)
        embedding = await self._generate_embedding(resume_content)
        
        vector_id = f"resume_{user_id}_{int(datetime.utcnow().timestamp())}"
        
        if self.store_type == "chromadb":
            self.collection.add(
                ids=[vector_id],
                embeddings=[embedding],
                documents=[resume_content],
                metadatas=[{
                    "user_id": str(user_id),
                    "file_name": file_name,
                    "created_at": datetime.utcnow().isoformat()
                }]
            )
        elif self.store_type == "faiss":
            self.metadata[vector_id] = {
                "user_id": user_id,
                "file_name": file_name,
                "content": resume_content,
                "created_at": datetime.utcnow().isoformat()
            }
            self.index.add(self.np.array([embedding], dtype=self.np.float32))
            self._save_metadata()
        
        return vector_id
    
    async def search_resumes(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search resumes based on query text.
        
        Args:
            query: Search query
            top_k: Number of top results to return
        
        Returns:
            List of matching resumes with scores
        """
        query_embedding = await self._generate_embedding(query)
        
        if self.store_type == "chromadb":
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            formatted_results = []
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    "vector_id": results['ids'][0][i],
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i] if 'distances' in results else None
                })
            return formatted_results
        
        elif self.store_type == "faiss":
            distances, indices = self.index.search(
                self.np.array([query_embedding], dtype=self.np.float32),
                top_k
            )
            
            formatted_results = []
            for idx in indices[0]:
                if idx >= 0:  # FAISS returns -1 for non-existent indices
                    vector_id = list(self.metadata.keys())[idx]
                    metadata = self.metadata[vector_id]
                    formatted_results.append({
                        "vector_id": vector_id,
                        "content": metadata.get("content"),
                        "metadata": {k: v for k, v in metadata.items() if k != "content"},
                        "distance": float(distances[0][list(indices[0]).index(idx)])
                    })
            return formatted_results
    
    async def get_resume(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific resume from vector store.
        
        Args:
            vector_id: Vector store ID
        
        Returns:
            Resume data or None if not found
        """
        if self.store_type == "chromadb":
            results = self.collection.get(ids=[vector_id])
            if results and results['ids']:
                return {
                    "vector_id": results['ids'][0],
                    "content": results['documents'][0],
                    "metadata": results['metadatas'][0]
                }
        
        elif self.store_type == "faiss":
            if vector_id in self.metadata:
                metadata = self.metadata[vector_id]
                return {
                    "vector_id": vector_id,
                    "content": metadata.get("content"),
                    "metadata": {k: v for k, v in metadata.items() if k != "content"}
                }
        
        return None
    
    async def delete_resume(self, vector_id: str) -> bool:
        """
        Delete a resume from vector store.
        
        Args:
            vector_id: Vector store ID
        
        Returns:
            True if deleted successfully
        """
        try:
            if self.store_type == "chromadb":
                self.collection.delete(ids=[vector_id])
            elif self.store_type == "faiss":
                if vector_id in self.metadata:
                    del self.metadata[vector_id]
                    self._save_metadata()
            return True
        except Exception as e:
            print(f"Error deleting resume: {e}")
            return False
    
    async def update_resume(self, user_id: int, resume_content: str, vector_id: str) -> bool:
        """
        Update an existing resume.
        
        Args:
            user_id: User ID
            resume_content: Updated resume content
            vector_id: Existing vector store ID
        
        Returns:
            True if updated successfully
        """
        try:
            # Delete old resume
            await self.delete_resume(vector_id)
            
            # Add updated resume
            new_id = await self.add_resume(user_id, resume_content, f"updated_{vector_id}")
            return True
        except Exception as e:
            print(f"Error updating resume: {e}")
            return False
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text.
        This is a placeholder - in production, use proper embedding models like:
        - sentence-transformers
        - OpenAI embeddings
        - Google embeddings
        - LangChain embedding models
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector
        """
        try:
            # Try to use sentence-transformers if available
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            embedding = model.encode(text, convert_to_tensor=False).tolist()
            return embedding
        except ImportError:
            # Fallback: Simple TF-IDF style embedding (not recommended for production)
            import hashlib
            
            # Create a deterministic 768-dimensional vector from text
            hash_obj = hashlib.sha256(text.encode())
            hash_bytes = hash_obj.digest()
            
            # Generate 768-dimensional vector from hash
            import struct
            embedding = []
            for i in range(768):
                # Use different parts of hash and modulo for variety
                chunk = (i * 3) % len(hash_bytes)
                value = struct.unpack('B', bytes([hash_bytes[chunk]]))[0]
                embedding.append(float((value - 128) / 128.0))
            
            return embedding

# Create a singleton instance
_vector_store = None

def get_vector_store() -> VectorStoreService:
    """Get or create vector store service instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreService()
    return _vector_store
