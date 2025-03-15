from fastapi import APIRouter, Body, HTTPException
from models.request_models import ContractReviewRequest
from models.response_models import BaseResponse, format_response, handle_error
from agents.contract_agent import analyze_contract

router = APIRouter()

@router.post(
    "/api/contract-review",
    response_model=BaseResponse,
    summary="AI-Powered Contract Review & Analysis",
    description="""
    Analyzes contracts to provide executive summaries, identify key obligations, 
    critical dates, unusual clauses, and potential risks. Can also check compliance 
    with specific regulations.
    """
)
async def contract_review_endpoint(
    request: ContractReviewRequest = Body(
        ...,
        example={
            "contract_text": "This agreement is made between Party A and Party B...",
            "contract_type": "Service Agreement",
            "parties": ["Company A", "Company B"],
            "specific_concerns": ["Liability", "Termination"],
            "relevant_regulations": ["GDPR"]
        }
    )
):
    """
    Analyze a contract and provide detailed insights including executive summary,
    key obligations, critical dates, unusual clauses, and risk assessment.
    """
    try:
        result = await analyze_contract(
            contract_text=request.contract_text,
            contract_type=request.contract_type,
            parties=request.parties,
            specific_concerns=request.specific_concerns,
            relevant_regulations=request.relevant_regulations
        )
        return await format_response({"analysis": result})
    except Exception as e:
        raise HTTPException(status_code=500, detail=await handle_error(e)) 