from fastapi import APIRouter, Body, HTTPException
from models.request_models import WhistleblowerAnalysisRequest
from models.response_models import BaseResponse, format_response, handle_error
from agents.whistleblower_agent import analyze_whistleblower_report

router = APIRouter()

@router.post(
    "/api/whistleblower-analysis",
    response_model=BaseResponse,
    summary="Whistleblower Report Analysis",
    description="""
    Analyzes whistleblower reports to assess severity, credibility, and regulatory
    implications, providing recommendations for investigation and response.
    """
)
async def whistleblower_analysis_endpoint(
    request: WhistleblowerAnalysisRequest = Body(
        ...,
        example={
            "report_content": "Allegations of financial misconduct in procurement department",
            "company_context": {
                "industry": "Healthcare",
                "size": "Large",
                "regulatory_environment": "Heavily regulated"
            },
            "applicable_policies": [
                "Code of Conduct",
                "Whistleblower Protection Policy",
                "Anti-Fraud Policy"
            ],
            "regulatory_framework": [
                "Sarbanes-Oxley Act",
                "False Claims Act"
            ],
            "prior_related_issues": [
                "Previous audit findings in procurement",
                "Employee training gaps identified"
            ]
        }
    )
):
    """
    Analyze a whistleblower report to determine its credibility, severity, and
    appropriate response actions, while ensuring compliance with relevant laws
    and internal policies.
    """
    try:
        result = await analyze_whistleblower_report(
            report_content=request.report_content,
            company_context=request.company_context,
            applicable_policies=request.applicable_policies,
            regulatory_framework=request.regulatory_framework,
            prior_related_issues=request.prior_related_issues
        )
        return await format_response({"analysis_report": result})
    except Exception as e:
        raise HTTPException(status_code=500, detail=await handle_error(e)) 