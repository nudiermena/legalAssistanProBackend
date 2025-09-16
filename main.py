from fastapi import FastAPI, HTTPException, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
from datetime import datetime
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse

# Import force Mistral embedder first to patch agno framework - temporarily disabled
try:
    # from config.force_mistral_embedder import force_mistral_embedder
    print("✅ Force Mistral embedder module loaded in main.py")
except Exception as e:
    print(f"⚠️  Could not load force Mistral embedder module in main.py: {e}")

# Import embedder configuration to ensure it's configured
try:
    from config.agno_embedder_config import configure_agno_embedder
    print("✅ Agno embedder configuration loaded in main.py")
except ImportError as e:
    print(f"⚠️  Could not load agno embedder configuration in main.py: {e}")

from endpoints import (
    contract_review,
    legal_research,
    regulatory_analysis,
    legal_chat,
    patent_search,
    document_drafting,
    whistleblower_analysis,
    demand_letter,
    legal_diagnosis,
    case_prediction,
    dashboard,
    autorag_chat,
    invitation
)
from endpoints.document_drafting import router as document_router
from endpoints.legal_research import router as legal_research_router
from endpoints.autorag_chat import router as autorag_router
from endpoints.security_dashboard import router as security_router
from endpoints.auth import router as auth_router
from endpoints.example_protected_endpoint import router as protected_router
from endpoints.invitation import router as invitation_router
import os
import logging
from dotenv import load_dotenv
from config.security import SECURITY_CONFIG, SecurityLevel
from middleware.security import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    AuthenticationMiddleware,
    RequestLoggingMiddleware,
    InputValidationMiddleware
)
from utils.security_validators import log_security_event
from utils.security_monitor import security_monitor
from config.supabase import get_user_manager

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables (with error handling)
try:
    load_dotenv()
except Exception as e:
    logger.warning(f"Could not load .env file: {e}")

app = FastAPI(
    title="Legal AI Assistant API",
    description="""
    A comprehensive API for legal assistance, providing various tools for contract review,
    legal research, regulatory analysis, and more. Each endpoint is specialized for
    specific legal tasks and includes appropriate disclaimers and compliance checks.
    
    **Security Features:**
    - Rate limiting to prevent abuse
    - API key authentication
    - Input validation and sanitization
    - Security headers for protection
    - Request logging and monitoring
    - Real-time security dashboard
    """,
    version="1.0.0",
    docs_url="/docs" if SECURITY_CONFIG.environment != SecurityLevel.PRODUCTION else None,
    redoc_url="/redoc" if SECURITY_CONFIG.environment != SecurityLevel.PRODUCTION else None
)

# Get the base directory
BASE_DIR = Path(__file__).resolve().parent

# Log the directories for debugging
logger.debug(f"Base directory: {BASE_DIR}")
logger.debug(f"Static directory: {BASE_DIR / 'static'}")

# Removed Jinja2Templates setup (no server-side HTML rendering)

# Mount static files - make sure the directories exist
app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static"
)

# Create the necessary directories if they don't exist
static_dir = BASE_DIR / "static"
css_dir = static_dir / "css"
css_dir.mkdir(parents=True, exist_ok=True)

# Add security middleware in order of execution
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(InputValidationMiddleware)
app.add_middleware(AuthenticationMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# Add CORS middleware with security configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=SECURITY_CONFIG.cors_origins,
    allow_credentials=True,
    allow_methods=SECURITY_CONFIG.cors_methods,
    allow_headers=SECURITY_CONFIG.cors_headers,
)

class BaseResponse(BaseModel):
    status: str
    timestamp: datetime
    data: Dict[str, Any]

async def format_response(data: Dict[str, Any]) -> BaseResponse:
    return BaseResponse(
        status="success",
        timestamp=datetime.now(),
        data=data
    )

async def handle_error(e: Exception) -> Dict[str, Any]:
    # Log security event for errors
    log_security_event(
        "api_error",
        {
            "error_type": type(e).__name__,
            "error_message": str(e)
        },
        severity="ERROR"
    )
    
    return {
        "status": "error",
        "timestamp": datetime.now(),
        "error": str(e) if SECURITY_CONFIG.environment == SecurityLevel.DEVELOPMENT else "Internal server error"
    }

# Register exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    # Log security event for HTTP exceptions
    log_security_event(
        "http_exception",
        {
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": str(request.url)
        },
        severity="WARNING"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Include routers
app.include_router(contract_review.router)
app.include_router(legal_research_router)
app.include_router(regulatory_analysis.router)
app.include_router(legal_chat.router)
app.include_router(patent_search.router)
app.include_router(document_router)
app.include_router(whistleblower_analysis.router)
app.include_router(demand_letter.router)
app.include_router(legal_diagnosis.router)
app.include_router(case_prediction.router)
app.include_router(dashboard.router)
app.include_router(autorag_router)
app.include_router(security_router)
app.include_router(auth_router)
app.include_router(protected_router)
app.include_router(invitation_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": SECURITY_CONFIG.environment.value
    }

# Security status endpoint
@app.get("/security/status")
async def security_status():
    """Security status endpoint for monitoring"""
    return {
        "security_level": SECURITY_CONFIG.environment.value,
        "rate_limiting_enabled": True,
        "authentication_enabled": True,
        "security_headers_enabled": SECURITY_CONFIG.enable_security_headers,
        "cors_enabled": SECURITY_CONFIG.enable_cors,
        "file_upload_scanning": SECURITY_CONFIG.scan_uploads,
        "max_file_size": SECURITY_CONFIG.max_file_size,
        "rate_limits": {
            "per_minute": SECURITY_CONFIG.rate_limit.requests_per_minute,
            "per_hour": SECURITY_CONFIG.rate_limit.requests_per_hour,
            "per_day": SECURITY_CONFIG.rate_limit.requests_per_day
        }
    }

# Root route for Vercel
@app.get("/")
async def root():
    return {
        "message": "Welcome to Legal AI Assistant API",
        "version": "1.0.0",
        "security": "enabled",
        "docs": "/docs" if SECURITY_CONFIG.environment != SecurityLevel.PRODUCTION else None,
        "security_dashboard": "/security/dashboard"
    }

# Error handling for 404
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    logger.error(f"404 error for path: {request.url.path}")
    
    # Log security event for 404 errors
    log_security_event(
        "not_found",
        {
            "path": str(request.url.path),
            "method": request.method,
            "user_agent": request.headers.get("User-Agent", "")
        },
        severity="INFO"
    )
    
    return JSONResponse(
        status_code=404,
        content={"detail": {"message": f"Endpoint not found: {request.url.path}"}}
    )

@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    logger.error(f"500 error for path: {request.url.path}, error: {exc}")
    
    # Log security event for 500 errors
    log_security_event(
        "server_error",
        {
            "path": str(request.url.path),
            "method": request.method,
            "error": str(exc)
        },
        severity="ERROR"
    )
    
    return JSONResponse(
        status_code=500,
        content={"detail": {"message": "Internal server error"}}
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("Starting Legal AI Assistant API with security features")
    logger.info(f"Security level: {SECURITY_CONFIG.environment.value}")
    logger.info(f"Rate limiting: {SECURITY_CONFIG.rate_limit.requests_per_minute} requests/minute")

    # Ensure user_manager is initialized at startup
    get_user_manager()
    logger.info("Supabase User Manager initialized during startup.")

    # Start security monitoring
    await security_monitor.ensure_monitoring_started()
    logger.info("Security monitoring started")
    
    # Log security event for startup
    log_security_event(
        "application_startup",
        {
            "security_level": SECURITY_CONFIG.environment.value,
            "rate_limits": {
                "per_minute": SECURITY_CONFIG.rate_limit.requests_per_minute,
                "per_hour": SECURITY_CONFIG.rate_limit.requests_per_hour,
                "per_day": SECURITY_CONFIG.rate_limit.requests_per_day
            }
        },
        severity="INFO"
    )

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Shutting down Legal AI Assistant API")
    
    # Log security event for shutdown
    log_security_event(
        "application_shutdown",
        {},
        severity="INFO"
    )

# Debug endpoint for environment variables (development only)
@app.get("/debug/env")
async def debug_env():
    """Debug environment variables (remove in production)"""
    return {
        "SUPABASE_URL": os.getenv("SUPABASE_URL", "NOT_SET"),
        "SUPABASE_ANON_KEY": os.getenv("SUPABASE_ANON_KEY", "NOT_SET")[:20] + "..." if os.getenv("SUPABASE_ANON_KEY") else "NOT_SET",
        "SUPABASE_SERVICE_ROLE_KEY": os.getenv("SUPABASE_SERVICE_ROLE_KEY", "NOT_SET")[:20] + "..." if os.getenv("SUPABASE_SERVICE_ROLE_KEY") else "NOT_SET",
        "DATABASE_URL": os.getenv("DATABASE_URL", "NOT_SET")[:50] + "..." if os.getenv("DATABASE_URL") else "NOT_SET",
        "SECURITY_ENVIRONMENT": os.getenv("SECURITY_ENVIRONMENT", "NOT_SET"),
        "REDIS_URL": os.getenv("REDIS_URL", "NOT_SET"),
    }

# For local development
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
