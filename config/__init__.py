"""
Configuration module initialization
Ensures embedder configuration is loaded before any agno components
"""
# Import force Mistral embedder first to patch agno framework
try:
    from . import force_mistral_embedder
    print("✅ Force Mistral embedder module loaded successfully")
except Exception as e:
    print(f"⚠️  Could not load force Mistral embedder module: {e}")

# Import embedder configuration to ensure it's configured
try:
    from . import agno_embedder_config
    print("✅ Agno embedder configuration loaded successfully")
except ImportError as e:
    print(f"⚠️  Could not load agno embedder configuration: {e}")

# Import other configuration modules
from . import settings
from . import ai_models
from . import database
from . import knowledge_base_integration
from . import enhanced_agent_config
from . import supabase_knowledge_base

__all__ = [
    'settings',
    'ai_models', 
    'database',
    'knowledge_base_integration',
    'enhanced_agent_config',
    'supabase_knowledge_base',
    'agno_embedder_config',
    'force_mistral_embedder'
] 