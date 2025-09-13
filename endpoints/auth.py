"""
Authentication endpoints for the Legal AI Assistant API.
Handles JWT token validation and user management with Supabase.
Note: User registration and login are handled by the frontend with Supabase Auth.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging
import secrets

from config.security import SECURITY_CONFIG, SecurityUtils
from config.supabase import get_user_manager, UserUpdate, UserCreate
from utils.security_validators import InputValidator, log_security_event
from middleware.security import get_request_id, get_client_ip

# Configure logging
logger = logging.getLogger(__name__)

# Security scheme for token authentication
security = HTTPBearer()

router = APIRouter(prefix="/auth", tags=["authentication"])

# Pydantic models for authentication
class TokenValidationResponse(BaseModel):
    """Token validation response model"""
    valid: bool = Field(..., description="Whether the token is valid")
    user_id: Optional[str] = Field(None, description="User ID if token is valid")
    expires_at: Optional[datetime] = Field(None, description="Token expiration time")
    scopes: Optional[list] = Field(None, description="Token scopes/permissions")

class SignupRequest(BaseModel):
    """User signup request model"""
    email: str = Field(..., description="User email")
    password: str = Field(..., min_length=6, description="User password")
    username: Optional[str] = Field(None, max_length=50, description="Username")
    full_name: Optional[str] = Field(None, max_length=100, description="Full name")
    organization: Optional[str] = Field(None, max_length=100, description="Organization")
    
    @field_validator('email')
    def validate_email(cls, v):
        """Validate email format"""
        if not v or '@' not in v:
            raise ValueError("Invalid email format")
        return v.lower().strip()
    
    @field_validator('username')
    def validate_username(cls, v):
        """Validate and sanitize username"""
        if v:
            sanitized = InputValidator.sanitize_text(v, 50)
            if not sanitized.replace('_', '').replace('-', '').isalnum():
                raise ValueError("Username can only contain letters, numbers, underscores, and hyphens")
            return sanitized
        return v
    
    @field_validator('full_name')
    def validate_full_name(cls, v):
        """Validate and sanitize full name"""
        if v:
            return InputValidator.sanitize_text(v, 100)
        return v
    
    @field_validator('organization')
    def validate_organization(cls, v):
        """Validate and sanitize organization"""
        if v:
            return InputValidator.sanitize_text(v, 100)
        return v

class SignupResponse(BaseModel):
    """User signup response model"""
    success: bool = Field(..., description="Whether the signup was successful")
    message: str = Field(..., description="Response message")
    user_id: Optional[str] = Field(None, description="User ID if created successfully")
    email: Optional[str] = Field(None, description="User email")
    user_exists: Optional[bool] = Field(None, description="Whether user already exists")
    error: Optional[str] = Field(None, description="Error type if any")

class TokenRefreshRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str = Field(..., description="Supabase refresh token")

class TokenRefreshResponse(BaseModel):
    """Token refresh response"""
    access_token: str
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    token_type: Optional[str] = None

class UserProfileUpdateRequest(BaseModel):
    """User profile update request model"""
    username: Optional[str] = Field(None, max_length=50, description="Username")
    full_name: Optional[str] = Field(None, max_length=100, description="Full name")
    organization: Optional[str] = Field(None, max_length=100, description="Organization")
    avatar_url: Optional[str] = Field(None, description="Profile picture URL")
    
    @field_validator('username')
    def validate_username(cls, v):
        """Validate and sanitize username"""
        if v:
            sanitized = InputValidator.sanitize_text(v, 50)
            if not sanitized.replace('_', '').replace('-', '').isalnum():
                raise ValueError("Username can only contain letters, numbers, underscores, and hyphens")
            return sanitized
        return v
    
    @field_validator('full_name')
    def validate_full_name(cls, v):
        """Validate and sanitize full name"""
        if v:
            return InputValidator.sanitize_text(v, 100)
        return v
    
    @field_validator('organization')
    def validate_organization(cls, v):
        """Validate and sanitize organization"""
        if v:
            return InputValidator.sanitize_text(v, 100)
        return v

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user from Supabase JWT token"""
    logger.debug("=== Starting get_current_user authentication process ===")
    
    token = credentials.credentials
    logger.debug(f"Extracted token from credentials: {token[:20]}...")
    logger.debug(f"Token length: {len(token)} characters")
    
    try:
        # Log request context
        request_id = get_request_id()
        client_ip = get_client_ip()
        logger.debug(f"Request ID: {request_id}")
        logger.debug(f"Client IP: {client_ip}")
        
        # Verify token with Supabase
        logger.debug("Calling user_manager.verify_user_token()")
        start_time = datetime.utcnow()
        
        user_manager_instance = get_user_manager()
        user = await user_manager_instance.verify_user_token(token)
        
        validation_time = (datetime.utcnow() - start_time).total_seconds()
        logger.debug(f"Token validation completed in {validation_time:.3f} seconds")
        
        if not user:
            logger.warning("Token validation failed - no user returned")
            log_security_event(
                "token_validation_failed",
                {
                    "request_id": request_id,
                    "client_ip": client_ip,
                    "token_prefix": token[:20] if token else "None",
                    "reason": "No user returned from verification"
                },
                severity="WARNING"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        logger.debug(f"Token validation successful for user: {user.get('email', 'Unknown')}")
        logger.debug(f"User ID: {user.get('user_id', 'Unknown')}")
        logger.debug(f"Username: {user.get('username', 'Unknown')}")
        
        # Check if user is active
        is_active = user.get("is_active", True)
        logger.debug(f"User active status: {is_active}")
        
        if not is_active:
            logger.warning(f"User account is inactive: {user.get('email', 'Unknown')}")
            log_security_event(
                "inactive_user_access_attempt",
                {
                    "request_id": request_id,
                    "user_id": user.get("user_id"),
                    "email": user.get("email"),
                    "client_ip": client_ip
                },
                severity="WARNING"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Update last login
        logger.debug("Updating user's last login timestamp")
        user_manager_instance = get_user_manager()
        await user_manager_instance.update_last_login(user["user_id"])
        
        # Log successful authentication
        logger.debug("=== Authentication successful ===")
        log_security_event(
            "user_authentication_success",
            {
                "request_id": request_id,
                "user_id": user["user_id"],
                "email": user.get("email"),
                "username": user.get("username"),
                "client_ip": client_ip,
                "is_admin": user.get("is_admin", False)
            },
            severity="INFO"
        )
        
        return user
        
    except HTTPException:
        logger.debug("HTTPException raised during authentication")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during token validation: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception details: {e}")
        
        # Log security event for unexpected errors
        log_security_event(
            "authentication_error",
            {
                "request_id": get_request_id(),
                "client_ip": get_client_ip(),
                "error": str(e),
                "error_type": type(e).__name__
            },
            severity="ERROR"
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )

# Authentication endpoints
@router.post("/validate", response_model=TokenValidationResponse)
async def validate_token(credentials: HTTPAuthorizationCredentials = Depends(security), req: Request = None):
    """Validate Supabase JWT token and return user information"""
    logger.debug("=== Starting token validation endpoint ===")
    
    request_id = get_request_id()
    client_ip = get_client_ip()
    
    logger.debug(f"Request ID: {request_id}")
    logger.debug(f"Client IP: {client_ip}")
    
    try:
        token = credentials.credentials
        logger.debug(f"Token to validate: {token[:20]}...")
        logger.debug(f"Token length: {len(token)} characters")
        
        logger.debug("Calling user_manager.verify_user_token()")
        start_time = datetime.utcnow()
        
        user_manager_instance = get_user_manager()
        user = await user_manager_instance.verify_user_token(token)
        
        validation_time = (datetime.utcnow() - start_time).total_seconds()
        logger.debug(f"Token validation completed in {validation_time:.3f} seconds")
        
        if not user:
            logger.warning("Token validation failed - returning invalid response")
            log_security_event(
                "token_validation_failed",
                {
                    "request_id": request_id,
                    "client_ip": client_ip,
                    "token_prefix": token[:20] if token else "None",
                    "reason": "No user returned from verification"
                },
                severity="WARNING"
            )
            return TokenValidationResponse(valid=False)
        
        # Check if user is active
        is_active = user.get("is_active", True)
        logger.debug(f"User active status: {is_active}")
        
        if not is_active:
            logger.warning(f"User account is inactive: {user.get('email', 'Unknown')}")
            log_security_event(
                "inactive_user_validation_attempt",
                {
                    "request_id": request_id,
                    "user_id": user.get("user_id"),
                    "email": user.get("email"),
                    "client_ip": client_ip
                },
                severity="WARNING"
            )
            return TokenValidationResponse(valid=False)
        
        # Log token validation
        logger.debug("Token validation successful - logging security event")
        log_security_event(
            "token_validation",
            {
                "user_id": user["user_id"],
                "username": user.get("username"),
                "client_ip": client_ip,
                "valid": True
            },
            severity="INFO"
        )
        
        # Determine scopes based on user role
        scopes = ["read", "write"] if user.get("is_admin") else ["read"]
        logger.debug(f"User scopes: {scopes}")
        
        response = TokenValidationResponse(
            valid=True,
            user_id=user["user_id"],
            expires_at=datetime.utcnow() + timedelta(hours=1),  # Approximate
            scopes=scopes
        )
        
        logger.debug(f"Returning successful validation response for user: {user.get('email', 'Unknown')}")
        logger.debug("=== Token validation endpoint completed ===")
        
        return response
        
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception details: {e}")
        
        log_security_event(
            "token_validation_error",
            {
                "request_id": request_id,
                "client_ip": client_ip,
                "error": str(e),
                "error_type": type(e).__name__
            },
            severity="ERROR"
        )
        
        logger.debug("=== Token validation endpoint failed ===")
        return TokenValidationResponse(valid=False)

@router.post("/signup", response_model=SignupResponse)
async def signup_user(
    signup_data: SignupRequest,
    req: Request = None
):
    """Sign up a new user"""
    logger.debug("=== Starting signup endpoint ===")
    
    request_id = get_request_id()
    client_ip = get_client_ip()
    
    logger.debug(f"Request ID: {request_id}")
    logger.debug(f"Client IP: {client_ip}")
    
    try:
        user_manager_instance = get_user_manager()
        
        # Check if user already exists
        existing_user = await user_manager_instance.get_user_by_email(signup_data.email)
        if existing_user:
            logger.warning(f"User with email {signup_data.email} already exists.")
            log_security_event(
                "user_signup_duplicate_email",
                {
                    "request_id": request_id,
                    "client_ip": client_ip,
                    "email": signup_data.email
                },
                severity="WARNING"
            )
            return SignupResponse(
                success=False,
                message="User with this email already exists.",
                user_exists=True,
                error="email_exists"
            )
        
        # Create new user
        new_user = await user_manager_instance.create_user(
            UserCreate(
                email=signup_data.email,
                password=signup_data.password,
                username=signup_data.username,
                full_name=signup_data.full_name,
                organization=signup_data.organization
            )
        )
        
        # Check if user creation failed due to duplicate user
        if "error" in new_user and new_user.get("user_exists"):
            logger.warning(f"User with email {signup_data.email} already exists.")
            log_security_event(
                "user_signup_duplicate_email",
                {
                    "request_id": request_id,
                    "client_ip": client_ip,
                    "email": signup_data.email
                },
                severity="WARNING"
            )
            return SignupResponse(
                success=False,
                message=new_user.get("message", "User with this email already exists."),
                user_exists=True,
                error=new_user.get("error", "email_exists"),
                email=signup_data.email
            )
        
        # Check if user creation failed for other reasons
        if "error" in new_user:
            logger.error(f"Failed to create user with email: {signup_data.email}, error: {new_user.get('error')}")
            log_security_event(
                "user_signup_failed",
                {
                    "request_id": request_id,
                    "client_ip": client_ip,
                    "email": signup_data.email,
                    "error": new_user.get("error", "Unknown error")
                },
                severity="ERROR"
            )
            return SignupResponse(
                success=False,
                message=new_user.get("message", "Failed to create user"),
                error=new_user.get("error", "creation_failed"),
                email=signup_data.email
            )
        
        # User created successfully
        if "user_id" in new_user:
            logger.info(f"User created successfully with ID: {new_user.get('user_id')}")
            log_security_event(
                "user_signup_success",
                {
                    "request_id": request_id,
                    "client_ip": client_ip,
                    "user_id": new_user.get("user_id"),
                    "email": new_user.get("email")
                },
                severity="INFO"
            )
            
            return SignupResponse(
                success=True,
                message="User created successfully",
                user_id=new_user.get("user_id"),
                email=new_user.get("email")
            )
        else:
            # Unexpected response format
            logger.error(f"Unexpected response format from create_user: {new_user}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unexpected response from user creation service"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception details: {e}")
        
        log_security_event(
            "signup_error",
            {
                "request_id": request_id,
                "client_ip": client_ip,
                "error": str(e),
                "error_type": type(e).__name__
            },
            severity="ERROR"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sign up user"
        )

@router.get("/me", response_model=Dict[str, Any])
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user information"""
    return {
        "user_id": current_user["user_id"],
        "email": current_user["email"],
        "username": current_user.get("username"),
        "full_name": current_user.get("full_name"),
        "organization": current_user.get("organization"),
        "is_admin": current_user.get("is_admin", False),
        "avatar_url": current_user.get("avatar_url"),
        "created_at": current_user["created_at"].isoformat(),
        "last_login": current_user["last_login"].isoformat() if current_user.get("last_login") else None
    }

@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(payload: TokenRefreshRequest):
    """Refresh access token using Supabase refresh token"""
    try:
        user_manager = get_user_manager()
        data = user_manager.refresh_access_token(payload.refresh_token)
        if not data or "access_token" not in data:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        return TokenRefreshResponse(
            access_token=data.get("access_token"),
            refresh_token=data.get("refresh_token"),
            expires_in=data.get("expires_in"),
            token_type=data.get("token_type")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to refresh token")

@router.put("/profile", response_model=Dict[str, Any])
async def update_user_profile(
    profile_data: UserProfileUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update current user profile"""
    try:
        # Convert to UserUpdate model
        update_data = UserUpdate(
            username=profile_data.username,
            full_name=profile_data.full_name,
            organization=profile_data.organization,
            avatar_url=profile_data.avatar_url
        )
        
        # Update profile
        user_manager_instance = get_user_manager()
        updated_profile = await user_manager_instance.update_user_profile(current_user["user_id"], update_data)
        
        if not updated_profile:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile"
            )
        
        return {
            "message": "Profile updated successfully",
            "profile": {
                "user_id": current_user["user_id"],
                "email": current_user["email"],
                "username": updated_profile.get("username"),
                "full_name": updated_profile.get("full_name"),
                "organization": updated_profile.get("organization"),
                "avatar_url": updated_profile.get("avatar_url"),
                "is_admin": current_user.get("is_admin", False)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile update error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/users", response_model=List[Dict[str, Any]])
async def list_users(
    limit: int = 100,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List users (admin only)"""
    # Check if user is admin
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    try:
        user_manager_instance = get_user_manager()
        users = await user_manager_instance.list_users(limit=limit, offset=offset)
        return users
        
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/user/{user_id}", response_model=Dict[str, Any])
async def get_user_by_id(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get user by ID (admin only or own profile)"""
    # Check if user is admin or requesting their own profile
    if not current_user.get("is_admin", False) and current_user["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        user_manager_instance = get_user_manager()
        user = await user_manager_instance.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Health check endpoint
@router.get("/health")
async def auth_health_check():
    """Authentication service health check"""
    try:
        # Test Supabase connection
        user_manager_instance = get_user_manager()
        test_user = await user_manager_instance.get_user_by_id("test")
        supabase_status = "connected"
    except Exception as e:
        supabase_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "service": "authentication",
        "timestamp": datetime.utcnow().isoformat(),
        "supabase_status": supabase_status
    }

# Debug endpoint for JWT analysis (development only)
@router.post("/debug/token-analysis")
async def analyze_token_debug(
    token: str = Body(..., embed=True, description="JWT token to analyze")
):
    """Debug endpoint to analyze JWT token structure (development only)"""
    logger.debug("=== JWT Token Analysis Debug Endpoint ===")
    
    try:
        # Analyze token structure
        user_manager_instance = get_user_manager()
        token_analysis = user_manager_instance._analyze_jwt_token(token)
        
        # Additional analysis
        analysis_result = {
            "token_analysis": token_analysis,
            "token_preview": f"{token[:20]}..." if token else "None",
            "token_length": len(token) if token else 0,
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
        
        # Try to verify with Supabase (without returning user data)
        try:
            logger.debug("Attempting Supabase verification for analysis")
            user_manager_instance = get_user_manager()
            user = await user_manager_instance.verify_user_token(token)
            analysis_result["supabase_verification"] = {
                "success": user is not None,
                "user_found": user is not None,
                "user_active": user.get("is_active", False) if user else False
            }
        except Exception as e:
            analysis_result["supabase_verification"] = {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
        
        logger.debug(f"Token analysis completed: {analysis_result}")
        return analysis_result
        
    except Exception as e:
        logger.error(f"Error in token analysis: {str(e)}")
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "analysis_timestamp": datetime.utcnow().isoformat()
        }

# Specific debug endpoint for expired token issues
@router.post("/debug/expired-token-check")
async def check_expired_token_issue(
    token: str = Body(..., embed=True, description="JWT token to check for expired issue")
):
    """Debug endpoint specifically for expired token issues"""
    logger.debug("=== Expired Token Issue Debug Endpoint ===")
    
    try:
        import jwt
        from datetime import datetime
        
        # Step 1: Decode token without verification to check expiration
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            
            # Check expiration
            exp_timestamp = payload.get("exp")
            iat_timestamp = payload.get("iat")
            current_timestamp = datetime.utcnow().timestamp()
            
            token_info = {
                "exp_timestamp": exp_timestamp,
                "iat_timestamp": iat_timestamp,
                "current_timestamp": current_timestamp,
                "exp_datetime": datetime.fromtimestamp(exp_timestamp) if exp_timestamp else None,
                "iat_datetime": datetime.fromtimestamp(iat_timestamp) if iat_timestamp else None,
                "current_datetime": datetime.utcnow(),
                "is_expired": exp_timestamp and current_timestamp > exp_timestamp,
                "time_until_expiry": exp_timestamp - current_timestamp if exp_timestamp else None,
                "token_age_hours": (current_timestamp - iat_timestamp) / 3600 if iat_timestamp else None
            }
            
        except Exception as e:
            token_info = {
                "error": f"Failed to decode token: {str(e)}",
                "error_type": type(e).__name__
            }
        
        # Step 2: Test Supabase client directly
        supabase_test = {}
        try:
            user_manager_instance = get_user_manager()
            supabase_client = user_manager_instance.client
            
            # Test the auth.get_user method directly
            logger.debug("Testing Supabase auth.get_user() directly")
            user_response = supabase_client.auth.get_user(token)
            
            supabase_test = {
                "success": True,
                "user_response_type": type(user_response).__name__,
                "has_user_attribute": hasattr(user_response, 'user'),
                "user_found": user_response.user is not None if hasattr(user_response, 'user') else False
            }
            
        except Exception as e:
            supabase_test = {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "error_lowercase": str(e).lower(),
                "contains_expired": "expired" in str(e).lower(),
                "contains_invalid": "invalid" in str(e).lower()
            }
        
        # Step 3: Check Supabase configuration
        config_info = {}
        try:
            user_manager_instance = get_user_manager()
            config = user_manager_instance.config
            
            config_info = {
                "supabase_url": config.url,
                "supabase_key_length": len(config.anon_key) if config.anon_key else 0,
                "supabase_key_preview": config.anon_key[:10] + "..." if config.anon_key else None
            }
            
        except Exception as e:
            config_info = {
                "error": f"Failed to get config: {str(e)}"
            }
        
        result = {
            "token_analysis": token_info,
            "supabase_test": supabase_test,
            "config_info": config_info,
            "debug_timestamp": datetime.utcnow().isoformat()
        }
        
        logger.debug(f"Expired token check completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in expired token check: {str(e)}")
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "debug_timestamp": datetime.utcnow().isoformat()
        }

# New debug endpoint for JWKS validation
@router.post("/debug/jwks-validation")
async def test_jwks_validation(
    token: str = Body(..., embed=True, description="JWT token to test with JWKS validation")
):
    """Debug endpoint to test JWT validation with JWKS"""
    logger.debug("=== JWKS Validation Debug Endpoint ===")
    
    try:
        import jwt
        import requests
        from datetime import datetime
        
        # Get user manager to access config
        user_manager_instance = get_user_manager()
        config = user_manager_instance.config
        
        # Step 1: Get JWKS from Supabase
        # Try the standard .well-known endpoint first, fallback to /auth/v1/keys
        jwks_url = f"{config.url}/auth/v1/.well-known/jwks.json"
        logger.debug(f"Fetching JWKS from: {jwks_url}")
        
        jwks_response = requests.get(jwks_url)
        if jwks_response.status_code != 200:
            # Fallback to the older endpoint
            jwks_url = f"{config.url}/auth/v1/keys"
            logger.debug(f"Fallback: Fetching JWKS from: {jwks_url}")
            jwks_response = requests.get(jwks_url)
        jwks_info = {
            "url": jwks_url,
            "status_code": jwks_response.status_code,
            "success": jwks_response.status_code == 200
        }
        
        if jwks_response.status_code == 200:
            jwks = jwks_response.json()
            jwks_info["keys_count"] = len(jwks.get('keys', []))
            jwks_info["keys"] = [{"kid": key.get("kid"), "alg": key.get("alg")} for key in jwks.get('keys', [])]
        else:
            jwks_info["error"] = jwks_response.text
        
        # Step 2: Analyze JWT token
        token_analysis = {}
        try:
            # Decode header without verification
            header = jwt.get_unverified_header(token)
            token_analysis["header"] = header
            token_analysis["kid"] = header.get("kid")
            token_analysis["alg"] = header.get("alg")
            
            # Decode payload without verification
            payload = jwt.decode(token, options={"verify_signature": False})
            token_analysis["payload"] = {
                "sub": payload.get("sub"),
                "exp": payload.get("exp"),
                "iat": payload.get("iat"),
                "iss": payload.get("iss"),
                "aud": payload.get("aud")
            }
            
            # Check expiration
            exp_timestamp = payload.get("exp")
            current_timestamp = datetime.utcnow().timestamp()
            token_analysis["expiration_check"] = {
                "exp_timestamp": exp_timestamp,
                "current_timestamp": current_timestamp,
                "is_expired": exp_timestamp and current_timestamp > exp_timestamp,
                "time_until_expiry": exp_timestamp - current_timestamp if exp_timestamp else None
            }
            
        except Exception as e:
            token_analysis["error"] = str(e)
        
        # Step 3: Test JWKS validation
        validation_test = {}
        if jwks_info["success"] and token_analysis.get("kid"):
            try:
                jwks = jwks_response.json()
                kid = token_analysis["kid"]
                
                # Find matching key
                matching_key = None
                for key in jwks.get('keys', []):
                    if key.get('kid') == kid:
                        matching_key = key
                        break
                
                validation_test["matching_key_found"] = matching_key is not None
                
                if matching_key:
                    # Try to create public key
                    try:
                        # Handle different key types based on algorithm
                        if matching_key.get('kty') == 'EC' and matching_key.get('alg') == 'ES256':
                            # ES256 uses ECDSA with P-256 curve
                            public_key = jwt.algorithms.ECAlgorithm.from_jwk(matching_key)
                            algorithms = ["ES256"]
                            validation_test["key_type"] = "ES256"
                        elif matching_key.get('kty') == 'RSA' and matching_key.get('alg') == 'RS256':
                            # RS256 uses RSA
                            public_key = jwt.algorithms.RSAAlgorithm.from_jwk(matching_key)
                            algorithms = ["RS256"]
                            validation_test["key_type"] = "RS256"
                        else:
                            validation_test["key_type"] = f"Unsupported: {matching_key.get('kty')}-{matching_key.get('alg')}"
                            raise ValueError(f"Unsupported key type: {matching_key.get('kty')} with algorithm: {matching_key.get('alg')}")
                        
                        validation_test["public_key_created"] = True
                        
                        # Try to verify token
                        try:
                            verified_payload = jwt.decode(
                                token, 
                                public_key, 
                                algorithms=algorithms,
                                audience=None,
                                options={
                                    "verify_signature": True,
                                    "verify_exp": True,
                                    "verify_iat": True,
                                    "verify_nbf": False
                                }
                            )
                            validation_test["verification_success"] = True
                            validation_test["verified_user_id"] = verified_payload.get("sub")
                            
                        except Exception as verify_e:
                            validation_test["verification_success"] = False
                            validation_test["verification_error"] = str(verify_e)
                            validation_test["verification_error_type"] = type(verify_e).__name__
                    
                    except Exception as key_e:
                        validation_test["public_key_created"] = False
                        validation_test["key_error"] = str(key_e)
                else:
                    validation_test["matching_key_found"] = False
                    validation_test["available_kids"] = [key.get("kid") for key in jwks.get('keys', [])]
                    
            except Exception as e:
                validation_test["error"] = str(e)
        
        result = {
            "jwks_info": jwks_info,
            "token_analysis": token_analysis,
            "validation_test": validation_test,
            "debug_timestamp": datetime.utcnow().isoformat()
        }
        
        logger.debug(f"JWKS validation test completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in JWKS validation test: {str(e)}")
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "debug_timestamp": datetime.utcnow().isoformat()
        }

# Export authentication dependency for use in other endpoints
__all__ = [
    "get_current_user",
    "TokenValidationResponse",
    "UserProfileUpdateRequest",
    "SignupRequest",
    "SignupResponse"
] 