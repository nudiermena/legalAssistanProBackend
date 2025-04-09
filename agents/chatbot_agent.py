import datetime
from agno.agent import Agent, RunResponse
from config.ai_models import get_model
from typing import Dict, List, Optional, Any

def create_chatbot_agent(
    practice_area: str = None,
    authentication_token: str = None,
    client_id: str = None
) -> Agent:
    """Create a specialized agent for client chat"""
    system_instructions = [
        "Eres un asistente virtual especializado en información legal colombiana",
        "Proporciona información general precisa según la jurisdicción colombiana",
        "Utiliza lenguaje claro y accesible para personas sin formación jurídica",
        "Mantén coherencia con el contexto de la conversación anterior"
    ]
    
    if practice_area:
        system_instructions.append(f"Te especializas en derecho {practice_area}.")
    
    return Agent(
        name="Asistente Legal Virtual",
        role="Asistente de información jurídica",
        model=get_model("chatbot"),
        instructions=system_instructions,
        markdown=True,
        add_context=True
    )

def get_legal_references(practice_area: Optional[str] = None) -> Dict[str, List[str]]:
    """Get legal references based on practice area with guaranteed list returns"""
    if practice_area == "arrendamiento":
        return {
            "normativa": [
                "Ley 820 de 2003",
                "Código Civil Colombiano - Artículos 1973 a 2044"
            ],
            "jurisprudencia": [
                "Sentencia C-670 de 2004",
                "Sentencia C-731 de 2005"
            ],
            "doctrina": [
                "Manual de Contratos de Arrendamiento",
                "Guía práctica de arrendamiento en Colombia"
            ]
        }
    elif practice_area == "derecho_laboral":
        return {
            "normativa": [
                "Código Sustantivo del Trabajo",
                "Ley 100 de 1993"
            ],
            "jurisprudencia": [
                "Sentencia T-480 de 2016",
                "Sentencia C-593 de 2014"
            ],
            "doctrina": [
                "Manual de Derecho Laboral",
                "Principios del Derecho Laboral Colombiano"
            ]
        }
    # Default empty references
    return {
        "normativa": [],
        "jurisprudencia": [],
        "doctrina": []
    }

async def process_client_message(
    client_id: str,
    message: str,
    conversation_id: Optional[str] = None,
    practice_area: Optional[str] = None,
    legal_terms: Optional[List[str]] = None,
    data_processing: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Process a client message and return a response"""
    try:
        # Create chatbot agent
        agent = create_chatbot_agent(
            practice_area=practice_area,
            authentication_token=None,
            client_id=client_id
        )

        # Process message
        response: RunResponse = agent.run(message)
        # Extract just the content from the response
        response_content = response.content if hasattr(response, 'content') else str(response)

        # Get references with guaranteed lists
        references = get_legal_references(practice_area)

        # Ensure references are properly structured
        response_data = {
            "response": {
                "content": response_content,  # This will be the markdown content
                "relevant_laws": references["normativa"],
                "recommendations": [
                    "Leer detenidamente el contrato antes de firmar",
                    "Verificar el estado del inmueble",
                    "Documentar todas las comunicaciones",
                    "Consultar con un abogado especializado"
                ] if practice_area == "arrendamiento" else []
            },
            "conversation_id": conversation_id or f"conv_{client_id}_{datetime.datetime.now().timestamp()}",
            "disclaimer": """Esta información es de carácter general y no constituye asesoría jurídica.
                        Cada caso particular puede requerir un análisis específico y profesional.""",
            "colombian_compliance": {
                "version": "1.0",
                "constitutional_principles": ["Debido proceso", "Buena fe"],
                "data_protection": {
                    "law": "Ley 1581 de 2012",
                    "status": "Cumple"
                }
            },
            "practice_area": practice_area or "derecho_civil",
            "legal_terms": {
                "canon": "Precio acordado por el arrendamiento",
                "clausula_penal": "Sanción por incumplimiento del contrato",
                "deposito": "Garantía para cubrir posibles daños"
            },
            "references": references
        }

        return response_data

    except Exception as e:
        print(f"Error processing message: {str(e)}")
        return {
            "response": {
                "content": "Error procesando la consulta",
                "relevant_laws": [],
                "recommendations": []
            },
            "conversation_id": f"error_{datetime.datetime.now().timestamp()}",
            "disclaimer": "Error en el procesamiento",
            "colombian_compliance": {
                "version": "1.0",
                "constitutional_principles": [],
                "data_protection": {
                    "law": "",
                    "status": "Error"
                }
            },
            "practice_area": "error",
            "legal_terms": {},
            "references": {
                "normativa": [],
                "jurisprudencia": [],
                "doctrina": []
            }
        } 