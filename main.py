from fastapi import FastAPI, HTTPException, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
from datetime import datetime
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
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
    dashboard
)
from endpoints.document_drafting import router as document_router
from endpoints.legal_research import router as legal_research_router
from fastapi.templating import Jinja2Templates
import os
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Legal AI Assistant API",
    description="""
    A comprehensive API for legal assistance, providing various tools for contract review,
    legal research, regulatory analysis, and more. Each endpoint is specialized for
    specific legal tasks and includes appropriate disclaimers and compliance checks.
    """,
    version="1.0.0"
)

# Get the base directory
BASE_DIR = Path(__file__).resolve().parent

# Log the directories for debugging
logger.debug(f"Base directory: {BASE_DIR}")
logger.debug(f"Static directory: {BASE_DIR / 'static'}")

# Set up templates
templates = Jinja2Templates(directory=str(BASE_DIR / "static"))

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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

# Register exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
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

# Error handling for 404
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    logger.error(f"404 error for path: {request.url.path}")
    return JSONResponse(
        status_code=404,
        content={"detail": {"message": f"Endpoint not found: {request.url.path}"}}
    )

@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    logger.error(f"500 error for path: {request.url.path}, error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": {"message": "Internal server error"}}
    )
