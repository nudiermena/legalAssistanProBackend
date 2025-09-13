"""
Supabase configuration and client setup for the Legal AI Assistant API.
Handles database connection, authentication, and user management.
"""

import os
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
from supabase import create_client, Client
from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)

class SupabaseConfig:
    """Supabase configuration"""
    
    def __init__(self):
        self.url: Optional[str] = None
        self.anon_key: Optional[str] = None
        self.service_role_key: Optional[str] = None
        self.client: Optional[Client] = None
        self.admin_client: Optional[Client] = None
        self._initialized = False
    
    def _initialize(self):
        """Initialize configuration and clients"""
        if self._initialized:
            return
            
        # Load environment variables
        self.url = os.getenv("SUPABASE_URL")
        self.anon_key = os.getenv("SUPABASE_ANON_KEY")
        self.service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
        
        # Add logging for key presence and length
        if self.url:
            logger.debug(f"Supabase URL loaded: {self.url}")
        else:
            logger.error("Supabase URL is not set in environment variables (SUPABASE_URL)")
        
        if self.anon_key:
            logger.debug(f"Supabase Key loaded. Length: {len(self.anon_key)} characters.")
        else:
            logger.error("Supabase Key is not set in environment variables (SUPABASE_ANON_KEY)")
        
        if not self.url:
            logger.error("SUPABASE_URL environment variable is not set")
            raise ValueError("SUPABASE_URL must be set")
        
        if not self.anon_key:
            logger.error("SUPABASE_ANON_KEY environment variable is not set")
            raise ValueError("SUPABASE_ANON_KEY must be set")
        
        try:
            logger.debug(f"Initializing Supabase client with URL: {self.url}")
            # Public client (for frontend-like operations)
            self.client = create_client(self.url, self.anon_key)
            
            # Admin client (for backend operations with service role)
            if self.service_role_key:
                logger.debug("Initializing Supabase admin client")
                self.admin_client = create_client(self.url, self.service_role_key)
            
            self._initialized = True
            logger.info("Supabase clients initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase clients: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Supabase URL: {self.url}")
            logger.error(f"Anon Key length: {len(self.anon_key) if self.anon_key else 0}")
            raise
    
    def get_client(self) -> Client:
        """Get the public Supabase client"""
        if not self._initialized:
            self._initialize()
        return self.client
    
    def get_admin_client(self) -> Client:
        """Get the admin Supabase client"""
        if not self._initialized:
            self._initialize()
        if not self.admin_client:
            if not self.service_role_key:
                raise ValueError("SUPABASE_SERVICE_ROLE_KEY not configured")
        return self.admin_client

# Pydantic models for user data
class UserProfile(BaseModel):
    """User profile model"""
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    username: Optional[str] = Field(None, description="Username")
    full_name: Optional[str] = Field(None, description="Full name")
    organization: Optional[str] = Field(None, description="Organization")
    is_admin: bool = Field(default=False, description="Admin privileges")
    is_active: bool = Field(default=True, description="Account status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Account creation date")
    last_login: Optional[datetime] = Field(None, description="Last login date")
    avatar_url: Optional[str] = Field(None, description="Profile picture URL")
    
    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    """User creation model"""
    email: str = Field(..., description="User email")
    password: str = Field(..., min_length=6, description="User password")
    username: Optional[str] = Field(None, description="Username")
    full_name: Optional[str] = Field(None, description="Full name")
    organization: Optional[str] = Field(None, description="Organization")

class UserUpdate(BaseModel):
    """User update model"""
    username: Optional[str] = Field(None, description="Username")
    full_name: Optional[str] = Field(None, description="Full name")
    organization: Optional[str] = Field(None, description="Organization")
    avatar_url: Optional[str] = Field(None, description="Profile picture URL")

# Supabase user management class
class SupabaseUserManager:
    """Manages user operations with Supabase"""
    
    def __init__(self):
        self.config = SupabaseConfig()
        self._client: Optional[Client] = None
        self._admin_client: Optional[Client] = None
    
    @property
    def client(self) -> Client:
        """Get the public Supabase client"""
        if not self._client:
            self._client = self.config.get_client()
        return self._client
    
    @property
    def admin_client(self) -> Client:
        """Get the admin Supabase client"""
        if not self._admin_client:
            self._admin_client = self.config.get_admin_client()
        return self._admin_client
    
    async def create_user(self, user_data: UserCreate) -> Dict[str, Any]:
        """Create a new user in Supabase"""
        try:
            # First check if user already exists
            try:
                # Check if user exists in auth.users
                existing_user = self.client.auth.admin.list_users()
                for user in existing_user.users:
                    if user.email == user_data.email:
                        logger.info(f"User already exists with email: {user_data.email}")
                        return {
                            "error": "User already exists",
                            "message": "An account with this email address already exists. Please try logging in instead.",
                            "user_exists": True,
                            "email": user_data.email
                        }
            except Exception as check_error:
                logger.debug(f"Could not check existing users: {check_error}")
                # Continue with creation attempt
            
            # Create user in Supabase Auth
            auth_response = self.client.auth.sign_up({
                "email": user_data.email,
                "password": user_data.password,
                "options": {
                    "data": {
                        "username": user_data.username,
                        "full_name": user_data.full_name,
                        "organization": user_data.organization,
                        "is_admin": False,
                        "is_active": True
                    }
                }
            })
            
            if auth_response.user:
                # Create profile in profiles table
                profile_data = {
                    "id": auth_response.user.id,
                    "email": user_data.email,
                    "username": user_data.username,
                    "full_name": user_data.full_name,
                    "organization": user_data.organization,
                    "is_admin": False,
                    "is_active": True,
                    "created_at": datetime.utcnow().isoformat()
                }
                
                try:
                    profile_response = self.client.table("profiles").insert(profile_data).execute()
                except Exception as profile_error:
                    # If profile creation fails due to duplicate, handle gracefully
                    if "duplicate key value violates unique constraint" in str(profile_error).lower():
                        logger.info(f"Profile already exists for user: {user_data.email}")
                        return {
                            "error": "Profile already exists",
                            "message": "An account with this email address already exists. Please try logging in instead.",
                            "user_exists": True,
                            "email": user_data.email
                        }
                    else:
                        # Re-raise if it's a different error
                        raise profile_error
                
                logger.info(f"User created successfully: {user_data.email}")
                return {
                    "user_id": auth_response.user.id,
                    "email": user_data.email,
                    "username": user_data.username,
                    "full_name": user_data.full_name,
                    "organization": user_data.organization,
                    "is_admin": False,
                    "is_active": True,
                    "created_at": datetime.utcnow()
                }
            else:
                raise Exception("Failed to create user")
                
        except Exception as e:
            error_str = str(e).lower()
            
            # Handle specific Supabase duplicate user errors
            if any(keyword in error_str for keyword in [
                "duplicate key value violates unique constraint",
                "user already registered",
                "already exists",
                "unique constraint",
                "23505"  # PostgreSQL duplicate key error code
            ]):
                logger.info(f"User already exists: {user_data.email}")
                return {
                    "error": "User already exists",
                    "message": "An account with this email address already exists. Please try logging in instead.",
                    "user_exists": True,
                    "email": user_data.email
                }
            
            # Handle other specific Supabase errors
            elif "invalid email" in error_str:
                logger.warning(f"Invalid email format: {user_data.email}")
                return {
                    "error": "Invalid email",
                    "message": "Please provide a valid email address.",
                    "user_exists": False,
                    "email": user_data.email
                }
            elif "password" in error_str and ("weak" in error_str or "short" in error_str):
                logger.warning(f"Password too weak for user: {user_data.email}")
                return {
                    "error": "Weak password",
                    "message": "Password must be at least 6 characters long and contain a mix of letters, numbers, and symbols.",
                    "user_exists": False,
                    "email": user_data.email
                }
            else:
                # Log and re-raise unexpected errors
                logger.error(f"Error creating user: {e}")
                raise
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID - use profiles table as primary source"""
        logger.debug(f"Fetching user profile for ID: {user_id}")
        
        try:
            # Use admin client to bypass user JWT requirements and avoid RLS failures on expired tokens
            logger.debug("Querying profiles table for user data using admin client (service role) when available")
            try:
                client_for_query = self.admin_client if self.config.service_role_key else self.client
            except Exception:
                client_for_query = self.client

            response = client_for_query.table("profiles").select("*").eq("id", user_id).execute()
            
            if response.data:
                user_data = response.data[0]
                logger.debug(f"User data found in profiles: {user_data.get('email', 'Unknown')}")
                
                return {
                    "user_id": user_data["id"],
                    "email": user_data["email"],
                    "username": None,  # profiles doesn't have username column
                    "full_name": user_data.get("full_name"),
                    "organization": user_data.get("company"),  # profiles has 'company' instead of 'organization'
                    "is_admin": False,  # profiles doesn't have is_admin
                    "is_active": True,  # profiles doesn't have is_active
                    "created_at": datetime.fromisoformat(user_data["created_at"]) if user_data.get("created_at") else datetime.utcnow(),
                    "last_login": datetime.fromisoformat(user_data["last_login"]) if user_data.get("last_login") else None,
                    "avatar_url": user_data.get("avatar_url")
                }
            
            # If not found in profiles, try auth.users as fallback
            logger.debug("User not found in profiles, checking auth.users table")
            try:
                from sqlalchemy import create_engine, text
                from config.settings import POSTGRES_URL
                
                engine = create_engine(POSTGRES_URL)
                with engine.connect() as conn:
                    result = conn.execute(text("""
                        SELECT id, email, is_super_admin, deleted_at, created_at, last_sign_in_at
                        FROM auth.users 
                        WHERE id = :user_id
                    """), {"user_id": user_id})
                    
                    user_data = result.fetchone()
                    if user_data:
                        logger.debug(f"User data found in auth.users: {user_data[1]}")
                        
                        return {
                            "user_id": user_data[0],
                            "email": user_data[1],
                            "username": None,
                            "full_name": None,
                            "organization": None,
                            "is_admin": user_data[2] if user_data[2] else False,
                            "is_active": user_data[3] is None,  # Not deleted
                            "created_at": user_data[4] if user_data[4] else datetime.utcnow(),
                            "last_login": user_data[5] if user_data[5] else None,
                            "avatar_url": None
                        }
                        
            except Exception as db_error:
                logger.debug(f"Database query failed: {db_error}")
            
            logger.debug(f"User not found with ID: {user_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email - check both profiles and auth.users tables"""
        logger.debug(f"Fetching user profile for email: {email}")
        
        try:
            # First check profiles table
            try:
                client_for_query = self.admin_client if self.config.service_role_key else self.client
            except Exception:
                client_for_query = self.client

            response = client_for_query.table("profiles").select("*").eq("email", email).execute()
            
            if response.data:
                user_data = response.data[0]
                logger.debug(f"User data found in profiles: {user_data.get('email', 'Unknown')}")
                
                return {
                    "user_id": user_data["id"],
                    "email": user_data["email"],
                    "username": None,  # profiles doesn't have username column
                    "full_name": user_data.get("full_name"),
                    "organization": user_data.get("company"),  # profiles has 'company' instead of 'organization'
                    "is_admin": False,  # profiles doesn't have is_admin
                    "is_active": True,  # profiles doesn't have is_active
                    "created_at": datetime.fromisoformat(user_data["created_at"]) if user_data.get("created_at") else datetime.utcnow(),
                    "last_login": datetime.fromisoformat(user_data["last_login"]) if user_data.get("last_login") else None,
                    "avatar_url": user_data.get("avatar_url")
                }
            
            # If not found in profiles, try auth.users as fallback
            logger.debug("User not found in profiles, checking auth.users table")
            try:
                from sqlalchemy import create_engine, text
                from config.settings import POSTGRES_URL
                
                engine = create_engine(POSTGRES_URL)
                with engine.connect() as conn:
                    result = conn.execute(text("""
                        SELECT id, email, is_super_admin, deleted_at, created_at, last_sign_in_at
                        FROM auth.users 
                        WHERE email = :email
                    """), {"email": email})
                    
                    user_data = result.fetchone()
                    if user_data:
                        logger.debug(f"User data found in auth.users: {user_data[1]}")
                        
                        return {
                            "user_id": user_data[0],
                            "email": user_data[1],
                            "username": None,
                            "full_name": None,
                            "organization": None,
                            "is_admin": user_data[2] if user_data[2] else False,
                            "is_active": user_data[3] is None,  # Not deleted
                            "created_at": user_data[4] if user_data[4] else datetime.utcnow(),
                            "last_login": user_data[5] if user_data[5] else None,
                            "avatar_url": None
                        }
                        
            except Exception as db_error:
                logger.debug(f"Database query failed: {db_error}")
            
            logger.debug(f"User not found with email: {email}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    async def update_user_profile(self, user_id: str, profile_data: UserUpdate) -> Optional[Dict[str, Any]]:
        """Update user profile"""
        try:
            update_data = profile_data.dict(exclude_unset=True)
            
            response = self.client.table("profiles").update(update_data).eq("id", user_id).execute()
            
            if response.data:
                return response.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            return None
    
    async def update_last_login(self, user_id: str) -> bool:
        """Update user's last login timestamp"""
        logger.debug(f"Updating last login timestamp for user: {user_id}")
        
        try:
            current_time = datetime.utcnow().isoformat()
            logger.debug(f"Setting last_login to: {current_time}")
            
            self.client.table("profiles").update({
                "last_login": current_time
            }).eq("id", user_id).execute()
            
            logger.debug(f"Successfully updated last_login for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating last login for user {user_id}: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            return False
    
    async def verify_user_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return user info"""
        logger.debug(f"Starting JWT token verification for token: {token[:20]}...")
        
        try:
            # Log token characteristics
            logger.debug(f"Token length: {len(token)} characters")
            logger.debug(f"Token format check: {'Bearer ' in token}")
            
            # Analyze JWT token structure
            token_analysis = self._analyze_jwt_token(token)
            logger.debug(f"JWT token analysis: {token_analysis}")
            
            # Check if token looks like a JWT
            if not token or len(token.split('.')) != 3:
                logger.warning(f"Invalid JWT format detected. Token parts: {len(token.split('.')) if token else 0}")
                return None
            
            logger.debug("JWT format appears valid, proceeding with Supabase verification")
            
            # Verify token with Supabase
            logger.debug("Calling Supabase auth.get_user() for token verification")
            start_time = datetime.utcnow()

            user = None
            supabase_client_error = None # Initialize to None
            try:
                user = self.client.auth.get_user(token)
            except Exception as e: # Catch all exceptions from Supabase client's get_user
                supabase_client_error = e # Store the exception
                logger.error(f"Supabase client auth.get_user() failed: {str(e)}")

            verification_time = (datetime.utcnow() - start_time).total_seconds()
            logger.debug(f"Supabase verification completed in {verification_time:.3f} seconds")
            
            # If user successfully verified by Supabase client
            if user and hasattr(user, 'user') and user.user:
                logger.debug(f"Supabase client verification successful for user: {user.user.id}")
                # Do not set global Authorization header on the public client to avoid stale/expired tokens affecting other calls.
                # For queries that need elevated access, use admin client in specific calls.
                logger.debug("Skipping setting global Authorization header on the public client.")

                # Get additional profile data and return
                profile = await self.get_user_by_id(user.user.id)
                if profile:
                    logger.debug("User profile successfully fetched after Supabase client verification.")
                    return profile
                else:
                    logger.warning(f"No profile data found for user ID: {user.user.id} after Supabase client verification.")
                    return None
            else:
                # Supabase client either returned None, or user.user is None, or it raised an exception
                logger.warning("Supabase auth.get_user() returned no user or failed. Attempting proper JWT verification with JWKS.")
                
                # --- Fallback to proper JWT verification using JWKS --- 
                try:
                    import jwt
                    import requests
                    from jwt.exceptions import InvalidSignatureError, ExpiredSignatureError, DecodeError

                    logger.debug("Attempting JWT verification with Supabase JWKS.")
                    
                    # Get the JWKS from Supabase
                    # Try the standard .well-known endpoint first, fallback to /auth/v1/keys
                    jwks_url = f"{self.config.url}/auth/v1/.well-known/jwks.json"
                    logger.debug(f"Fetching JWKS from: {jwks_url}")
                    
                    jwks_response = requests.get(jwks_url)
                    if jwks_response.status_code != 200:
                        # Fallback to the older endpoint
                        jwks_url = f"{self.config.url}/auth/v1/keys"
                        logger.debug(f"Fallback: Fetching JWKS from: {jwks_url}")
                        jwks_response = requests.get(jwks_url)
                        if jwks_response.status_code != 200:
                            logger.error(f"Failed to fetch JWKS from both endpoints")
                            raise ValueError("Failed to fetch JWKS from Supabase")
                    
                    if jwks_response.status_code != 200:
                        logger.error(f"Failed to fetch JWKS: {jwks_response.status_code} - {jwks_response.text}")
                        raise ValueError("Failed to fetch JWKS from Supabase")
                    
                    jwks = jwks_response.json()
                    logger.debug(f"JWKS fetched successfully with {len(jwks.get('keys', []))} keys")
                    
                    # Get the unverified header to find the key ID
                    unverified_header = jwt.get_unverified_header(token)
                    kid = unverified_header.get('kid')
                    
                    if not kid:
                        logger.error("No 'kid' (Key ID) found in JWT header")
                        raise ValueError("Invalid JWT header: missing 'kid'")
                    
                    logger.debug(f"JWT Key ID (kid): {kid}")
                    
                    # Find the matching public key
                    public_key = None
                    for key in jwks.get('keys', []):
                        if key.get('kid') == kid:
                            try:
                                # Handle different key types based on algorithm
                                if key.get('kty') == 'EC' and key.get('alg') == 'ES256':
                                    # ES256 uses ECDSA with P-256 curve
                                    public_key = jwt.algorithms.ECAlgorithm.from_jwk(key)
                                    logger.debug(f"Found matching ES256 public key for kid: {kid}")
                                elif key.get('kty') == 'RSA' and key.get('alg') == 'RS256':
                                    # RS256 uses RSA
                                    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
                                    logger.debug(f"Found matching RS256 public key for kid: {kid}")
                                else:
                                    logger.warning(f"Unsupported key type: {key.get('kty')} with algorithm: {key.get('alg')}")
                                    continue
                                break
                            except Exception as key_error:
                                logger.warning(f"Failed to create public key from JWK: {key_error}")
                                continue
                    
                    if not public_key:
                        logger.error(f"No matching public key found for kid: {kid}")
                        raise ValueError("Public key not found for JWT")
                    
                    # Decode and verify the token
                    # Determine algorithm based on key type
                    if isinstance(public_key, jwt.algorithms.ECAlgorithm):
                        algorithms = ["ES256"]
                        logger.debug("Using ES256 algorithm for JWT verification")
                    elif isinstance(public_key, jwt.algorithms.RSAAlgorithm):
                        algorithms = ["RS256"]
                        logger.debug("Using RS256 algorithm for JWT verification")
                    else:
                        raise ValueError(f"Unsupported public key type: {type(public_key)}")
                    
                    payload = jwt.decode(
                        token, 
                        public_key, 
                        algorithms=algorithms,
                        audience=None,  # Supabase doesn't use audience validation
                        options={
                            "verify_signature": True,
                            "verify_exp": True,
                            "verify_iat": True,
                            "verify_nbf": False  # Supabase doesn't use 'not before'
                        }
                    )
                    
                    logger.debug(f"JWT verification successful for user ID: {payload.get('sub')}")
                    
                    # If verification succeeds, fetch the full profile from the DB for consistency
                    user_id_from_payload = payload.get("sub")
                    if user_id_from_payload:
                        logger.debug(f"Attempting to fetch user profile for {user_id_from_payload} after JWT verification.")
                        profile = await self.get_user_by_id(user_id_from_payload)
                        if profile:
                            logger.debug("User profile successfully fetched after JWT verification.")
                            return profile
                        else:
                            logger.warning(f"User profile not found in DB for ID {user_id_from_payload} after JWT verification.")
                            return None # User not found in DB even if token is valid
                    else:
                        logger.warning("JWT payload 'sub' (user ID) not found.")
                        return None # Invalid token payload

                except (InvalidSignatureError, ExpiredSignatureError) as jwt_e:
                    logger.error(f"JWT verification failed (signature/expiry): {jwt_e}")
                    if "expired" in str(jwt_e).lower():
                        raise ValueError("Token is expired") from jwt_e
                    else:
                        raise ValueError("Invalid JWT signature") from jwt_e
                except DecodeError as decode_e:
                    logger.error(f"JWT decoding failed: {decode_e}")
                    raise ValueError("Malformed JWT token") from decode_e
                except requests.RequestException as req_e:
                    logger.error(f"Failed to fetch JWKS: {req_e}")
                    raise ValueError("Failed to fetch JWT verification keys") from req_e
                except Exception as other_e:
                    logger.error(f"Unexpected error during JWT verification: {other_e}")
                    raise ValueError("Internal authentication error during JWT verification") from other_e

        except ValueError: # Catch explicit ValueErrors raised within this method
            raise # Re-raise them to be caught by get_current_user's outer exception handler
        except Exception as e: # Catch any other unexpected errors in this outermost try block
            logger.error(f"Overall error verifying token: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Exception details: {e}")
            return None # Indicate verification failed

    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh access token using Supabase GoTrue endpoint.

        Returns a dict with keys: access_token, refresh_token, expires_in, token_type, user (if provided)
        or None on failure.
        """
        try:
            if not self.config.url or not self.config.anon_key:
                raise ValueError("Supabase URL or ANON key not configured")

            refresh_url = f"{self.config.url}/auth/v1/token?grant_type=refresh_token"
            headers = {
                "apikey": self.config.anon_key,
                "Content-Type": "application/json",
            }
            payload = {"refresh_token": refresh_token}

            logger.debug("Calling Supabase refresh token endpoint")
            response = requests.post(refresh_url, json=payload, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                # Optionally set Authorization header for subsequent client calls
                if "access_token" in data:
                    try:
                        self.client.options.headers.update({"Authorization": f"Bearer {data['access_token']}"})
                    except Exception:
                        pass
                logger.info("Supabase token refresh successful")
                return data
            else:
                logger.warning(f"Supabase token refresh failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error refreshing access token: {e}")
            return None
    
    def _analyze_jwt_token(self, token: str) -> Dict[str, Any]:
        """Analyze JWT token structure for debugging purposes"""
        try:
            import jwt
            from jwt.exceptions import DecodeError
            
            analysis = {
                "token_length": len(token),
                "parts_count": len(token.split('.')),
                "is_valid_format": len(token.split('.')) == 3,
                "header": None,
                "payload": None,
                "signature_length": 0,
                "expiration": None,
                "issuer": None,
                "subject": None,
                "audience": None,
                "issued_at": None,
                "not_before": None
            }
            
            if analysis["is_valid_format"]:
                parts = token.split('.')
                analysis["signature_length"] = len(parts[2]) if len(parts) > 2 else 0
                
                try:
                    # Decode header and payload without verification
                    header = jwt.get_unverified_header(token)
                    payload = jwt.decode(token, options={"verify_signature": False})
                    
                    analysis["header"] = header
                    analysis["payload"] = payload
                    
                    # Extract common JWT claims
                    if "exp" in payload:
                        analysis["expiration"] = payload["exp"]
                    if "iss" in payload:
                        analysis["issuer"] = payload["iss"]
                    if "sub" in payload:
                        analysis["subject"] = payload["sub"]
                    if "aud" in payload:
                        analysis["audience"] = payload["aud"]
                    if "iat" in payload:
                        analysis["issued_at"] = payload["iat"]
                    if "nbf" in payload:
                        analysis["not_before"] = payload["nbf"]
                        
                except DecodeError as e:
                    analysis["decode_error"] = str(e)
                    
            return analysis
            
        except Exception as e:
            return {
                "error": f"Failed to analyze token: {str(e)}",
                "token_length": len(token) if token else 0
            }
    
    async def list_users(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List users (admin only)"""
        try:
            response = self.client.table("profiles").select("*").range(offset, offset + limit - 1).execute()
            
            users = []
            for user_data in response.data:
                users.append({
                    "user_id": user_data["id"],
                    "email": user_data["email"],
                    "username": user_data.get("username"),
                    "full_name": user_data.get("full_name"),
                    "organization": user_data.get("organization"),
                    "is_admin": user_data.get("is_admin", False),
                    "is_active": user_data.get("is_active", True),
                    "created_at": datetime.fromisoformat(user_data["created_at"]),
                    "last_login": datetime.fromisoformat(user_data["last_login"]) if user_data.get("last_login") else None
                })
            
            return users
            
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return []

# Initialize global instances (lazy initialization)
supabase_config: Optional[SupabaseConfig] = None
user_manager: Optional[SupabaseUserManager] = None

def get_supabase_config() -> SupabaseConfig:
    """Get or create Supabase configuration instance"""
    global supabase_config
    if supabase_config is None:
        supabase_config = SupabaseConfig()
    return supabase_config

def get_user_manager() -> SupabaseUserManager:
    """Get or create user manager instance"""
    global user_manager
    if user_manager is None:
        user_manager = SupabaseUserManager()
    return user_manager

# Export for use in other modules
__all__ = [
    "SupabaseConfig",
    "SupabaseUserManager",
    "UserProfile",
    "UserCreate", 
    "UserUpdate",
    "get_supabase_config",
    "get_user_manager"
] 