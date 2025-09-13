from fastapi import APIRouter, HTTPException, Body, Depends
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from agents.demand_letter_agent import draft_demand_letter
from config.colombian_compliance import ColombianLegalFramework
from endpoints.auth import get_current_user

router = APIRouter(prefix="/demand-letter", tags=["demands"])

class DemandLetterRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    situation_description: str = Field(..., description="Descripción de la situación")
    jurisdiction: str = Field(default="Colombia", description="Jurisdicción")
    legal_basis: List[str] = Field(..., description="Fundamentos jurídicos")
    requested_actions: List[str] = Field(..., description="Pretensiones")
    deadline: Optional[str] = Field(None, description="Plazo")
    parties: List[Dict[str, str]] = Field(..., description="Partes involucradas")
    administrative_procedure: Optional[str] = Field(None, description="Procedimiento")
    legal_terms: Optional[List[str]] = Field(None, description="Términos jurídicos")
    data_processing: Optional[Dict[str, str]] = Field(None, description="Tratamiento de datos")

    model_config = {
        "json_schema_extra": {
            "example": {
                "situation_description": "Incumplimiento contractual...",
                "legal_basis": ["Art. 1546 Código Civil"],
                "requested_actions": ["Cumplimiento del contrato"]
            }
        }
    }

class DemandLetterResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    letter: Dict[str, Union[str, List[str]]] = Field(..., description="Carta generada")
    situation_description: str = Field(..., description="Situación")
    jurisdiction: str = Field(..., description="Jurisdicción")
    legal_basis: List[str] = Field(..., description="Fundamentos")
    requested_actions: List[str] = Field(..., description="Pretensiones")
    deadline: Optional[str] = Field(None, description="Plazo")
    parties: List[Dict[str, str]] = Field(..., description="Partes")
    colombian_compliance: Dict[str, Any] = Field(..., description="Cumplimiento")
    administrative_procedure: Optional[Dict[str, str]] = None
    legal_terms: Optional[Dict[str, str]] = None
    data_processing: Optional[Dict[str, str]] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = {
        "json_schema_extra": {
            "example": {
                "letter": {
                    "content": "Mediante la presente...",
                    "sections": ["Hechos", "Pretensiones"]
                }
            }
        }
    }

@router.post(
    "/generate",
    response_model=DemandLetterResponse,
    summary="Generación de Carta de Reclamación",
    description="""
    Genera cartas de reclamación formales según el ordenamiento jurídico
    colombiano, incluyendo requisitos legales específicos y cumplimiento normativo.
    """
)
async def draft_demand_letter_endpoint(
    request: DemandLetterRequest = Body(
        ...,
        description="Parámetros para la generación de la carta"
    ),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Genera carta de reclamación con cumplimiento normativo colombiano"""
    try:
        result = await draft_demand_letter(
            situation_description=request.situation_description,
            jurisdiction=request.jurisdiction,
            legal_basis=request.legal_basis,
            requested_actions=request.requested_actions,
            deadline=request.deadline,
            parties=request.parties,
            administrative_procedure=request.administrative_procedure,
            legal_terms=request.legal_terms,
            data_processing=request.data_processing
        )
        
        # Add Colombian compliance details
        result["colombian_compliance"].update({
            "framework_version": ColombianLegalFramework.FRAMEWORK_VERSION,
            "constitutional_principles": ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES,
            "letter_date": datetime.now().isoformat(),
            "validation_status": "Verificado"
        })
        
        # Add administrative procedure details if applicable
        if request.administrative_procedure:
            result["administrative_procedure"] = get_administrative_procedure(
                request.administrative_procedure
            )
        
        return DemandLetterResponse(**result)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "message": "Error en la generación de la carta",
                "timestamp": datetime.now().isoformat()
            }
        )

@router.get(
    "/templates",
    response_model=Dict[str, List[str]],
    summary="Plantillas Disponibles",
    description="Obtiene las plantillas de cartas de reclamación disponibles"
)
async def get_demand_letter_templates(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Retorna las plantillas de cartas disponibles"""
    return {
        "derecho_civil": [
            "Incumplimiento contractual",
            "Responsabilidad civil",
            "Reclamación de perjuicios"
        ],
        "derecho_comercial": [
            "Cobro de facturas",
            "Incumplimiento mercantil",
            "Competencia desleal"
        ],
        "derecho_administrativo": [
            "Derecho de petición",
            "Recurso de reposición",
            "Recurso de apelación"
        ],
        "derecho_laboral": [
            "Acoso laboral",
            "Despido injusto",
            "Prestaciones sociales"
        ]
    }

def get_administrative_procedure(procedure_type: str) -> Dict[str, str]:
    """Obtiene detalles del procedimiento administrativo"""
    procedures = {
        "derecho_peticion": {
            "termino_respuesta": "15 días hábiles",
            "fundamento_legal": "Art. 14 Ley 1437 de 2011",
            "recurso_procedente": "Insistencia",
            "autoridad_competente": "Misma autoridad"
        },
        "recurso_reposicion": {
            "termino_respuesta": "2 meses",
            "fundamento_legal": "Art. 76 Ley 1437 de 2011",
            "recurso_procedente": "Apelación",
            "autoridad_competente": "Mismo funcionario"
        }
    }
    return procedures.get(procedure_type, {}) 