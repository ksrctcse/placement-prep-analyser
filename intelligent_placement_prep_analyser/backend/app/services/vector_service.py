
from langchain.vectorstores import FAISS
from langchain.embeddings import GoogleGenerativeAIEmbeddings

embeddings=GoogleGenerativeAIEmbeddings(model="models/embedding-001")
vector_store=FAISS.from_texts(["init"],embeddings)

def add_chunks(chunks):
    vector_store.add_texts(chunks)

def search_resume(query):
    return vector_store.similarity_search(query)
