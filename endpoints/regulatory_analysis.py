from fastapi import APIRouter, Body, HTTPException
from models.request_models import RegulatoryChangeRequest
from models.response_models import BaseResponse, format_response, handle_error
from agents.compliance_agent import analyze_regulatory_change

router = APIRouter()

@router.post(
    "/api/regulatory-analysis",
    response_model=BaseResponse,
    summary="AI-Powered Compliance Monitoring System",
    description="""
    Analyzes regulatory changes and their impact on business operations, providing 
    actionable compliance strategies, implementation timelines, and resource requirements.
    """
)
async def regulatory_analysis_endpoint(
    request: RegulatoryChangeRequest = Body(
        ...,
        example={
            "regulation_text": "All companies must implement data protection measures...",
            "effective_date": "2024-01-01",
            "industry": "Healthcare",
            "business_operations": ["Patient data management", "Telemedicine", "Billing"],
            "current_compliance_status": {
                "Data encryption": "Partial implementation",
                "Access controls": "Fully implemented",
                "Audit logging": "Not implemented"
            }
        }
    )
):
    """
    Analyze regulatory changes and their impact on business operations, providing
    actionable compliance strategies and implementation plans.
    """
    try:
        result = await analyze_regulatory_change(
            regulation_text=request.regulation_text,
            effective_date=request.effective_date,
            industry=request.industry,
            business_operations=request.business_operations,
            current_compliance_status=request.current_compliance_status
        )
        return await format_response({"analysis": result})
    except Exception as e:
        raise HTTPException(status_code=500, detail=await handle_error(e)) 