from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict
from agents.whistleblower_agent import analyze_whistleblower_report, draft_whistleblower_policy
from config.colombian_compliance import ColombianLegalFramework

router = APIRouter(prefix="/whistleblower", tags=["whistleblower"])

class WhistleblowerReportRequest(BaseModel):
    report_content: str
    report_type: str = "Denuncia administrativa"  # Default to administrative complaint
    jurisdiction: str = "Colombia"
    specific_concerns: Optional[List[str]] = None
    data_processing: Optional[Dict[str, str]] = None
    legal_terms: Optional[List[str]] = None

    class Config:
        schema_extra = {
            "example": {
                "report_content": "Se ha identificado un posible caso de corrupción...",
                "report_type": "Denuncia administrativa",
                "jurisdiction": "Colombia",
                "specific_concerns": [
                    "Posible conflicto de interés",
                    "Irregularidades en contratación"
                ],
                "data_processing": {
                    "type": "sensitive",
                    "consent": {"provided": True, "date": "2024-03-31"},
                    "purpose": "investigación administrativa"
                },
                "legal_terms": [
                    "debido proceso",
                    "derecho de defensa"
                ]
            }
        }

class WhistleblowerPolicyRequest(BaseModel):
    organization_type: str
    jurisdiction: str = "Colombia"
    specific_requirements: Optional[List[str]] = None
    data_processing: Optional[Dict[str, str]] = None

    class Config:
        schema_extra = {
            "example": {
                "organization_type": "Entidad pública",
                "jurisdiction": "Colombia",
                "specific_requirements": [
                    "Ley 1778 de 2016",
                    "Ley 1952 de 2019"
                ],
                "data_processing": {
                    "type": "confidential",
                    "retention_period": "5 years",
                    "security_level": "alto"
                }
            }
        }

@router.post("/report/analyze")
async def analyze_report(request: WhistleblowerReportRequest):
    try:
        result = await analyze_whistleblower_report(
            report_content=request.report_content,
            report_type=request.report_type,
            jurisdiction=request.jurisdiction,
            specific_concerns=request.specific_concerns,
            data_processing=request.data_processing
        )
        return {
            "status": "success",
            "data": result,
            "colombian_compliance": {
                "framework": ColombianLegalFramework.FRAMEWORK_VERSION,
                "principles": ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/policy/draft")
async def draft_policy(request: WhistleblowerPolicyRequest):
    try:
        result = await draft_whistleblower_policy(
            organization_type=request.organization_type,
            jurisdiction=request.jurisdiction,
            specific_requirements=request.specific_requirements,
            data_processing=request.data_processing
        )
        return {
            "status": "success",
            "data": result,
            "colombian_compliance": {
                "framework": ColombianLegalFramework.FRAMEWORK_VERSION,
                "principles": ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 