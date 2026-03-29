
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from backend directory (parent of app directory)
backend_dir = Path(__file__).parent.parent.parent  # app/config/settings.py -> backend/
env_file = backend_dir / ".env"
load_dotenv(env_file)

class Settings:
    # Load API key from .env file
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    JWT_SECRET = os.getenv("JWT_SECRET", "placement_secret")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///placement.db")
    SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", "False").lower() == "true"
    SQLALCHEMY_POOL_SIZE = int(os.getenv("SQLALCHEMY_POOL_SIZE", "5"))
    SQLALCHEMY_MAX_OVERFLOW = int(os.getenv("SQLALCHEMY_MAX_OVERFLOW", "10"))

settings = Settings()
