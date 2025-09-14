from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Legal AI Assistant API - CORS Fixed",
    description="A CORS-fixed API for legal assistance",
    version="1.0.0"
)

# Allowed frontend domains
origins = [
    "https://miasistentelegalia.com",   # your production frontend
    "http://localhost:3000",            # for local testing (optional)
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],    # allows GET, POST, OPTIONS, etc.
    allow_headers=["*"],    # allows Content-Type, Authorization, etc.
)

# Custom CORS middleware for serverless environments
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    """Add CORS headers to all responses"""
    response = await call_next(request)
    
    # Add CORS headers
    response.headers["Access-Control-Allow-Origin"] = "https://miasistentelegalia.com"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    
    # Handle preflight requests
    if request.method == "OPTIONS":
        response.status_code = 200
    
    return response

# Pydantic models
class LegalChatRequest(BaseModel):
    message: str
    user_id: str = None
    session_id: str = None

# Root route
@app.get("/")
async def root():
    return {
        "message": "Welcome to Legal AI Assistant API - CORS Fixed Version",
        "cors_enabled": True,
        "frontend_domain": "https://miasistentelegalia.com"
    }

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "version": "cors-fixed",
        "cors_enabled": True
    }

# Legal chat endpoint
@app.post("/legal-chat/consulta")
async def legal_chat_consulta(request: LegalChatRequest):
    """Legal chat consultation endpoint with CORS fixed"""
    try:
        logger.info(f"Legal chat consultation request received for user: {request.user_id}")
        logger.info(f"Request message: {request.message[:100]}...")  # Log first 100 chars
        logger.info("CORS headers should be set by middleware")
        
        # Basic response for now
        return {
            "success": True,
            "response": "Legal chat consultation endpoint is working with CORS fixed!",
            "message": "CORS is working correctly",
            "timestamp": datetime.now(),
            "cors_status": "working",
            "user_message": request.message
        }
        
    except Exception as e:
        logger.error(f"Error in legal chat consultation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Legal chat consultation failed: {str(e)}"
        )

# CORS test endpoint
@app.post("/cors-test")
async def cors_test():
    return {"message": "CORS working ✅", "timestamp": datetime.now()}

# Simple GET test endpoint
@app.get("/test")
async def test_endpoint():
    return {"message": "API is working", "timestamp": datetime.now(), "cors": "enabled"}

# Explicit OPTIONS handler for legal-chat endpoint
@app.options("/legal-chat/consulta")
async def options_legal_chat():
    """Handle OPTIONS preflight for legal-chat endpoint"""
    return JSONResponse(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "https://miasistentelegalia.com",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true"
        }
    )

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": f"Endpoint not found: {request.url.path}"}
    )

@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
