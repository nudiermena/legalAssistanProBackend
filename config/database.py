import os
from agno.storage.postgres import PostgresStorage
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
db_url = os.getenv('DATABASE_URL', 'postgresql+psycopg://postgres:postgres@localhost:5432/ai_legal_vector')

def get_agent_storage(table_name: str) -> PostgresStorage:
    """Get a PostgresStorage instance for the specified table"""
    return PostgresStorage(
        table_name=table_name,
        db_url=db_url,
        schema="ai",
        auto_upgrade_schema=True,
        schema_version=1
    ) 