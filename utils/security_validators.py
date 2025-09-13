"""
Security validation utilities for input sanitization and validation.
"""

import re
import hashlib
import mimetypes
import uuid
from typing import Dict, List, Optional, Any, Tuple, Union
from pathlib import Path
import logging
from datetime import datetime
import json

from fastapi import HTTPException, status, UploadFile
from pydantic import BaseModel, validator, Field
import magic

from config.security import SECURITY_CONFIG, SecurityUtils

# Security logger
security_logger = logging.getLogger("security")

class SecurityValidationError(Exception):
    """Custom exception for security validation errors"""
    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class InputValidator:
    """Input validation utilities"""
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = None) -> str:
        """Sanitize text input to prevent injection attacks"""
        if not text:
            return ""
        
        # Use security config max length if not specified
        if max_length is None:
            max_length = SECURITY_CONFIG.max_input_length
        
        # Apply security utils sanitization
        sanitized = SecurityUtils.sanitize_input(text, max_length)
        
        # Additional sanitization for legal documents
        # Remove potential SQL injection patterns
        sql_patterns = [
            r"(\b(union|select|insert|update|delete|drop|create|alter)\b)",
            r"(\b(or|and)\b\s+\d+\s*=\s*\d+)",
            r"(--|#|/\*|\*/)",
            r"(\b(exec|execute|script)\b)",
        ]
        
        for pattern in sql_patterns:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)
        
        # Remove null bytes and control characters
        sanitized = "".join(char for char in sanitized if ord(char) >= 32 or char in "\n\r\t")
        
        return sanitized.strip()
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        if not email:
            return False
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number format"""
        if not phone:
            return False
        
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        
        # Check if it's a valid length (7-15 digits)
        return 7 <= len(digits_only) <= 15
    
    @staticmethod
    def validate_document_id(doc_id: str) -> bool:
        """Validate Colombian document ID format (CC, CE, NIT)"""
        if not doc_id:
            return False
        doc_id = doc_id.strip()
        # NIT: 8-10 digits, optional hyphen, 1 check digit (e.g., 900123456-7)
        nit_pattern = r'^\d{8,10}-\d{1}$'
        # CC/CE: 6-11 digits, no hyphen
        cc_ce_pattern = r'^\d{6,11}$'
        if re.match(nit_pattern, doc_id):
            return True
        if re.match(cc_ce_pattern, doc_id):
            return True
        return False
    
    @staticmethod
    def validate_json_payload(payload: Dict[str, Any], max_depth: int = 10) -> bool:
        """Validate JSON payload structure and size"""
        try:
            # Check payload size
            payload_str = json.dumps(payload)
            if len(payload_str) > SECURITY_CONFIG.max_json_payload_size:
                return False
            
            # Check nesting depth
            def check_depth(obj, current_depth=0):
                if current_depth > max_depth:
                    return False
                
                if isinstance(obj, dict):
                    return all(check_depth(v, current_depth + 1) for v in obj.values())
                elif isinstance(obj, list):
                    return all(check_depth(item, current_depth + 1) for item in obj)
                else:
                    return True
            
            return check_depth(payload)
            
        except Exception:
            return False

class FileValidator:
    """File upload validation utilities"""
    
    @staticmethod
    def validate_file_type(file: UploadFile, allowed_types: List[str] = None) -> bool:
        """Validate file type using multiple methods"""
        if not file or not file.filename:
            return False
        
        if allowed_types is None:
            allowed_types = SECURITY_CONFIG.allowed_file_types
        
        filename = file.filename.lower()
        
        # Check file extension
        file_ext = Path(filename).suffix
        if file_ext not in allowed_types:
            return False
        
        # Additional MIME type validation
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type:
            # Map extensions to expected MIME types
            expected_mime_types = {
                ".pdf": "application/pdf",
                ".doc": "application/msword",
                ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                ".txt": "text/plain",
                ".rtf": "application/rtf",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".bmp": "image/bmp"
            }
            
            expected_mime = expected_mime_types.get(file_ext)
            if expected_mime and mime_type != expected_mime:
                return False
        
        return True
    
    @staticmethod
    async def validate_file_content(file: UploadFile) -> Tuple[bool, str]:
        """Validate file content using magic numbers"""
        try:
            # Read first 2048 bytes for magic number detection
            content = await file.read(2048)
            await file.seek(0)  # Reset file pointer
            
            if not content:
                return False, "Empty file"
            
            # Use python-magic to detect file type
            mime_type = magic.from_buffer(content, mime=True)
            
            # Validate against expected MIME types
            allowed_mime_types = [
                "application/pdf",
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "text/plain",
                "application/rtf",
                "image/jpeg",
                "image/png",
                "image/gif",
                "image/bmp"
            ]
            
            if mime_type not in allowed_mime_types:
                return False, f"Invalid file type: {mime_type}"
            
            # Check for malicious content patterns
            content_str = content.decode('utf-8', errors='ignore')
            malicious_patterns = [
                r"<script[^>]*>",
                r"javascript:",
                r"vbscript:",
                r"onload\s*=",
                r"onerror\s*=",
                r"onclick\s*=",
                r"eval\s*\(",
                r"document\.write",
                r"window\.open",
                r"<iframe[^>]*>"
            ]
            
            for pattern in malicious_patterns:
                if re.search(pattern, content_str, re.IGNORECASE):
                    return False, f"Malicious content detected: {pattern}"
            
            return True, "File content is valid"
            
        except Exception as e:
            return False, f"Error validating file content: {str(e)}"
    
    @staticmethod
    def validate_file_size(file_size: int, max_size: int = None) -> bool:
        """Validate file size"""
        if max_size is None:
            max_size = SECURITY_CONFIG.max_file_size
        
        return file_size <= max_size
    
    @staticmethod
    def generate_file_hash(content: bytes) -> str:
        """Generate SHA-256 hash of file content"""
        return hashlib.sha256(content).hexdigest()

class RequestValidator:
    """Request validation utilities"""
    
    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """Validate API key format"""
        if not api_key:
            return False
        
        # Basic API key validation
        # In production, this would check against a database
        if len(api_key) < 10 or len(api_key) > 100:
            return False
        
        # Check for common patterns
        if re.search(r'[^a-zA-Z0-9\-_]', api_key):
            return False
        
        return True
    
    @staticmethod
    def validate_request_headers(headers: Dict[str, str]) -> bool:
        """Validate request headers for security"""
        required_headers = ["User-Agent"]
        
        for header in required_headers:
            if header not in headers:
                return False
        
        # Check for suspicious headers
        suspicious_headers = [
            "X-Forwarded-For",
            "X-Real-IP",
            "X-Forwarded-Host",
            "X-Forwarded-Proto"
        ]
        
        # In production, you might want to validate these headers
        # For now, we'll just log them
        for header in suspicious_headers:
            if header in headers:
                security_logger.info(f"Suspicious header detected: {header}")
        
        return True
    
    @staticmethod
    def validate_content_type(content_type: str, allowed_types: List[str] = None) -> bool:
        """Validate content type"""
        if allowed_types is None:
            allowed_types = [
                "application/json",
                "multipart/form-data",
                "application/x-www-form-urlencoded",
                "text/plain"
            ]
        
        return any(allowed_type in content_type for allowed_type in allowed_types)

class SecurityDecorators:
    """Security decorators for endpoints"""
    
    @staticmethod
    def require_authentication(func):
        """Decorator to require authentication"""
        async def wrapper(*args, **kwargs):
            # This would be implemented in the middleware
            # For now, just pass through
            return await func(*args, **kwargs)
        return wrapper
    
    @staticmethod
    def rate_limit(requests_per_minute: int = 60):
        """Decorator to apply rate limiting"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                # This would be implemented in the middleware
                # For now, just pass through
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    @staticmethod
    def validate_input(func):
        """Decorator to validate input"""
        async def wrapper(*args, **kwargs):
            # This would be implemented in the middleware
            # For now, just pass through
            return await func(*args, **kwargs)
        return wrapper

class SecureBaseModel(BaseModel):
    """Base model with automatic input sanitization"""
    
    @validator('*', pre=True)
    def sanitize_strings(cls, v):
        """Sanitize string inputs"""
        if isinstance(v, str):
            return InputValidator.sanitize_text(v)
        return v

class FileUploadRequest(SecureBaseModel):
    """Secure file upload request model"""
    file: UploadFile
    description: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = Field(None, max_items=10)
    
    @validator('description')
    def validate_description(cls, v):
        if v:
            return InputValidator.sanitize_text(v, 500)
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        if v:
            return [InputValidator.sanitize_text(tag, 50) for tag in v[:10]]
        return v

class SecureChatRequest(SecureBaseModel):
    """Secure chat request model"""
    message: str = Field(..., max_length=5000)
    client_id: str = Field(..., max_length=100)
    practice_area: Optional[str] = Field(None, max_length=50)
    
    @validator('message')
    def validate_message(cls, v):
        return InputValidator.sanitize_text(v, 5000)
    
    @validator('client_id')
    def validate_client_id(cls, v):
        return InputValidator.sanitize_text(v, 100)

def validate_and_sanitize_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize request data"""
    sanitized_data = {}
    
    for key, value in request_data.items():
        if isinstance(value, str):
            sanitized_data[key] = InputValidator.sanitize_text(value)
        elif isinstance(value, dict):
            sanitized_data[key] = validate_and_sanitize_request(value)
        elif isinstance(value, list):
            sanitized_data[key] = [
                InputValidator.sanitize_text(item) if isinstance(item, str) else item
                for item in value
            ]
        else:
            sanitized_data[key] = value
    
    return sanitized_data

def log_security_event(event_type: str, details: Dict[str, Any], severity: str = "INFO"):
    """Log security events"""
    try:
        event_data = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "severity": severity,
            "details": details
        }
        
        if severity.upper() == "ERROR":
            security_logger.error(f"Security event: {json.dumps(event_data)}")
        elif severity.upper() == "WARNING":
            security_logger.warning(f"Security event: {json.dumps(event_data)}")
        else:
            security_logger.info(f"Security event: {json.dumps(event_data)}")
            
    except Exception as e:
        security_logger.error(f"Error logging security event: {e}")

def sanitize_text_input(text: str, max_length: int = None) -> str:
    """Sanitize text input for document requests"""
    if not text:
        return ""
    
    # Use security config max length if not specified
    if max_length is None:
        max_length = SECURITY_CONFIG.max_input_length
    
    # Apply security utils sanitization
    sanitized = SecurityUtils.sanitize_input(text, max_length)
    
    # Additional sanitization for legal documents
    # Remove potential SQL injection patterns
    sql_patterns = [
        r"(\b(union|select|insert|update|delete|drop|create|alter)\b)",
        r"(\b(or|and)\b\s+\d+\s*=\s*\d+)",
        r"(--|#|/\*|\*/)",
        r"(\b(exec|execute|script)\b)",
    ]
    
    for pattern in sql_patterns:
        sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)
    
    # Remove null bytes and control characters
    sanitized = "".join(char for char in sanitized if ord(char) >= 32 or char in "\n\r\t")
    
    return sanitized.strip()

def validate_document_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize document request data"""
    try:
        # Validate required fields
        required_fields = ["document_type", "description", "parties", "key_points", "industry", "jurisdiction", "complexity"]
        for field in required_fields:
            if field not in request_data or not request_data[field]:
                raise SecurityValidationError(f"Missing required field: {field}")
        
        # Validate document type
        document_type = sanitize_text_input(request_data["document_type"], 200)
        if len(document_type) < 3:
            raise SecurityValidationError("Document type must be at least 3 characters long")
        
        # Validate description
        description = sanitize_text_input(request_data["description"], 2000)
        if len(description) < 10:
            raise SecurityValidationError("Description must be at least 10 characters long")
        
        # Validate parties
        if not isinstance(request_data["parties"], list) or len(request_data["parties"]) < 1:
            raise SecurityValidationError("At least one party is required")
        
        if len(request_data["parties"]) > 10:
            raise SecurityValidationError("Maximum 10 parties allowed")
        
        validated_parties = []
        for party in request_data["parties"]:
            if not isinstance(party, dict):
                raise SecurityValidationError("Invalid party format")
            
            required_party_fields = ["name", "identification", "role"]
            for field in required_party_fields:
                if field not in party or not party[field]:
                    raise SecurityValidationError(f"Missing required party field: {field}")
            
            validated_party = {
                "name": sanitize_text_input(party["name"], 200),
                "identification": sanitize_text_input(party["identification"], 50),
                "role": sanitize_text_input(party["role"], 100)
            }
            
            # Validate party name
            if len(validated_party["name"]) < 2:
                raise SecurityValidationError("Party name must be at least 2 characters long")
            
            # Validate identification
            if not InputValidator.validate_document_id(validated_party["identification"]):
                raise SecurityValidationError(
                    "Invalid document identification format. Accepted formats: CC/CE (6-11 digits), NIT (8-10 digits, optionally with hyphen and check digit, e.g., 900123456-7)."
                )
            
            validated_parties.append(validated_party)
        
        # Validate key points
        key_points = sanitize_text_input(request_data["key_points"], 1000)
        if len(key_points) < 5:
            raise SecurityValidationError("Key points must be at least 5 characters long")
        
        # Validate industry
        valid_industries = [
            "technology", "healthcare", "finance", "real-estate", 
            "retail", "agriculture", "oil-gas", "education", 
            "construction", "other"
        ]
        if request_data["industry"] not in valid_industries:
            raise SecurityValidationError("Invalid industry selection")
        
        # Validate jurisdiction
        valid_jurisdictions = [
            "federal", "bogota", "medellin", "cali", "barranquilla",
            "bucaramanga", "cartagena", "pereira", "other"
        ]
        if request_data["jurisdiction"] not in valid_jurisdictions:
            raise SecurityValidationError("Invalid jurisdiction selection")
        
        # Validate complexity
        valid_complexities = ["simple", "standard", "complex"]
        if request_data["complexity"] not in valid_complexities:
            raise SecurityValidationError("Invalid complexity selection")
        
        # Return validated data
        return {
            "document_type": document_type,
            "description": description,
            "parties": validated_parties,
            "key_points": key_points,
            "industry": request_data["industry"],
            "jurisdiction": request_data["jurisdiction"],
            "complexity": request_data["complexity"]
        }
        
    except SecurityValidationError:
        raise
    except Exception as e:
        security_logger.error(f"Error validating document request: {e}")
        raise SecurityValidationError("Invalid request format")

def validate_legal_document_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize legal document request data (for the original endpoint)"""
    try:
        # Validate required fields
        required_fields = ["document_type", "parties"]
        for field in required_fields:
            if field not in request_data or not request_data[field]:
                raise SecurityValidationError(f"Missing required field: {field}")
        
        # Validate document type
        document_type = sanitize_text_input(request_data["document_type"], 200)
        if len(document_type) < 3:
            raise SecurityValidationError("Document type must be at least 3 characters long")
        
        # Validate jurisdiction
        jurisdiction = sanitize_text_input(request_data.get("jurisdiction", "Colombia"), 100)
        
        # Validate key requirements
        key_requirements = []
        if "key_requirements" in request_data and isinstance(request_data["key_requirements"], list):
            for req in request_data["key_requirements"]:
                sanitized_req = sanitize_text_input(str(req), 500)
                if sanitized_req:
                    key_requirements.append(sanitized_req)
        
        # Validate parties
        if not isinstance(request_data["parties"], list) or len(request_data["parties"]) < 1:
            raise SecurityValidationError("At least one party is required")
        
        if len(request_data["parties"]) > 10:
            raise SecurityValidationError("Maximum 10 parties allowed")
        
        validated_parties = []
        for party in request_data["parties"]:
            if not isinstance(party, dict):
                raise SecurityValidationError("Invalid party format")
            
            if "name" not in party or not party["name"]:
                raise SecurityValidationError("Party name is required")
            
            validated_party = {
                "name": sanitize_text_input(party["name"], 200),
                "role": sanitize_text_input(party.get("role", "Parte"), 100)
            }
            
            if len(validated_party["name"]) < 2:
                raise SecurityValidationError("Party name must be at least 2 characters long")
            
            validated_parties.append(validated_party)
        
        # Validate legal terms
        legal_terms = []
        if "legal_terms" in request_data and isinstance(request_data["legal_terms"], list):
            for term in request_data["legal_terms"]:
                sanitized_term = sanitize_text_input(str(term), 200)
                if sanitized_term:
                    legal_terms.append(sanitized_term)
        
        # Validate data processing
        data_processing = {}
        if "data_processing" in request_data and isinstance(request_data["data_processing"], dict):
            for key, value in request_data["data_processing"].items():
                sanitized_key = sanitize_text_input(str(key), 50)
                sanitized_value = sanitize_text_input(str(value), 200)
                if sanitized_key and sanitized_value:
                    data_processing[sanitized_key] = sanitized_value
        
        # Return validated data
        return {
            "document_type": document_type,
            "jurisdiction": jurisdiction,
            "key_requirements": key_requirements,
            "parties": validated_parties,
            "legal_terms": legal_terms,
            "data_processing": data_processing
        }
        
    except SecurityValidationError:
        raise
    except Exception as e:
        security_logger.error(f"Error validating legal document request: {e}")
        raise SecurityValidationError("Invalid request format")

# Export classes and functions
__all__ = [
    "SecurityValidationError",
    "InputValidator",
    "FileValidator", 
    "RequestValidator",
    "SecurityDecorators",
    "SecureBaseModel",
    "FileUploadRequest",
    "SecureChatRequest",
    "validate_and_sanitize_request",
    "log_security_event",
    "sanitize_text_input",
    "validate_document_request",
    "validate_legal_document_request"
] 