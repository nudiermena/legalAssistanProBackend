"""
Security middleware for FastAPI application.
Includes rate limiting, authentication, security headers, and request logging.
"""

import time
import json
import hashlib
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import logging
import asyncio
from contextvars import ContextVar

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

import redis.asyncio as redis
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config.security import (
    SECURITY_CONFIG,
    SecurityUtils,
    SecurityHeaders,
    SecurityLevel
)
from config.supabase import get_user_manager

# Request context variables
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
user_id_var: ContextVar[str] = ContextVar("user_id", default="")
client_ip_var: ContextVar[str] = ContextVar("client_ip", default="")

# Security logger
security_logger = logging.getLogger("security")

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis with in-memory fallback"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.redis_client: Optional[redis.Redis] = None
        self.in_memory_limits: Dict[str, Dict[str, List[int]]] = {}
        self.rate_limits = {
            "minute": SECURITY_CONFIG.rate_limit.requests_per_minute,
            "hour": SECURITY_CONFIG.rate_limit.requests_per_hour,
            "day": SECURITY_CONFIG.rate_limit.requests_per_day
        }
    
    async def connect_redis(self):
        """Connect to Redis for rate limiting"""
        if not self.redis_client:
            try:
                self.redis_client = redis.from_url(
                    SECURITY_CONFIG.redis_url,
                    db=SECURITY_CONFIG.redis_db,
                    decode_responses=True
                )
                await self.redis_client.ping()
                security_logger.info("Connected to Redis for rate limiting")
            except Exception as e:
                security_logger.warning(f"Failed to connect to Redis: {e}")
                security_logger.warning("Rate limiting will be disabled - all requests will be allowed")
                self.redis_client = None
    
    def get_client_identifier(self, request: Request) -> str:
        """Get unique identifier for rate limiting"""
        # Try to get user ID from JWT token first
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            # Use token hash as identifier instead of full verification
            token_hash = hashlib.md5(token.encode()).hexdigest()[:8]
            return f"jwt:{token_hash}"
        
        # Try to get API key
        api_key = request.headers.get(SECURITY_CONFIG.api_key_header)
        if api_key:
            return f"api_key:{api_key}"
        
        # Fall back to IP address
        client_ip = self.get_client_ip(request)
        return f"ip:{client_ip}"
    
    def get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct connection
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"
    
    async def check_rate_limit(self, identifier: str, window: str) -> bool:
        """Check if request is within rate limit for given window"""
        current_time = int(time.time())
        
        # Try Redis first
        if self.redis_client:
            try:
                key = f"rate_limit:{identifier}:{window}"
                
                # Remove old entries
                await self.redis_client.zremrangebyscore(key, 0, current_time - 60)
                
                # Count current requests
                count = await self.redis_client.zcard(key)
                
                if count >= self.rate_limits[window]:
                    return False
                
                # Add current request
                await self.redis_client.zadd(key, {str(current_time): current_time})
                await self.redis_client.expire(key, 60)  # Expire after 60 seconds
                
                return True
            except Exception as e:
                security_logger.warning(f"Redis rate limit check failed, falling back to in-memory: {e}")
        
        # Fallback to in-memory storage
        try:
            if identifier not in self.in_memory_limits:
                self.in_memory_limits[identifier] = {"minute": [], "hour": [], "day": []}
            
            # Clean old entries based on window
            window_seconds = {"minute": 60, "hour": 3600, "day": 86400}[window]
            cutoff_time = current_time - window_seconds
            
            # Remove old timestamps
            self.in_memory_limits[identifier][window] = [
                ts for ts in self.in_memory_limits[identifier][window] 
                if ts > cutoff_time
            ]
            
            # Check if limit exceeded
            if len(self.in_memory_limits[identifier][window]) >= self.rate_limits[window]:
                return False
            
            # Add current request
            self.in_memory_limits[identifier][window].append(current_time)
            
            return True
            
        except Exception as e:
            security_logger.error(f"In-memory rate limit check failed: {e}")
            return True  # Allow on error
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process request with rate limiting"""
        # Skip rate limiting for certain endpoints
        if request.url.path in ["/health", "/metrics", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        # Connect to Redis if needed
        await self.connect_redis()
        
        # Get client identifier
        identifier = self.get_client_identifier(request)
        client_ip = self.get_client_ip(request)
        
        # Set context variables
        client_ip_var.set(client_ip)
        request_id_var.set(SecurityUtils.generate_request_id())
        
        # Check rate limits
        for window in ["minute", "hour", "day"]:
            if not await self.check_rate_limit(identifier, window):
                security_logger.warning(f"Rate limit exceeded for {identifier} on {window} window")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded",
                        "retry_after": 60,
                        "request_id": request_id_var.get()
                    }
                )
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.rate_limits["minute"])
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.rate_limits["minute"] - 1))
        response.headers["X-Process-Time"] = str(process_time)
        
        return response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Add security headers to response"""
        response = await call_next(request)
        
        if SECURITY_CONFIG.enable_security_headers:
            headers = SecurityHeaders.get_security_headers()
            for header, value in headers.items():
                response.headers[header] = value
        
        return response

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for Supabase JWT tokens and API key validation"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.api_keys: Dict[str, Dict[str, Any]] = {}
        self.load_api_keys()
    
    def load_api_keys(self):
        """Load API keys from environment or database"""
        # In production, this would load from a secure database
        # For now, we'll use environment variables
        import os
        
        # Load from environment variables (format: API_KEY_1=key1,API_KEY_2=key2)
        api_keys_env = os.getenv("API_KEYS", "")
        if api_keys_env:
            keys = api_keys_env.split(",")
            for key in keys:
                if key.strip():
                    self.api_keys[key.strip()] = {
                        "user_id": f"user_{hashlib.md5(key.encode()).hexdigest()[:8]}",
                        "permissions": ["read", "write"],
                        "created_at": datetime.now().isoformat()
                    }
        
        # Add default test key if no keys are configured
        if not self.api_keys:
            self.api_keys["test_key_12345"] = {
                "user_id": "test_user",
                "permissions": ["read", "write"],
                "created_at": datetime.now().isoformat()
            }
            security_logger.warning("Using default test API key. Configure API_KEYS environment variable for production.")
    
    def get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct connection
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"
    
    def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Validate API key and return user info"""
        return self.api_keys.get(api_key)
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process request with authentication"""
        # Skip authentication for certain endpoints
        if not self.requires_auth(request.url.path):
            security_logger.debug(f"Skipping authentication for public endpoint: {request.url.path}")
            return await call_next(request)
        
        security_logger.debug(f"=== Processing authentication for: {request.url.path} ===")
        security_logger.debug(f"Request method: {request.method}")
        security_logger.debug(f"Client IP: {self.get_client_ip(request)}")
        
        # Check for JWT token first (Bearer token) - Supabase Auth
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            security_logger.debug(f"JWT token found: {token[:20]}...")
            security_logger.debug(f"Token length: {len(token)} characters")
            
            try:
                # Verify JWT token with Supabase
                security_logger.debug("Calling user_manager.verify_user_token() from middleware")
                start_time = datetime.utcnow()
                
                user_manager = get_user_manager()
                user = await user_manager.verify_user_token(token)
                
                validation_time = (datetime.utcnow() - start_time).total_seconds()
                security_logger.debug(f"Middleware token validation completed in {validation_time:.3f} seconds")
                
                if user and user.get("is_active", True):
                    security_logger.debug(f"JWT validation successful for user: {user.get('email', 'Unknown')}")
                    security_logger.debug(f"User ID: {user.get('user_id', 'Unknown')}")
                    security_logger.debug(f"User admin status: {user.get('is_admin', False)}")
                    
                    user_id_var.set(user["user_id"])
                    # Add user info to request state
                    request.state.user = {
                        "user_id": user["user_id"],
                        "username": user.get("username"),
                        "email": user.get("email"),
                        "is_admin": user.get("is_admin", False),
                        "auth_type": "supabase_jwt"
                    }
                    
                    security_logger.debug("User context set successfully")
                    return await call_next(request)
                else:
                    # Try automatic refresh if refresh token header present
                    refresh_token = request.headers.get("X-Refresh-Token")
                    if refresh_token:
                        try:
                            security_logger.debug("Attempting automatic token refresh via X-Refresh-Token header")
                            data = user_manager.refresh_access_token(refresh_token)
                            if data and data.get("access_token"):
                                # Re-verify with new token
                                new_token = data["access_token"]
                                user = await user_manager.verify_user_token(new_token)
                                if user and user.get("is_active", True):
                                    # Attach new tokens to response headers
                                    response = await call_next(request)
                                    response.headers["X-New-Access-Token"] = new_token
                                    if data.get("refresh_token"):
                                        response.headers["X-New-Refresh-Token"] = data.get("refresh_token")
                                    return response
                        except Exception as refresh_error:
                            security_logger.warning(f"Auto refresh failed: {refresh_error}")

                    if user:
                        security_logger.warning(f"User account is inactive: {user.get('email', 'Unknown')}")
                    else:
                        security_logger.warning("JWT token validation failed - no user returned")
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={
                            "error": "Invalid or inactive user token",
                            "request_id": request_id_var.get()
                        }
                    )
            except Exception as e:
                security_logger.warning(f"JWT token validation failed: {str(e)}")
                security_logger.warning(f"Exception type: {type(e).__name__}")
        
        # Fall back to API key authentication
        api_key = request.headers.get(SECURITY_CONFIG.api_key_header)
        if api_key:
            security_logger.debug(f"API key found: {api_key[:8]}...")
            user_info = self.validate_api_key(api_key)
            if user_info:
                security_logger.debug(f"API key validation successful for user: {user_info.get('user_id', 'Unknown')}")
                user_id_var.set(user_info["user_id"])
                # Add user info to request state
                request.state.user = {**user_info, "auth_type": "api_key"}
                return await call_next(request)
            else:
                security_logger.warning(f"Invalid API key used: {api_key[:8]}...")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "error": "Invalid API key",
                        "request_id": request_id_var.get()
                    }
                )
        
        # No valid authentication found
        security_logger.warning(f"No valid authentication for {request.url.path}")
        security_logger.debug("=== Authentication failed ===")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": "Authentication required. Use Bearer token (Supabase JWT) or API key.",
                "request_id": request_id_var.get()
            }
        )
    
    def requires_auth(self, path: str) -> bool:
        """Check if endpoint requires authentication"""
        # Skip auth for public endpoints
        public_paths = [
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/security/dashboard",
            "/security/health",
            "/auth/validate",  # Allow token validation without auth
            "/auth/refresh",   # Allow token refresh without auth
            "/auth/health",
            "/api/friend-invite/validate",  # Allow friend invite validation without auth
            "/api/friend-invite/accept"  # Allow friend invite acceptance without auth
        ]
        
        return not any(path.startswith(public_path) for public_path in public_paths)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests for security monitoring"""
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Log request details"""
        start_time = time.time()
        
        # Log request
        security_logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {client_ip_var.get()} "
            f"ID: {request_id_var.get()}"
        )
        
        # Process request
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log response
        security_logger.info(
            f"Response: {response.status_code} "
            f"in {process_time:.3f}s "
            f"ID: {request_id_var.get()}"
        )
        
        return response

class InputValidationMiddleware(BaseHTTPMiddleware):
    """Validate and sanitize input data"""
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Validate request input"""
        # Basic input validation for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Check content length
                content_length = request.headers.get("content-length")
                if content_length and int(content_length) > SECURITY_CONFIG.max_json_payload_size:
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={
                            "error": "Request too large",
                            "request_id": request_id_var.get()
                        }
                    )
            except Exception as e:
                security_logger.warning(f"Input validation error: {e}")
        
        return await call_next(request)

# Utility functions for accessing context variables
def get_request_id() -> str:
    """Get current request ID from context"""
    return request_id_var.get()

def get_user_id() -> str:
    """Get current user ID from context"""
    return user_id_var.get()

def get_client_ip() -> str:
    """Get client IP from context"""
    return client_ip_var.get()

# Export middleware classes
__all__ = [
    "RateLimitMiddleware",
    "SecurityHeadersMiddleware", 
    "AuthenticationMiddleware",
    "RequestLoggingMiddleware",
    "InputValidationMiddleware",
    "get_request_id",
    "get_user_id",
    "get_client_ip"
] 