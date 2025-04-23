from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app import create_app

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/api/chat")
async def chat(request: Request):
    try:
        data = await request.json()
        # Add your chat logic here
        return JSONResponse(content={"response": "Chat response"})
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

# Export the app for Cloudflare Workers
app = app 