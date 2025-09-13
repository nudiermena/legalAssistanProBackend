"""
Enhanced Agent Configuration for Legal AI Assistant
Implements Reasoning, Knowledge, Storage, and Memory capabilities
"""

import os as os_module
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
from agno.storage.agent.postgres import PostgresAgentStorage
from agno.knowledge.pdf_url import PDFUrlKnowledgeBase
from agno.knowledge.website import WebsiteKnowledgeBase
from agno.knowledge.combined import CombinedKnowledgeBase
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.ai_models import get_embedder

logger = logging.getLogger(__name__)

class EnhancedAgentConfig:
    """Configuration for enhanced agent capabilities"""
    
    def __init__(self):
        self.vector_db = None
        self.knowledge_base = None
        self.storage = None
        
    def initialize_vector_db(self):
        """Initialize vector database for knowledge storage using Supabase"""
        # Check if vector database is enabled - default to true for development
        if os_module.getenv("ENABLE_VECTOR_DB", "true").lower() == "false":
            logger.info("Vector database disabled for development")
            self.vector_db = None
            return
            
        try:
            # Get Supabase configuration from environment or settings
            supabase_url = os_module.getenv("SUPABASE_URL")
            supabase_service_role_key = os_module.getenv("SUPABASE_SERVICE_ROLE_KEY")
            
            # If not in environment, try to get from settings
            if not supabase_url or not supabase_service_role_key:
                try:
                    from config.settings import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
                    supabase_url = SUPABASE_URL
                    supabase_service_role_key = SUPABASE_SERVICE_ROLE_KEY
                except ImportError:
                    pass
            
            if supabase_url and supabase_service_role_key:
                # Use the correct POSTGRES_URL from settings
                try:
                    from config.settings import POSTGRES_URL
                    db_url = POSTGRES_URL
                except ImportError:
                    # Fallback to constructing the URL
                    project_ref = supabase_url.split('//')[1].split('.')[0]
                    db_url = f"postgresql://postgres.{project_ref}:{supabase_service_role_key.split('.')[0]}@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
                
                # Try to use Supabase as vector database
                try:
                    from agno.vectordb.pgvector import PgVector, SearchType
                    # Initialize PgVector without embedder first to avoid validation issues
                    self.vector_db = PgVector(
                        table_name="legal_documents_ai",
                        db_url=db_url,
                        search_type=SearchType.hybrid
                    )
                    logger.info("Using Supabase as vector database with PgVector")
                    
                    # Try to set embedder after initialization if available
                    try:
                        embedder = get_embedder()
                        if embedder and hasattr(self.vector_db, 'embedder'):
                            self.vector_db.embedder = embedder
                            logger.info("Mistral embedder set on PgVector successfully")
                    except Exception as embedder_error:
                        logger.warning(f"Could not set embedder on PgVector: {embedder_error}")
                        # Continue without embedder - PgVector will use default
                except ImportError:
                    logger.warning("agno.vectordb.pgvector not available, using fallback")
                    # Fallback to in-memory vector database
                    try:
                        from agno.vectordb.memory import MemoryVectorDB
                        self.vector_db = MemoryVectorDB()
                        logger.info("Using in-memory vector database as fallback")
                    except ImportError:
                        logger.warning("No vector database available, knowledge base disabled")
                        self.vector_db = None
            else:
                self.vector_db = None
                logger.warning("Supabase credentials not found, vector database disabled")
                
        except Exception as e:
            logger.warning(f"Failed to initialize vector database: {e}")
            # Fallback to in-memory vector database
            try:
                from agno.vectordb.memory import MemoryVectorDB
                self.vector_db = MemoryVectorDB()
                logger.info("Using in-memory vector database as fallback")
            except ImportError:
                self.vector_db = None
                logger.warning("No vector database available, knowledge base disabled")
    
    def initialize_knowledge_base(self):
        """Initialize knowledge base with legal documents and websites"""
        if not self.vector_db:
            self.initialize_vector_db()
            
        try:
            if self.vector_db:
                # Get Mistral embedder from our custom implementation
                embedder = None
                try:
                    from config.ai_models import get_embedder
                    embedder = get_embedder()
                    if embedder:
                        logger.info("Mistral embedder loaded from custom implementation")
                    else:
                        logger.warning("Mistral embedder not available from custom implementation")
                except Exception as e:
                    logger.warning(f"Failed to load Mistral embedder: {e}")
                
                if not embedder:
                    logger.warning("Mistral embedder not available, knowledge base will use default embedder")
                
                # Colombian legal knowledge sources
                legal_sources = {
                    "pdfs": [
                        "https://biblioteca.gafilat.org/wp-content/uploads/2024/07/Recomendaciones-metodologia-actDIC2023.pdf",
                        "https://www.supersociedades.gov.co/web/sites/default/files/2024-01/Manual%20de%20Autocontrol%20y%20Gesti%C3%B3n%20del%20Riesgo%20Integral.pdf"
                    ],
                    "websites": [
                        "https://www.supersociedades.gov.co/web/nuestra-entidad/cap-10-autocontrol-y-gesti%C3%B3n-del-riesgo-integral",
                        "https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=175606",
                        "https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=43292",
                        "https://www.ramajudicial.gov.co",
                        "https://www.corteconstitucional.gov.co",
                        "https://www.consejodeestado.gov.co",
                        "https://www.cortesuprema.gov.co"
                    ]
                }
                
                # Create knowledge bases with Supabase vector database and Mistral embedder
                # Following the pattern from Agno docs: knowledge_base = AgentKnowledge(vector_db=PgVector(...), embedder=MistralEmbedder())
                pdf_knowledge = PDFUrlKnowledgeBase(
                    urls=legal_sources["pdfs"],
                    vector_db=self.vector_db,
                    embedder=embedder
                )
                
                website_knowledge = WebsiteKnowledgeBase(
                    urls=legal_sources["websites"],
                    vector_db=self.vector_db,
                    embedder=embedder
                )
                
                # Combine knowledge bases
                self.knowledge_base = CombinedKnowledgeBase(
                    sources=[pdf_knowledge, website_knowledge],
                    vector_db=self.vector_db,
                    embedder=embedder
                )
                
                logger.info("Knowledge base initialized successfully with Supabase vector database and Mistral embedder following Agno docs pattern")
            else:
                self.knowledge_base = None
                logger.warning("Vector database not available, knowledge base disabled")
            
        except Exception as e:
            logger.error(f"Failed to initialize knowledge base: {e}")
            self.knowledge_base = None
    
    def initialize_storage_system(self, agent_name: str):
        """Initialize storage system for a specific agent"""
        try:
            # Check if SQLite fallback is enabled
            if os_module.getenv("USE_SQLITE_FALLBACK", "true").lower() == "true":
                from agno.storage.sqlite import SqliteStorage
                
                # Ensure tmp directory exists
                os_module.makedirs("tmp", exist_ok=True)
                
                storage = SqliteStorage(
                    table_name="agent_sessions",
                    db_file="tmp/agent_storage.db"
                )
                
                logger.info(f"Storage system initialized for {agent_name} with SQLite")
                return storage
            
            # Get Supabase configuration from environment or settings
            supabase_url = os_module.getenv("SUPABASE_URL")
            supabase_service_role_key = os_module.getenv("SUPABASE_SERVICE_ROLE_KEY")
            
            # If not in environment, try to get from settings
            if not supabase_url or not supabase_service_role_key:
                try:
                    from config.settings import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
                    supabase_url = SUPABASE_URL
                    supabase_service_role_key = SUPABASE_SERVICE_ROLE_KEY
                except ImportError:
                    pass
            
            if not supabase_url or not supabase_service_role_key:
                logger.warning("Supabase credentials not found, using SQLite fallback")
                # Fallback to SQLite for development
                from agno.storage.sqlite import SqliteStorage
                
                storage = SqliteStorage(
                    table_name="agent_sessions",
                    db_file="tmp/agent_storage.db"
                )
                
                logger.info(f"Storage system initialized for {agent_name} with SQLite")
                return storage
            
            # Use the correct POSTGRES_URL from settings
            try:
                from config.settings import POSTGRES_URL
                db_url = POSTGRES_URL
            except ImportError:
                # Fallback to constructing the URL
                project_ref = supabase_url.split('//')[1].split('.')[0]
                db_url = f"postgresql://postgres.{project_ref}:{supabase_service_role_key.split('.')[0]}@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
            
            # Create SQLAlchemy engine and session factory
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            
            try:
                engine = create_engine(db_url)
                SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
                
                # Test the connection
                with engine.connect() as conn:
                    from sqlalchemy import text
                    conn.execute(text("SELECT 1"))
                
                # Initialize storage for session history
                storage = PostgresAgentStorage(
                    table_name="agent_sessions",
                    db_engine=engine
                )
                
                logger.info(f"Storage system initialized for {agent_name} with PostgreSQL")
                return storage
                
            except Exception as e:
                logger.warning(f"PostgreSQL connection failed: {e}")
                logger.info(f"Falling back to SQLite for {agent_name}")
                
                # Fallback to SQLite
                from agno.storage.sqlite import SqliteStorage
                
                # Ensure tmp directory exists
                os_module.makedirs("tmp", exist_ok=True)
                
                storage = SqliteStorage(
                    table_name="agent_sessions",
                    db_file="tmp/agent_storage.db"
                )
                
                logger.info(f"Storage system initialized for {agent_name} with SQLite")
                return storage
            
        except Exception as e:
            logger.error(f"Failed to initialize storage system for {agent_name}: {e}")
            return None
    
    def get_enhanced_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get enhanced configuration for a specific agent"""
        # Initialize knowledge base if not already done
        if not self.knowledge_base:
            self.initialize_knowledge_base()
        
        # Initialize storage system for this agent
        storage = self.initialize_storage_system(agent_name)
        
        # Initialize memory system
        try:
            from postgres_memory import get_memory_instance
            memory_instance = get_memory_instance(agent_name)
            
            # Verify the memory instance has the required interface
            if memory_instance and hasattr(memory_instance, 'runs') and hasattr(memory_instance, 'add_run'):
                logger.info(f"Memory system initialized for {agent_name} with proper agno interface")
            else:
                logger.warning(f"Memory instance for {agent_name} missing required agno interface, using default")
                memory_instance = None
                
        except Exception as e:
            logger.warning(f"Failed to initialize memory system for {agent_name}: {e}")
            memory_instance = None
        
        config = {
            "knowledge": self.knowledge_base,
            "search_knowledge": True if self.knowledge_base else False,
            "storage": storage,
            "reasoning": False,
            "show_tool_calls": False,
             #"debug_mode": os_module.getenv("DEBUG_MODE", "false").lower() == "true",
              "debug_mode": False,
            # Do NOT pass custom memory instance directly to Agent; agno expects dict or AgentMemory
            # Keep a reference separately so agents can use it for external persistence
            "memory": None,
            "memory_instance": memory_instance,
            "add_history_to_messages": True,  # Enable history
            "num_history_runs": 5,  # Keep last 5 interactions
            "enable_user_memories": True,  # Enable user memories
            "enable_session_summaries": True,  # Enable session summaries
            "enable_agentic_memory": True,  # Enable agentic memory
            "read_chat_history": True,  # Read chat history
            "read_tool_call_history": True  # Read tool call history
        }
        
        return config

# Global instance
_enhanced_config = EnhancedAgentConfig()

def get_enhanced_agent_config(agent_name: str) -> Dict[str, Any]:
    """Get enhanced configuration for a specific agent"""
    return _enhanced_config.get_enhanced_agent_config(agent_name)

def get_agent_memory(agent_name: str) -> Dict[str, Any]:
    """Get agent memory (not available in current version)"""
    return {}

def update_agent_memory(agent_name: str, memory_data: Dict[str, Any]):
    """Update agent memory (not available in current version)"""
    pass

def get_agent_storage(agent_name: str = "default"):
    """Get agent storage"""
    return _enhanced_config.initialize_storage_system(agent_name)

def get_knowledge_base():
    """Get knowledge base"""
    if not _enhanced_config.knowledge_base:
        _enhanced_config.initialize_knowledge_base()
    return _enhanced_config.knowledge_base 