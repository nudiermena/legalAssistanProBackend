from fastapi import APIRouter, Body, HTTPException
from models.request_models import DemandLetterRequest
from models.response_models import BaseResponse, format_response, handle_error
from agents.demand_letter_agent import generate_demand_letter
from agents.document_drafting_agent import draft_document

router = APIRouter()

@router.post(
    "/api/demand-letter",
    response_model=BaseResponse,
    summary="Debt Collection Demand Letter Generation",
    description="""
    Generates legally compliant demand letters for debt collection purposes,
    incorporating relevant laws and regulations while maintaining professional tone.
    """
)
async def demand_letter_endpoint(
    request: DemandLetterRequest = Body(
        ...,
        example={
            "debtor_info": {
                "name": "John Doe",
                "address": "123 Main St, Anytown, USA",
                "account_number": "ACC123456"
            },
            "debt_details": {
                "amount": 5000.00,
                "due_date": "2024-02-15",
                "interest_rate": "5%",
                "late_fees": 250.00
            },
            "collection_history": [
                "Initial invoice sent on 2024-01-15",
                "Payment reminder sent on 2024-02-01"
            ],
            "jurisdiction": "New York",
            "compliance_requirements": [
                "Fair Debt Collection Practices Act",
                "New York State Debt Collection Laws"
            ],
            "client_tone_preference": "Professional but firm"
        }
    )
):
    """
    Generate a legally compliant demand letter for debt collection, ensuring
    adherence to relevant laws and regulations while maintaining appropriate
    professional tone.
    """
    try:
        result = await generate_demand_letter(
            debtor_info=request.debtor_info,
            debt_details=request.debt_details,
            collection_history=request.collection_history,
            jurisdiction=request.jurisdiction,
            compliance_requirements=request.compliance_requirements,
            client_tone_preference=request.client_tone_preference
        )
        return await format_response({"demand_letter": result})
    except Exception as e:
        raise HTTPException(status_code=500, detail=await handle_error(e)) 