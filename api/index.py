from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create FastAPI app
app = FastAPI(
    title="Legal AI Assistant API",
    description="Minimal API for legal assistance",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple request models
class ContractRequest(BaseModel):
    contract_text: str
    contract_type: str = "general"

class LegalResearchRequest(BaseModel):
    query: str
    jurisdiction: str = "Colombia"

class ChatRequest(BaseModel):
    message: str
    context: str = ""

class PatentRequest(BaseModel):
    invention_description: str
    jurisdiction: str = "Colombia"

class WhistleblowerRequest(BaseModel):
    report_content: str
    report_type: str = "administrative"

# Root route
@app.get("/")
async def root():
    return {"message": "Welcome to Legal AI Assistant API - Minimal Version"}

# Contract Review Endpoint
@app.post("/contract/review")
async def review_contract(request: ContractRequest):
    return {
        "status": "success",
        "analysis": f"Contract analysis for {request.contract_type} contract",
        "recommendations": ["Review clause 1", "Consider liability terms"],
        "risk_level": "medium"
    }

# Legal Research Endpoint
@app.post("/legal/research")
async def legal_research(request: LegalResearchRequest):
    return {
        "status": "success",
        "query": request.query,
        "jurisdiction": request.jurisdiction,
        "results": [
            {
                "title": "Relevant Law",
                "summary": "Legal framework applicable to your query",
                "relevance": "high"
            }
        ]
    }

# Legal Chat Endpoint
@app.post("/legal/chat")
async def legal_chat(request: ChatRequest):
    return {
        "status": "success",
        "response": f"Legal advice regarding: {request.message}",
        "context": request.context,
        "confidence": 0.85
    }

# Patent Search Endpoint
@app.post("/patent/search")
async def patent_search(request: PatentRequest):
    return {
        "status": "success",
        "invention": request.invention_description,
        "jurisdiction": request.jurisdiction,
        "search_results": [
            {
                "patent_id": "CO2024001",
                "relevance": "medium",
                "similarity": 0.65
            }
        ],
        "recommendations": [
            {
                "type": "info",
                "title": "Patent Search Complete",
                "description": "Search completed successfully"
            }
        ]
    }

# Whistleblower Analysis Endpoint
@app.post("/whistleblower/analyze")
async def analyze_whistleblower(request: WhistleblowerRequest):
    return {
        "status": "success",
        "analysis": f"Analysis of {request.report_type} report",
        "report_type": request.report_type,
        "recommendations": [
            "Follow due process",
            "Maintain confidentiality",
            "Document all actions"
        ]
    }

# Dashboard Endpoint
@app.get("/dashboard")
async def dashboard():
    return {
        "status": "success",
        "data": {
            "total_requests": 0,
            "active_sessions": 0,
            "system_status": "operational"
        }
    }

# Health Check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

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