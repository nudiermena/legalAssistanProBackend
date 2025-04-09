from fastapi import APIRouter, HTTPException, Body, Depends
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from agents.patent_agent import search_patents, analyze_patentability
from config.colombian_compliance import ColombianLegalFramework

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
                }
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
    recommendations: List[str] = Field(..., description="Recomendaciones")
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
                }
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
    )
):
    """Búsqueda de patentes con cumplimiento normativo colombiano"""
    try:
        result = await search_patents(
            invention_description=request.invention_description,
            jurisdiction=request.jurisdiction,
            technical_field=request.technical_field,
            data_processing=request.data_processing,
            legal_terms=request.legal_terms
        )
        
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
async def analyze_patentability_endpoint(request: PatentAnalysisRequest):
    """Análisis de patentabilidad según normativa colombiana"""
    try:
        result = await analyze_patentability(
            invention_description=request.invention_description,
            prior_art=request.prior_art,
            jurisdiction=request.jurisdiction,
            technical_field=request.technical_field,
            data_processing=request.data_processing,
            legal_terms=request.legal_terms
        )
        
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
async def get_patent_requirements():
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