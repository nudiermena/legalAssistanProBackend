from fastapi import APIRouter, HTTPException, Body, Depends, Request
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict, Any, Union, AsyncGenerator
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import httpx
import json
import asyncio
from config.cloudflare import CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_API_TOKEN_CHATBOT
import re

router = APIRouter(prefix="/autorag", tags=["autorag"])

class AutoRagRequest(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "query": "¿Cuáles son mis derechos laborales?",
                "model": "@cf/meta/llama-3.1-8b-instruct-fast",
                "rewrite_query": False,
                "max_num_results": 10,
                "ranking_options": {
                    "score_threshold": 0.3
                },
                "stream": False
            }
        }
    )

    query: str = Field(..., description="Query to search")
    model: Optional[str] = Field(
        default="@cf/meta/llama-3.1-8b-instruct-fast",
        description="Model to use for generation (must be a string with @ prefix)"
    )
    rewrite_query: Optional[bool] = Field(
        default=False,
        description="Whether to rewrite the query for better search"
    )
    max_num_results: Optional[int] = Field(
        default=10,
        description="Maximum number of results to return"
    )
    ranking_options: Optional[Dict[str, float]] = Field(
        default={"score_threshold": 0.3},
        description="Options for ranking results"
    )
    stream: Optional[bool] = Field(
        default=True,
        description="Whether to stream the response"
    )

class AutoRagResponse(BaseModel):
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

def clean_text(text: str) -> str:
    """Clean and format the text with proper spacing and formatting"""
    try:
        # Ensure text is string
        if not isinstance(text, str):
            text = str(text)
            
        # Remove any null bytes
        text = text.replace('\x00', '')
        
        # Fix common encoding issues with special characters
        text = text.replace('í', 'í').replace('ó', 'ó').replace('ú', 'ú')
        text = text.replace('á', 'á').replace('é', 'é').replace('ñ', 'ñ')
        text = text.replace('ü', 'ü').replace('¿', '¿').replace('¡', '¡')
        
        # Add spaces between words that are incorrectly joined
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Add space between camelCase
        text = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', text)  # Add space between letter and number
        text = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', text)  # Add space between number and letter
        
        # Fix specific cases where words are incorrectly joined
        common_fixes = {
            'EnColombia': 'En Colombia',
            'losderechos': 'los derechos',
            'estánregulados': 'están regulados',
            'porlaConstitución': 'por la Constitución',
            'elCódigo': 'el Código',
            'SustantivodelTrabajo': 'Sustantivo del Trabajo',
            'otroscuerpos': 'otros cuerpos',
            'legalessecundarios': 'legales secundarios',
            'Acontinuación': 'A continuación',
            'tepresento': 'te presento',
            'algunosdelos': 'algunos de los',
            'derechoslaborales': 'derechos laborales',
            'másimportantes': 'más importantes',
            'Igualdaddeoportunidades': 'Igualdad de oportunidades',
            'Teneracceso': 'Tener acceso',
            'aempleos': 'a empleos',
            'sindiscriminación': 'sin discriminación',
            'porrazones': 'por razones',
            'degénero': 'de género',
            'Derechoal': 'Derecho al',
            'lalibertad': 'la libertad',
            'sindical': 'sindical',
            'Organizarseen': 'Organizarse en',
            'sindicatosy': 'sindicatos y',
            'asociacionespara': 'asociaciones para',
            'protegersus': 'proteger sus',
            'intereseslaborales': 'intereses laborales',
            'Derechoalanegociación': 'Derecho a la negociación',
            'colectiva': 'colectiva',
            'Participaren': 'Participar en',
            'lanegociación': 'la negociación',
            'decondiciones': 'de condiciones',
            'laboralescon': 'laborales con',
            'losempleadores': 'los empleadores',
            'atravésde': 'a través de',
            'convenioscolectivos': 'convenios colectivos',
            'Derechoalahuelga': 'Derecho a la huelga',
            'Realizarhuelgas': 'Realizar huelgas',
            'legalespara': 'legales para',
            'defendersus': 'defender sus',
            'ProtecciónLaboral': 'Protección Laboral',
            'Derechoalaseguridad': 'Derecho a la seguridad',
            'ysalud': 'y salud',
            'eneltrabajo': 'en el trabajo',
            'Tenerunambiente': 'Tener un ambiente',
            'laboralseguro': 'laboral seguro',
            'ysaludable': 'y saludable',
            'Derechoalaindemnización': 'Derecho a la indemnización',
            'pordespido': 'por despido',
            'Recibiruna': 'Recibir una',
            'indemnizaciónen': 'indemnización en',
            'casodedespido': 'caso de despido',
            'injustificado': 'injustificado',
            'Derechoalaprestación': 'Derecho a la prestación',
            'deservicios': 'de servicios',
            'Cumplircon': 'Cumplir con',
            'loscontratos': 'los contratos',
            'detrabajoen': 'de trabajo en',
            'lascondiciones': 'las condiciones',
            'acordadas': 'acordadas',
            'Derechoalacapacitación': 'Derecho a la capacitación',
            'yformación': 'y formación',
            'Recibircapacitación': 'Recibir capacitación',
            'yformaciónlaboral': 'y formación laboral',
            'DerechosdelEmpleado': 'Derechos del Empleado',
            'Derechoalaremuneración': 'Derecho a la remuneración',
            'justayproporcional': 'justa y proporcional',
            'asutrabajo': 'a su trabajo',
            'Derechoaldescanso': 'Derecho al descanso',
            'yvacaciones': 'y vacaciones',
            'Disfrutarde': 'Disfrutar de',
            'descansosemanal': 'descanso semanal',
            'vacacionesanuales': 'vacaciones anuales',
            'ypermisos': 'y permisos',
            'Derechoalamaternidad': 'Derecho a la maternidad',
            'ypaternidad': 'y paternidad',
            'Gozarde': 'Gozar de',
            'permisosdematernidad': 'permisos de maternidad',
            'ypaternidad': 'y paternidad',
            'Derechoalaprotección': 'Derecho a la protección',
            'delamujer': 'de la mujer',
            'Serprotegida': 'Ser protegida',
            'dediscriminación': 'de discriminación',
            'yacososexual': 'y acoso sexual',
            'DerechosdelEmpleadoenCaso': 'Derechos del Empleado en Caso',
            'deDespido': 'de Despido',
            'Derechoalaindemnización': 'Derecho a la indemnización',
            'pordespidoinjustificado': 'por despido injustificado',
            'Derechoalaprotección': 'Derecho a la protección',
            'delaestabilidad': 'de la estabilidad',
            'laboralenciertoscasos': 'laboral en ciertos casos',
            'porejemplo': 'por ejemplo',
            'encasosdedespido': 'en casos de despido',
            'AccesoaJusticiaLaboral': 'Acceso a Justicia Laboral',
            'Derechoaladefensa': 'Derecho a la defensa',
            'jurídica': 'jurídica',
            'Accedera': 'Acceder a',
            'lajusticialaboral': 'la justicia laboral',
            'yaladefensa': 'y a la defensa',
            'Derechoalaconciliación': 'Derecho a la conciliación',
            'laboral': 'laboral',
            'Buscarla': 'Buscar la',
            'conciliaciónlaboral': 'conciliación laboral',
            'antesdeacudir': 'antes de acudir',
            'alajusticia': 'a la justicia',
            'Paraconocer': 'Para conocer',
            'mássobre': 'más sobre',
            'tusderechos': 'tus derechos',
            'laboralesespecíficos': 'laborales específicos',
            'terecomiendo': 'te recomiendo',
            'consultarel': 'consultar el',
            'CódigoSustantivo': 'Código Sustantivo',
            'delTrabajo': 'del Trabajo',
            'y losconvenios': 'y los convenios',
            'colectivosaplicables': 'colectivos aplicables',
            'atusector': 'a tu sector',
            'laboral': 'laboral',
            'Sitienes': 'Si tienes',
            'dudas': 'dudas',
            'o necesitas': 'o necesitas',
            'asesoramiento': 'asesoramiento',
            'legal': 'legal',
            'esrecomendable': 'es recomendable',
            'consultarcon': 'consultar con',
            'unabogado': 'un abogado',
            'laboralista': 'laboralista'
        }
        
        for wrong, correct in common_fixes.items():
            text = text.replace(wrong, correct)
        
        # Fix spacing around punctuation
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)  # Remove spaces before punctuation
        text = re.sub(r'([.,;:!?])\s+', r'\1 ', text)  # Ensure single space after punctuation
        text = re.sub(r'\s+', ' ', text)  # Normalize multiple spaces to single space
        
        # Fix formatting for headers and lists
        text = re.sub(r'###\s*([^#\n]+)', r'\n### \1\n', text)  # Format headers
        text = re.sub(r'(\d+\.)\s*', r'\n\1 ', text)  # Format numbered lists
        text = re.sub(r'\*\*\s*([^*]+)\s*\*\*', r'**\1**', text)  # Fix bold text
        
        # Add proper spacing around headers and lists
        text = re.sub(r'(\n###[^\n]+\n)', r'\n\1\n', text)  # Add line breaks around headers
        text = re.sub(r'(\n\d+\.[^\n]+\n)', r'\n\1\n', text)  # Add line breaks around list items
        
        # Clean up any remaining formatting issues
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Remove excessive line breaks
        text = re.sub(r' +', ' ', text)  # Remove multiple spaces
        text = text.strip()  # Remove leading/trailing whitespace
        
        return text
        
    except Exception as e:
        print(f"Error cleaning text: {str(e)}")  # Debug log
        return str(text)

async def stream_autorag_response(response) -> AsyncGenerator[str, None]:
    """Stream the AutoRAG response as JSON chunks"""
    try:
        print("Starting to stream AutoRAG response")  # Debug log
        buffer = ""
        sentence_endings = {'.', '!', '?', '\n'}
        
        async for line in response.aiter_lines():
            line = clean_text(line.strip())
            if not line:
                continue
                
            # Handle JSON data
            if line.startswith("data: "):
                data = line[6:]  # Remove "data: " prefix
                if data == "[DONE]":
                    # Send any remaining buffered text as JSON
                    if buffer.strip():
                        yield json.dumps({
                            "type": "chunk",
                            "content": buffer.strip()
                        }, ensure_ascii=False) + "\n"
                    # Send done signal as JSON
                    yield json.dumps({"type": "done"}, ensure_ascii=False) + "\n"
                    break
                    
                try:
                    # Try to parse the JSON data
                    json_data = json.loads(data)
                    if isinstance(json_data, dict) and "response" in json_data:
                        chunk = json_data["response"]
                        if chunk:
                            # Clean and decode the chunk
                            cleaned_chunk = clean_text(chunk)
                            buffer += " " + cleaned_chunk if buffer else cleaned_chunk
                            
                            # Check if we have a complete sentence or section
                            if any(buffer.endswith(end) for end in sentence_endings) or buffer.endswith('**'):
                                # Clean and yield the complete sentence as JSON
                                sentence = clean_text(buffer.strip())
                                if sentence:
                                    print(f"Yielding sentence: {sentence}")  # Debug log
                                    yield json.dumps({
                                        "type": "chunk",
                                        "content": sentence
                                    }, ensure_ascii=False) + "\n"
                                buffer = ""  # Clear buffer after yielding
                            
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")  # Debug log
                    # If it's not JSON, add to buffer and send as JSON when complete
                    if data and data != "[DONE]":
                        cleaned_data = clean_text(data)
                        buffer += " " + cleaned_data if buffer else cleaned_data
                        if any(buffer.endswith(end) for end in sentence_endings) or buffer.endswith('**'):
                            sentence = clean_text(buffer.strip())
                            if sentence:
                                yield json.dumps({
                                    "type": "chunk",
                                    "content": sentence
                                }, ensure_ascii=False) + "\n"
                            buffer = ""

    except Exception as e:
        print(f"Error in stream_autorag_response: {str(e)}")  # Debug log
        # Send any remaining buffered text as JSON before the error
        if buffer.strip():
            yield json.dumps({
                "type": "chunk",
                "content": buffer.strip()
            }, ensure_ascii=False) + "\n"
        # Send error as JSON
        yield json.dumps({
            "type": "error",
            "error": str(e)
        }, ensure_ascii=False) + "\n"
    finally:
        print("Finished streaming AutoRAG response")  # Debug log
        # Send final done signal as JSON
        yield json.dumps({"type": "done"}, ensure_ascii=False) + "\n"

async def _make_autorag_request(
    endpoint: str,
    data: Dict[str, Any],
    stream: bool = False
) -> Union[Dict[str, Any], httpx.Response]:
    """Make a request to AutoRAG API (internal helper function)"""
    url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/autorag/rags/legalassistant-rag/{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN_CHATBOT}",
        "Accept": "application/json"
    }

    print(f"Sending AutoRAG {endpoint} request: {json.dumps(data, indent=2)}")  # Debug log
    print(f"Request headers: {headers}")  # Debug log

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url,
                headers=headers,
                json=data,
                timeout=None if stream else 30.0
            )

            print(f"AutoRAG response status: {response.status_code}")  # Debug log
            print(f"AutoRAG response headers: {dict(response.headers)}")  # Debug log

            if response.status_code != 200:
                error_detail = response.json()
                print(f"AutoRAG error response: {json.dumps(error_detail, indent=2)}")  # Debug log
                raise HTTPException(
                    status_code=response.status_code,
                    detail=error_detail
                )

            # Ensure response has JSON content type
            response.headers["Content-Type"] = "application/json"
            
            if stream:
                return response
            else:
                result = response.json()
                print(f"AutoRAG non-streaming response: {json.dumps(result, indent=2)}")  # Debug log
                return result

        except httpx.RequestError as e:
            print(f"Request error: {str(e)}")  # Debug log
            raise HTTPException(
                status_code=500,
                detail={
                    "error": str(e),
                    "message": "Error connecting to AutoRAG API",
                    "timestamp": datetime.now().isoformat()
                }
            )

async def process_autorag_search(
    message: str,
    rewrite_query: bool = True,
    max_num_results: int = 10,
    ranking_options: Dict[str, float] = {"score_threshold": 0.3}
) -> Dict[str, Any]:
    """Process a request to AutoRAG search endpoint"""
    try:
        data = {
            "query": message,
            "rewrite_query": rewrite_query,
            "max_num_results": max_num_results,
            "ranking_options": {
                "score_threshold": ranking_options.get("score_threshold", 0.3)
            }
        }

        result = await _make_autorag_request("search", data)
        return {
            "success": result.get("success", False),
            "result": result.get("result", {}),
            "search_query": result.get("result", {}).get("search_query", message),
            "data": result.get("result", {}).get("data", []),
            "has_more": result.get("result", {}).get("has_more", False),
            "next_page": result.get("result", {}).get("next_page")
        }

    except Exception as e:
        print(f"Error in process_autorag_search: {str(e)}")  # Debug log
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "message": "Error in AutoRAG search request",
                "timestamp": datetime.now().isoformat()
            }
        )

async def process_autorag_ai_search(
    message: str,
    model: str = "@cf/meta/llama-3.1-8b-instruct-fast",
    rewrite_query: bool = False,
    max_num_results: int = 10,
    ranking_options: Dict[str, float] = {"score_threshold": 0.3},
    stream: bool = False
) -> Dict[str, Any]:
    """Process a request to AutoRAG AI search endpoint"""
    try:
        # Ensure model is a string with @ prefix
        if not isinstance(model, str):
            model = str(model)
        if not model.startswith("@"):
            model = f"@{model}"

        data = {
            "query": message,
            "model": model,
            "rewrite_query": rewrite_query,
            "max_num_results": max_num_results,
            "ranking_options": {
                "score_threshold": ranking_options.get("score_threshold", 0.3)
            },
            "stream": False  # Always set to False to get complete response
        }

        print(f"Sending AutoRAG request with model: {model}")  # Debug log
        print(f"Request data: {json.dumps(data, indent=2)}")  # Debug log

        result = await _make_autorag_request("ai-search", data, stream=False)
        print(f"Got response: {json.dumps(result, indent=2)}")  # Debug log
        
        # Get the response text from the result
        response_text = ""
        if "result" in result and "response" in result["result"]:
            response_text = clean_text(result["result"]["response"])
        elif "result" in result and "data" in result["result"]:
            # If no direct response, concatenate content from data
            response_parts = []
            for item in result["result"]["data"]:
                if "content" in item:
                    for content in item["content"]:
                        if "text" in content:
                            response_parts.append(clean_text(content["text"]))
            response_text = "\n\n".join(response_parts)
        
        # Format the response according to the expected structure
        return {
            "success": result.get("success", True),
            "result": {
                "object": "vector_store.search_results.page",
                "search_query": result.get("result", {}).get("search_query", message),
                "response": response_text,  # Add the response field
                "data": [
                    {
                        "file_id": item.get("file_id", f"file_{i}"),
                        "filename": item.get("filename", ""),
                        "score": item.get("score", 0.0),
                        "attributes": {
                            "modified_date": int(datetime.now().timestamp() * 1000),  # Convert to milliseconds
                            "folder": item.get("attributes", {}).get("folder", ""),
                        },
                        "content": [
                            {
                                "id": item.get("file_id", f"file_{i}"),
                                "type": "text",
                                "text": clean_text(item.get("content", ""))
                            }
                        ]
                    }
                    for i, item in enumerate(result.get("result", {}).get("data", []))
                ],
                "has_more": result.get("result", {}).get("has_more", False),
                "next_page": result.get("result", {}).get("next_page")
            }
        }

    except Exception as e:
        print(f"Error in process_autorag_ai_search: {str(e)}")  # Debug log
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "message": "Error in AutoRAG AI search request",
                "timestamp": datetime.now().isoformat()
            }
        )

# For backward compatibility
async def process_autorag_request(
    message: str,
    rewrite_query: bool = True,
    max_num_results: int = 10,
    ranking_options: Dict[str, float] = {"score_threshold": 0.3}
) -> Dict[str, Any]:
    """Alias for process_autorag_search for backward compatibility"""
    return await process_autorag_search(
        message=message,
        rewrite_query=rewrite_query,
        max_num_results=max_num_results,
        ranking_options=ranking_options
    )

def get_legal_disclaimer() -> str:
    """Returns the standard legal disclaimer"""
    return """
    Esta información es de carácter general y no constituye asesoría jurídica.
    Cada caso particular puede requerir un análisis específico y profesional.
    Se recomienda consultar con un abogado para obtener asesoría legal específica.
    La información proporcionada cumple con la normatividad colombiana vigente.
    """

def get_colombian_compliance() -> Dict[str, Any]:
    """Returns the Colombian compliance details"""
    return {
        "version": "2.0",
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