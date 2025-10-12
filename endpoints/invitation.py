#!/usr/bin/env python3
"""
Friend Invitation Endpoint
Handles sending invitation emails to friends using Resend
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
import resend
from dotenv import load_dotenv

# Set up logging first
logger = logging.getLogger(__name__)

# Load environment variables (with error handling)
try:
    load_dotenv()
except Exception as e:
    logger.warning(f"Could not load .env file: {e}")

# Set Resend environment variables if not already set
if not os.getenv("RESEND_API_KEY"):
    os.environ["RESEND_API_KEY"] = "re_YdBnq9ZN_KEnQFxmq3xwaVDfdYhrzugxp"
if not os.getenv("RESEND_FROM_EMAIL"):
    os.environ["RESEND_FROM_EMAIL"] = "noreply@miasistentelegalia.com"
if not os.getenv("RESEND_REPLY_TO_EMAIL"):
    os.environ["RESEND_REPLY_TO_EMAIL"] = "support@miasistentelegalia.com"

# Initialize Resend
resend.api_key = os.getenv("RESEND_API_KEY")

# Create router
router = APIRouter(prefix="/api/friend-invite", tags=["Invitation"])

class InvitationRequest(BaseModel):
    friendName: str
    inviteCode: str
    shareUrl: str
    dailyLimit: int
    trialDays: int
    expiresAt: str
    friendEmail: EmailStr  # Adding email field for the recipient

class InvitationResponse(BaseModel):
    success: bool
    message: str
    email_id: Optional[str] = None

# New models for friend invite validation
class FriendInviteValidationRequest(BaseModel):
    inviteCode: str

class FriendInviteValidationResponse(BaseModel):
    valid: bool
    invite: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# New models for accepting friend invites
class AcceptInviteRequest(BaseModel):
    inviteCode: str
    userId: str

class AcceptInviteResponse(BaseModel):
    success: bool
    error: Optional[str] = None

def sanitize_tag_value(value: str) -> str:
    """
    Sanitize tag values to be ASCII-compliant for Resend API
    """
    import unicodedata
    
    # Normalize unicode characters and convert to ASCII
    normalized = unicodedata.normalize('NFKD', value)
    ascii_value = normalized.encode('ASCII', 'ignore').decode('ASCII')
    
    # Replace spaces and special characters with underscores
    sanitized = ascii_value.replace(' ', '_').replace('-', '_').replace('.', '_')
    
    # Remove any remaining non-alphanumeric characters except underscores
    import re
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '', sanitized)
    
    # Ensure it's not empty and limit length
    if not sanitized:
        sanitized = "value"
    
    return sanitized[:50]  # Limit to 50 characters

def get_email_template(
    friend_name: str,
    invite_code: str,
    share_url: str,
    daily_limit: int,
    trial_days: int,
    expires_at: str
) -> str:
    """
    Generate the HTML email template for the invitation
    """
    return f"""<!DOCTYPE html>
<html lang="es">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Invitación para probar MiAsistenteLegalIA</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 10px 10px 0 0;
        }}

        .content {{
            background: #f9f9f9;
            padding: 30px;
            border-radius: 0 0 10px 10px;
        }}

        .button {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
            margin: 20px 0;
        }}

        .highlight {{
            background: #e8f4fd;
            padding: 20px;
            border-radius: 5px;
            border-left: 4px solid #667eea;
            margin: 20px 0;
        }}

        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #666;
            font-size: 14px;
        }}

        .code {{
            background: #f0f0f0;
            padding: 10px;
            border-radius: 5px;
            font-family: monospace;
            font-size: 16px;
            text-align: center;
            margin: 10px 0;
        }}
    </style>
</head>

<body>
    <div class="header">
        <h1>🤖 MiAsistenteLegalIA</h1>
        <p>Tu asistente legal con Inteligencia Artificial</p>
    </div>

    <div class="content">
        <h2>¡Hola {friend_name}!</h2>

        <p>Has sido invitado a probar <strong>MiAsistenteLegalIA</strong>, una plataforma revolucionaria que utiliza inteligencia artificial para asistirte en asuntos legales.</p>

        <div class="highlight">
            <h3>🎁 ¿Qué incluye tu invitación?</h3>
            <ul>
                <li><strong>{trial_days} días de prueba gratuita</strong></li>
                <li><strong>{daily_limit} consultas diarias</strong> con IA</li>
                <li>Acceso completo a todas las herramientas legales</li>
                <li>Sin compromisos ni tarjetas de crédito</li>
            </ul>
        </div>

        <h3>🔑 Tu código de invitación:</h3>
        <div class="code">{invite_code}</div>

        <h3>📅 Fecha de expiración:</h3>
        <p>Esta invitación expira el <strong>{expires_at}</strong></p>

        <div style="text-align: center;">
            <a href="{share_url}" class="button">🚀 Comenzar Ahora</a>
        </div>

        <h3>✨ ¿Qué puedes hacer con MiAsistenteLegalIA?</h3>
        <ul>
            <li>📄 Generar documentos legales</li>
            <li>🔍 Investigar precedentes legales</li>
            <li>📋 Revisar contratos</li>
            <li>💬 Consultar dudas legales</li>
            <li>📊 Analizar casos legales</li>
        </ul>

        <div class="highlight">
            <p><strong>⚠️ Importante:</strong> Esta es una invitación personal y no debe ser compartida. Cada código es único y solo puede ser usado una vez.</p>
        </div>
    </div>

    <div class="footer">
        <p>Si tienes alguna pregunta, no dudes en contactarnos.</p>
        <p>© 2024 MiAsistenteLegalIA. Todos los derechos reservados.</p>
    </div>
</body>

</html>"""

@router.post("/send", response_model=InvitationResponse)
async def send_invitation(request: InvitationRequest):
    """
    Send an invitation email to a friend
    
    Parameters:
    - friendName: Name of the friend being invited
    - inviteCode: Unique invitation code
    - shareUrl: URL for the friend to access the platform
    - dailyLimit: Number of daily requests allowed
    - trialDays: Number of trial days
    - expiresAt: Expiration date of the invitation
    - friendEmail: Email address of the friend to send the invitation to
    """
    try:
        # Validate Resend API key
        if not resend.api_key:
            logger.error("RESEND_API_KEY not found in environment variables")
            raise HTTPException(
                status_code=500,
                detail="Email service not configured. Please contact support."
            )
        
        # Generate the email template
        html_content = get_email_template(
            friend_name=request.friendName,
            invite_code=request.inviteCode,
            share_url=request.shareUrl,
            daily_limit=request.dailyLimit,
            trial_days=request.trialDays,
            expires_at=request.expiresAt
        )
        
        # Prepare email parameters
        params = {
            "from": os.getenv("RESEND_FROM_EMAIL", "noreply@miasistentelegalia.com"),
            "to": [request.friendEmail],
            "subject": f"🎁 Invitación para probar MiAsistenteLegalIA",
            "html": html_content,
            "reply_to": os.getenv("RESEND_REPLY_TO_EMAIL", "support@miasistentelegalia.com"),
            "tags": [
                {"name": "invitation_type", "value": "friend_invite"},
                {"name": "invite_code", "value": sanitize_tag_value(request.inviteCode)},
                {"name": "trial_days", "value": str(request.trialDays)},
                {"name": "daily_limit", "value": str(request.dailyLimit)}
            ]
        }
        
        # Send the email using Resend
        logger.info(f"Sending invitation email to {request.friendEmail}")
        email_response = resend.Emails.send(params)
        
        # Log successful email sending
        logger.info(f"Invitation email sent successfully. Response: {email_response}")
        
        # Handle different response formats
        email_id = None
        if hasattr(email_response, 'id'):
            email_id = email_response.id
        elif isinstance(email_response, dict) and 'id' in email_response:
            email_id = email_response['id']
        
        return InvitationResponse(
            success=True,
            message=f"Invitation sent successfully to {request.friendEmail}",
            email_id=email_id
        )
        
    except Exception as e:
        if "resend" in str(e).lower() or "email" in str(e).lower():
            logger.error(f"Resend API error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send invitation email: {str(e)}"
            )
        else:
            logger.error(f"Unexpected error sending invitation: {e}")
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred while sending the invitation"
            )

@router.get("/health")
async def health_check():
    """
    Health check endpoint for the invitation service
    """
    try:
        # Check if Resend API key is configured
        if not resend.api_key:
            return {
                "status": "warning",
                "message": "RESEND_API_KEY not configured",
                "service": "invitation"
            }
        
        return {
            "status": "healthy",
            "message": "Invitation service is operational",
            "service": "invitation",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Service error: {str(e)}",
            "service": "invitation",
            "timestamp": datetime.now().isoformat()
        }

async def validate_invite_code_se(invite_code: str) -> Optional[Dict[str, Any]]:
    """
    Validate an invite code against the Supabase database
    """
    try:
        from config.supabase import get_supabase_config
        
        # Get Supabase client
        supabase_config = get_supabase_config()
        client = supabase_config.get_client()
        
        # Query the friend_testing_invites table
        response = client.table('friend_testing_invites').select('*').eq('invite_code', invite_code).eq('status', 'pending').gte('expires_at', datetime.now().isoformat()).execute()
        
        if response.data and len(response.data) > 0:
            invite = response.data[0]
            return {
                'invite_code': invite['invite_code'],
                'friend_email': invite['friend_email'],
                'friend_name': invite['friend_name'],
                'daily_limit': invite['daily_limit'],
                'trial_days': invite['trial_days'],
                'expires_at': invite['expires_at'],
                'status': invite['status']
            }
        
        return None
        
    except ImportError:
        logger.warning("Supabase config not available, using mock validation")
        # Fallback to mock validation if Supabase is not configured
        return validate_invite_code(invite_code)
    except Exception as e:
        logger.error(f"Error validating invite code with Supabase: {e}")
        return None

def validate_invite_code(invite_code: str) -> Optional[Dict[str, Any]]:
    """
    Mock validation function for testing when Supabase is not available
    """
    try:
        # Mock validation logic for testing - matches actual table structure
        if invite_code and len(invite_code) >= 6:
            # Simulate a valid invite with the actual table fields
            return {
                'invite_code': invite_code,
                'friend_email': 'friend@example.com',
                'friend_name': 'Friend Name',
                'daily_limit': 5,  # Default from your table
                'trial_days': 3,   # Default from your table
                'expires_at': '2025-12-31T23:59:59Z',
                'status': 'pending'
            }
        return None
        
    except Exception as e:
        logger.error(f"Error in mock validation: {e}")
        return None

@router.post("/validate", response_model=FriendInviteValidationResponse)
async def validate_friend_invite(request: FriendInviteValidationRequest):
    """
    Validate a friend invite code
    """
    try:
        invite_code = request.inviteCode
        
        if not invite_code:
            return FriendInviteValidationResponse(
                valid=False,
                error="Invite code is required"
            )
        
        # Validate the invite code against your database
        invite = await validate_invite_code_supabase(invite_code)
        
        if invite and invite.get('status') == 'pending':
            return FriendInviteValidationResponse(
                valid=True,
                invite={
                    'invite_code': invite['invite_code'],
                    'friend_email': invite['friend_email'],
                    'friend_name': invite['friend_name'],
                    'daily_limit': invite['daily_limit'],
                    'trial_days': invite['trial_days'],
                    'expires_at': invite['expires_at']
                }
            )
        else:
            return FriendInviteValidationResponse(
                valid=False,
                error="Invalid or expired invite code"
            )
            
    except Exception as e:
        logger.error(f"Error validating friend invite: {e}")
        return FriendInviteValidationResponse(
            valid=False,
            error=str(e)
        )

async def accept_invite_supabase(invite_code: str, user_id: str) -> bool:
    """
    Accept a friend invite in the Supabase database to create a new user
    """
    try:
        from config.supabase import get_supabase_config
        
        # Get Supabase client
        supabase_config = get_supabase_config()
        client = supabase_config.get_client()
        
        # First, check if the invite is still valid
        response = client.table('friend_testing_invites').select('*').eq('invite_code', invite_code).eq('status', 'pending').gte('expires_at', datetime.now().isoformat()).execute()
        
        if not response.data or len(response.data) == 0:
            logger.warning(f"Invite {invite_code} is not valid for acceptance")
            return False
        
        invite = response.data[0]
        
        # Update the invite to accepted status
        update_response = client.table('friend_testing_invites').update({
            'status': 'accepted',
            'accepted_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }).eq('invite_code', invite_code).execute()
        
        # Check if the update was successful
        # Supabase PATCH operations return success even with empty data array
        # We need to check the response status and handle the response properly
        if hasattr(update_response, 'status_code') and update_response.status_code == 200:
            logger.info(f"Successfully accepted invite {invite_code} for user {user_id}")
            return True
        elif hasattr(update_response, 'data'):
            # Some Supabase clients return data even for successful updates
            if update_response.data is not None:  # Allow empty arrays
                logger.info(f"Successfully accepted invite {invite_code} for user {user_id}")
                return True
        
        # If we get here, the update might have failed
        logger.error(f"Failed to update invite {invite_code} status. Response: {update_response}")
        return False
        
    except ImportError:
        logger.warning("Supabase config not available, using mock acceptance")
        # Fallback to mock acceptance if Supabase is not configured
        return accept_invite_mock(invite_code, user_id)
    except Exception as e:
        logger.error(f"Error accepting invite with Supabase: {e}")
        return False

def accept_invite_mock(invite_code: str, user_id: str) -> bool:
    """
    Mock accept function for testing when Supabase is not available
    """
    try:
        # Mock acceptance logic for testing
        if invite_code and user_id and len(invite_code) >= 6:
            logger.info(f"Mock: Accepted invite {invite_code} for user {user_id}")
            return True
        return False
        
    except Exception as e:
        logger.error(f"Error in mock acceptance: {e}")
        return False

@router.post("/accept", response_model=AcceptInviteResponse)
async def accept_friend_invite(request: AcceptInviteRequest):
    """
    Accept a friend invite
    """
    try:
        invite_code = request.inviteCode
        user_id = request.userId
        
        if not invite_code:
            return AcceptInviteResponse(
                success=False,
                error="Invite code is required"
            )
        
        if not user_id:
            return AcceptInviteResponse(
                success=False,
                error="User ID is required"
            )
        
        # Accept the invite
        success = await accept_invite_supabase(invite_code, user_id)
        
        if success:
            return AcceptInviteResponse(
                success=True
            )
        else:
            return AcceptInviteResponse(
                success=False,
                error="Failed to accept invite. The invite may be invalid, expired, or already accepted."
            )
            
    except Exception as e:
        logger.error(f"Error accepting friend invite: {e}")
        return AcceptInviteResponse(
            success=False,
            error=str(e)
        )
