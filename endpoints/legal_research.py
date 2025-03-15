from fastapi import APIRouter, Body, HTTPException
from models.request_models import LegalResearchRequest
from models.response_models import BaseResponse, format_response, handle_error
from agents.legal_research_agent import conduct_legal_research

router = APIRouter()

@router.post(
    "/api/legal-research",
    response_model=BaseResponse,
    summary="AI Legal Research Assistant",
    description="""
    Conducts comprehensive legal research on specific issues, providing analysis of 
    relevant case law, statutes, and regulations. Can focus on specific jurisdictions 
    and timeframes.
    """
)
async def legal_research_endpoint(
    request: LegalResearchRequest = Body(
        ...,
        example={
            "jurisdiction": "California",
            "legal_issue": "Employment discrimination based on age",
            "relevant_facts": ["Employee over 40", "Replaced by younger worker", "Performance reviews were positive"],
            "timeframe": "Last 10 years",
            "case_law_only": False
        }
    )
):
    """
    Conduct legal research on a specific issue and provide comprehensive analysis
    of relevant case law, statutes, and regulations.
    """
    try:
        result = await conduct_legal_research(
            jurisdiction=request.jurisdiction,
            legal_issue=request.legal_issue,
            relevant_facts=request.relevant_facts,
            timeframe=request.timeframe,
            case_law_only=request.case_law_only
        )
        return await format_response({"research": result})
    except Exception as e:
        raise HTTPException(status_code=500, detail=await handle_error(e)) 