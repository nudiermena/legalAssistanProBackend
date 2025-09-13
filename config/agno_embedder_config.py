"""
Global Embedder Configuration for Agno Framework
Ensures Mistral embedder is used by default instead of OpenAI fallback
"""
import os
import logging
from typing import Optional
logger = logging.getLogger(__name__)

def get_agno_default_embedder():
    """Get the default embedder for agno framework"""
    try:
        mistral_api_key = os.getenv("MISTRAL_API_KEY")
        if not mistral_api_key:
            try:
                from config.settings import MISTRAL_API_KEY
                mistral_api_key = MISTRAL_API_KEY
            except ImportError:
                mistral_api_key = None
        
        if mistral_api_key:
            from agno.embedder.mistral import MistralEmbedder
            embedder = MistralEmbedder(api_key=mistral_api_key)
            logger.info("Global Mistral embedder configured for agno framework")
            return embedder
        else:
            logger.warning("MISTRAL_API_KEY not found, agno framework will use default embedder")
            return None
    except Exception as e:
        logger.warning(f"Failed to configure global Mistral embedder: {e}")
        return None

def force_mistral_embedder():
    """Force agno framework to use Mistral embedder by aggressively patching"""
    try:
        # Force unset OPENAI_API_KEY to prevent fallback
        if 'OPENAI_API_KEY' in os.environ:
            logger.info("Unsetting OPENAI_API_KEY to prevent OpenAI embedder fallback")
            del os.environ['OPENAI_API_KEY']
        
        # Set environment variables to force Mistral
        os.environ["AGNO_MISTRAL_EMBEDDER_AVAILABLE"] = "true"
        os.environ["AGNO_DEFAULT_EMBEDDER_TYPE"] = "mistral"
        os.environ["AGNO_FORCE_MISTRAL"] = "true"
        os.environ["OPENAI_API_KEY"] = ""  # Set to empty string
        
        # Aggressively monkey patch agno's embedder selection
        try:
            import agno.embedder
            import agno.knowledge.base
            import agno.knowledge.pdf_url
            import agno.knowledge.website
            import agno.knowledge.combined
            
            # Get Mistral embedder instance
            mistral_key = os.getenv("MISTRAL_API_KEY")
            if not mistral_key:
                try:
                    from config.settings import MISTRAL_API_KEY
                    mistral_key = MISTRAL_API_KEY
                except ImportError:
                    mistral_key = None
            
            if mistral_key:
                from agno.embedder.mistral import MistralEmbedder
                forced_mistral = MistralEmbedder(api_key=mistral_key)
                
                # Patch the base embedder selection
                if hasattr(agno.embedder, 'get_default_embedder'):
                    original_get_default = agno.embedder.get_default_embedder
                    
                    def force_mistral_default(*args, **kwargs):
                        """Force Mistral embedder instead of OpenAI fallback"""
                        logger.info("Forcing Mistral embedder in agno framework")
                        return forced_mistral
                    
                    agno.embedder.get_default_embedder = force_mistral_default
                    logger.info("Successfully monkey patched agno.embedder.get_default_embedder")
                
                # Patch knowledge base constructors to force Mistral embedder
                if hasattr(agno.knowledge.pdf_url, 'PDFUrlKnowledgeBase'):
                    original_pdf_init = agno.knowledge.pdf_url.PDFUrlKnowledgeBase.__init__
                    
                    def forced_pdf_init(self, *args, **kwargs):
                        """Force Mistral embedder in PDF knowledge base"""
                        if 'embedder' not in kwargs or kwargs['embedder'] is None:
                            kwargs['embedder'] = forced_mistral
                            logger.info("Forcing Mistral embedder in PDFUrlKnowledgeBase")
                        return original_pdf_init(self, *args, **kwargs)
                    
                    agno.knowledge.pdf_url.PDFUrlKnowledgeBase.__init__ = forced_pdf_init
                    logger.info("Successfully monkey patched PDFUrlKnowledgeBase")
                
                if hasattr(agno.knowledge.website, 'WebsiteKnowledgeBase'):
                    original_web_init = agno.knowledge.website.WebsiteKnowledgeBase.__init__
                    
                    def forced_web_init(self, *args, **kwargs):
                        """Force Mistral embedder in website knowledge base"""
                        if 'embedder' not in kwargs or kwargs['embedder'] is None:
                            kwargs['embedder'] = forced_mistral
                            logger.info("Forcing Mistral embedder in WebsiteKnowledgeBase")
                        return original_web_init(self, *args, **kwargs)
                    
                    agno.knowledge.website.WebsiteKnowledgeBase.__init__ = forced_web_init
                    logger.info("Successfully monkey patched WebsiteKnowledgeBase")
                
                if hasattr(agno.knowledge.combined, 'CombinedKnowledgeBase'):
                    original_combined_init = agno.knowledge.combined.CombinedKnowledgeBase.__init__
                    
                    def forced_combined_init(self, *args, **kwargs):
                        """Force Mistral embedder in combined knowledge base"""
                        if 'embedder' not in kwargs or kwargs['embedder'] is None:
                            kwargs['embedder'] = forced_mistral
                            logger.info("Forcing Mistral embedder in CombinedKnowledgeBase")
                        return original_combined_init(self, *args, **kwargs)
                    
                    agno.knowledge.combined.CombinedKnowledgeBase.__init__ = forced_combined_init
                    logger.info("Successfully monkey patched CombinedKnowledgeBase")
                
                logger.info("Successfully applied aggressive Mistral embedder patching")
                return True
            else:
                logger.warning("MISTRAL_API_KEY not available for forced embedder")
                return False
                
        except Exception as e:
            logger.warning(f"Could not aggressively patch agno embedder: {e}")
            return False
        
    except Exception as e:
        logger.error(f"Error in force_mistral_embedder: {e}")
        return False

def configure_agno_embedder():
    """Configure agno framework to use Mistral embedder by default"""
    return force_mistral_embedder()

_global_embedder = None

def get_global_embedder():
    """Get the global embedder instance"""
    global _global_embedder
    if _global_embedder is None:
        _global_embedder = get_agno_default_embedder()
    return _global_embedder

def set_global_embedder(embedder):
    """Set the global embedder instance"""
    global _global_embedder
    _global_embedder = embedder
    logger.info(f"Global embedder set to: {type(embedder).__name__}")

# Configure embedder on module import
force_mistral_embedder()
