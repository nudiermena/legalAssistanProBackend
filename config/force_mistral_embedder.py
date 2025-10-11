"""
Force Mistral Embedder Usage in Agno Framework
This module patches agno framework internals to ensure Mistral is used instead of OpenAI
"""
import os
import logging
from typing import Optional, Any
logger = logging.getLogger(__name__)

def force_mistral_embedder():
    """Force agno framework to use Mistral embedder instead of OpenAI"""
    try:
        # First, unset OPENAI_API_KEY to prevent fallback
        if 'OPENAI_API_KEY' in os.environ:
            logger.info("Unsetting OPENAI_API_KEY to prevent OpenAI embedder fallback")
            del os.environ['OPENAI_API_KEY']
        
        # Ensure Mistral API key is available
        mistral_key = os.getenv('MISTRAL_API_KEY')
        if not mistral_key:
            logger.warning("MISTRAL_API_KEY not found, vector database will be disabled")
            return None
        
        # Set environment variables to force Mistral
        os.environ["AGNO_MISTRAL_EMBEDDER_AVAILABLE"] = "true"
        os.environ["AGNO_DEFAULT_EMBEDDER_TYPE"] = "mistral"
        os.environ["AGNO_FORCE_MISTRAL"] = "true"
        os.environ["OPENAI_API_KEY"] = ""  # Set to empty string
        
        # Try to patch agno framework internals
        try:
            import agno.embedder
            
            # Get Mistral embedder instance
            mistral_key = os.getenv("MISTRAL_API_KEY")
            if not mistral_key:
                try:
                    from config.settings import MISTRAL_API_KEY
                    mistral_key = MISTRAL_API_KEY
                except ImportError:
                    mistral_key = None
            
            if mistral_key:
                from mistralai import Mistral
                
                # Create custom embedder class
                class CustomMistralEmbedder:
                    def __init__(self, api_key, model="mistral-embed", *args, **kwargs):
                        # Handle additional arguments that agno might pass
                        self.mistral_client = Mistral(api_key=api_key)
                        self.embedding_model = model
                        # Store any additional arguments for compatibility
                        self._args = args
                        self._kwargs = kwargs
                    
                    async def aembed(self, texts):
                        response = self.mistral_client.embeddings.create(
                            model=self.embedding_model,
                            inputs=texts
                        )
                        return [d.embedding for d in response.data]
                    
                    def embed(self, texts):
                        """Synchronous embed method for compatibility"""
                        import asyncio
                        try:
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                # If we're in an async context, use a new event loop
                                import concurrent.futures
                                with concurrent.futures.ThreadPoolExecutor() as executor:
                                    future = executor.submit(asyncio.run, self.aembed(texts))
                                    return future.result()
                            else:
                                return asyncio.run(self.aembed(texts))
                        except RuntimeError:
                            # Fallback for cases where no event loop is available
                            return asyncio.run(self.aembed(texts))
                
                # Create embedder instance
                custom_embedder = CustomMistralEmbedder(
                    api_key=mistral_key,
                    model="mistral-embed"
                )
                
                # Try to patch agno embedder selection
                if hasattr(agno.embedder, 'get_default_embedder'):
                    original_get_default = agno.embedder.get_default_embedder
                    
                    def force_mistral_default(*args, **kwargs):
                        """Force Mistral embedder instead of OpenAI fallback"""
                        logger.info("Forcing Mistral embedder in agno framework")
                        return custom_embedder
                    
                    agno.embedder.get_default_embedder = force_mistral_default
                    logger.info("Successfully patched agno.embedder.get_default_embedder")
            
                # Try to patch the embedder selection logic
                if hasattr(agno.embedder, 'select_embedder'):
                    original_select = agno.embedder.select_embedder
                    
                    def force_mistral_select(*args, **kwargs):
                        """Force Mistral embedder selection"""
                        logger.info("Forcing Mistral embedder selection in agno framework")
                        return custom_embedder
                    
                    agno.embedder.select_embedder = force_mistral_select
                    logger.info("Successfully patched agno.embedder.select_embedder")
            
                # Try to patch the OpenAI embedder to use Mistral instead
                try:
                    import agno.embedder.openai
                    if hasattr(agno.embedder.openai, 'OpenAIEmbedder'):
                        original_openai_init = agno.embedder.openai.OpenAIEmbedder.__init__
                        
                        def force_mistral_openai_init(self, *args, **kwargs):
                            """Force Mistral embedder even when OpenAI is requested"""
                            logger.info("Intercepting OpenAI embedder request, using Mistral instead")
                            # Initialize with Mistral instead, passing all arguments
                            custom_embedder.__init__(self, mistral_key, "mistral-embed", *args, **kwargs)
                            # Copy attributes
                            for attr, value in custom_embedder.__dict__.items():
                                setattr(self, attr, value)
                        
                        agno.embedder.openai.OpenAIEmbedder.__init__ = force_mistral_openai_init
                        logger.info("Successfully patched OpenAIEmbedder to use Mistral")
                except ImportError:
                    logger.warning("Could not patch OpenAI embedder")
                
                logger.info("✅ Successfully forced Mistral embedder usage in agno framework")
                return custom_embedder
            else:
                logger.warning("MISTRAL_API_KEY not found, cannot force Mistral embedder")
                return None
                
        except ImportError as e:
            logger.warning(f"Could not patch agno framework: {e}")
            return None
        except Exception as e:
            logger.error(f"Error forcing Mistral embedder: {e}")
            return None
            
    except Exception as e:
        logger.error(f"Error in force_mistral_embedder: {e}")
        return None

def get_mistral_embedder():
    """Get a Mistral embedder instance"""
    try:
        mistral_key = os.getenv("MISTRAL_API_KEY")
        if not mistral_key:
            try:
                from config.settings import MISTRAL_API_KEY
                mistral_key = MISTRAL_API_KEY
            except ImportError:
                mistral_key = None
        
        if mistral_key:
            from mistralai import Mistral
            
            class MistralEmbedder:
                def __init__(self, api_key, model="mistral-embed", *args, **kwargs):
                    # Handle additional arguments that agno might pass
                    self.mistral_client = Mistral(api_key=api_key)
                    self.embedding_model = model
                    # Store any additional arguments for compatibility
                    self._args = args
                    self._kwargs = kwargs
                
                async def aembed(self, texts):
                    response = self.mistral_client.embeddings.create(
                        model=self.embedding_model,
                        inputs=texts
                    )
                    return [d.embedding for d in response.data]
                
                def embed(self, texts):
                    """Synchronous embed method for compatibility"""
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # If we're in an async context, use a new event loop
                            import concurrent.futures
                            with concurrent.futures.ThreadPoolExecutor() as executor:
                                future = executor.submit(asyncio.run, self.aembed(texts))
                                return future.result()
                        else:
                            return asyncio.run(self.aembed(texts))
                    except RuntimeError:
                        # Fallback for cases where no event loop is available
                        return asyncio.run(self.aembed(texts))
            
            return MistralEmbedder(
                api_key=mistral_key,
                model="mistral-embed"
            )
        else:
            logger.warning("MISTRAL_API_KEY not found")
            return None
                
    except Exception as e:
        logger.error(f"Error creating Mistral embedder: {e}")
        return None

# Auto-execute when module is imported
if __name__ != "__main__":
    force_mistral_embedder()

