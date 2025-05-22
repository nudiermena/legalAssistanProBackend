import datetime
from agno.agent import Agent, RunResponse
from config.ai_models import get_model
from typing import Dict, List, Optional, Any
from agno.team import Team
from agno.tools.googlesearch import GoogleSearchTools
from agno.models.deepseek import DeepSeek

def create_chatbot_agent(
    practice_area: str = None,
    authentication_token: str = None,
    client_id: str = None,
    instructions: str = None,
    file_content: str = None
) -> Agent:
    """Create a specialized agent team for client chat"""
    # Main legal chatbot agent
    system_instructions = system_instructions = [
    "Eres un asistente virtual especializado en información legal colombiana",
    "Proporciona información general precisa según la jurisdicción colombiana",
    "Utiliza lenguaje claro y accesible para personas sin formación jurídica",
    "Mantén coherencia con el contexto de la conversación anterior",
    "Cita las fuentes legales relevantes como códigos, leyes y sentencias de la Corte Constitucional cuando corresponda",
    "Especifica cuando la información proporcionada es de carácter general y recomienda consultar con un abogado para casos específicos",
    "Explica términos jurídicos técnicos cuando los utilices por primera vez",
    "Organiza respuestas complejas en secciones claramente definidas para facilitar su comprensión",
    "Cuando existan diferentes interpretaciones legales sobre un tema, presenta las principales posturas",
    "Actualiza tus respuestas según la legislación vigente, mencionando reformas recientes si son relevantes",
    "Evita dar consejos que puedan considerarse ejercicio no autorizado de la abogacía",
    "Responde en español utilizando terminología jurídica colombiana apropiada",
    "Adapta el nivel de tecnicismo según el contexto y las necesidades del usuario",
    "Proporciona ejemplos prácticos para ilustrar conceptos legales complejos",
    "Cuando sea apropiado, menciona procedimientos o recursos legales disponibles",
    "Identifica claramente cuando una situación puede requerir distintos enfoques según la jurisdicción dentro de Colombia",
    "Mantén neutralidad en temas legales controvertidos, presentando los argumentos de manera equilibrada",
     "Realiza búsquedas en Google y bases de datos legales (e.g., Corte Constitucional, Consejo de Estado, vLex, Legis) para encontrar información relevante y actualizada.",
        "Prioriza fuentes oficiales (gobierno, cortes, diarios oficiales) y fuentes académicas confiables.",
        "Filtra información no confiable o desactualizada, verificando la fecha de publicación.",
        "Proporciona un resumen breve (máximo 100 palabras por fuente) y el enlace correspondiente.",
        "Incluye metadatos básicos (fecha, autor, fuente) para cada resultado.",
        "Si no encuentras información relevante, indica que no hay datos disponibles y sugiere al usuario proporcionar más contexto."
    "Analiza la consulta del usuario para identificar ambigüedades o falta de contexto.",
      "Genera un máximo de 3 preguntas claras y concisas para obtener detalles relevantes (e.g., jurisdicción, tipo de caso, detalles del problema).",
      "Adapta las preguntas al tono y nivel de conocimiento del usuario, utilizando análisis de sentimiento para detectar urgencia o confusión.",
      "Evita preguntas redundantes o excesivamente técnicas si el usuario parece no tener formación jurídica.",
      "Si el usuario proporciona un archivo, genera preguntas basadas en su contenido para confirmar su relevancia."
    ]
    if practice_area:
        system_instructions.append(f"Te especializas en derecho {practice_area}.")
    if instructions:
        system_instructions.append(f"Instrucción del usuario: {instructions}")
    if file_content:
        system_instructions.append(f"El usuario ha adjuntado el siguiente archivo para contexto: {file_content}")
        
    legal_agent = Agent(
        name="Asistente Legal Virtual",
        role="Asistente de información jurídica",
        model=get_model("chatbot"),
        tools=[GoogleSearchTools()],
        instructions=system_instructions,
        markdown=True,
        add_context=True,
        reasoning=True,
    )
    # # Web Search Agent
    # web_search_agent = Agent(
    # name="Legal Web Search Agent",
    # role="Busca y sintetiza información legal actualizada desde fuentes confiables",
    # tools=[GoogleSearchTools()],  # Added specialized legal database tool
    # instructions=[
    #     "Realiza búsquedas en Google y bases de datos legales (e.g., Corte Constitucional, Consejo de Estado, vLex, Legis) para encontrar información relevante y actualizada.",
    #     "Prioriza fuentes oficiales (gobierno, cortes, diarios oficiales) y fuentes académicas confiables.",
    #     "Filtra información no confiable o desactualizada, verificando la fecha de publicación.",
    #     "Proporciona un resumen breve (máximo 100 palabras por fuente) y el enlace correspondiente.",
    #     "Incluye metadatos básicos (fecha, autor, fuente) para cada resultado.",
    #     "Si no encuentras información relevante, indica que no hay datos disponibles y sugiere al usuario proporcionar más contexto."
    # ],
    # markdown=True,
    # )
    # # Context Question Agent
    # context_question_agent = Agent(model=DeepSeek(),
    #     name="Context Question Agent",
    #     role="Genera preguntas de contexto para clarificar la consulta del usuario",
    #     instructions=[
    #     "Analiza la consulta del usuario para identificar ambigüedades o falta de contexto.",
    #     "Genera un máximo de 3 preguntas claras y concisas para obtener detalles relevantes (e.g., jurisdicción, tipo de caso, detalles del problema).",
    #     "Adapta las preguntas al tono y nivel de conocimiento del usuario, utilizando análisis de sentimiento para detectar urgencia o confusión.",
    #     "Evita preguntas redundantes o excesivamente técnicas si el usuario parece no tener formación jurídica.",
    #     "Si el usuario proporciona un archivo, genera preguntas basadas en su contenido para confirmar su relevancia."
    #     ],
    #     markdown=True,
    #     add_context=True
    # )
    
    # response_formatter_agent = Agent(model=DeepSeek(),
    # name="Response Formatter Agent",
    # role="Formatea y optimiza las respuestas para máxima claridad y profesionalismo",
    # instructions=[
    #     "Recibe las respuestas de los agentes Legal, Web Search y Context Question.",
    #     "Organiza la información en una respuesta unificada con secciones claras: 'Respuesta Legal', 'Información Adicional (Web)', y 'Preguntas para Clarificar' (si aplica).",
    #     "Asegúrate de que el tono sea profesional, coherente y adaptado al nivel de conocimiento del usuario.",
    #     "Elimina redundancias y corrige inconsistencias entre las respuestas de los agentes.",
    #     "Incluye un resumen introductorio breve (máximo 50 palabras) que explique el propósito de la respuesta.",
    #     "Asegúrate de que todas las citas legales y enlaces estén correctamente formateados en Markdown."
    # ],
    # markdown=True,
    # add_context=True
    # )
    # # Team
    # team = Team(
    #     name="Legal Assistant Team",
    #     mode="coordinate",
    #     model=get_model("chatbot"),
    #     members=[legal_agent, response_formatter_agent],
    #     instructions=[
    #     "Coordina las acciones de todos los agentes para proporcionar una respuesta completa, precisa y bien estructurada.",
    #     "El Legal Agent proporciona la respuesta jurídica principal basada en la normativa colombiana.",
    #     "El Web Search Agent complementa con información actualizada de fuentes confiables.",
    #     "El Response Formatter Agent unifica las respuestas, elimina redundancias y asegura un formato claro y profesional.",
    #     "Prioriza la claridad, la precisión y la satisfacción del usuario en todas las interacciones.",
    #     "Si el usuario sube un archivo, todos los agentes deben considerarlo en sus respuestas."
    #     ],
    #     markdown=True,
    #     add_context=True,
    #     show_tool_calls=True,
    # )
    return legal_agent

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
    data_processing: Optional[Dict[str, str]] = None,
    instructions: Optional[str] = None,
    file_content: Optional[str] = None
) -> Dict[str, Any]:
    """Process a client message and return a response"""
    try:
        # Create chatbot agent
        agent = create_chatbot_agent(
            practice_area=practice_area,
            authentication_token=None,
            client_id=client_id,
            instructions=instructions,
            file_content=file_content
        )

        # Process message
        response: RunResponse = agent.run(message)
        
        # Extract content from response, handling different response types
        if isinstance(response, dict) and 'content' in response:
            response_content = response['content']
        elif hasattr(response, 'content'):
            response_content = response.content
        else:
            response_content = str(response)
            
        # Clean up any task transfer metadata
        if isinstance(response_content, str):
            response_content = response_content.split("transfer_task_to_member")[0].strip()
            if response_content.startswith("[") and response_content.endswith("]"):
                response_content = response_content[1:-1].strip()

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