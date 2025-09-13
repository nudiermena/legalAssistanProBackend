import os
from typing import Optional, Any
from agno.storage.agent.postgres import PostgresAgentStorage
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def _resolve_database_url() -> str:
    """Resolve the Postgres connection URL.

    Preference order:
    1) Environment POSTGRES_URL
    2) config.settings.POSTGRES_URL
    3) Environment DATABASE_URL
    4) Local default
    """
    # 1) Environment POSTGRES_URL
    postgres_url = os.getenv("POSTGRES_URL")
    if postgres_url:
        return postgres_url

    # 2) config.settings.POSTGRES_URL (if available)
    try:
        from config.settings import POSTGRES_URL as SETTINGS_POSTGRES_URL  # type: ignore
        if SETTINGS_POSTGRES_URL:
            return SETTINGS_POSTGRES_URL
    except Exception:
        pass

    # 3) Environment DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    # 4) Local default
    return "postgresql://postgres:postgres@localhost:5432/legal_assistant"

def get_agent_storage(table_name: str = "agent_sessions") -> Optional[Any]:
    """Get agent storage with optional table name.

    Accepts an optional table_name so callers like agents can pass
    a session-specific table (e.g., "document_sessions"). Falls back
    gracefully to SQLite if configured or if the database is unavailable.
    """
    # Allow explicit SQLite fallback via env var
    use_sqlite_fallback = os.getenv("USE_SQLITE_FALLBACK", "false").lower() == "true"

    # If explicitly using SQLite fallback, return a SqliteStorage instance
    if use_sqlite_fallback:
        try:
            from agno.storage.sqlite import SqliteStorage
            os.makedirs("tmp", exist_ok=True)
            return SqliteStorage(table_name=table_name, db_file="tmp/agent_storage.db")
        except Exception as e:
            print(f"Warning: Could not initialize SQLite storage: {str(e)}")
            # Continue to try Postgres below as a last resort

    # Try Postgres first
    pg_url = _resolve_database_url()
    try:
        engine = create_engine(pg_url)
        # Initialize a session factory (kept for completeness; not used directly here)
        _ = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return PostgresAgentStorage(table_name=table_name, db_engine=engine)
    except Exception as e:
        print(f"Warning: Could not initialize Postgres storage: {str(e)}")

    # Fallback to SQLite if Postgres failed
    try:
        from agno.storage.sqlite import SqliteStorage
        os.makedirs("tmp", exist_ok=True)
        return SqliteStorage(table_name=table_name, db_file="tmp/agent_storage.db")
    except Exception as e:
        print(f"Warning: Could not initialize SQLite storage on fallback: {str(e)}")
        print("Falling back to in-memory storage")
        return None

# For local development
if __name__ == "__main__":
    storage = get_agent_storage()
    if storage:
        print("Database connection successful")
    else:
        print("Using in-memory storage") 