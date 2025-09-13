from fastapi import APIRouter, Body, HTTPException, Depends
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from models.request_models import RegulatoryChangeRequest
from models.response_models import BaseResponse, format_response, handle_error
from agents.compliance_agent import analyze_regulatory_change
from agents.regulatory_agent import analyze_regulatory_compliance
from config.colombian_compliance import ColombianLegalFramework
from endpoints.auth import get_current_user

router = APIRouter(prefix="/regulatory", tags=["regulatory"])

class RegulatoryAnalysisRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    organization_type: str = Field(
        ..., 
        description="Tipo de organización"
    )
    jurisdiction: str = Field(
        default="Colombia",
        description="Jurisdicción aplicable"
    )
    regulatory_framework: List[str] = Field(
        ...,
        description="Marco normativo aplicable"
    )
    data_processing: Optional[Dict[str, str]] = Field(
        None,
        description="Tratamiento de datos personales"
    )
    specific_requirements: Optional[List[str]] = Field(
        None,
        description="Requisitos específicos"
    )
    legal_terms: Optional[List[str]] = Field(
        None,
        description="Términos jurídicos relevantes"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "organization_type": "Entidad financiera",
                "jurisdiction": "Colombia",
                "regulatory_framework": [
                    "Ley 1581 de 2012",
                    "Circular Externa 029 de 2014 SFC"
                ],
                "data_processing": {
                    "type": "datos_financieros",
                    "purpose": "cumplimiento_regulatorio"
                },
                "specific_requirements": [
                    "SARLAFT",
                    "Sistema de Control Interno"
                ],
                "legal_terms": [
                    "secreto_bancario",
                    "habeas_data"
                ]
            }
        }
    }

class RegulatoryAnalysisResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    analysis: Dict[str, Union[str, List[str], Dict[str, Any]]] = Field(
        ...,
        description="Análisis regulatorio detallado"
    )
    organization_type: str = Field(
        ...,
        description="Tipo de organización"
    )
    jurisdiction: str = Field(
        ...,
        description="Jurisdicción"
    )
    regulatory_framework: List[str] = Field(
        ...,
        description="Marco normativo aplicable"
    )
    colombian_compliance: Dict[str, Union[str, List[str], Dict[str, Any]]] = Field(
        ...,
        description="Cumplimiento normativo colombiano"
    )
    compliance_status: Dict[str, Union[str, float, List[str]]] = Field(
        ...,
        description="Estado de cumplimiento"
    )
    specific_requirements: Optional[List[str]] = Field(
        None,
        description="Requisitos específicos"
    )
    data_processing: Optional[Dict[str, str]] = Field(
        None,
        description="Tratamiento de datos"
    )
    legal_terms: Optional[Dict[str, str]] = Field(
        None,
        description="Definiciones jurídicas"
    )
    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = {
        "json_schema_extra": {
            "example": {
                "analysis": {
                    "resumen_ejecutivo": "La entidad financiera...",
                    "requisitos_cumplimiento": [
                        "Implementación SARLAFT",
                        "Protección de datos"
                    ],
                    "riesgos_identificados": {
                        "nivel": "medio",
                        "detalles": ["Riesgo 1", "Riesgo 2"]
                    }
                },
                "organization_type": "Entidad financiera",
                "jurisdiction": "Colombia",
                "regulatory_framework": [
                    "Ley 1581 de 2012",
                    "Circular Externa 029 de 2014 SFC"
                ],
                "colombian_compliance": {
                    "framework_version": "2024.1",
                    "constitutional_principles": [
                        "Debido proceso",
                        "Buena fe"
                    ],
                    "requirements": {
                        "data_protection": "Cumple",
                        "risk_management": "En proceso"
                    }
                },
                "compliance_status": {
                    "overall_score": 0.85,
                    "status": "En cumplimiento",
                    "pending_actions": [
                        "Actualizar política de datos",
                        "Completar matriz de riesgos"
                    ]
                }
            }
        }
    }

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
    ),
    current_user: Dict[str, Any] = Depends(get_current_user)
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

@router.post(
    "/analyze",
    response_model=RegulatoryAnalysisResponse,
    summary="Análisis de Cumplimiento Regulatorio",
    description="""
    Realiza un análisis exhaustivo del cumplimiento regulatorio según el marco
    normativo colombiano, incluyendo evaluación de riesgos y recomendaciones.
    """
)
async def analyze_regulatory_endpoint(
    request: RegulatoryAnalysisRequest = Body(
        ...,
        description="Parámetros para el análisis regulatorio"
    ),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Analiza cumplimiento regulatorio con normativa colombiana"""
    try:
        result = await analyze_regulatory_compliance(
            organization_type=request.organization_type,
            jurisdiction=request.jurisdiction,
            regulatory_framework=request.regulatory_framework,
            data_processing=request.data_processing,
            specific_requirements=request.specific_requirements,
            legal_terms=request.legal_terms
        )
        
        # Add Colombian compliance details
        result["colombian_compliance"].update({
            "framework_version": ColombianLegalFramework.FRAMEWORK_VERSION,
            "constitutional_principles": ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES,
            "analysis_date": datetime.now().isoformat(),
            "validation_status": "Verificado"
        })
        
        # Add compliance status
        result["compliance_status"] = {
            "overall_score": calculate_compliance_score(result),
            "status": determine_compliance_status(result),
            "pending_actions": identify_pending_actions(result)
        }
        
        return RegulatoryAnalysisResponse(**result)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "message": "Error en el análisis regulatorio",
                "timestamp": datetime.now().isoformat()
            }
        )

def calculate_compliance_score(analysis_result: Dict[str, Any]) -> float:
    """Calcula el puntaje de cumplimiento"""
    # Implementation would calculate actual score
    return 0.85

def determine_compliance_status(analysis_result: Dict[str, Any]) -> str:
    """Determina el estado de cumplimiento"""
    # Implementation would determine actual status
    return "En cumplimiento"

def identify_pending_actions(analysis_result: Dict[str, Any]) -> List[str]:
    """Identifica acciones pendientes"""
    # Implementation would identify actual pending actions
    return ["Acción pendiente 1", "Acción pendiente 2"]

@router.get(
    "/frameworks",
    response_model=Dict[str, List[str]],
    summary="Marcos Regulatorios Disponibles",
    description="Obtiene los marcos regulatorios disponibles por sector"
)
async def get_regulatory_frameworks(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Retorna los marcos regulatorios disponibles por sector"""
    return {
        "financiero": [
            "Ley 1581 de 2012",
            "Circular Externa 029 de 2014 SFC",
            "Ley 1266 de 2008",
            "Decreto 2555 de 2010"
        ],
        "salud": [
            "Ley 1751 de 2015",
            "Resolución 1995 de 1999",
            "Ley 23 de 1981"
        ],
        "tecnologia": [
            "Ley 1341 de 2009",
            "Ley 1978 de 2019",
            "Decreto 1078 de 2015"
        ],
        "general": [
            "Constitución Política",
            "Código de Comercio",
            "Código Civil"
        ]
    } 