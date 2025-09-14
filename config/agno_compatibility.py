"""
agno Compatibility Module
Provides fallback implementations when agno is not available
"""

import logging
from typing import Optional, Any, Dict, List

logger = logging.getLogger(__name__)

# Global flag to track agno availability
AGNO_AVAILABLE = False
AGNO_VERSION = None

# Try to import agno and its components
try:
    import agno
    from agno.agent import Agent
    from agno.storage.agent.postgres import PostgresAgentStorage
    from agno.storage.sqlite import SqliteStorage
    from agno.knowledge.pdf_url import PDFUrlKnowledgeBase
    from agno.knowledge.website import WebsiteKnowledgeBase
    from agno.knowledge.combined import CombinedKnowledgeBase
    from agno.tools.googlesearch import GoogleSearchTools
    from agno.vectordb.memory import MemoryVectorDB
    
    AGNO_AVAILABLE = True
    AGNO_VERSION = getattr(agno, '__version__', 'unknown')
    logger.info(f"agno {AGNO_VERSION} successfully imported")
    
except ImportError as e:
    logger.warning(f"agno not available: {e}")
    # Set all agno classes to None
    Agent = None
    PostgresAgentStorage = None
    SqliteStorage = None
    PDFUrlKnowledgeBase = None
    WebsiteKnowledgeBase = None
    CombinedKnowledgeBase = None
    GoogleSearchTools = None
    MemoryVectorDB = None

# Fallback implementations
class FallbackAgent:
    """Fallback agent when agno is not available"""
    
    def __init__(self, name: str = "Fallback Agent", role: str = "Basic Agent"):
        self.name = name
        self.role = role
        logger.warning(f"Using FallbackAgent: {name}")
    
    async def run(self, message: str, **kwargs):
        """Basic fallback run method"""
        return {
            "response": "Funcionalidad limitada - agno no disponible",
            "status": "limited_functionality",
            "agent": self.name
        }
    
    def __getattr__(self, name):
        """Fallback for any missing methods"""
        return lambda *args, **kwargs: {
            "response": "Método no disponible en modo limitado",
            "status": "limited_functionality"
        }

class FallbackStorage:
    """Fallback storage when agno storage is not available"""
    
    def __init__(self, table_name: str = "fallback_storage"):
        self.table_name = table_name
        self._data = {}
        logger.warning(f"Using FallbackStorage: {table_name}")
    
    def add_run(self, *args, **kwargs):
        """Fallback add_run method"""
        logger.warning("FallbackStorage: add_run not implemented")
        return None
    
    def get_runs(self, *args, **kwargs):
        """Fallback get_runs method"""
        logger.warning("FallbackStorage: get_runs not implemented")
        return []
    
    def __getattr__(self, name):
        """Fallback for any missing methods"""
        return lambda *args, **kwargs: None

class FallbackKnowledgeBase:
    """Fallback knowledge base when agno knowledge is not available"""
    
    def __init__(self):
        logger.warning("Using FallbackKnowledgeBase")
    
    def search(self, query: str, **kwargs):
        """Fallback search method"""
        logger.warning("FallbackKnowledgeBase: search not implemented")
        return []
    
    def __getattr__(self, name):
        """Fallback for any missing methods"""
        return lambda *args, **kwargs: []

class FallbackGoogleSearchTools:
    """Fallback Google search tools when agno tools are not available"""
    
    def __init__(self):
        logger.warning("Using FallbackGoogleSearchTools")
    
    def search(self, query: str, **kwargs):
        """Fallback search method"""
        logger.warning("FallbackGoogleSearchTools: search not implemented")
        return []
    
    def __getattr__(self, name):
        """Fallback for any missing methods"""
        return lambda *args, **kwargs: []

# Factory functions
def get_agent_class():
    """Get the appropriate Agent class"""
    return Agent if AGNO_AVAILABLE else FallbackAgent

def get_storage_class():
    """Get the appropriate storage class"""
    return PostgresAgentStorage if AGNO_AVAILABLE else FallbackStorage

def get_sqlite_storage_class():
    """Get the appropriate SQLite storage class"""
    return SqliteStorage if AGNO_AVAILABLE else FallbackStorage

def get_knowledge_base_class():
    """Get the appropriate knowledge base class"""
    return CombinedKnowledgeBase if AGNO_AVAILABLE else FallbackKnowledgeBase

def get_google_search_tools_class():
    """Get the appropriate Google search tools class"""
    return GoogleSearchTools if AGNO_AVAILABLE else FallbackGoogleSearchTools

def get_memory_vector_db_class():
    """Get the appropriate memory vector DB class"""
    return MemoryVectorDB if AGNO_AVAILABLE else None

# Utility functions
def is_agno_available():
    """Check if agno is available"""
    return AGNO_AVAILABLE

def get_agno_version():
    """Get agno version if available"""
    return AGNO_VERSION

def log_agno_status():
    """Log the current agno status"""
    if AGNO_AVAILABLE:
        logger.info(f"agno {AGNO_VERSION} is available and ready")
    else:
        logger.warning("agno is not available - using fallback implementations")
