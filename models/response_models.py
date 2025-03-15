import datetime
from typing import Dict, Any
from pydantic import BaseModel

class BaseResponse(BaseModel):
    status: str
    timestamp: datetime.datetime
    data: Dict[str, Any]

class DocumentDraftingResponse(BaseModel):
    document: str
    metadata: Dict[str, Any]

async def format_response(data: Dict[str, Any]) -> BaseResponse:
    return BaseResponse(
        status="success",
        timestamp=datetime.datetime.now(),
        data=data
    )

async def handle_error(e: Exception) -> Dict[str, Any]:
    return {
        "status": "error",
        "timestamp": datetime.datetime.now(),
        "error": str(e)
    } 