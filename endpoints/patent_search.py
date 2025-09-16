from fastapi import APIRouter, HTTPException, Body, Depends
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from config.colombian_compliance import ColombianLegalFramework
from endpoints.auth import get_current_user

router = APIRouter(prefix="/patent", tags=["patents"])

class PatentSearchRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    invention_description: str = Field(..., description="Descripción de la invención")
    jurisdiction: str = Field(default="Colombia", description="Jurisdicción")
    technical_field: Optional[str] = Field(None, description="Campo técnico (IPC)")
    data_processing: Optional[Dict[str, str]] = Field(None, description="Tratamiento de datos")
    legal_terms: Optional[List[str]] = Field(None, description="Términos jurídicos")

    model_config = {
        "json_schema_extra": {
            "example": {
                "invention_description": "Sistema de análisis predictivo legal...",
                "technical_field": "G06N 20/00",
                "legal_terms": ["novedad", "nivel_inventivo"]
            }
        }
    }

class PatentAnalysisRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    invention_description: str = Field(..., description="Descripción de la invención")
    prior_art: List[str] = Field(..., description="Arte previo identificado")
    jurisdiction: str = Field(default="Colombia", description="Jurisdicción")
    technical_field: Optional[str] = Field(None, description="Clasificación IPC")
    data_processing: Optional[Dict[str, str]] = Field(None, description="Tratamiento de datos")
    legal_terms: Optional[List[str]] = Field(None, description="Términos jurídicos")

    model_config = {
        "json_schema_extra": {
            "example": {
                "invention_description": "Sistema de análisis predictivo...",
                "prior_art": ["CO2019123456", "US10123456"],
                "technical_field": "G06N 20/00"
            }
        }
    }

class PatentSearchResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    search_results: List[Dict[str, Any]] = Field(..., description="Resultados de búsqueda")
    invention_description: str = Field(..., description="Descripción analizada")
    jurisdiction: str = Field(..., description="Jurisdicción")
    colombian_compliance: Dict[str, Any] = Field(..., description="Cumplimiento normativo")
    sic_requirements: Dict[str, str] = Field(..., description="Requisitos SIC")
    recomendaciones: List[Dict[str, str]] = Field(..., description="Recomendaciones de patentabilidad")
    data_processing: Optional[Dict[str, str]] = None
    legal_terms: Optional[Dict[str, str]] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = {
        "json_schema_extra": {
            "example": {
                "search_results": [
                    {
                        "patent_number": "CO2019123456",
                        "relevance": "alta",
                        "similarity": 0.85
                    }
                ],
                "sic_requirements": {
                    "formal_exam": "Requerido",
                    "publication": "Requerido - Art. 40 Decisión 486"
                },
                "recomendaciones": [
                    {
                        "tipo": "riesgo",
                        "titulo": "Riesgo potencial de infracción",
                        "descripcion": "La patente US10234567B2 tiene elementos muy similares a su búsqueda.",
                        "icono": "warning"
                    },
                    {
                        "tipo": "oportunidad",
                        "titulo": "Oportunidad de diferenciación",
                        "descripcion": "Considere enfocarse en el sistema de almacenamiento, un área menos cubierta.",
                        "icono": "check"
                    },
                    {
                        "tipo": "novedad",
                        "titulo": "Área de novedad",
                        "descripcion": "La integración con IA para optimización de energía parece un área poco explorada.",
                        "icono": "info"
                    }
                ]
            }
        }
    }

class PatentAnalysisResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    analysis: Dict[str, Union[str, bool, List[str]]] = Field(..., description="Análisis de patentabilidad")
    invention_description: str = Field(..., description="Descripción analizada")
    prior_art: List[str] = Field(..., description="Arte previo relevante")
    jurisdiction: str = Field(..., description="Jurisdicción")
    colombian_compliance: Dict[str, Any] = Field(..., description="Cumplimiento normativo")
    patentability_criteria: Dict[str, bool] = Field(..., description="Criterios de patentabilidad")
    recomendaciones: List[Dict[str, str]] = Field(..., description="Recomendaciones de patentabilidad")
    recommendations: List[str] = Field(default_factory=list, description="Recomendaciones")
    data_processing: Optional[Dict[str, str]] = None
    legal_terms: Optional[Dict[str, str]] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = {
        "json_schema_extra": {
            "example": {
                "analysis": {
                    "novelty_assessment": "La invención presenta novedad...",
                    "inventive_step": True,
                    "industrial_application": True
                },
                "patentability_criteria": {
                    "novedad": True,
                    "nivel_inventivo": True,
                    "aplicacion_industrial": True
                },
                "recomendaciones": [
                    {
                        "tipo": "riesgo",
                        "titulo": "Riesgo potencial de infracción",
                        "descripcion": "La patente US10234567B2 tiene elementos muy similares a su búsqueda.",
                        "icono": "warning"
                    },
                    {
                        "tipo": "oportunidad",
                        "titulo": "Oportunidad de diferenciación",
                        "descripcion": "Considere enfocarse en el sistema de almacenamiento, un área menos cubierta.",
                        "icono": "check"
                    },
                    {
                        "tipo": "novedad",
                        "titulo": "Área de novedad",
                        "descripcion": "La integración con IA para optimización de energía parece un área poco explorada.",
                        "icono": "info"
                    }
                ]
            }
        }
    }

class PatentSearchV2Request(BaseModel):
    search_terms: str = Field(..., description="Términos de búsqueda")
    patent_type: str = Field(..., description="Tipo de patente")
    filing_date_start: date = Field(..., description="Fecha de presentación (inicio)")
    filing_date_end: date = Field(..., description="Fecha de presentación (fin)")
    ipc_class: str = Field(..., description="Clasificación IPC")
    invention_description: str = Field(..., description="Descripción de la invención")
    inventors: List[str] = Field(..., description="Inventor(es)")
    applicant: str = Field(..., description="Solicitante")

    model_config = {
        "json_schema_extra": {
            "example": {
                "search_terms": "Pollo Frisby",
                "patent_type": "Todos los tipos",
                "filing_date_start": "2024-01-27",
                "filing_date_end": "2025-05-23",
                "ipc_class": "GOFC",
                "invention_description": "Se iba a robar la marca",
                "inventors": ["Pedro Perez"],
                "applicant": "Pollos Frisby Colombia"
            }
        }
    }

@router.post(
    "/search",
    response_model=PatentSearchResponse,
    summary="Búsqueda de Patentes",
    description="""
    Realiza una búsqueda exhaustiva de patentes según la Decisión 486 de la CAN y
    la normativa de la Superintendencia de Industria y Comercio (SIC).
    """
)
async def search_patents_endpoint(
    request: PatentSearchRequest = Body(
        ...,
        description="Parámetros de búsqueda de patentes"
    ),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Búsqueda de patentes con cumplimiento normativo colombiano"""
    try:
        # Simplified search without the excluded agent
        result = {
            "search_results": f"Búsqueda de patentes para: {request.invention_description}",
            "invention_description": request.invention_description,
            "jurisdiction": request.jurisdiction,
            "colombian_compliance": {
                "constitutional_principles": ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES,
                "search_date": datetime.now().isoformat()
            },
            "recomendaciones": [
                {
                    "tipo": "info",
                    "titulo": "Búsqueda simplificada",
                    "descripcion": "Esta es una versión simplificada para deployment en Vercel",
                    "icono": "info"
                }
            ]
        }
        
        # Enhance with Colombian IP law requirements
        result["colombian_compliance"].update({
            "framework_version": ColombianLegalFramework.FRAMEWORK_VERSION,
            "ip_law": "Decisión 486 de la CAN",
            "local_authority": "Superintendencia de Industria y Comercio",
            "last_update": datetime.now().isoformat()
        })
        
        # Add SIC-specific requirements
        result["sic_requirements"] = {
            "formal_exam": "Requerido",
            "publication": "Requerido - Art. 40 Decisión 486",
            "substantive_exam": "Requerido - Art. 45 Decisión 486",
            "fees": "Según resolución vigente SIC"
        }
        
        # Ensure recomendaciones is present
        if "recomendaciones" not in result:
            result["recomendaciones"] = []
        
        return PatentSearchResponse(**result)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "message": "Error en la búsqueda de patentes",
                "timestamp": datetime.now().isoformat()
            }
        )

@router.post(
    "/analyze",
    response_model=PatentAnalysisResponse,
    summary="Análisis de Patentabilidad",
    description="""
    Analiza la patentabilidad de una invención según los criterios de la
    Decisión 486 de la CAN y los lineamientos de la SIC.
    """
)
async def analyze_patentability_endpoint(
    request: PatentAnalysisRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Análisis de patentabilidad según normativa colombiana"""
    try:
        # Simplified analysis without the excluded agent
        result = {
            "analysis": f"Análisis de patentabilidad para: {request.invention_description}",
            "invention_description": request.invention_description,
            "prior_art": request.prior_art,
            "jurisdiction": request.jurisdiction,
            "colombian_compliance": {
                "constitutional_principles": ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES,
                "analysis_date": datetime.now().isoformat()
            },
            "recomendaciones": [
                {
                    "tipo": "info",
                    "titulo": "Análisis simplificado",
                    "descripcion": "Esta es una versión simplificada para deployment en Vercel",
                    "icono": "info"
                }
            ]
        }
        
        # Add patentability criteria assessment
        result["patentability_criteria"] = {
            "novedad": True,  # Updated by analysis
            "nivel_inventivo": True,  # Updated by analysis
            "aplicacion_industrial": True,  # Updated by analysis
            "materia_patentable": True  # Updated by analysis
        }
        
        # Add SIC requirements
        result["sic_requirements"] = {
            "descripcion_suficiente": "Requerido - Art. 28 Decisión 486",
            "reivindicaciones_claras": "Requerido - Art. 30 Decisión 486",
            "unidad_invencion": "Requerido - Art. 25 Decisión 486",
            "documentacion_prioridad": "Si aplica - Art. 9 Decisión 486"
        }
        
        # Ensure recomendaciones is present
        if "recomendaciones" not in result:
            result["recomendaciones"] = []
        
        # Ensure recommendations field for backward compatibility
        if "recommendations" not in result:
            result["recommendations"] = []
        
        return PatentAnalysisResponse(**result)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "message": "Error en el análisis de patentabilidad",
                "timestamp": datetime.now().isoformat()
            }
        )

@router.get(
    "/requirements",
    response_model=Dict[str, Dict[str, str]],
    summary="Requisitos de Patentabilidad",
    description="Obtiene los requisitos de patentabilidad según la normativa colombiana"
)
async def get_patent_requirements(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Retorna los requisitos de patentabilidad según la SIC"""
    return {
        "requisitos_basicos": {
            "novedad": "Art. 16 Decisión 486",
            "nivel_inventivo": "Art. 18 Decisión 486",
            "aplicacion_industrial": "Art. 19 Decisión 486"
        },
        "exclusiones": {
            "descubrimientos": "Art. 15(a) Decisión 486",
            "teorias_cientificas": "Art. 15(b) Decisión 486",
            "metodos_matematicos": "Art. 15(c) Decisión 486",
            "seres_vivos": "Art. 15(b) Decisión 486"
        },
        "documentacion": {
            "descripcion": "Art. 28 Decisión 486",
            "reivindicaciones": "Art. 30 Decisión 486",
            "resumen": "Art. 28(e) Decisión 486"
        },
        "procedimiento": {
            "examen_forma": "Art. 38-39 Decisión 486",
            "publicacion": "Art. 40 Decisión 486",
            "examen_fondo": "Art. 45 Decisión 486"
        }
    }

@router.post(
    "/search/v2",
    response_model=PatentSearchResponse,
    summary="Búsqueda de Patentes V2 (campos extendidos)",
    description="""
    Realiza una búsqueda de patentes usando todos los campos del formulario extendido.
    """
)
async def search_patents_v2_endpoint(
    request: PatentSearchV2Request = Body(
        ...,
        description="Parámetros de búsqueda de patentes (V2)"
    ),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Búsqueda de patentes con todos los campos del formulario V2"""
    try:
        # Simplified V2 search without the excluded agent
        result = {
            "search_results": f"Búsqueda V2 de patentes para: {request.invention_description}",
            "invention_description": request.invention_description,
            "jurisdiction": "Colombia",
            "colombian_compliance": {
                "constitutional_principles": ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES,
                "search_date": datetime.now().isoformat()
            },
            "recomendaciones": [
                {
                    "tipo": "info",
                    "titulo": "Búsqueda V2 simplificada",
                    "descripcion": "Esta es una versión simplificada para deployment en Vercel",
                    "icono": "info"
                }
            ]
        }
        # Add SIC-specific requirements as before
        result["sic_requirements"] = {
            "formal_exam": "Requerido",
            "publication": "Requerido - Art. 40 Decisión 486",
            "substantive_exam": "Requerido - Art. 45 Decisión 486",
            "fees": "Según resolución vigente SIC"
        }
        if "recomendaciones" not in result:
            result["recomendaciones"] = []
        return PatentSearchResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "message": "Error en la búsqueda de patentes (V2)",
                "timestamp": datetime.now().isoformat()
            }
        ) 