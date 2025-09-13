"""
Example protected endpoint showing how to use authentication.
This demonstrates how to protect endpoints with JWT authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from pydantic import BaseModel, Field

from endpoints.auth import get_current_user

router = APIRouter(prefix="/protected", tags=["protected-example"])

class ProtectedResponse(BaseModel):
    """Response model for protected endpoint"""
    message: str = Field(..., description="Response message")
    user_info: Dict[str, Any] = Field(..., description="Current user information")
    endpoint_data: Dict[str, Any] = Field(..., description="Endpoint specific data")

@router.get("/example", response_model=ProtectedResponse)
async def protected_example_endpoint(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Example protected endpoint that requires authentication.
    
    This endpoint demonstrates how to:
    1. Require JWT authentication using the get_current_user dependency
    2. Access current user information
    3. Return user-specific data
    """
    
    # Access user information
    user_id = current_user["user_id"]
    username = current_user["username"]
    is_admin = current_user.get("is_admin", False)
    
    # Example of role-based access
    if is_admin:
        endpoint_data = {
            "access_level": "admin",
            "permissions": ["read", "write", "delete", "admin"],
            "sensitive_data": "This is admin-only data"
        }
    else:
        endpoint_data = {
            "access_level": "user",
            "permissions": ["read", "write"],
            "sensitive_data": "This is user data"
        }
    
    return ProtectedResponse(
        message=f"Hello {username}! This is a protected endpoint.",
        user_info={
            "user_id": user_id,
            "username": username,
            "email": current_user.get("email"),
            "is_admin": is_admin,
            "auth_type": current_user.get("auth_type", "unknown")
        },
        endpoint_data=endpoint_data
    )

@router.post("/admin-only", response_model=Dict[str, Any])
async def admin_only_endpoint(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Example endpoint that requires admin privileges.
    
    This demonstrates how to implement role-based access control.
    """
    
    # Check if user is admin
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return {
        "message": "Admin access granted",
        "user_id": current_user["user_id"],
        "username": current_user["username"],
        "admin_actions": [
            "manage_users",
            "view_logs",
            "system_config",
            "security_settings"
        ]
    }

@router.get("/user-profile", response_model=Dict[str, Any])
async def get_user_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Example endpoint that returns user-specific data.
    
    This shows how to use authentication to provide personalized responses.
    """
    
    return {
        "message": "User profile retrieved successfully",
        "profile": {
            "user_id": current_user["user_id"],
            "username": current_user["username"],
            "email": current_user.get("email"),
            "full_name": current_user.get("full_name"),
            "organization": current_user.get("organization"),
            "is_admin": current_user.get("is_admin", False),
            "created_at": current_user.get("created_at"),
            "last_login": current_user.get("last_login")
        },
        "preferences": {
            "theme": "dark",
            "language": "es",
            "notifications": True
        }
    } 