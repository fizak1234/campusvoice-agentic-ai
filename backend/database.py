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
                # Users table
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'user';"))
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();"))
                
                # Grievances table
                conn.execute(text("ALTER TABLE grievances ADD COLUMN IF NOT EXISTS priority VARCHAR(50) DEFAULT 'Medium';"))
                conn.execute(text("ALTER TABLE grievances ADD COLUMN IF NOT EXISTS ai_summary TEXT;"))
                conn.execute(text("ALTER TABLE grievances ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();"))
                conn.execute(text("ALTER TABLE grievances ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();"))
                
                # Service Requests table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS service_requests (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id),
                        request_type VARCHAR(50) NOT NULL DEFAULT 'Grievance',
                        title VARCHAR(250) NOT NULL,
                        description TEXT NOT NULL,
                        category VARCHAR(100) NOT NULL,
                        status VARCHAR(50) DEFAULT 'Pending',
                        priority VARCHAR(50) DEFAULT 'Medium',
                        detected_language VARCHAR(20) DEFAULT 'en',
                        agent_plan TEXT,
                        policy_citations TEXT,
                        requires_hitl BOOLEAN DEFAULT FALSE,
                        hitl_reason TEXT,
                        hitl_decision VARCHAR(50),
                        hitl_approver VARCHAR(100),
                        hitl_notes TEXT,
                        execution_result TEXT,
                        ai_summary TEXT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """))
                
                # Audit Logs table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS audit_logs (
                        id SERIAL PRIMARY KEY,
                        request_id INTEGER NOT NULL REFERENCES service_requests(id) ON DELETE CASCADE,
                        step_number INTEGER NOT NULL,
                        actor VARCHAR(50) NOT NULL,
                        action VARCHAR(100) NOT NULL,
                        details TEXT NOT NULL,
                        policy_ref VARCHAR(100),
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """))
                
                conn.commit()
            except Exception as e:
                logger.warning(f"Database schema initialization note: {e}")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()