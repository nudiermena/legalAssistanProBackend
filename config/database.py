from agno.storage.agent.postgres import PostgresAgentStorage

# Database configuration
db_url = "postgresql+psycopg://postgres:postgres@localhost:5432/ai_legal_vector"

def get_agent_storage(table_name: str) -> PostgresAgentStorage:
    """Get a PostgresAgentStorage instance for the specified table"""
    return PostgresAgentStorage(table_name=table_name, db_url=db_url) 