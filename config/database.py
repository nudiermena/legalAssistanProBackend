import os
from typing import Optional
from agno.storage.agent.postgres import PostgresAgentStorage
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Get database URL from environment variable or use a default for local development
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/legal_assistant"
)

def get_agent_storage() -> Optional[PostgresAgentStorage]:
    """Get agent storage with fallback to in-memory storage if database is not available"""
    try:
        # Create SQLAlchemy engine
        engine = create_engine(DATABASE_URL)
        
        # Create session factory
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Create and return PostgresAgentStorage
        return PostgresAgentStorage(engine=engine, session_factory=SessionLocal)
    except Exception as e:
        print(f"Warning: Could not initialize database storage: {str(e)}")
        print("Falling back to in-memory storage")
        return None

# For local development
if __name__ == "__main__":
    storage = get_agent_storage()
    if storage:
        print("Database connection successful")
    else:
        print("Using in-memory storage") 