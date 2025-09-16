from fastapi import APIRouter, HTTPException, Body, Depends, Request
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from agents.case_prediction_agent import (
    predict_case_outcome,
    analyze_relevant_laws,
    analyze_similar_cases_from_altas_cortes,
    create_case_prediction_agent
)
from frameworks.colombian_legal_framework import ColombianLegalFramework
from endpoints.auth import get_current_user
import os
import json
from models.case_prediction import CasePredictionRequest

router = APIRouter(prefix="/dashboard/case-prediction", tags=["case_prediction"])

# Removed HTML case prediction page route
        
class CasePredictionResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    prediction: Dict[str, Union[str, float, List[str]]] = Field(..., description="Predicción del caso")
    case_type: str = Field(..., description="Tipo de proceso")
    jurisdiction: str = Field(..., description="Jurisdicción")
    key_factors: List[str] = Field(..., description="Factores clave")
    colombian_compliance: Dict[str, Any] = Field(..., description="Cumplimiento normativo")
    success_probability: float = Field(..., description="Probabilidad de éxito")
    judge_analysis: Optional[Dict[str, Any]] = Field(None, description="Análisis del juez")
    opposing_counsel: Optional[str] = Field(None, description="Contraparte")
    relevant_precedents: Optional[List[str]] = Field(None, description="Precedentes")
    legal_terms: Optional[Dict[str, str]] = Field(None, description="Términos jurídicos")
    administrative_procedure: Optional[Dict[str, str]] = Field(None, description="Procedimiento")
    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = {
        "json_schema_extra": {
            "example": {
                "prediction": {
                    "outcome": "favorable",
                    "probability": 0.75,
                    "key_factors": ["Antigüedad del empleado", "Falta de justa causa"]
                }
            }
        }
    }

def _calculate_procedural_risk(risk_factors: List[Dict]) -> str:
    """Calculate procedural risk level based on risk factors"""
    procedural_risks = [r for r in risk_factors if "procedural" in r["factor"].lower()]
    if not procedural_risks:
        return "Medio"
    
    high_risks = sum(1 for r in procedural_risks if r["risk_level"] == "alto")
    if high_risks > len(procedural_risks) / 2:
        return "Alto"
    return "Medio"

def _calculate_financial_risk(risk_factors: List[Dict]) -> str:
    """Calculate financial risk level based on risk factors"""
    financial_risks = [r for r in risk_factors if "financial" in r["factor"].lower()]
    if not financial_risks:
        return "Medio"
    
    high_risks = sum(1 for r in financial_risks if r["risk_level"] == "alto")
    if high_risks > len(financial_risks) / 2:
        return "Alto"
    return "Medio"

def _risk_level_to_percentage(risk_level: str) -> int:
    """Convert risk level to percentage for UI display"""
    risk_percentages = {
        "bajo": 25,
        "medio": 50,
        "alto": 75,
        "crítico": 90
    }
    return risk_percentages.get(risk_level.lower(), 50)

@router.post("/analyze")
async def analyze_case(
    request: CasePredictionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Analyze case endpoint"""
    try:
        # Validate case type
        if not ColombianLegalFramework.validate_case_type(request.case_type):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid case type",
                    "message": "El tipo de caso no es válido",
                    "timestamp": datetime.now().isoformat()
                }
            )

        # Only validate administrative procedure if it's provided and not empty
        if (request.administrative_procedure and 
            request.administrative_procedure != "" and 
            not ColombianLegalFramework.validate_administrative_procedure(request.administrative_procedure)):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid administrative procedure",
                    "message": "El procedimiento administrativo no es válido",
                    "timestamp": datetime.now().isoformat()
                }
            )

        # Create agent and process prediction
        agent = create_case_prediction_agent()
        prediction_result = await agent.predict_case(request)
        
        # Get case outcome prediction
        detailed_outcome = await predict_case_outcome(
            case_type=request.case_type,
            jurisdiction=request.jurisdiction,
            key_facts=request.key_facts,
            legal_issues=request.legal_issues,
            judge_name=request.judge_name,
            opposing_counsel=request.opposing_counsel,
            relevant_precedents=request.relevant_precedents,
            administrative_procedure=request.administrative_procedure,
            legal_terms=request.legal_terms
        )

        # Get relevant precedents with a limit of 3
        precedents = detailed_outcome.get("relevant_precedents", [{"description": "Resolución favorable"}])
        if len(precedents) > 3:
            precedents = precedents[:3]

        # Structure the response to match UI expectations
        response = {
            "prediction": {
                "probability_of_success": float(prediction_result["probability_of_success"]),
                "estimated_duration": {
                    "months": prediction_result["estimated_duration"]["min_months"],
                    "display": f"{prediction_result['estimated_duration']['min_months']} - {prediction_result['estimated_duration']['max_months']} meses"
                },
                "risk_level": "Medio",
                "estimated_value": "$50K",
            },
            "key_factors": [
                {
                    "factor": fact,
                    "importance": "Alto",
                    "percentage": 85
                } for fact in request.key_facts
            ],
            "strategic_recommendations": [
                {
                    "title": rec,
                    "priority": "high" if i < 2 else "medium",
                    "status": "pending",
                    "description": "Recomendación estratégica basada en el análisis del caso."
                } for i, rec in enumerate(prediction_result["key_recommendations"])
            ],
            "risk_assessment": {
                "Riesgo Procesal": _calculate_procedural_risk(prediction_result["risk_factors"]),
                "Riesgo Financiero": _calculate_financial_risk(prediction_result["risk_factors"])
            },
            "similar_cases": [
                {
                    "title": f"Caso #{datetime.now().year}-{100 + i}",
                    "summary": precedent["description"] if isinstance(precedent, dict) else str(precedent),
                    "similarity": str(85 - (i * 13)),
                    "outcome": "success" if i == 0 else "warning"
                } for i, precedent in enumerate(precedents)
            ],
            "case_type": ColombianLegalFramework.get_case_type_name(request.case_type),
            "jurisdiction": request.jurisdiction,
            "success_probability": round(float(prediction_result["probability_of_success"]) * 100),
            "timestamp": datetime.now().isoformat()
        }

        # Add strategy section
        strategy = prediction_result["suggested_strategy"]
        response["strategy"] = {
            "primary": strategy["primary_strategy"],
            "alternatives": strategy["alternative_strategies"],
            "actions": strategy["key_actions"],
            "priority": strategy["priority_level"],
            "timeline": strategy["timeline"]
        }

        # Add risk factors with proper formatting
        response["risk_factors"] = [
            {
                "name": risk["factor"],
                "level": risk["risk_level"],
                "description": risk["description"],
                "percentage": _risk_level_to_percentage(risk["risk_level"])
            }
            for risk in prediction_result["risk_factors"]
        ]

        return response

    except Exception as e:
        # Add debug information to the error
        error_detail = f"{str(e)}\nPrediction result: {prediction_result if 'prediction_result' in locals() else 'Not available'}"
        raise HTTPException(
            status_code=500,
            detail={
                "error": error_detail,
                "message": "Error en la predicción del caso",
                "timestamp": datetime.now().isoformat()
            }
        )

@router.get(
    "/case-types",
    response_model=Dict[str, List[str]],
    summary="Tipos de Procesos",
    description="Obtiene los tipos de procesos disponibles para análisis"
)
async def get_case_types(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Retorna los tipos de procesos disponibles"""
    return {
        "procesos_ordinarios": [
            "Civil ordinario",
            "Laboral ordinario",
            "Administrativo ordinario"
        ],
        "acciones_constitucionales": [
            "Tutela",
            "Popular",
            "Cumplimiento"
        ],
        "procesos_ejecutivos": [
            "Singular",
            "Hipotecario",
            "Prendario"
        ],
        "procedimientos_especiales": [
            "Verbal sumario",
            "Monitorio",
            "Divisorio"
        ]
    }

def calculate_success_probability(
    case_type: str,
    key_facts: List[str],
    legal_issues: List[str]
) -> float:
    """Calcula probabilidad de éxito del caso"""
    # Implementation would connect to a prediction model
    return 0.75

@router.post("/analyze-laws")
async def analyze_laws(
    request: CasePredictionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Analyze laws endpoint"""
    try:
        agent = create_case_prediction_agent()
        analysis = await analyze_relevant_laws(agent, request.dict())
        
        return JSONResponse(content={
            "status": "success",
            "data": json.loads(analysis) if isinstance(analysis, str) else analysis,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "message": "Error al analizar leyes relevantes",
                "timestamp": datetime.now().isoformat()
            }
        )

@router.post("/analyze-similar-cases")
async def analyze_similar_cases(
    request: CasePredictionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Analyze similar cases endpoint"""
    try:
        agent = create_case_prediction_agent()
        analysis = await analyze_similar_cases_from_altas_cortes(agent, request.dict())
        
        return JSONResponse(content={
            "status": "success",
            "data": json.loads(analysis) if isinstance(analysis, str) else analysis,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "message": "Error al analizar casos similares",
                "timestamp": datetime.now().isoformat()
            }
        )

@router.post("/debug")
async def debug_request(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Debug endpoint to check incoming request data"""
    body = await request.json()
    return JSONResponse({
        "received_data": body,
        "validation_errors": None  # Add validation logic here if needed
    }) 