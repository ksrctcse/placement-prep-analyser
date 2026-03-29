
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from app.config.settings import settings

# Create engine with connection pooling for PostgreSQL
if "postgresql" in settings.DATABASE_URL:
    engine = create_engine(
        settings.DATABASE_URL,
        poolclass=QueuePool,
        pool_size=settings.SQLALCHEMY_POOL_SIZE,
        max_overflow=settings.SQLALCHEMY_MAX_OVERFLOW,
        echo=settings.SQLALCHEMY_ECHO,
        connect_args={"connect_timeout": 10}
    )
else:
    engine = create_engine(settings.DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
