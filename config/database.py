import os
from agno.storage.agent.postgres import PostgresAgentStorage
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
db_url = os.getenv('DATABASE_URL', 'postgresql+psycopg://postgres:postgres@localhost:5432/ai_legal_vector')

def get_agent_storage(table_name: str) -> PostgresAgentStorage:
    """Get a PostgresAgentStorage instance for the specified table"""
    return PostgresAgentStorage(connection_string=db_url) 