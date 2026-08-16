import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/ai_grievance_db"
)

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )
except Exception as e:
    logger.error(f"Failed to create database engine for {DATABASE_URL}: {e}")
    engine = create_engine("sqlite:///./ai_grievance_fallback.db", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def init_db_schema():
    """Ensures tables and all required columns exist in PostgreSQL or SQLite."""
    Base.metadata.create_all(bind=engine)
    # Perform column migrations safely if using PostgreSQL
    if "postgresql" in str(engine.url):
        with engine.connect() as conn:
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'user';"))
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();"))
                conn.execute(text("ALTER TABLE grievances ADD COLUMN IF NOT EXISTS priority VARCHAR(50) DEFAULT 'Medium';"))
                conn.execute(text("ALTER TABLE grievances ADD COLUMN IF NOT EXISTS ai_summary TEXT;"))
                conn.execute(text("ALTER TABLE grievances ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();"))
                conn.execute(text("ALTER TABLE grievances ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();"))
                conn.commit()
            except Exception as e:
                logger.warning(f"Column check warning: {e}")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()