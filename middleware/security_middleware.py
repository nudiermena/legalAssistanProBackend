"""
Security Middleware for Agent Protection
Implements comprehensive security measures across all agent endpoints
"""

import logging
import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from functools import wraps
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

from utils.security_protection import (
    protect_agent_input, 
    protect_agent_response, 
    get_security_stats,
    SecurityAlert,
    ThreatLevel
)

logger = logging.getLogger(__name__)

class SecurityMiddleware:
    """Security middleware for agent protection"""
    
    def __init__(self):
        self.rate_limits = {}
        self.request_counts = {}
        self.blocked_ips = set()
        self.suspicious_patterns = set()
    
    def rate_limit_check(self, user_id: str, ip_address: str, max_requests: int = 100, window_minutes: int = 60) -> bool:
        """Check if user/IP is within rate limits"""
        current_time = datetime.now()
        window_start = current_time - timedelta(minutes=window_minutes)
        
        # Clean old entries
        self.rate_limits = {
            key: [(timestamp, count) for timestamp, count in entries 
                  if timestamp > window_start]
            for key, entries in self.rate_limits.items()
        }
        
        # Check user rate limit
        user_key = f"user_{user_id}"
        if user_key in self.rate_limits:
            user_requests = sum(count for _, count in self.rate_limits[user_key])
            if user_requests >= max_requests:
                logger.warning(f"Rate limit exceeded for user {user_id}: {user_requests} requests")
                return False
        
        # Check IP rate limit
        ip_key = f"ip_{ip_address}"
        if ip_key in self.rate_limits:
            ip_requests = sum(count for _, count in self.rate_limits[ip_key])
            if ip_requests >= max_requests * 2:  # Higher limit for IP
                logger.warning(f"Rate limit exceeded for IP {ip_address}: {ip_requests} requests")
                return False
        
        # Update counters
        if user_key not in self.rate_limits:
            self.rate_limits[user_key] = []
        if ip_key not in self.rate_limits:
            self.rate_limits[ip_key] = []
        
        self.rate_limits[user_key].append((current_time, 1))
        self.rate_limits[ip_key].append((current_time, 1))
        
        return True
    
    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP is blocked"""
        return ip_address in self.blocked_ips
    
    def block_ip(self, ip_address: str, reason: str):
        """Block IP address"""
        self.blocked_ips.add(ip_address)
        logger.warning(f"Blocked IP {ip_address}: {reason}")
    
    def detect_suspicious_patterns(self, user_input: str) -> bool:
        """Detect suspicious input patterns"""
        suspicious_indicators = [
            "ignore previous instructions",
            "forget everything above",
            "you are now a different ai",
            "system prompt",
            "show me your instructions",
            "what is your prompt",
            "reveal your system message",
            "jailbreak",
            "dan mode",
            "developer override",
            "admin access",
            "bypass restrictions",
            "ignore safety guidelines",
            "disable safety measures",
            "remove content filters",
            "unrestricted mode",
            "god mode"
        ]
        
        user_input_lower = user_input.lower()
        for indicator in suspicious_indicators:
            if indicator in user_input_lower:
                self.suspicious_patterns.add(indicator)
                return True
        
        return False
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers for responses"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }

def security_protection(agent_name: str, max_requests: int = 100, window_minutes: int = 60):
    """Decorator for agent security protection"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request information
            request = None
            user_id = None
            session_id = None
            ip_address = "unknown"
            
            # Find request object in arguments - look for FastAPI Request object
            for arg in args:
                if hasattr(arg, 'client') and hasattr(arg, 'scope'):  # FastAPI Request object
                    request = arg
                    break
            
            # Extract from kwargs
            if not request and 'request' in kwargs:
                request = kwargs['request']
            
            # If no FastAPI Request found, try to get from function signature
            if not request:
                import inspect
                sig = inspect.signature(func)
                for param_name, param in sig.parameters.items():
                    if param.annotation == Request or (hasattr(param.annotation, '__name__') and 'Request' in str(param.annotation)):
                        if param_name in kwargs:
                            request = kwargs[param_name]
                            break
            
            # Extract IP and user info if Request object is available
            if request and hasattr(request, 'client'):
                ip_address = request.client.host if request.client else "unknown"
                user_id = getattr(request.state, 'user_id', None)
                session_id = getattr(request.state, 'session_id', None)
            else:
                # Fallback: try to get user info from current_user if available
                if 'current_user' in kwargs:
                    current_user = kwargs['current_user']
                    if isinstance(current_user, dict):
                        user_id = current_user.get('user_id') or current_user.get('id')
                        session_id = current_user.get('session_id')
                # Use a default IP for rate limiting when no request object
                ip_address = "default"
            
            # Initialize security middleware
            security_middleware = SecurityMiddleware()
            
            # Check if IP is blocked
            if security_middleware.is_ip_blocked(ip_address):
                logger.warning(f"Blocked IP {ip_address} attempted to access {agent_name}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied due to security violations"
                )
            
            # Check rate limits
            if not security_middleware.rate_limit_check(user_id or "anonymous", ip_address, max_requests, window_minutes):
                logger.warning(f"Rate limit exceeded for {agent_name} - User: {user_id}, IP: {ip_address}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please try again later."
                )
            
            # Extract user input from function arguments
            user_input = None
            
            # Try to extract from various possible sources
            if 'message' in kwargs:
                user_input = kwargs['message']
            elif 'query' in kwargs:
                user_input = kwargs['query']
            elif 'text' in kwargs:
                user_input = kwargs['text']
            elif len(args) > 0 and isinstance(args[0], str):
                user_input = args[0]
            else:
                # Try to extract from request objects (like ChatRequest)
                for arg in args:
                    if hasattr(arg, 'message'):
                        user_input = arg.message
                        break
                    elif hasattr(arg, 'query'):
                        user_input = arg.query
                        break
                    elif hasattr(arg, 'text'):
                        user_input = arg.text
                        break
                
                # Try from kwargs
                for key in ['request', 'chat_request', 'data']:
                    if key in kwargs:
                        obj = kwargs[key]
                        if hasattr(obj, 'message'):
                            user_input = obj.message
                            break
                        elif hasattr(obj, 'query'):
                            user_input = obj.query
                            break
                        elif hasattr(obj, 'text'):
                            user_input = obj.text
                            break
            
            # Protect input if found
            if user_input:
                # Detect suspicious patterns
                if security_middleware.detect_suspicious_patterns(user_input):
                    logger.warning(f"Suspicious pattern detected in {agent_name} - User: {user_id}, IP: {ip_address}")
                    # Don't block immediately, let the security protector handle it
                
                # Use security protection
                is_safe, sanitized_input, alert = protect_agent_input(
                    user_input, agent_name, user_id, session_id
                )
                
                if not is_safe:
                    logger.warning(f"Security threat detected in {agent_name}: {alert.attack_type if alert else 'Unknown'}")
                    
                    # Block IP for critical threats
                    if alert and alert.threat_level == ThreatLevel.CRITICAL:
                        security_middleware.block_ip(ip_address, f"Critical threat: {alert.attack_type}")
                    
                    # Return safe response
                    safe_response = {
                        "response": {
                            "content": "I'm a legal assistant specialized in Colombian law. I can help you with legal questions, research, and guidance within my expertise.",
                            "security_warning": "Your request was flagged for security review.",
                            "relevant_laws": [],
                            "recommendations": ["Please rephrase your question in a clear, legal context."],
                            "clarifying_questions": []
                        },
                        "security_status": "threat_detected",
                        "threat_level": alert.threat_level.value if alert else "unknown",
                        "agent_name": agent_name
                    }
                    
                    return JSONResponse(
                        content=safe_response,
                        headers=security_middleware.get_security_headers(),
                        status_code=status.HTTP_200_OK
                    )
                
                # Update kwargs with sanitized input
                if 'message' in kwargs:
                    kwargs['message'] = sanitized_input
                elif 'query' in kwargs:
                    kwargs['query'] = sanitized_input
                elif 'text' in kwargs:
                    kwargs['text'] = sanitized_input
                elif len(args) > 0 and isinstance(args[0], str):
                    args = (sanitized_input,) + args[1:]
                else:
                    # Update request objects with sanitized input
                    for arg in args:
                        if hasattr(arg, 'message'):
                            arg.message = sanitized_input
                            break
                        elif hasattr(arg, 'query'):
                            arg.query = sanitized_input
                            break
                        elif hasattr(arg, 'text'):
                            arg.text = sanitized_input
                            break
                    
                    # Update from kwargs
                    for key in ['request', 'chat_request', 'data']:
                        if key in kwargs:
                            obj = kwargs[key]
                            if hasattr(obj, 'message'):
                                obj.message = sanitized_input
                                break
                            elif hasattr(obj, 'query'):
                                obj.query = sanitized_input
                                break
                            elif hasattr(obj, 'text'):
                                obj.text = sanitized_input
                                break
            
            # Execute the original function
            try:
                start_time = time.time()
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Log successful execution
                logger.info(f"Secure execution of {agent_name} - User: {user_id}, Time: {execution_time:.2f}s")
                
                # Protect response if it's a dictionary with content
                if isinstance(result, dict) and 'response' in result:
                    if isinstance(result['response'], dict) and 'content' in result['response']:
                        result['response']['content'] = protect_agent_response(
                            result['response']['content'], agent_name
                        )
                
                # Add security headers
                if hasattr(result, 'headers'):
                    result.headers.update(security_middleware.get_security_headers())
                
                return result
                
            except Exception as e:
                logger.error(f"Error in secure execution of {agent_name}: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error. Please try again."
                )
        
        return wrapper
    return decorator

def create_security_response(content: str, agent_name: str, status_code: int = 200) -> JSONResponse:
    """Create a secure response with proper headers"""
    security_middleware = SecurityMiddleware()
    
    response_data = {
        "response": {
            "content": protect_agent_response(content, agent_name),
            "security_status": "secure",
            "agent_name": agent_name
        },
        "timestamp": datetime.now().isoformat()
    }
    
    return JSONResponse(
        content=response_data,
        headers=security_middleware.get_security_headers(),
        status_code=status_code
    )

def get_security_dashboard_data() -> Dict[str, Any]:
    """Get security dashboard data for monitoring"""
    stats = get_security_stats()
    security_middleware = SecurityMiddleware()
    
    return {
        "security_stats": stats,
        "blocked_ips": len(security_middleware.blocked_ips),
        "suspicious_patterns": len(security_middleware.suspicious_patterns),
        "rate_limits": {
            "active_limits": len(security_middleware.rate_limits),
            "blocked_users": len([k for k in security_middleware.rate_limits.keys() if k.startswith("user_")])
        },
        "timestamp": datetime.now().isoformat()
    }

# Import asyncio for the decorator
import asyncio
