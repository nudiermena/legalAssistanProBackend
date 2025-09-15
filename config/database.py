import os
from typing import Optional, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Try to import the correct Agno v2.0 API, fallback to older API if needed
try:
    from agno.db.postgres import PostgresDb
    from agno.db.sqlite import SqliteDb
    AGNO_V2_AVAILABLE = True
except ImportError:
    # Fallback to older API
    try:
        from agno.storage.postgres import PostgresStorage as PostgresDb
        from agno.storage.sqlite import SqliteStorage as SqliteDb
        AGNO_V2_AVAILABLE = False
    except ImportError:
        # No Agno database support available
        PostgresDb = None
        SqliteDb = None
        AGNO_V2_AVAILABLE = False

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

    # If explicitly using SQLite fallback, return a SqliteDb instance
    if use_sqlite_fallback:
        if SqliteDb is None:
            print("Warning: No SQLite database support available")
            return None
        try:
            os.makedirs("tmp", exist_ok=True)
            if AGNO_V2_AVAILABLE:
                return SqliteDb(db_file="tmp/agent_storage.db")
            else:
                return SqliteDb(table_name=table_name, db_file="tmp/agent_storage.db")
        except Exception as e:
            print(f"Warning: Could not initialize SQLite storage: {str(e)}")
            # Continue to try Postgres below as a last resort

    # Try Postgres first
    if PostgresDb is None:
        print("Warning: No PostgreSQL database support available")
        return None
        
    pg_url = _resolve_database_url()
    try:
        if AGNO_V2_AVAILABLE:
            # Use PostgresDb from agno.db.postgres (Agno v2.0)
            return PostgresDb(db_url=pg_url)
        else:
            # Use PostgresStorage from agno.storage.postgres (older API)
            return PostgresDb(table_name=table_name, db_url=pg_url)
    except Exception as e:
        print(f"Warning: Could not initialize Postgres storage: {str(e)}")

    # Fallback to SQLite if Postgres failed
    if SqliteDb is None:
        print("Warning: No SQLite database support available for fallback")
        return None
        
    try:
        os.makedirs("tmp", exist_ok=True)
        if AGNO_V2_AVAILABLE:
            return SqliteDb(db_file="tmp/agent_storage.db")
        else:
            return SqliteDb(table_name=table_name, db_file="tmp/agent_storage.db")
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