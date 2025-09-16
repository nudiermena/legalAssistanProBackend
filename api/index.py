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

# Import only essential routers for minimal deployment
from endpoints import (
    contract_review,
    legal_research,
    legal_chat,
    patent_search,
    whistleblower_analysis,
    dashboard
)

# Include only essential routers
app.include_router(contract_review.router)
app.include_router(legal_research.router)
app.include_router(legal_chat.router)
app.include_router(patent_search.router)
app.include_router(whistleblower_analysis.router)
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