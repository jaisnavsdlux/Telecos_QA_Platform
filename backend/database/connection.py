"""
Database Connection & Engine Factory for Neon PostgreSQL & Local SQLite Fallback.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

# Neon PostgreSQL connection string (or local SQLite fallback)
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if not DATABASE_URL:
    # Local fallback SQLite database
    db_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db")
    os.makedirs(db_dir, exist_ok=True)
    sqlite_path = os.path.join(db_dir, "telecos.db")
    DATABASE_URL = f"sqlite:///{sqlite_path}"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    # Fix postgres:// legacy prefixes from some providers to postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    # Connection pool configuration for Neon Serverless Postgres
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=5,
        max_overflow=10
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """FastAPI Dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
