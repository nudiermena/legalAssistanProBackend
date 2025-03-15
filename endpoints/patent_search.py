from fastapi import APIRouter, Body, HTTPException
from models.request_models import PatentSearchRequest
from models.response_models import BaseResponse, format_response, handle_error
from agents.patent_agent import search_prior_art

router = APIRouter()

@router.post(
    "/api/patent-search",
    response_model=BaseResponse,
    summary="Patent Prior Art Search",
    description="""
    Conducts comprehensive prior art searches for patent applications, analyzing
    existing patents and publications to assess novelty and non-obviousness.
    """
)
async def patent_search_endpoint(
    request: PatentSearchRequest = Body(
        ...,
        example={
            "invention_description": "A novel method for automated legal document analysis using AI",
            "technical_features": [
                "Natural language processing for legal text",
                "Machine learning for pattern recognition",
                "Automated citation analysis"
            ],
            "jurisdiction": "US",
            "search_depth": "comprehensive",
            "include_non_patent_literature": True
        }
    )
):
    """
    Perform a thorough prior art search for a patent application, including
    analysis of existing patents and non-patent literature.
    """
    try:
        result = await search_prior_art(
            invention_description=request.invention_description,
            technical_features=request.technical_features,
            jurisdiction=request.jurisdiction,
            search_depth=request.search_depth,
            include_non_patent_literature=request.include_non_patent_literature
        )
        return await format_response({"search_results": result})
    except Exception as e:
        raise HTTPException(status_code=500, detail=await handle_error(e)) 