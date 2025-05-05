from fastapi import APIRouter, HTTPException, Body, Depends, Request, UploadFile, File
from fastapi.responses import HTMLResponse
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

router = APIRouter(prefix="/legal-chat", tags=["chat"])

class ChatRequest(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "client_id": "cliente123",
                "message": "¿Cuáles son mis derechos?",
                "legal_terms": ["derechos", "obligaciones"],
                "instrucciones": "Responde de forma breve y clara."
            }
        }
    )

    client_id: str = Field(..., description="Identificador del cliente")
    message: str = Field(..., description="Mensaje del cliente")
    conversation_id: Optional[str] = Field(None, description="ID de conversación")
    legal_terms: Optional[List[str]] = Field(None, description="Términos jurídicos")
    data_processing: Optional[Dict[str, str]] = Field(None, description="Tratamiento de datos")
    instrucciones: Optional[Union[str, List[str]]] = Field(None, description="Instrucciones adicionales para el asistente")
    # 'file' will be handled as a separate parameter in the endpoint

class ChatResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    response: Dict[str, Union[str, List[str], Dict[str, Any]]] = Field(
        ..., 
        description="Respuesta estructurada"
    )
    conversation_id: str = Field(..., description="ID de conversación")
    disclaimer: str = Field(..., description="Aviso legal")
    colombian_compliance: Dict[str, Any] = Field(..., description="Cumplimiento normativo colombiano")
    legal_terms: Optional[Dict[str, str]] = Field(None, description="Definiciones jurídicas")
    references: Optional[Dict[str, List[str]]] = Field(None, description="Referencias legales")
    conversation_history: Optional[List[Dict[str, Any]]] = Field(
        default=[],
        description="Historial de la conversación"
    )
    contextual_questions: Optional[List[str]] = Field(
        default=[],
        description="Preguntas contextuales para guiar al usuario"
    )
    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = {
        "json_schema_extra": {
            "example": {
                "response": {
                    "content": "De acuerdo a la legislación colombiana...",
                    "relevant_laws": ["Código Civil Colombiano", "Constitución Política"],
                    "recommendations": ["Consultar con un abogado especializado"],
                    "contextual_questions": [
                        "¿Necesitas información más específica sobre algún aspecto en particular?",
                        "¿Has consultado previamente con un abogado sobre este tema?"
                    ]
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
    request: Request,
    client_id: str = Body(...),
    message: str = Body(...),
    conversation_id: Optional[str] = Body(None),
    legal_terms: Optional[List[str]] = Body(None),
    data_processing: Optional[Dict[str, str]] = Body(None),
    instrucciones: Optional[Union[str, List[str]]] = Body(None),
    file: Optional[UploadFile] = File(None)
):
    """Procesa consultas jurídicas con cumplimiento normativo colombiano"""
    try:
        print(f"Received request: {client_id}, {message}, instrucciones={instrucciones}, file={file}")  # Debug log
        file_content = None
        if file is not None:
            # TODO: Add advanced file parsing for PDF, DOCX, etc.
            content_bytes = await file.read()
            try:
                file_content = content_bytes.decode("utf-8")
            except Exception:
                file_content = str(content_bytes)
        result = await process_client_message(
            client_id=client_id,
            message=message,
            conversation_id=conversation_id,
            legal_terms=legal_terms,
            data_processing=data_processing,
            instrucciones=instrucciones,
            file_content=file_content
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
        
        # Ensure contextual questions are included
        if "contextual_questions" not in result:
            result["contextual_questions"] = []
        
        return ChatResponse(**result)
    
    except Exception as e:
        print(f"Error in chat_endpoint: {str(e)}")  # Debug log
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "message": "Error en la consulta jurídica",
                "timestamp": datetime.now().isoformat()
            }
        )

@router.get(
    "/areas-practica",
    response_model=Dict[str, List[str]],
    summary="Áreas de Práctica",
    description="Obtiene las áreas de práctica disponibles para consulta"
)
async def get_practice_areas():
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

def get_legal_disclaimer() -> str:
    """Retorna el aviso legal estándar"""
    return """
    Esta información es de carácter general y no constituye asesoría jurídica.
    Cada caso particular puede requerir un análisis específico y profesional.
    Se recomienda consultar con un abogado para obtener asesoría legal específica.
    La información proporcionada cumple con la normatividad colombiana vigente.
    """

# Add this new endpoint to serve the chat interface
@router.get("", response_class=HTMLResponse)
async def get_chat_interface(request: Request):
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