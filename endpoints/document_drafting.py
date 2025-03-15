from fastapi import APIRouter, HTTPException
from models.request_models import DocumentDraftingRequest
from models.response_models import DocumentDraftingResponse
from agents.document_drafting_agent import draft_document
from utils.error_handling import handle_error

router = APIRouter()

@router.post("/api/document-drafting", response_model=DocumentDraftingResponse)
async def document_drafting_endpoint(request: DocumentDraftingRequest):
    """
    Generate legal documents based on provided parameters
    
    Parameters:
    - document_type: Type of document to generate
    - parties: List of parties involved
    - key_terms: Key terms and conditions
    - jurisdiction: Applicable jurisdiction
    - special_considerations: Special requirements or conditions
    - risk_profile: Risk assessment profile
    - negotiation_context: Context for negotiations
    
    Returns:
    - Generated document content
    - Document metadata
    """
    try:
        # Create document content from request parameters
        document_content = f"Document Type: {request.document_type}\n\nKey Terms:\n"
        for term in request.key_terms:
            document_content += f"- {term}\n"
            
        # Create document context
        document_context = {
            "risk_profile": request.risk_profile,
            "negotiation_context": request.negotiation_context
        }
        
        result = await draft_document(
            document_content=document_content,
            document_context=document_context,
            parties=request.parties,
            jurisdiction=request.jurisdiction,
            special_considerations=request.special_considerations
        )
        
        return DocumentDraftingResponse(
            document=result["document"],
            metadata={
                "document_type": request.document_type,
                "jurisdiction": request.jurisdiction,
                "parties": request.parties
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 