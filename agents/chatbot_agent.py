import datetime
from agno.agent import Agent, RunResponse
from config.ai_models import get_model
from typing import Dict, List, Optional, Any, Union

def generate_contextual_questions(ai_response: str) -> List[str]:
    """Generate dynamic contextual questions based on the AI model's response"""
    questions = []
    response_lower = ai_response.lower()
    
    # Dynamic question generation based on legal concepts
    legal_concepts = {
        "precedente": [
            "¿Tienes un caso específico en mente donde un juez podría considerar apartarse de un precedente?",
            "¿Conoces algún caso reciente donde la Corte haya modificado su jurisprudencia?",
            "¿En qué circunstancias consideras que sería justificable apartarse del precedente?",
            "¿Has identificado contradicciones entre diferentes precedentes aplicables a tu caso?"
        ],
        "constitucional": [
            "¿Qué derechos fundamentales específicos consideras que están en juego?",
            "¿Has considerado presentar una acción de tutela para proteger tus derechos?",
            "¿Conoces casos similares donde la Corte Constitucional haya fallado a favor?",
            "¿Has analizado si existe un conflicto entre diferentes derechos fundamentales?"
        ],
        "jurisprudencia": [
            "¿Estás buscando información sobre alguna área particular del derecho donde los precedentes son más relevantes?",
            "¿Has encontrado jurisprudencia contradictoria sobre tu caso?",
            "¿Conoces las últimas decisiones de las altas cortes sobre este tema?",
            "¿Has identificado cambios importantes en la línea jurisprudencial?"
        ],
        "procedimiento": [
            "¿En qué etapa procesal te encuentras actualmente?",
            "¿Has considerado los requisitos de procedibilidad aplicables?",
            "¿Conoces los términos procesales que debes tener en cuenta?",
            "¿Has evaluado las diferentes vías procesales disponibles?"
        ],
        "pruebas": [
            "¿Qué tipo de material probatorio tienes para sustentar tu caso?",
            "¿Has considerado la necesidad de pruebas periciales?",
            "¿Conoces los criterios de valoración probatoria aplicables?",
            "¿Has identificado las pruebas clave que necesitas obtener?"
        ],
        "competencia": [
            "¿Has verificado cuál es el juez competente para conocer tu caso?",
            "¿Existen conflictos de competencia que deban resolverse?",
            "¿Has considerado si tu caso podría ser de competencia de una jurisdicción especial?",
            "¿Conoces las reglas de reparto aplicables?"
        ]
    }

    # Extract relevant questions based on concepts mentioned in the response
    relevant_questions = []
    for concept, concept_questions in legal_concepts.items():
        if concept in response_lower:
            relevant_questions.extend(concept_questions)
    
    # Dynamic generation based on specific legal terms
    legal_terms = {
        "acción": "¿Has evaluado todas las acciones legales disponibles para tu caso?",
        "recurso": "¿Conoces los recursos procedentes contra las decisiones que te afectan?",
        "derecho": "¿Puedes identificar específicamente qué derechos consideras vulnerados?",
        "tribunal": "¿Has investigado decisiones similares de este tribunal en casos análogos?",
        "sentencia": "¿Has analizado los fundamentos jurídicos de las sentencias relevantes?",
        "proceso": "¿Has considerado las diferentes etapas procesales y sus requisitos?",
        "demanda": "¿Has evaluado todos los elementos necesarios para tu demanda?",
        "apelación": "¿Conoces los requisitos específicos para presentar una apelación?",
        "nulidad": "¿Has identificado posibles causales de nulidad en el proceso?",
        "medida": "¿Has considerado solicitar medidas cautelares para proteger tus derechos?"
    }

    # Add questions based on specific terms found in response
    for term, question in legal_terms.items():
        if term in response_lower:
            relevant_questions.append(question)
    
    # Add procedural questions based on context
    if "procedimiento" in response_lower or "proceso" in response_lower:
        procedural_questions = [
            "¿Has verificado los términos procesales aplicables?",
            "¿Conoces las consecuencias procesales de cada decisión?",
            "¿Has considerado las diferentes etapas del proceso?",
            "¿Tienes clara la estrategia procesal a seguir?"
        ]
        relevant_questions.extend(procedural_questions)
    
    # Add questions about legal strategy if relevant
    if any(term in response_lower for term in ["estrategia", "defensa", "argumento"]):
        strategy_questions = [
            "¿Has desarrollado una estrategia legal clara para tu caso?",
            "¿Has considerado los contraargumentos posibles?",
            "¿Has evaluado los riesgos y beneficios de cada estrategia?",
            "¿Has consultado casos similares para refinar tu estrategia?"
        ]
        relevant_questions.extend(strategy_questions)
    
    # Add questions about evidence if relevant
    if any(term in response_lower for term in ["prueba", "evidencia", "documento"]):
        evidence_questions = [
            "¿Has identificado todas las fuentes de prueba disponibles?",
            "¿Has considerado la pertinencia de cada prueba?",
            "¿Conoces los requisitos para la admisión de las pruebas?",
            "¿Has evaluado la necesidad de pruebas técnicas o periciales?"
        ]
        relevant_questions.extend(evidence_questions)

    # Select most relevant questions (avoid too many)
    if relevant_questions:
        # Prioritize questions based on response content
        return relevant_questions[:5]  # Limit to 5 most relevant questions
    else:
        # Fallback general questions if no specific concepts are found
        return [
            "¿Podrías proporcionar más detalles sobre tu situación legal específica?",
            "¿Has consultado jurisprudencia relacionada con tu caso?",
            "¿Tienes dudas sobre algún aspecto procesal en particular?",
            "¿Necesitas información sobre algún precedente específico?"
        ]

def get_legal_references() -> Dict[str, List[str]]:
    """Get legal references with guaranteed list returns"""
    return {
        "normativa": [
            "Código Civil Colombiano",
            "Código de Procedimiento Civil",
            "Constitución Política de Colombia",
            "Ley 1564 de 2012 (Código General del Proceso)",
            "Ley 1437 de 2011 (Código de Procedimiento Administrativo)",
            "Ley 1098 de 2006 (Código de la Infancia y la Adolescencia)",
            "Ley 1564 de 2012 (Código General del Proceso)",
            "Ley 1437 de 2011 (Código de Procedimiento Administrativo)"
        ],
        "jurisprudencia": [
            "Sentencia C-700 de 1999 - Corte Constitucional: Principio de buena fe",
            "Sentencia T-406 de 1992 - Corte Constitucional: Debido proceso",
            "Sentencia C-083 de 1995 - Corte Constitucional: Derechos fundamentales",
            "Sentencia C-700 de 1999 - Corte Constitucional: Principio de buena fe",
            "Sentencia T-406 de 1992 - Corte Constitucional: Debido proceso",
            "Sentencia C-083 de 1995 - Corte Constitucional: Derechos fundamentales",
            "Sentencia C-700 de 1999 - Corte Constitucional: Principio de buena fe",
            "Sentencia T-406 de 1992 - Corte Constitucional: Debido proceso"
        ],
        "doctrina": [
            "Manual de Derecho Civil - Universidad Nacional",
            "Principios Generales del Derecho - Universidad de los Andes",
            "Tratado de Derecho Procesal Civil - Universidad Externado",
            "Manual de Derecho Civil - Universidad Nacional",
            "Principios Generales del Derecho - Universidad de los Andes",
            "Tratado de Derecho Procesal Civil - Universidad Externado"
        ],
        "informacion_relevante": [
            "Plazos procesales generales: 10 días hábiles para contestar demandas",
            "Medios de prueba: Documentos, testigos, peritos, inspección judicial",
            "Recursos: Reposición, apelación, casación, revisión",
            "Costas procesales: Generalmente las paga la parte vencida",
            "Medidas cautelares: Disponibles para proteger derechos",
            "Conciliación: Obligatoria en asuntos de familia y laborales"
        ]
    }

def create_chatbot_agent(
    authentication_token: str = None,
    client_id: str = None,
    instrucciones: Optional[Union[str, List[str]]] = None,
    file_content: Optional[str] = None
) -> Agent:
    """Create a specialized agent for client chat, with optional instrucciones and file context"""
    system_instructions = [
        "Eres un asistente virtual especializado en información legal colombiana",
        "Proporciona información general precisa según la jurisdicción colombiana",
        "Utiliza lenguaje claro y accesible para personas sin formación jurídica",
        "Mantén coherencia con el contexto de la conversación anterior",
        "Genera preguntas contextuales relevantes para guiar al usuario",
        "Incluye referencias a jurisprudencia relevante cuando sea apropiado",
        "Proporciona información sobre plazos y procedimientos cuando sea relevante"
    ]
    # Add user-provided instrucciones
    if instrucciones:
        if isinstance(instrucciones, list):
            system_instructions.extend([str(instr) for instr in instrucciones])
        else:
            system_instructions.append(str(instrucciones))
    # Add file content as context if provided
    context = []
    if file_content:
        context.append({
            "role": "user_file",
            "content": file_content[:5000]  # Limit context size for now
        })
        # TODO: Advanced file context integration (e.g., chunking, semantic search)
    return Agent(
        name="Asistente Legal Virtual",
        role="Asistente de información jurídica",
        model=get_model("chatbot"),
        instructions=system_instructions,
        markdown=True,
        add_context=True,
        context=context if context else None
    )

async def process_client_message(
    client_id: str,
    message: str,
    conversation_id: Optional[str] = None,
    legal_terms: Optional[List[str]] = None,
    data_processing: Optional[Dict[str, str]] = None,
    instrucciones: Optional[Union[str, List[str]]] = None,
    file_content: Optional[str] = None
) -> Dict[str, Any]:
    """Process a client message and return a response, supporting instrucciones and file context"""
    try:
        # Create chatbot agent with instrucciones and file context
        agent = create_chatbot_agent(
            authentication_token=None,
            client_id=client_id,
            instrucciones=instrucciones,
            file_content=file_content
        )
        # Process message
        response: RunResponse = agent.run(message)
        # Extract just the content from the response
        response_content = response.content if hasattr(response, 'content') else str(response)
        # Get references with guaranteed lists
        references = get_legal_references()
        # Generate contextual questions based on AI response
        contextual_questions = generate_contextual_questions(response_content)
        # Ensure references are properly structured
        response_data = {
            "response": {
                "content": response_content,  # This will be the markdown content
                "relevant_laws": references["normativa"],
                "recommendations": [
                    "Documentar todas las comunicaciones",
                    "Consultar con un abogado especializado",
                    "Mantener un registro de fechas importantes",
                    "Guardar copias de todos los documentos relevantes",
                    "Verificar plazos procesales",
                    "Considerar la conciliación como primera opción"
                ],
                "contextual_questions": contextual_questions,
                "jurisprudencia": references["jurisprudencia"],
                "informacion_relevante": references["informacion_relevante"]
            },
            "conversation_id": conversation_id or f"conv_{client_id}_{datetime.datetime.now().timestamp()}",
            "disclaimer": """Esta información es de carácter general y no constituye asesoría jurídica.\n                        Cada caso particular puede requerir un análisis específico y profesional.""",
            "colombian_compliance": {
                "version": "1.0",
                "constitutional_principles": ["Debido proceso", "Buena fe"],
                "data_protection": {
                    "law": "Ley 1581 de 2012",
                    "status": "Cumple"
                }
            },
            "legal_terms": {
                "demanda": "Solicitud formal ante un juez",
                "prueba": "Elemento que demuestra un hecho",
                "jurisdicción": "Competencia de un juez o tribunal",
                "plazo": "Tiempo establecido para realizar un acto procesal",
                "recurso": "Medio para impugnar una decisión judicial",
                "conciliación": "Mecanismo alternativo de solución de conflictos"
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
                "recommendations": [],
                "contextual_questions": [],
                "jurisprudencia": [],
                "informacion_relevante": []
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
            "legal_terms": {},
            "references": {
                "normativa": [],
                "jurisprudencia": [],
                "doctrina": [],
                "informacion_relevante": []
            }
        } 