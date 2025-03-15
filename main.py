from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
from datetime import datetime
from pydantic import BaseModel
from endpoints import (
    contract_review,
    legal_research,
    regulatory_analysis,
    legal_chat,
    patent_search,
    document_drafting,
    whistleblower_analysis,
    demand_letter,
    legal_diagnosis
)

app = FastAPI(
    title="Legal AI Assistant API",
    description="""
    A comprehensive API for legal assistance, providing various tools for contract review,
    legal research, regulatory analysis, and more. Each endpoint is specialized for
    specific legal tasks and includes appropriate disclaimers and compliance checks.
    """,
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    return {
        "status": "error",
        "timestamp": datetime.now(),
        "error": str(e)
    }

@app.get("/")
async def root():
    """
    Root endpoint providing basic API information and available endpoints.
    """
    return {
        "message": "Welcome to the Legal AI Assistant API",
        "version": "1.0.0",
        "endpoints": [
            "/api/contract-review",
            "/api/legal-research",
            "/api/regulatory-analysis",
            "/api/legal-chat",
            "/api/patent-search",
            "/api/document-drafting",
            "/api/whistleblower-analysis",
            "/api/demand-letter",
            "/api/legal-diagnosis"
        ]
    }

# Include routers
app.include_router(contract_review.router)
app.include_router(legal_research.router)
app.include_router(regulatory_analysis.router)
app.include_router(legal_chat.router)
app.include_router(patent_search.router)
app.include_router(document_drafting.router)
app.include_router(whistleblower_analysis.router)
app.include_router(demand_letter.router)
app.include_router(legal_diagnosis.router)
