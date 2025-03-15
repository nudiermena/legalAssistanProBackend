from fastapi import APIRouter, Body, HTTPException
from models.request_models import LegalDiagnosisRequest
from models.response_models import BaseResponse, format_response, handle_error
from agents.legal_diagnosis_agent import diagnose_legal_issue

router = APIRouter()

@router.post(
    "/api/legal-diagnosis",
    response_model=BaseResponse,
    summary="Personal Legal Issue Diagnosis",
    description="""
    Provides personalized legal guidance for consumers based on their specific
    situations, including relevant laws, potential approaches, and when to seek
    professional legal counsel.
    """
)
async def legal_diagnosis_endpoint(
    request: LegalDiagnosisRequest = Body(
        ...,
        example={
            "situation_description": "Landlord refusing to return security deposit",
            "jurisdiction": "California",
            "user_goal": "Recover security deposit",
            "timeline": {
                "lease_end_date": "2024-03-01",
                "deposit_due_date": "2024-03-15"
            },
            "financial_considerations": {
                "deposit_amount": 2000.00,
                "monthly_rent": 2000.00,
                "legal_fees_budget": 500.00
            }
        }
    )
):
    """
    Analyze a personal legal situation and provide guidance on relevant laws,
    potential approaches, and recommendations for next steps, including when
    to consult an attorney.
    """
    try:
        result = await diagnose_legal_issue(
            situation_description=request.situation_description,
            jurisdiction=request.jurisdiction,
            user_goal=request.user_goal,
            timeline=request.timeline,
            financial_considerations=request.financial_considerations
        )
        return await format_response({"diagnosis": result})
    except Exception as e:
        raise HTTPException(status_code=500, detail=await handle_error(e)) 