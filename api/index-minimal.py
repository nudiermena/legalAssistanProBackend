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
    title="Legal AI Assistant API - Minimal",
    description="A minimal API for legal assistance",
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

# Import only essential routers
try:
    from endpoints import contract_review_minimal
    app.include_router(contract_review_minimal.router)
except ImportError as e:
    print(f"Warning: Could not import contract review endpoint: {e}")

# Basic auth endpoint
@app.post("/auth/login")
async def login():
    return {"message": "Auth endpoint - minimal mode", "status": "available"}

# Root route
@app.get("/")
async def root():
    return {"message": "Welcome to Legal AI Assistant API - Minimal Version"}

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "minimal"}

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
