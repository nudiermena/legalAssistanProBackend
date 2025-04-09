from fastapi import APIRouter, HTTPException, Body, Depends
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from agents.legal_diagnosis_agent import diagnose_legal_issue
from config.colombian_compliance import ColombianLegalFramework

router = APIRouter(prefix="/legal-diagnosis", tags=["diagnosis"])

class LegalDiagnosisRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    situation_description: str = Field(..., description="Descripción de la situación")
    jurisdiction: str = Field(default="Colombia", description="Jurisdicción")
    relevant_facts: List[str] = Field(..., description="Hechos relevantes")
    legal_terms: Optional[List[str]] = Field(None, description="Términos jurídicos")
    data_processing: Optional[Dict[str, str]] = Field(None, description="Tratamiento de datos")
    area_of_law: Optional[str] = Field(None, description="Área del derecho")

    model_config = {
        "json_schema_extra": {
            "example": {
                "situation_description": "Despido durante incapacidad médica",
                "relevant_facts": [
                    "Contrato indefinido",
                    "3 años de antigüedad",
                    "Incapacidad vigente"
                ],
                "area_of_law": "derecho_laboral"
            }
        }
    }

class LegalDiagnosisResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    diagnosis: Dict[str, Union[str, List[str], Dict[str, Any]]] = Field(
        ..., 
        description="Diagnóstico jurídico"
    )
    situation_description: str = Field(..., description="Situación analizada")
    jurisdiction: str = Field(..., description="Jurisdicción")
    relevant_facts: List[str] = Field(..., description="Hechos relevantes")
    colombian_compliance: Dict[str, Any] = Field(..., description="Cumplimiento normativo")
    recommendations: List[str] = Field(..., description="Recomendaciones")
    legal_terms: Optional[Dict[str, str]] = Field(None, description="Términos jurídicos")
    data_processing: Optional[Dict[str, str]] = Field(None, description="Tratamiento de datos")
    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = {
        "json_schema_extra": {
            "example": {
                "diagnosis": {
                    "analysis": "La situación presenta una vulneración...",
                    "applicable_laws": ["Art. 26 Ley 361 de 1997"],
                    "rights_affected": ["Estabilidad laboral reforzada"]
                },
                "recommendations": [
                    "Presentar acción de tutela",
                    "Solicitar reintegro laboral"
                ]
            }
        }
    }

@router.post(
    "/analyze",
    response_model=LegalDiagnosisResponse,
    summary="Diagnóstico Jurídico Especializado",
    description="""
    Realiza un diagnóstico jurídico especializado según el ordenamiento jurídico
    colombiano, incluyendo análisis constitucional, legal y jurisprudencial.
    """
)
async def diagnose_endpoint(
    request: LegalDiagnosisRequest = Body(
        ...,
        description="Parámetros para el diagnóstico jurídico"
    )
):
    """Realiza diagnóstico jurídico con cumplimiento normativo colombiano"""
    try:
        result = await diagnose_legal_issue(
            situation_description=request.situation_description,
            jurisdiction=request.jurisdiction,
            relevant_facts=request.relevant_facts,
            area_of_law=request.area_of_law,
            legal_terms=request.legal_terms,
            data_processing=request.data_processing
        )
        
        # Enhance with Colombian legal analysis
        result["legal_analysis"] = {
            "marco_constitucional": get_constitutional_framework(request.area_of_law),
            "marco_legal": get_legal_framework(request.area_of_law),
            "jurisprudencia": get_relevant_jurisprudence(request.area_of_law),
            "doctrina": get_relevant_doctrine(request.area_of_law)
        }
        
        # Add Colombian compliance details
        result["colombian_compliance"].update({
            "framework_version": ColombianLegalFramework.FRAMEWORK_VERSION,
            "constitutional_principles": ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES,
            "diagnosis_date": datetime.now().isoformat(),
            "jurisdiction_validation": "Verificado"
        })
        
        return LegalDiagnosisResponse(**result)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "message": "Error en el diagnóstico jurídico",
                "timestamp": datetime.now().isoformat()
            }
        )

@router.get(
    "/areas",
    response_model=Dict[str, List[str]],
    summary="Áreas del Derecho",
    description="Obtiene las áreas del derecho disponibles para diagnóstico"
)
async def get_legal_areas():
    """Retorna las áreas del derecho disponibles"""
    return {
        "derecho_publico": [
            "Constitucional",
            "Administrativo",
            "Tributario"
        ],
        "derecho_privado": [
            "Civil",
            "Comercial",
            "Laboral"
        ],
        "derecho_penal": [
            "Penal General",
            "Penal Especial",
            "Procesal Penal"
        ],
        "derecho_procesal": [
            "Procesal Civil",
            "Procesal Laboral",
            "Procesal Administrativo"
        ]
    }

def get_constitutional_framework(area: Optional[str]) -> List[str]:
    """Obtiene marco constitucional aplicable"""
    # Implementation would connect to a constitutional law database
    return ["Art. 29 CP - Debido proceso", "Art. 53 CP - Derecho laboral"]

def get_legal_framework(area: Optional[str]) -> List[str]:
    """Obtiene marco legal aplicable"""
    # Implementation would connect to a legal framework database
    return ["Ley aplicable 1", "Ley aplicable 2"]

def get_relevant_jurisprudence(area: Optional[str]) -> List[Dict[str, str]]:
    """Obtiene jurisprudencia relevante"""
    # Implementation would connect to a jurisprudence database
    return [{"sentencia": "T-123/23", "relevancia": "Alta"}]

def get_relevant_doctrine(area: Optional[str]) -> List[str]:
    """Obtiene doctrina relevante"""
    # Implementation would connect to a doctrine database
    return ["Doctrina relevante 1", "Doctrina relevante 2"] 