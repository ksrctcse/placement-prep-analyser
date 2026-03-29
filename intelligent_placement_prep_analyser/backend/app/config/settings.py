
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # API Configuration
    APP_NAME = "Placement Prep Analyser"
    DEBUG = os.getenv("DEBUG", "True") == "True"
    
    # Database Configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///placement.db")
    
    # JWT Configuration
    JWT_SECRET = os.getenv("JWT_SECRET", "placement_secret_key_change_in_production")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 24
    REFRESH_TOKEN_EXPIRATION_DAYS = 7
    
    # Gemini API Configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
    
    # Vector Store Configuration
    VECTOR_STORE_TYPE = os.getenv("VECTOR_STORE_TYPE", "chromadb")  # chromadb or faiss
    VECTOR_STORE_PATH = os.getenv("VECTOR_STORE_PATH", "./vector_store")
    
    # Security
    ALLOW_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
    ]

settings = Settings()
