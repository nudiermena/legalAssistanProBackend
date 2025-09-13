
import os
import logging
import asyncio
from typing import Optional, Dict, Any, List
from agno.models.mistral import MistralChat
from agno.models.groq import Groq
import time
from functools import wraps

logger = logging.getLogger(__name__)

class ModelFallbackManager:
    """Manages AI model availability and fallback logic"""
    
    def __init__(self):
        self.fallback_order = ["mistral", "groq"]  # Priority order
        self.model_status = {}  # available, temporarily_unavailable, permanently_unavailable
        self.model_instances = {}
        self.last_error_time = {}  # Track error timestamps for each model
        self.error_threshold = 2  # Mark as unavailable after 2 errors (reduced from 3)
        self.error_window = 300  # 5 minutes (reduced from 600 seconds)
        
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize all available models"""
        # Get API keys from settings
        try:
            from config.settings import MISTRAL_API_KEY, GROQ_API_KEY
        except ImportError:
            MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
            GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        
        # Initialize Mistral
        if MISTRAL_API_KEY:
            try:
                self.model_instances["mistral"] = MistralChat(id="mistral-large-latest")
                self.model_status["mistral"] = "available"
                logger.info("✅ Mistral model initialized successfully")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize Mistral: {e}")
                self.model_status["mistral"] = "unavailable"
        else:
            self.model_status["mistral"] = "unavailable"
            logger.warning("⚠️ MISTRAL_API_KEY not found")
        
        # Initialize Groq
        if GROQ_API_KEY:
            try:
                self.model_instances["groq"] = Groq(id="llama-3.3-70b-versatile")
                self.model_status["groq"] = "available"
                logger.info("✅ Groq model initialized successfully with llama-3.3-70b-versatile")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize Groq: {e}")
                self.model_status["groq"] = "unavailable"
        else:
            self.model_status["groq"] = "unavailable"
            logger.warning("⚠️ GROQ_API_KEY not found")
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        return [model for model, status in self.model_status.items() if status == "available"]
    
    def get_best_available_model(self) -> Optional[str]:
        """Get the best available model based on fallback order"""
        for model in self.fallback_order:
            if self.model_status.get(model) == "available":
                return model
        return None
    
    def mark_model_error(self, model_name: str, error: Exception):
        """Mark a model as having an error"""
        current_time = time.time()
        
        if model_name not in self.last_error_time:
            self.last_error_time[model_name] = []
        
        # Add current error timestamp
        self.last_error_time[model_name].append(current_time)
        
        # Remove old errors outside the window
        self.last_error_time[model_name] = [
            t for t in self.last_error_time[model_name] 
            if current_time - t < self.error_window
        ]
        
        # Check if we should mark model as temporarily unavailable
        if len(self.last_error_time[model_name]) >= self.error_threshold:
            self.model_status[model_name] = "temporarily_unavailable"
            logger.warning(f"⚠️ Model {model_name} marked as temporarily unavailable due to {len(self.last_error_time[model_name])} errors")
            
            # Schedule reactivation after error window
            asyncio.create_task(self._reactivate_model_after_delay(model_name))
        
        # For rate limit errors, immediately mark as temporarily unavailable
        if self.is_rate_limit_error(error):
            self.model_status[model_name] = "temporarily_unavailable"
            logger.warning(f"⚠️ Model {model_name} immediately marked as temporarily unavailable due to rate limit error")
            
            # Schedule reactivation after shorter delay for rate limits
            asyncio.create_task(self._reactivate_model_after_delay(model_name, delay=60))  # 1 minute for rate limits
        
        # Log the error for debugging
        logger.debug(f"Error recorded for {model_name}: {error} (Total errors: {len(self.last_error_time[model_name])})")
    
    async def _reactivate_model_after_delay(self, model_name: str, delay: int = None):
        """Reactivate a model after a delay"""
        if delay is None:
            delay = self.error_window
        
        await asyncio.sleep(delay)
        if self.model_status.get(model_name) == "temporarily_unavailable":
            self.model_status[model_name] = "available"
            self.last_error_time[model_name] = []
            logger.info(f"✅ Model {model_name} reactivated after error window")
    
    def get_model_instance(self, model_name: str):
        """Get a model instance by name"""
        return self.model_instances.get(model_name)
    
    def is_rate_limit_error(self, error: Exception) -> bool:
        """Check if an error is a rate limit error"""
        error_str = str(error).lower()
        rate_limit_indicators = [
            "429", "rate limit", "capacity exceeded", "quota exceeded",
            "too many requests", "service tier capacity exceeded"
        ]
        
        # Check for agno ModelProviderError specifically
        if hasattr(error, '__class__') and 'ModelProviderError' in error.__class__.__name__:
            # For agno errors, check the underlying cause
            if hasattr(error, '__cause__') and error.__cause__:
                error_str = str(error.__cause__).lower()
            else:
                error_str = str(error).lower()
        
        return any(indicator in error_str for indicator in rate_limit_indicators)

# Global fallback manager instance
fallback_manager = ModelFallbackManager()

# Initialize AI models with fallback support
def create_model_with_fallback(model_type: str = "general"):
    """Create a model instance with automatic fallback support"""
    
    class FallbackModel:
        def __init__(self, model_type: str):
            self.model_type = model_type
            self.current_model_name = None
            self.current_model_instance = None
            self._select_best_model()
            
        def _select_best_model(self):
            """Select the best available model"""
            best_model = fallback_manager.get_best_available_model()
            if best_model:
                self.current_model_name = best_model
                self.current_model_instance = fallback_manager.get_model_instance(best_model)
                logger.info(f"🎯 Selected {self.current_model_name} for {self.model_type}")
            else:
                raise RuntimeError("No AI models available")
        
        def _create_wrapped_model(self, model_instance):
            """Create a completely wrapped version of the underlying model"""
            class WrappedModel:
                def __init__(self, fallback_model, original_model):
                    self.fallback_model = fallback_model
                    self.original_model = original_model
                
                def __getattr__(self, name):
                    """Intercept ALL attribute access to ensure fallback system is used"""
                    if hasattr(self.original_model, name):
                        attr = getattr(self.original_model, name)
                        
                        # If it's a method that might make API calls, use our fallback system
                        if callable(attr) and name in ['invoke', 'ainvoke', 'response', 'aresponse', 'stream', 'astream']:
                            def wrapped_method(*args, **kwargs):
                                if asyncio.iscoroutinefunction(attr):
                                    return self.fallback_model._execute_with_fallback(name, *args, **kwargs)
                                else:
                                    return self.fallback_model._execute_with_fallback_sync(name, *args, **kwargs)
                            
                            # Preserve method metadata
                            wrapped_method.__name__ = name
                            wrapped_method.__doc__ = getattr(attr, '__doc__', f'Wrapped {name} method with fallback support')
                            
                            return wrapped_method
                        
                        # For non-callable attributes, return directly
                        return attr
                    
                    # If attribute doesn't exist, raise AttributeError
                    raise AttributeError(f"'{self.original_model.__class__.__name__}' object has no attribute '{name}'")
            
            return WrappedModel(self, model_instance)
        
        def _execute_with_fallback_sync(self, method_name: str, *args, **kwargs):
            """Execute a method synchronously with automatic fallback on errors"""
            max_attempts = len(fallback_manager.get_available_models())
            attempt = 0
            
            while attempt < max_attempts:
                try:
                    # Check if we need to select a new model (either no instance or current model unavailable)
                    if (not self.current_model_instance or 
                        self.current_model_name not in fallback_manager.get_available_models()):
                        self._select_best_model()
                    
                    # Get the method from the current model instance
                    method = getattr(self.current_model_instance, method_name)
                    
                    # Handle message formatting for agno compatibility
                    processed_args = self._process_args_for_agno(method_name, args, kwargs)
                    
                    # Execute the method synchronously
                    result = method(*processed_args, **kwargs)
                    
                    logger.info(f"✅ Successfully executed {method_name} using {self.current_model_name}")
                    return result
                    
                except Exception as e:
                    attempt += 1
                    logger.warning(f"⚠️ Attempt {attempt}/{max_attempts} failed with {self.current_model_name}: {e}")
                    
                    # Mark current model as having an error
                    fallback_manager.mark_model_error(self.current_model_name, e)
                    
                    # Force model selection to get next available model
                    self.current_model_instance = None
                    self.current_model_name = None
                    
                    # Try to switch to next available model
                    if attempt < max_attempts:
                        try:
                            self._select_best_model()
                            if self.current_model_instance:
                                logger.info(f"🔄 Switched to {self.current_model_name} for retry")
                                continue
                        except RuntimeError as re:
                            logger.error(f"❌ No more models available: {re}")
                            raise e
                    
                    # If we've exhausted all models, raise the last error
                    logger.error(f"❌ All models failed after {max_attempts} attempts")
                    raise e
        
        async def _execute_with_fallback(self, method_name: str, *args, **kwargs):
            """Execute a method asynchronously with automatic fallback on errors"""
            max_attempts = len(fallback_manager.get_available_models())
            attempt = 0
            
            while attempt < max_attempts:
                try:
                    # Check if we need to select a new model (either no instance or current model unavailable)
                    if (not self.current_model_instance or 
                        self.current_model_name not in fallback_manager.get_available_models()):
                        self._select_best_model()
                    
                    # Get the method from the current model instance
                    method = getattr(self.current_model_instance, method_name)
                    
                    # Handle message formatting for agno compatibility
                    processed_args = self._process_args_for_agno(method_name, args, kwargs)
                    
                    # Execute the method
                    if asyncio.iscoroutinefunction(method):
                        result = await method(*processed_args, **kwargs)
                    else:
                        result = method(*processed_args, **kwargs)
                    
                    logger.info(f"✅ Successfully executed {method_name} using {self.current_model_name}")
                    return result
                    
                except Exception as e:
                    attempt += 1
                    logger.warning(f"⚠️ Attempt {attempt}/{max_attempts} failed with {self.current_model_name}: {e}")
                    
                    # Mark current model as having an error
                    fallback_manager.mark_model_error(self.current_model_name, e)
                    
                    # Force model selection to get next available model
                    self.current_model_instance = None
                    self.current_model_name = None
                    
                    # Try to switch to next available model
                    if attempt < max_attempts:
                        try:
                            self._select_best_model()
                            if self.current_model_instance:
                                logger.info(f"🔄 Switched to {self.current_model_name} for retry")
                                continue
                        except RuntimeError as re:
                            logger.error(f"❌ No more models available: {re}")
                            raise e
                    
                    # If we've exhausted all models, raise the last error
                    logger.error(f"❌ All models failed after {max_attempts} attempts")
                    raise e
        
        def _process_args_for_agno(self, method_name: str, args, kwargs):
            """Process arguments to ensure agno compatibility"""
            if method_name in ['ainvoke', 'invoke', 'astream', 'stream'] and args:
                # Check if first argument is a string and convert to Message object
                if isinstance(args[0], str):
                    from agno.models.message import Message
                    message = Message(role="user", content=args[0])
                    # Return a list containing the Message object as the first argument
                    result = ([message],) + args[1:]
                    logger.debug(f"String converted to Message: {message}, returning: {result}")
                    return result
                elif isinstance(args[0], list) and args[0] and isinstance(args[0][0], str):
                    # Handle list of strings - return the messages list directly
                    from agno.models.message import Message
                    messages = [Message(role="user", content=msg) if isinstance(msg, str) else msg for msg in args[0]]
                    # Return the messages list as the first argument
                    result = (messages,) + args[1:]
                    logger.debug(f"List of strings converted to Messages: {messages}, returning: {result}")
                    return result
            logger.debug(f"No processing needed, returning original args: {args}")
            return args
        
        # Core agno model methods with fallback support
        async def ainvoke(self, *args, **kwargs):
            """Async invoke with fallback support"""
            return await self._execute_with_fallback("ainvoke", *args, **kwargs)
        
        def invoke(self, *args, **kwargs):
            """Sync invoke with fallback support"""
            return self._execute_with_fallback_sync("invoke", *args, **kwargs)
        
        async def astream(self, *args, **kwargs):
            """Async stream with fallback support"""
            return await self._execute_with_fallback("astream", *args, **kwargs)
        
        def stream(self, *args, **kwargs):
            """Sync stream with fallback support"""
            return self._execute_with_fallback_sync("stream", *args, **kwargs)
        
        # Additional agno model methods that need fallback support
        async def ainvoke_stream(self, *args, **kwargs):
            """Async invoke stream with fallback support"""
            return await self._execute_with_fallback("ainvoke_stream", *args, **kwargs)
        
        def invoke_stream(self, *args, **kwargs):
            """Sync invoke stream with fallback support"""
            return self._execute_with_fallback_sync("invoke_stream", *args, **kwargs)
        
        async def aresponse(self, *args, **kwargs):
            """Async response with fallback support"""
            return await self._execute_with_fallback("aresponse", *args, **kwargs)
        
        def response(self, *args, **kwargs):
            """Sync response with fallback support"""
            return self._execute_with_fallback_sync("response", *args, **kwargs)
        
        async def aresponse_stream(self, *args, **kwargs):
            """Async response stream with fallback support"""
            return await self._execute_with_fallback("aresponse_stream", *args, **kwargs)
        
        def response_stream(self, *args, **kwargs):
            """Sync response stream with fallback support"""
            return self._execute_with_fallback_sync("response_stream", *args, **kwargs)
        
        async def arun_function_calls(self, *args, **kwargs):
            """Async run function calls with fallback support"""
            return await self._execute_with_fallback("arun_function_calls", *args, **kwargs)
        
        def run_function_calls(self, *args, **kwargs):
            """Sync run function calls with fallback support"""
            return self._execute_with_fallback_sync("run_function_calls", *args, **kwargs)
        
        # Required abstract methods from agno.models.base.Model
        def parse_provider_response(self, *args, **kwargs):
            """Parse provider response - delegate to current model"""
            if self.current_model_instance:
                return self.current_model_instance.parse_provider_response(*args, **kwargs)
            raise RuntimeError("No model available")
        
        def parse_provider_response_delta(self, *args, **kwargs):
            """Parse provider response delta - delegate to current model"""
            if self.current_model_instance:
                return self.current_model_instance.parse_provider_response_delta(*args, **kwargs)
            raise RuntimeError("No model available")
        
        # Properties that delegate to current model instance
        @property
        def name(self):
            """Get model name from current model instance"""
            if self.current_model_instance:
                return self.current_model_instance.name
            return "fallback_model"
        
        @property
        def provider(self):
            """Get model provider from current model instance"""
            if self.current_model_instance:
                return self.current_model_instance.provider
            return "fallback"
        
        @property
        def id(self):
            """Get model id from current model instance"""
            if self.current_model_instance:
                return self.current_model_instance.id
            return "fallback"
        
        @property
        def instructions(self):
            """Get model instructions from current model instance"""
            if self.current_model_instance:
                return getattr(self.current_model_instance, 'instructions', None)
            return None
        
        @property
        def system_prompt(self):
            """Get model system prompt from current model instance"""
            if self.current_model_instance:
                return getattr(self.current_model_instance, 'system_prompt', None)
            return None
        
        # Methods that don't need fallback - delegate directly to current model
        def set_functions(self, *args, **kwargs):
            """Set functions on current model"""
            if self.current_model_instance:
                return self.current_model_instance.set_functions(*args, **kwargs)
            raise RuntimeError("No model available")
        
        def set_tools(self, *args, **kwargs):
            """Set tools on current model"""
            if self.current_model_instance:
                return self.current_model_instance.set_tools(*args, **kwargs)
            raise RuntimeError("No model available")
        
        def get_function_calls_to_run(self, *args, **kwargs):
            """Get function calls to run from current model"""
            if self.current_model_instance:
                return self.current_model_instance.get_function_calls_to_run(*args, **kwargs)
            raise RuntimeError("No model available")
        
        def get_instructions_for_model(self, *args, **kwargs):
            """Get instructions for current model"""
            if self.current_model_instance:
                return self.current_model_instance.get_instructions_for_model(*args, **kwargs)
            raise RuntimeError("No model available")
        
        def get_system_message_for_model(self, *args, **kwargs):
            """Get system message for current model"""
            if self.current_model_instance:
                return self.current_model_instance.get_system_message_for_model(*args, **kwargs)
            raise RuntimeError("No model available")
        
        def get_provider(self, *args, **kwargs):
            """Get provider from current model"""
            if self.current_model_instance:
                return self.current_model_instance.get_provider(*args, **kwargs)
            raise RuntimeError("No model available")
        
        def get_client(self, *args, **kwargs):
            """Get client from current model"""
            if self.current_model_instance:
                return self.current_model_instance.get_client(*args, **kwargs)
            raise RuntimeError("No model available")
        
        def get_async_client(self, *args, **kwargs):
            """Get async client from current model"""
            if self.current_model_instance:
                return self.current_model_instance.get_async_client(*args, **kwargs)
            raise RuntimeError("No model available")
        
        # Property delegation
        @property
        def temperature(self):
            """Get temperature from current model"""
            if self.current_model_instance:
                return self.current_model_instance.temperature
            return None
        
        @temperature.setter
        def temperature(self, value):
            """Set temperature on current model"""
            if self.current_model_instance:
                self.current_model_instance.temperature = value
        
        @property
        def max_tokens(self):
            """Get max tokens from current model"""
            if self.current_model_instance:
                return self.current_model_instance.max_tokens
            return None
        
        @max_tokens.setter
        def max_tokens(self, value):
            """Set max tokens on current model"""
            if self.current_model_instance:
                self.current_model_instance.max_tokens = value
        
        @property
        def timeout(self):
            """Get timeout from current model"""
            if self.current_model_instance:
                return self.current_model_instance.timeout
            return None
        
        @timeout.setter
        def timeout(self, value):
            """Set timeout on current model"""
            if self.current_model_instance:
                self.current_model_instance.timeout = value
        
        # Method delegation for other common methods
        def clear(self, *args, **kwargs):
            """Clear current model"""
            if self.current_model_instance:
                return self.current_model_instance.clear(*args, **kwargs)
            raise RuntimeError("No model available")
        
        def to_dict(self, *args, **kwargs):
            """Convert current model to dict"""
            if self.current_model_instance:
                return self.current_model_instance.to_dict(*args, **kwargs)
            raise RuntimeError("No model available")
        
        def supports_json_schema_outputs(self, *args, **kwargs):
            """Check if current model supports JSON schema outputs"""
            if self.current_model_instance:
                return self.current_model_instance.supports_json_schema_outputs(*args, **kwargs)
            return False
        
        def supports_native_structured_outputs(self, *args, **kwargs):
            """Check if current model supports native structured outputs"""
            if self.current_model_instance:
                return self.current_model_instance.supports_native_structured_outputs(*args, **kwargs)
            return False
        
        def show_tool_calls(self, *args, **kwargs):
            """Show tool calls on current model"""
            if self.current_model_instance:
                return self.current_model_instance.show_tool_calls(*args, **kwargs)
            raise RuntimeError("No model available")
        
        def tool_call_limit(self, *args, **kwargs):
            """Get tool call limit from current model"""
            if self.current_model_instance:
                return self.current_model_instance.tool_call_limit(*args, **kwargs)
            return None
        
        def tool_choice(self, *args, **kwargs):
            """Get tool choice from current model"""
            if self.current_model_instance:
                return self.current_model_instance.tool_choice(*args, **kwargs)
            return None
        
        def tool_message_role(self, *args, **kwargs):
            """Get tool message role from current model"""
            if self.current_model_instance:
                return self.current_model_instance.tool_message_role(*args, **kwargs)
            return None
        
        def assistant_message_role(self, *args, **kwargs):
            """Get assistant message role from current model"""
            if self.current_model_instance:
                return self.current_model_instance.assistant_message_role(*args, **kwargs)
            return None
        
        def user(self, *args, **kwargs):
            """Get user from current model"""
            if self.current_model_instance:
                return self.current_model_instance.user(*args, **kwargs)
            raise RuntimeError("No model available")
        
        def stop(self, *args, **kwargs):
            """Get stop from current model"""
            if self.current_model_instance:
                return self.current_model_instance.stop(*args, **kwargs)
            return None
        
        def top_p(self, *args, **kwargs):
            """Get top_p from current model"""
            if self.current_model_instance:
                return self.current_model_instance.top_p(*args, **kwargs)
            return None
        
        def frequency_penalty(self, *args, **kwargs):
            """Get frequency penalty from current model"""
            if self.current_model_instance:
                return self.current_model_instance.frequency_penalty(*args, **kwargs)
            return None
        
        def presence_penalty(self, *args, **kwargs):
            """Get presence penalty from current model"""
            if self.current_model_instance:
                return self.current_model_instance.presence_penalty(*args, **kwargs)
            return None
        
        def seed(self, *args, **kwargs):
            """Get seed from current model"""
            if self.current_model_instance:
                return self.current_model_instance.seed(*args, **kwargs)
            return None
        
        def logit_bias(self, *args, **kwargs):
            """Get logit bias from current model"""
            if self.current_model_instance:
                return self.current_model_instance.logit_bias(*args, **kwargs)
            return None
        
        def logprobs(self, *args, **kwargs):
            """Get logprobs from current model"""
            if self.current_model_instance:
                return self.current_model_instance.logprobs(*args, **kwargs)
            return None
        
        def top_logprobs(self, *args, **kwargs):
            """Get top logprobs from current model"""
            if self.current_model_instance:
                return self.current_model_instance.top_logprobs(*args, **kwargs)
            return None
        
        def response_format(self, *args, **kwargs):
            """Get response format from current model"""
            if self.current_model_instance:
                return self.current_model_instance.response_format(*args, **kwargs)
            return None
        
        def max_retries(self, *args, **kwargs):
            """Get max retries from current model"""
            if self.current_model_instance:
                return self.current_model_instance.max_retries(*args, **kwargs)
            return None
        
        def random_seed(self, *args, **kwargs):
            """Get random seed from current model"""
            if self.current_model_instance:
                return self.current_model_instance.random_seed(*args, **kwargs)
            return None
        
        def safe_mode(self, *args, **kwargs):
            """Get safe mode from current model"""
            if self.current_model_instance:
                return self.current_model_instance.safe_mode(*args, **kwargs)
            return None
        
        def safe_prompt(self, *args, **kwargs):
            """Get safe prompt from current model"""
            if self.current_model_instance:
                return self.current_model_instance.safe_prompt(*args, **kwargs)
            return None
        
        def api_key(self, *args, **kwargs):
            """Get API key from current model"""
            if self.current_model_instance:
                return self.current_model_instance.api_key(*args, **kwargs)
            return None
        
        def base_url(self, *args, **kwargs):
            """Get base URL from current model"""
            if self.current_model_instance:
                return self.current_model_instance.base_url(*args, **kwargs)
            return None
        
        def default_headers(self, *args, **kwargs):
            """Get default headers from current model"""
            if self.current_model_instance:
                return self.current_model_instance.default_headers(*args, **kwargs)
            return None
        
        def default_query(self, *args, **kwargs):
            """Get default query from current model"""
            if self.current_model_instance:
                return self.current_model_instance.default_query(*args, **kwargs)
            return None
        
        def extra_headers(self, *args, **kwargs):
            """Get extra headers from current model"""
            if self.current_model_instance:
                return self.current_model_instance.extra_headers(*args, **kwargs)
            return None
        
        def extra_query(self, *args, **kwargs):
            """Get extra query from current model"""
            if self.current_model_instance:
                return self.current_model_instance.extra_query(*args, **kwargs)
            return None
        
        def http_client(self, *args, **kwargs):
            """Get HTTP client from current model"""
            if self.current_model_instance:
                return self.current_model_instance.http_client(*args, **kwargs)
            return None
        
        def client_params(self, *args, **kwargs):
            """Get client params from current model"""
            if self.current_model_instance:
                return self.current_model_instance.client_params(*args, **kwargs)
            return None
        
        def request_params(self, *args, **kwargs):
            """Get request params from current model"""
            if self.current_model_instance:
                return self.current_model_instance.request_params(*args, **kwargs)
            return None
        
        def request_kwargs(self, *args, **kwargs):
            """Get request kwargs from current model"""
            if self.current_model_instance:
                return self.current_model_instance.request_kwargs(*args, **kwargs)
            return None
        
        def endpoint(self, *args, **kwargs):
            """Get endpoint from current model"""
            if self.current_model_instance:
                return self.current_model_instance.endpoint(*args, **kwargs)
            return None
        
        def mistral_client(self, *args, **kwargs):
            """Get Mistral client from current model"""
            if self.current_model_instance:
                return self.current_model_instance.mistral_client(*args, **kwargs)
            return None
        
        def async_client(self, *args, **kwargs):
            """Get async client from current model"""
            if self.current_model_instance:
                return self.current_model_instance.async_client(*args, **kwargs)
            return None
        
        def client(self, *args, **kwargs):
            """Get client from current model"""
            if self.current_model_instance:
                return self.current_model_instance.client(*args, **kwargs)
            return None
        
        # Generic attribute delegation for any other methods/properties
        def __getattr__(self, name):
            """Delegate any other attributes to the current model instance"""
            if self.current_model_instance:
                try:
                    return getattr(self.current_model_instance, name)
                except AttributeError:
                    pass
            
            # If attribute doesn't exist, raise AttributeError
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        
        def __copy__(self):
            """Custom copy method to prevent recursion"""
            return self
        
        def __deepcopy__(self, memo):
            """Custom deepcopy method to prevent recursion"""
            if id(self) in memo:
                return memo[id(self)]
            memo[id(self)] = self
            return self
        
        def get_functions(self):
            """Get functions from current model instance"""
            if self.current_model_instance and hasattr(self.current_model_instance, 'get_functions'):
                return self.current_model_instance.get_functions()
            return []
    
    return FallbackModel(model_type)

# Create fallback-enabled models for each use case
contract_review_model = create_model_with_fallback("contract_review")
legal_research_model = create_model_with_fallback("legal_research")
compliance_model = create_model_with_fallback("compliance")
chatbot_model = create_model_with_fallback("chatbot")
case_prediction_model = create_model_with_fallback("case_prediction")
patent_search_model = create_model_with_fallback("patent_search")
document_drafting_model = create_model_with_fallback("document_drafting")
whistleblower_model = create_model_with_fallback("whistleblower")
demand_letter_model = create_model_with_fallback("demand_letter")
legal_diagnosis_model = create_model_with_fallback("legal_diagnosis")

# Initialize Mistral embedder for vector database (keeping existing logic)
from mistralai import Mistral
try:
    from config.settings import MISTRAL_API_KEY
except ImportError:
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

if MISTRAL_API_KEY:
    # Create custom Mistral embedder class (same as in supabase_knowledge_base.py)
    class MistralEmbedder:
        def __init__(self, api_key, model="mistral-embed"):
            self.mistral_client = Mistral(api_key=api_key)
            self.embedding_model = model
        
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
    
    mistral_embedder = MistralEmbedder(
        api_key=MISTRAL_API_KEY,
        model="mistral-embed"
    )
    logger.info("Mistral embedder initialized successfully")
else:
    mistral_embedder = None
    logger.warning("MISTRAL_API_KEY not found, embedder disabled")

# Initialize Groq embedder
try:
    from config.settings import GROQ_API_KEY
except ImportError:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if GROQ_API_KEY:
    # Create custom Groq embedder class
    class GroqEmbedder:
        def __init__(self, api_key, model="llama-3.3-70b-versatile"):
            from groq import Groq
            self.groq_client = Groq(api_key=api_key)
            self.embedding_model = model
        
        async def aembed(self, texts):
            response = self.groq_client.embeddings.create(
                model=self.embedding_model,
                input=texts
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
    
    groq_embedder = GroqEmbedder(
        api_key=GROQ_API_KEY,
        model="llama-3.3-70b-versatile"
    )
    logger.info("Groq embedder initialized successfully with llama-3.3-70b-versatile")
else:
    groq_embedder = None
    logger.warning("GROQ_API_KEY not found, Groq embedder disabled")

# Model mapping for easy access
MODELS = {
    "contract_review": contract_review_model,
    "legal_research": legal_research_model,
    "compliance": compliance_model,
    "chatbot": chatbot_model,
    "case_prediction": case_prediction_model,
    "patent_search": patent_search_model,
    "document_drafting": document_drafting_model,
    "whistleblower": whistleblower_model,
    "demand_letter": demand_letter_model,
    "legal_diagnosis": legal_diagnosis_model
}

def get_model(model_name: str):
    """Get an AI model instance by name"""
    if model_name not in MODELS:
        raise ValueError(f"Model {model_name} not found")
    return MODELS[model_name]

def get_embedder():
    """Get the best available embedder instance (Mistral preferred, Groq as fallback)"""
    if mistral_embedder:
        return mistral_embedder
    elif groq_embedder:
        logger.info("Using Groq embedder as fallback")
        return groq_embedder
    else:
        logger.warning("No embedder available")
        return None

def get_embedder_status():
    """Get the status of all embedders"""
    return {
        "mistral_embedder": "available" if mistral_embedder else "unavailable",
        "groq_embedder": "available" if groq_embedder else "unavailable",
        "current_embedder": "mistral" if mistral_embedder else ("groq" if groq_embedder else "none")
    }

def get_model_status():
    """Get the status of all models"""
    return {
        "fallback_manager": {
            "available_models": fallback_manager.get_available_models(),
            "best_available": fallback_manager.get_best_available_model(),
            "model_status": fallback_manager.model_status
        },
        "models": {name: "available" for name in MODELS.keys()}
    }

def health_check():
    """Check the health of all AI models"""
    available_models = fallback_manager.get_available_models()
    best_model = fallback_manager.get_best_available_model()
    
    return {
        "status": "healthy" if available_models else "unhealthy",
        "available_models": available_models,
        "best_available_model": best_model,
        "total_models": len(fallback_manager.fallback_order),
        "available_count": len(available_models)
    }
