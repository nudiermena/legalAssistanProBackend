from datetime import datetime
from typing import Any

async def handle_error(error: Exception) -> dict[str, Any]:
    """Handle errors in a consistent way across the application"""
    return {
        "status": "error",
        "message": str(error),
        "type": error.__class__.__name__
    } 