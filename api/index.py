from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sys
import os
from pathlib import Path

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create FastAPI app
app = FastAPI(
    title="Legal AI Assistant API",
    description="A comprehensive API for legal assistance",
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

# Import routers after app creation
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
app.include_router(case_prediction.router)
app.include_router(dashboard.router)

# Root route
@app.get("/")
async def root():
    return {"message": "Welcome to Legal AI Assistant API"}

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