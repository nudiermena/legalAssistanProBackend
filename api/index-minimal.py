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
    title="Legal AI Assistant API - Minimal",
    description="A minimal API for legal assistance",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Pydantic models
class ContractReviewRequest(BaseModel):
    contract_text: str
    user_id: str = None

class ContractReviewResponse(BaseModel):
    success: bool
    analysis: dict = None
    message: str
    timestamp: datetime

# Root route
@app.get("/")
async def root():
    return {"message": "Welcome to Legal AI Assistant API - Minimal Version"}

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "minimal"}

# Contract review endpoint
@app.post("/contract/review", response_model=ContractReviewResponse)
async def review_contract(request: ContractReviewRequest):
    """Review a contract with basic analysis"""
    try:
        logger.info(f"Contract review request received for user: {request.user_id}")
        
        # Basic contract analysis
        analysis = {
            "contract_length": len(request.contract_text),
            "word_count": len(request.contract_text.split()),
            "analysis_status": "basic_analysis_completed",
            "recommendations": [
                "This is a basic analysis. For full functionality, please contact support.",
                f"Contract length: {len(request.contract_text)} characters",
                f"Word count: {len(request.contract_text.split())} words"
            ],
            "risk_level": "medium",
            "key_clauses": ["Basic analysis only - full analysis not available in minimal mode"]
        }
        
        return ContractReviewResponse(
            success=True,
            analysis=analysis,
            message="Basic contract analysis completed successfully",
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error in contract review: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Contract review failed: {str(e)}"
        )

# Contract status endpoint
@app.get("/contract/status")
async def get_contract_status():
    """Get the status of contract analysis service"""
    return {
        "status": "minimal_mode",
        "message": "Contract analysis service is running in minimal mode",
        "features_available": [
            "Basic text analysis",
            "Basic recommendations"
        ],
        "features_unavailable": [
            "Advanced AI analysis",
            "PDF form field extraction",
            "Knowledge base integration",
            "Memory system"
        ],
        "timestamp": datetime.now()
    }

# Legal chat endpoint
@app.post("/legal-chat/consulta")
async def legal_chat_consulta(request: dict):
    """Legal chat consultation endpoint"""
    try:
        logger.info("Legal chat consultation request received")
        
        # Basic response for now
        return {
            "success": True,
            "response": "Legal chat consultation endpoint is available in minimal mode. Full AI functionality will be restored soon.",
            "message": "Basic consultation completed",
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error in legal chat consultation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Legal chat consultation failed: {str(e)}"
        )

# Auth endpoint
@app.post("/auth/login")
async def login():
    return {"message": "Auth endpoint - minimal mode", "status": "available"}

# Add OPTIONS handler for CORS preflight
@app.options("/{path:path}")
async def options_handler(path: str):
    """Handle CORS preflight requests"""
    return JSONResponse(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
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
