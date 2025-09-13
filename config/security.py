"""
Security configuration and utilities for the Legal AI Assistant API.
Handles rate limiting, authentication, authorization, and security best practices.
"""

import os
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import logging
from dataclasses import dataclass, field
from pathlib import Path
import time

# Security logging
security_logger = logging.getLogger("security")

class SecurityLevel(Enum):
    """Security levels for different environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class RateLimitType(Enum):
    """Types of rate limiting"""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"

@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_limit: int = 10
    window_size: int = 60  # seconds
    rate_limit_type: RateLimitType = RateLimitType.SLIDING_WINDOW

@dataclass
class SecurityConfig:
    """Main security configuration"""
    # Environment
    environment: SecurityLevel = SecurityLevel.DEVELOPMENT
    
    # Rate limiting
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    
    # Authentication
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # API Keys
    api_key_header: str = "X-API-Key"
    api_key_length: int = 32
    
    # Security headers
    enable_security_headers: bool = True
    enable_cors: bool = True
    cors_origins: List[str] = field(default_factory=list)
    cors_methods: List[str] = field(default_factory=list)
    cors_headers: List[str] = field(default_factory=list)
    
    # File upload security
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: List[str] = field(default_factory=list)
    scan_uploads: bool = True
    
    # Input validation
    max_input_length: int = 10000
    max_json_payload_size: int = 1024 * 1024  # 1MB
    
    # Logging
    log_sensitive_data: bool = False
    log_request_headers: bool = True
    log_response_headers: bool = False
    
    # Redis configuration (for rate limiting)
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 0
    
    def __post_init__(self):
        if not self.secret_key:
            self.secret_key = self._generate_secret_key()
        
        # Set defaults if lists are empty
        if not self.cors_origins:
            self.cors_origins = ["*"] if self.environment == SecurityLevel.DEVELOPMENT else []
        if not self.cors_methods:
            self.cors_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        if not self.cors_headers:
            self.cors_headers = ["*"]
        if not self.allowed_file_types:
            self.allowed_file_types = [
                ".pdf", ".doc", ".docx", ".txt", ".rtf",
                ".jpg", ".jpeg", ".png", ".gif", ".bmp"
            ]

    def _generate_secret_key(self) -> str:
        """Generate a secure secret key"""
        return secrets.token_urlsafe(32)

# Load configuration from environment
def load_security_config() -> SecurityConfig:
    """Load security configuration from environment variables"""
    config = SecurityConfig()
    
    # Environment
    env = os.getenv("SECURITY_ENVIRONMENT", "development").lower()
    if env == "production":
        config.environment = SecurityLevel.PRODUCTION
    elif env == "staging":
        config.environment = SecurityLevel.STAGING
    
    # Secret key
    config.secret_key = os.getenv("SECRET_KEY", config.secret_key)
    
    # Rate limiting
    config.rate_limit.requests_per_minute = int(os.getenv("RATE_LIMIT_PER_MINUTE", config.rate_limit.requests_per_minute))
    config.rate_limit.requests_per_hour = int(os.getenv("RATE_LIMIT_PER_HOUR", config.rate_limit.requests_per_hour))
    config.rate_limit.requests_per_day = int(os.getenv("RATE_LIMIT_PER_DAY", config.rate_limit.requests_per_day))
    config.rate_limit.burst_limit = int(os.getenv("RATE_LIMIT_BURST", config.rate_limit.burst_limit))
    
    # CORS
    cors_origins = os.getenv("CORS_ORIGINS")
    if cors_origins:
        config.cors_origins = [origin.strip() for origin in cors_origins.split(",")]
    
    # File upload
    config.max_file_size = int(os.getenv("MAX_FILE_SIZE", config.max_file_size))
    config.scan_uploads = os.getenv("SCAN_UPLOADS", "true").lower() == "true"
    
    # Redis
    config.redis_url = os.getenv("REDIS_URL", config.redis_url)
    
    return config

# Security utilities
class SecurityUtils:
    """Utility functions for security operations"""
    
    @staticmethod
    def generate_request_id() -> str:
        """Generate a unique request ID"""
        return f"{int(time.time())}-{secrets.token_hex(8)}"
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a secure API key"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        import bcrypt
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify a password against its hash"""
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    @staticmethod
    def generate_token(data: Dict[str, Any], secret_key: str, expires_in: int = 30) -> str:
        """Generate a JWT token"""
        from jose import jwt
        from datetime import datetime, timedelta
        
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=expires_in)
        to_encode.update({"exp": expire})
        
        return jwt.encode(to_encode, secret_key, algorithm="HS256")
    
    @staticmethod
    def verify_token(token: str, secret_key: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token"""
        from jose import jwt, JWTError
        
        try:
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
            return payload
        except JWTError:
            return None
    
    @staticmethod
    def sanitize_input(text: str, max_length: int = 10000) -> str:
        """Sanitize user input to prevent injection attacks"""
        if not text:
            return ""
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Limit length
        if len(text) > max_length:
            text = text[:max_length]
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<script>', 'javascript:', 'vbscript:', 'onload=', 'onerror=']
        for char in dangerous_chars:
            text = text.replace(char.lower(), '')
            text = text.replace(char.upper(), '')
        
        return text.strip()
    
    @staticmethod
    def validate_file_type(filename: str, allowed_types: List[str]) -> bool:
        """Validate file type against allowed list"""
        if not filename:
            return False
        
        file_ext = Path(filename).suffix.lower()
        return file_ext in allowed_types
    
    @staticmethod
    def validate_file_size(file_size: int, max_size: int) -> bool:
        """Validate file size against maximum allowed size"""
        return file_size <= max_size
    
    @staticmethod
    def mask_sensitive_data(data: str, mask_char: str = "*") -> str:
        """Mask sensitive data in logs"""
        if not data:
            return data
        
        # Mask email addresses
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        data = re.sub(email_pattern, f'{mask_char * 8}@example.com', data)
        
        # Mask phone numbers
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        data = re.sub(phone_pattern, f'{mask_char * 10}', data)
        
        # Mask credit card numbers
        cc_pattern = r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
        data = re.sub(cc_pattern, f'{mask_char * 16}', data)
        
        return data

# Security middleware configuration
class SecurityHeaders:
    """Security headers configuration"""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get security headers for responses"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https:; frame-ancestors 'none';"
        }

# Load the security configuration
SECURITY_CONFIG = load_security_config()

# Export commonly used functions
__all__ = [
    "SECURITY_CONFIG",
    "SecurityConfig",
    "RateLimitConfig",
    "SecurityLevel",
    "RateLimitType",
    "SecurityUtils",
    "SecurityHeaders",
    "load_security_config"
] 