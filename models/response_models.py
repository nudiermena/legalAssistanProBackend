import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel
from fastapi import HTTPException
import json

class BaseResponse(BaseModel):
    status: str
    timestamp: datetime.datetime
    data: Dict[str, Any]

class DocumentDraftingResponse(BaseModel):
    document: str
    metadata: Dict[str, Any]

def format_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format the response data with standard structure
    
    Args:
        data: Response data to format
        
    Returns:
        Formatted response dictionary
    """
    return {
        "status": "success",
        "message": "Operación completada exitosamente",
        "data": data
    }

def handle_error(error: Exception) -> Dict[str, Any]:
    """
    Handle and format error responses
    
    Args:
        error: Exception to handle
        
    Returns:
        Formatted error response
    """
    if isinstance(error, HTTPException):
        return {
            "status": "error",
            "message": error.detail,
            "code": error.status_code
        }
    
    return {
        "status": "error",
        "message": str(error),
        "code": 500
    }

class ContractAnalysisResponse:
    """Response model for contract analysis"""
    
    @staticmethod
    def success(data: Dict[str, Any]) -> Dict[str, Any]:
        return format_response({
            "analysis": data.get("analysis", {}),
            "metadata": data.get("metadata", {})
        })
    
    @staticmethod
    def error(error: Exception) -> Dict[str, Any]:
        return handle_error(error)

class ChatResponse:
    """Response model for chat interactions"""
    
    @staticmethod
    def success(data: Dict[str, Any]) -> Dict[str, Any]:
        return format_response({
            "message": data.get("message", ""),
            "context": data.get("context", {}),
            "metadata": data.get("metadata", {})
        })
    
    @staticmethod
    def error(error: Exception) -> Dict[str, Any]:
        return handle_error(error) 