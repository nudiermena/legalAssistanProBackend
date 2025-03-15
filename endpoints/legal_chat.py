from fastapi import APIRouter, Body, HTTPException
from models.request_models import LegalChatbotRequest
from models.response_models import BaseResponse, format_response, handle_error
from agents.chatbot_agent import process_client_message

router = APIRouter()

@router.post(
    "/api/legal-chat",
    response_model=BaseResponse,
    summary="AI Legal Chatbot for Law Firms",
    description="""
    Provides conversational legal assistance to clients, answering questions about 
    legal topics in plain language while maintaining appropriate disclaimers.
    """
)
async def legal_chatbot_endpoint(
    request: LegalChatbotRequest = Body(
        ...,
        example={
            "client_id": "client123",
            "message": "What are my rights if my landlord refuses to make repairs?",
            "conversation_id": "conv_20240315123456",
            "authentication_token": None,
            "practice_area": "Real Estate Law"
        }
    )
):
    """
    Process client messages and provide helpful legal information with appropriate
    disclaimers. Can be specialized for different practice areas.
    """
    try:
        result = await process_client_message(
            client_id=request.client_id,
            message=request.message,
            conversation_id=request.conversation_id,
            authentication_token=request.authentication_token,
            practice_area=request.practice_area
        )
        return await format_response({"chat_response": result})
    except Exception as e:
        raise HTTPException(status_code=500, detail=await handle_error(e)) 