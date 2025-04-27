from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

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