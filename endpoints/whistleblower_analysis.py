from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from config.colombian_compliance import ColombianLegalFramework
from endpoints.auth import get_current_user

router = APIRouter(prefix="/whistleblower", tags=["whistleblower"])

class WhistleblowerReportRequest(BaseModel):
    report_content: str
    report_type: str = "Denuncia administrativa"  # Default to administrative complaint
    jurisdiction: str = "Colombia"
    specific_concerns: Optional[List[str]] = None
    data_processing: Optional[Dict[str, str]] = None
    legal_terms: Optional[List[str]] = None

    class Config:
        json_schema_extra = {
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
        json_schema_extra = {
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
async def analyze_report(
    request: WhistleblowerReportRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    try:
        # Simplified analysis without the excluded agent
        result = {
            "análisis": f"Análisis de denuncia tipo {request.report_type} en {request.jurisdiction}",
            "tipo_denuncia": request.report_type,
            "jurisdiccion": request.jurisdiction,
            "cumplimiento_colombiano": {
                "principios_constitucionales": ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES,
                "fecha_análisis": "2024-01-01T00:00:00"
            }
        }
        
        if request.specific_concerns:
            result["preocupaciones_específicas"] = request.specific_concerns
        
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
async def draft_policy(
    request: WhistleblowerPolicyRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    try:
        # Simplified policy drafting without the excluded agent
        result = {
            "politica": f"Política de denuncias para {request.organization_type} en {request.jurisdiction}",
            "tipo_organizacion": request.organization_type,
            "jurisdiccion": request.jurisdiction,
            "cumplimiento_colombiano": {
                "principios_constitucionales": ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES,
                "fecha_elaboracion": "2024-01-01T00:00:00"
            }
        }
        
        if request.specific_requirements:
            result["requisitos_especificos"] = request.specific_requirements
        
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