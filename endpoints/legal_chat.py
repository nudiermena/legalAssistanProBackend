from fastapi import APIRouter, HTTPException, Body, Depends, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from models.request_models import LegalChatbotRequest
from models.response_models import BaseResponse, format_response, handle_error
from agents.chatbot_agent import process_client_message, create_chatbot_agent
from config.colombian_compliance import ColombianLegalFramework
from pathlib import Path
from config.ai_models import get_model
from config.knowledge_base import get_knowledge_base
from config.cloudflare import CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID
from endpoints.autorag_chat import (
    process_autorag_request,
    stream_autorag_response,
    get_legal_disclaimer,
    get_colombian_compliance,
    process_autorag_ai_search
)
from endpoints.auth import get_current_user
import httpx
import json
import asyncio

router = APIRouter(prefix="/legal-chat", tags=["chat"])

class ChatRequest(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "client_id": "cliente123",
                "message": "¿Cuáles son mis derechos laborales?",
                "practice_area": "derecho_laboral",
                "legal_terms": ["contrato_trabajo", "prestaciones_sociales"],
                "instructions": "Instrucciones adicionales",
                "file_content": "Contenido de archivo adjunto"
            }
        }
    )

    client_id: str = Field(..., description="Identificador del cliente")
    message: str = Field(..., description="Mensaje del cliente")
    conversation_id: Optional[str] = Field(None, description="ID de conversación")
    practice_area: Optional[str] = Field(None, description="Área del derecho")
    legal_terms: Optional[List[str]] = Field(None, description="Términos jurídicos")
    data_processing: Optional[Dict[str, str]] = Field(None, description="Tratamiento de datos")
    instructions: Optional[str] = Field(None, description="Instrucciones adicionales para el agente")
    file_content: Optional[str] = Field(None, description="Contenido de archivo adjunto, si existe")

class ChatResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    response: Dict[str, Union[str, List[str], Dict[str, Any]]] = Field(
        ..., 
        description="Respuesta estructurada"
    )
    conversation_id: str = Field(..., description="ID de conversación")
    disclaimer: str = Field(..., description="Aviso legal")
    colombian_compliance: Dict[str, Any] = Field(..., description="Cumplimiento normativo colombiano")
    practice_area: Optional[str] = Field(None, description="Área del derecho")
    legal_terms: Optional[Dict[str, str]] = Field(None, description="Definiciones jurídicas")
    references: Optional[Dict[str, List[str]]] = Field(None, description="Referencias legales")
    conversation_history: Optional[List[Dict[str, Any]]] = Field(
        default=[],
        description="Historial de la conversación"
    )
    query_validation: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Resultado de la validación de consulta legal"
    )
    is_legal_query: Optional[bool] = Field(
        default=True,
        description="Indica si la consulta es de naturaleza legal"
    )
    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = {
        "json_schema_extra": {
            "example": {
                "response": {
                    "content": "De acuerdo a la legislación colombiana...",
                    "relevant_laws": ["Código Civil Colombiano", "Ley 820 de 2003"],
                    "recommendations": ["Consultar con un abogado especializado"]
                },
                "conversation_id": "conv_123",
                "disclaimer": "Esta información es general y no constituye asesoría legal...",
                "colombian_compliance": {
                    "version": "1.0",
                    "constitutional_principles": ["Debido proceso", "Buena fe"],
                    "data_protection": {
                        "law": "Ley 1581 de 2012",
                        "status": "Cumple"
                    }
                }
            }
        }
    }

class ChatV2Request(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "client_id": "cliente123",
                "message": "¿Cuáles son mis derechos laborales?",
                "practice_area": "derecho_laboral",
                "model": "@cf/meta/llama-3.1-8b-instruct-fast",
                "rewrite_query": False,
                "max_num_results": 10,
                "ranking_options": {
                    "score_threshold": 0.3
                },
                "stream": True,
                "legal_terms": ["contrato_trabajo", "prestaciones_sociales"],
                "instructions": "Instrucciones adicionales",
                "file_content": "Contenido de archivo adjunto"
            }
        }
    )

    client_id: str = Field(..., description="Identificador del cliente")
    message: str = Field(..., description="Mensaje del cliente")
    conversation_id: Optional[str] = Field(None, description="ID de conversación")
    practice_area: Optional[str] = Field(None, description="Área del derecho")
    model: Optional[str] = Field(
        default="@cf/meta/llama-3.1-8b-instruct-fast",
        description="Modelo a utilizar para la generación (debe ser un string con prefijo @)"
    )
    rewrite_query: Optional[bool] = Field(
        default=False,
        description="Si se debe reescribir la consulta para mejor búsqueda"
    )
    max_num_results: Optional[int] = Field(
        default=10,
        description="Número máximo de resultados"
    )
    ranking_options: Optional[Dict[str, float]] = Field(
        default={"score_threshold": 0.3},
        description="Opciones de ranking de resultados"
    )
    stream: Optional[bool] = Field(
        default=True,
        description="Si se debe transmitir la respuesta en tiempo real"
    )
    legal_terms: Optional[List[str]] = Field(None, description="Términos jurídicos")
    data_processing: Optional[Dict[str, str]] = Field(None, description="Tratamiento de datos")
    instructions: Optional[str] = Field(None, description="Instrucciones adicionales")
    file_content: Optional[str] = Field(None, description="Contenido de archivo adjunto")

class ChatV2Response(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    success: bool = Field(..., description="Whether the request was successful")
    result: Dict[str, Any] = Field(..., description="Search results", default_factory=lambda: {
        "object": "vector_store.search_results.page",
        "search_query": "",
        "response": "",
        "data": [],
        "has_more": False,
        "next_page": None
    })
    conversation_id: str = Field(..., description="ID de conversación")
    disclaimer: str = Field(..., description="Aviso legal")
    colombian_compliance: Dict[str, Any] = Field(..., description="Cumplimiento normativo")
    practice_area: Optional[str] = Field(None, description="Área del derecho")
    legal_terms: Optional[Dict[str, str]] = Field(None, description="Definiciones jurídicas")
    references: Optional[Dict[str, List[str]]] = Field(
        default_factory=lambda: {
            "normativa": [],
            "jurisprudencia": [],
            "doctrina": []
        },
        description="Referencias legales"
    )
    conversation_history: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list,
        description="Historial de la conversación"
    )
    query_validation: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Resultado de la validación de consulta legal"
    )
    is_legal_query: Optional[bool] = Field(
        default=True,
        description="Indica si la consulta es de naturaleza legal"
    )
    timestamp: datetime = Field(default_factory=datetime.now)

@router.post(
    "/consulta",
    response_model=ChatResponse,
    summary="Consulta Jurídica Virtual",
    description="""
    Proporciona orientación jurídica inicial basada en el ordenamiento jurídico
    colombiano, incluyendo referencias normativas y jurisprudenciales relevantes.
    """
)
async def chat_endpoint(
    request: ChatRequest = Body(
        ...,
        description="Parámetros de la consulta jurídica"
    ),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Procesa consultas jurídicas con cumplimiento normativo colombiano"""
    try:
        print(f"Received request: {request}")  # Debug log
        
        result = await process_client_message(
            client_id=request.client_id,
            message=request.message,
            conversation_id=request.conversation_id,
            practice_area=request.practice_area,
            legal_terms=request.legal_terms,
            data_processing=request.data_processing,
            instructions=request.instructions,
            file_content=request.file_content,
            user_id=current_user.get("user_id"),  # Use authenticated user's UUID
            session_id=request.conversation_id
        )
        
        print(f"Process result: {result}")  # Debug log
        
        # Don't overwrite the references, just ensure they exist
        if "references" not in result or not result["references"]:
            result["references"] = {
                "normativa": [],
                "jurisprudencia": [],
                "doctrina": []
            }
        
        # Update Colombian compliance details
        result["colombian_compliance"] = {
            "version": "1.0",
            "constitutional_principles": [
                "Debido proceso",
                "Buena fe",
                "Igualdad",
                "Libertad contractual",
                "Protección al consumidor"
            ],
            "data_protection": {
                "law": "Ley 1581 de 2012",
                "status": "Cumple",
                "requirements": [
                    "Autorización expresa",
                    "Finalidad específica",
                    "Tratamiento adecuado"
                ]
            },
            "legal_practice": {
                "decree": "Decreto 196 de 1971",
                "status": "Cumple"
            },
            "consultation_date": datetime.now().isoformat()
        }
        
        # Add standard disclaimer if not present
        if "disclaimer" not in result:
            result["disclaimer"] = get_legal_disclaimer()
        
        return ChatResponse(**result)
    
    except Exception as e:
        print(f"Error in chat_endpoint: {str(e)}")  # Debug log
        
        # Determine appropriate status code based on error type
        status_code = 500
        error_message = "Error en la consulta jurídica"
        
        # Check for specific error types
        error_str = str(e).lower()
        if "429" in error_str or "too many requests" in error_str or "rate limit" in error_str:
            status_code = 429
            error_message = "Límite de solicitudes excedido. Por favor, intente más tarde."
        elif "401" in error_str or "unauthorized" in error_str:
            status_code = 401
            error_message = "Error de autenticación"
        elif "403" in error_str or "forbidden" in error_str:
            status_code = 403
            error_message = "Acceso denegado"
        elif "timeout" in error_str or "timed out" in error_str:
            status_code = 408
            error_message = "Tiempo de espera agotado"
        elif "service tier capacity exceeded" in error_str:
            status_code = 503
            error_message = "Servicio temporalmente no disponible debido a alta demanda"
        
        raise HTTPException(
            status_code=status_code,
            detail={
                "error": str(e),
                "message": error_message,
                "timestamp": datetime.now().isoformat()
            }
        )

@router.get(
    "/areas-practica",
    response_model=Dict[str, List[str]],
    summary="Áreas de Práctica",
    description="Obtiene las áreas de práctica disponibles para consulta"
)
async def get_practice_areas(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Retorna las áreas de práctica disponibles"""
    return {
        "derecho_civil": [
            "Familia",
            "Contratos",
            "Responsabilidad"
        ],
        "derecho_laboral": [
            "Individual",
            "Colectivo",
            "Seguridad Social"
        ],
        "derecho_comercial": [
            "Sociedades",
            "Contratos Mercantiles",
            "Propiedad Industrial"
        ],
        "derecho_administrativo": [
            "Contratación Estatal",
            "Derecho Disciplinario",
            "Responsabilidad Estatal"
        ]
    }

def get_relevant_regulations(practice_area: Optional[str], ai_response: Any) -> List[str]:
    """Get relevant regulations based on AI analysis"""
    try:
        # Use AI to identify relevant regulations
        return ai_response.identified_regulations
    except:
        # Fallback to database if AI analysis fails
        return get_regulations_from_database(practice_area)

def get_relevant_cases(practice_area: Optional[str], ai_response: Any) -> List[str]:
    """Get relevant cases based on AI analysis"""
    try:
        # Use AI to identify relevant cases
        return ai_response.identified_cases
    except:
        # Fallback to database if AI analysis fails
        return get_cases_from_database(practice_area)

def get_relevant_doctrine(practice_area: Optional[str], ai_response: Any) -> List[str]:
    """Get relevant doctrine based on AI analysis"""
    try:
        # Use AI to identify relevant doctrine
        return ai_response.identified_doctrine
    except:
        # Fallback to database if AI analysis fails
        return get_doctrine_from_database(practice_area)

def get_regulations_from_database(practice_area: Optional[str]) -> List[str]:
    """Fallback function to get regulations from database"""
    # Implement database lookup here
    pass

def get_cases_from_database(practice_area: Optional[str]) -> List[str]:
    """Fallback function to get cases from database"""
    # Implement database lookup here
    pass

def get_doctrine_from_database(practice_area: Optional[str]) -> List[str]:
    """Fallback function to get doctrine from database"""
    # Implement database lookup here
    pass

# Add this new endpoint to serve the chat interface
@router.get("/", response_class=HTMLResponse)
async def get_chat_interface(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Serve the chat interface"""
    static_dir = Path("static")
    html_file = static_dir / "index.html"
    
    # Create the HTML file if it doesn't exist
    if not html_file.exists():
        html_content = """
<!DOCTYPE html>
<html lang="es">
<!-- Your HTML content from the previous response -->
</html>
"""
        html_file.write_text(html_content, encoding="utf-8")
    
    return HTMLResponse(content=html_file.read_text(encoding="utf-8"))

@router.post(
    "/v2/consulta",
    response_model=ChatV2Response,
    summary="Consulta Jurídica Virtual V2",
    description="""
    Proporciona orientación jurídica inicial basada en el ordenamiento jurídico
    colombiano utilizando AutoRAG para búsqueda vectorial y generación de respuestas
    contextuales precisas.
    """
)
async def chat_v2_endpoint(
    request: ChatV2Request = Body(
        ...,
        description="Parámetros de la consulta jurídica V2"
    ),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Procesa consultas jurídicas con AutoRAG y cumplimiento normativo colombiano"""
    try:
        print(f"Received V2 request: {request}")  # Debug log

        # Process AutoRAG request
        autorag_result = await process_autorag_ai_search(
            message=request.message,
            model=request.model,
            rewrite_query=request.rewrite_query,
            max_num_results=request.max_num_results,
            ranking_options=request.ranking_options
        )

        # Get current timestamp as ISO format string
        current_time = datetime.now().isoformat()

        # Extract relevant laws and recommendations from the search results
        relevant_laws = []
        recommendations = []
        content = autorag_result.get("result", {}).get("response", "")

        # Process search results to extract laws and recommendations
        if "data" in autorag_result.get("result", {}):
            for item in autorag_result["result"]["data"]:
                if "filename" in item:
                    # Add to relevant laws if it's a legal document
                    if any(term in item["filename"].lower() for term in ["ley", "código", "decreto", "constitución"]):
                        relevant_laws.append(item["filename"])
                    # Add to recommendations if it contains actionable advice
                    if "content" in item:
                        for content_item in item["content"]:
                            if "text" in content_item:
                                text = content_item["text"].lower()
                                if any(term in text for term in ["recomendamos", "se sugiere", "es importante", "debe", "debería"]):
                                    recommendations.append(content_item["text"][:200])  # Limit length

        # Format the response like V1
        processed_result = {
            "response": {
                "content": content,
                "relevant_laws": relevant_laws,
                "recommendations": recommendations
            },
            "conversation_id": request.conversation_id or f"conv_{request.client_id}_{int(datetime.now().timestamp())}",
            "disclaimer": get_legal_disclaimer(),
            "colombian_compliance": get_colombian_compliance(),
            "practice_area": request.practice_area,
            "legal_terms": {term: "" for term in (request.legal_terms or [])},
            "references": {
                "normativa": [],
                "jurisprudencia": [],
                "doctrina": []
            },
            "conversation_history": [],
            "timestamp": current_time
        }

        # Add references from search results if available
        if "data" in autorag_result.get("result", {}):
            for item in autorag_result["result"]["data"]:
                if "filename" in item:
                    if "normativa" in item["filename"].lower():
                        processed_result["references"]["normativa"].append(item["filename"])
                    elif "jurisprudencia" in item["filename"].lower():
                        processed_result["references"]["jurisprudencia"].append(item["filename"])
                    elif "doctrina" in item["filename"].lower():
                        processed_result["references"]["doctrina"].append(item["filename"])

        return ChatV2Response(
            success=True,
            result=autorag_result.get("result", {}),
            **processed_result
        )

    except Exception as e:
        print(f"Error in chat_v2_endpoint: {str(e)}")  # Debug log
        error_time = datetime.now().isoformat()
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "message": "Error en la consulta jurídica V2",
                "timestamp": error_time
            }
        ) 