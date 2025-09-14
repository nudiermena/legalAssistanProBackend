from fastapi import APIRouter, Body, HTTPException, File, UploadFile, Form
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import base64
import tempfile
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["contracts"])

class ContractReviewRequest(BaseModel):
    contract_text: str = Field(..., description="The contract text to analyze")
    user_id: Optional[str] = Field(None, description="User ID for session tracking")
    session_id: Optional[str] = Field(None, description="Session ID for tracking")

class ContractReviewResponse(BaseModel):
    success: bool
    analysis: Optional[Dict[str, Any]] = None
    message: str
    timestamp: datetime

@router.post("/contract/review", response_model=ContractReviewResponse)
async def review_contract(request: ContractReviewRequest):
    """Review a contract with basic analysis"""
    try:
        logger.info(f"Contract review request received for user: {request.user_id}")
        
        # Basic contract analysis (simplified)
        analysis = {
            "contract_length": len(request.contract_text),
            "word_count": len(request.contract_text.split()),
            "analysis_status": "basic_analysis_completed",
            "recommendations": [
                "This is a basic analysis. For full functionality, please contact support.",
                "Contract length: {} characters".format(len(request.contract_text)),
                "Word count: {} words".format(len(request.contract_text.split()))
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

@router.post("/contract/upload")
async def upload_contract(file: UploadFile = File(...)):
    """Upload and analyze a contract file"""
    try:
        logger.info(f"Contract upload request received: {file.filename}")
        
        # Basic file validation
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Check file size (limit to 10MB)
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")
        
        # Basic analysis
        analysis = {
            "filename": file.filename,
            "file_size": len(content),
            "file_type": file.content_type,
            "analysis_status": "basic_file_analysis_completed",
            "message": "File uploaded successfully. Full analysis not available in minimal mode."
        }
        
        return {
            "success": True,
            "analysis": analysis,
            "message": "File uploaded and basic analysis completed",
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error in contract upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Contract upload failed: {str(e)}"
        )

@router.get("/contract/status")
async def get_contract_status():
    """Get the status of contract analysis service"""
    return {
        "status": "minimal_mode",
        "message": "Contract analysis service is running in minimal mode",
        "features_available": [
            "Basic text analysis",
            "File upload",
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
