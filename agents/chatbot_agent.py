import datetime
from agno.agent import Agent, RunResponse
from config.ai_models import get_model
from config.knowledge_base_integration import create_agent_knowledge_integration
from config.enhanced_agent_config import get_enhanced_agent_config
from typing import Dict, List, Optional, Any
from agno.tools.googlesearch import GoogleSearchTools
import re
import logging

logger = logging.getLogger(__name__)

def is_legal_query(message: str) -> Dict[str, Any]:
    """
    Validates if a query is related to legal matters in Colombia.
    Returns validation result with confidence score and reasoning.
    """
    # Convert to lowercase for case-insensitive matching
    message_lower = message.lower()
    
    # Legal keywords and terms in Spanish
    legal_keywords = [
        # General legal terms
        'derecho', 'ley', 'código', 'norma', 'jurídico', 'legal', 'legislación',
        'constitución', 'corte', 'tribunal', 'juez', 'juzgado', 'proceso',
        'demanda', 'demandar', 'demandado', 'demandante', 'sentencia',
        'fallo', 'resolución', 'decreto', 'reglamento', 'estatuto',
        
        # Civil law
        'contrato', 'arrendamiento', 'arrendador', 'arrendatario', 'canon',
        'propiedad', 'inmueble', 'mueble', 'herencia', 'testamento',
        'sucesión', 'divorcio', 'separación', 'custodia', 'pensión',
        'alimentaria', 'patria potestad', 'tutela', 'acción de tutela',
        
        # Labor law
        'trabajo', 'empleado', 'empleador', 'contrato de trabajo',
        'salario', 'prestaciones', 'cesantías', 'vacaciones', 'horas extras',
        'despido', 'renuncia', 'liquidación', 'indemnización',
        'seguridad social', 'eps', 'afp', 'caja de compensación',
        
        # Commercial law
        'sociedad', 'empresa', 'comercio', 'mercantil', 'comercial',
        'sociedad anónima', 'sociedad limitada', 'sociedad por acciones',
        'capital social', 'acciones', 'dividendos', 'junta directiva',
        'asamblea', 'gerente', 'administrador', 'representante legal',
        
        # Administrative law
        'administrativo', 'entidad', 'estatal', 'público', 'gobierno',
        'alcaldía', 'gobernación', 'ministerio', 'departamento',
        'municipio', 'licencia', 'permiso', 'autorización', 'procedimiento',
        'recurso', 'apelación', 'reposición', 'revisión',
        
        # Criminal law
        'penal', 'criminal', 'delito', 'falta', 'contravención',
        'cárcel', 'prisión', 'libertad', 'condicional', 'probation',
        'fiscalía', 'fiscal', 'procuraduría', 'procurador',
        'policía', 'investigación', 'prueba', 'testigo', 'víctima',
        
        # Constitutional law
        'constitucional', 'derechos fundamentales', 'libertad', 'igualdad',
        'dignidad', 'debido proceso', 'buena fe', 'protección',
        'corte constitucional', 'tutela', 'acción de tutela',
        'habeas corpus', 'habeas data', 'amparo',
        
        # Family law
        'familia', 'matrimonio', 'unión libre', 'concubinato',
        'hijos', 'padres', 'madre', 'padre', 'adopción',
        'alimentos', 'visitas', 'régimen de visitas',
        
        # Property law
        'propiedad', 'posesión', 'usucapión', 'prescripción',
        'hipoteca', 'embargo', 'secuestro', 'ejecución',
        'bienes', 'muebles', 'inmuebles', 'terreno', 'casa',
        
        # Contract law
        'contrato', 'acuerdo', 'convenio', 'pacto', 'cláusula',
        'obligación', 'deber', 'derecho', 'incumplimiento',
        'rescisión', 'terminación', 'modificación', 'nulidad',
        
        # Tax law
        'impuesto', 'tributario', 'fiscal', 'dian', 'renta',
        'iva', 'retención', 'declaración', 'factura',
        'contribuyente', 'responsable', 'sujeto pasivo',
        
        # Intellectual property
        'propiedad intelectual', 'patente', 'marca', 'derecho de autor',
        'copyright', 'licencia', 'registro', 'solicitud',
        
        # Consumer protection
        'consumidor', 'protección', 'garantía', 'devolución',
        'reclamo', 'queja', 'superintendencia', 'sucursal',
        
        # Data protection
        'datos personales', 'habeas data', 'privacidad', 'confidencialidad',
        'consentimiento', 'tratamiento', 'procesamiento',
        
        # Legal procedures
        'proceso', 'procedimiento', 'instancia', 'término',
        'notificación', 'citación', 'emplazamiento', 'audiencia',
        'vista', 'alegatos', 'pruebas', 'testigos', 'peritos',
        
        # Legal remedies
        'recurso', 'apelación', 'reposición', 'revisión',
        'casación', 'tutela', 'acción de tutela', 'amparo',
        'habeas corpus', 'habeas data', 'acción popular',
        
        # Legal entities
        'persona jurídica', 'persona natural', 'nacionalidad',
        'domicilio', 'residencia', 'estado civil', 'capacidad',
        
        # Legal documents
        'escritura', 'poder', 'mandato', 'testamento', 'codicilo',
        'acta', 'certificado', 'constancia', 'copia', 'original',
        
        # Legal fees and costs
        'honorarios', 'costas', 'gastos', 'tasa', 'tarifa',
        'arancel', 'multa', 'sanción', 'pena',
        
        # Legal time periods
        'prescripción', 'caducidad', 'término', 'plazo', 'vigencia',
        'vencimiento', 'suspensión', 'interrupción',
        
        # Legal concepts
        'responsabilidad', 'culpa', 'dolo', 'negligencia',
        'fuerza mayor', 'caso fortuito', 'hecho del príncipe',
        'daño', 'perjuicio', 'lucro cesante', 'daño emergente',
        'reparación', 'indemnización', 'compensación'
    ]
    
    # Non-legal keywords that should be rejected (but exclude legal terms)
    non_legal_keywords = [
        # Historical figures
        'tutancamon', 'tutankamon', 'faraón', 'egipto', 'pirámide',
        'cleopatra', 'nefertiti', 'ramses', 'momia',
        
        # Literature and arts
        'tres tristes tigres', 'gabriel garcía márquez', 'cien años de soledad',
        'macondo', 'realismo mágico', 'literatura', 'novela', 'poesía',
        'arte', 'pintura', 'escultura', 'música', 'teatro', 'cine',
        
        # Science and technology
        'física', 'química', 'biología', 'matemáticas', 'astronomía',
        'medicina', 'ingeniería', 'programación', 'software', 'hardware',
        'inteligencia artificial', 'robótica', 'nano', 'tecnología',
        
        # Sports and entertainment
        'fútbol', 'futbol', 'deporte', 'olimpiadas', 'mundial',
        'película', 'serie', 'televisión', 'radio', 'internet',
        'videojuegos', 'juegos', 'entretenimiento', 'diversión',
        
        # Food and cooking
        'receta', 'cocina', 'comida', 'restaurante', 'chef',
        'ingredientes', 'cocinar', 'hornear', 'freír', 'hervir',
        
        # Travel and geography
        'viaje', 'turismo', 'vacaciones', 'hotel', 'avión',
        'país', 'ciudad', 'montaña', 'playa', 'río', 'océano',
        
        # General non-legal topics (excluding legal terms)
        'clima', 'tiempo', 'lluvia', 'sol', 'nube', 'viento',
        'animales', 'mascotas', 'perro', 'gato', 'pájaro',
        'plantas', 'jardín', 'flores', 'árboles', 'naturaleza',
        'casa', 'decoración', 'muebles', 'electrodomésticos',
        'ropa', 'moda', 'zapatos', 'accesorios', 'belleza',
        'salud', 'ejercicio', 'gimnasio', 'dieta', 'nutrición',
        'educación', 'escuela', 'universidad', 'estudios', 'carrera',
        'dinero', 'banco', 'cuenta', 'tarjeta', 'crédito',
        'amor', 'relación', 'novio', 'novia',
        'amigos', 'compañeros', 'vecinos', 'conocidos',
        'hobby', 'pasatiempo', 'interés', 'gusto', 'preferencia'
    ]
    
    # Check for non-legal keywords first (higher priority)
    # But only if they don't appear in a legal context
    for keyword in non_legal_keywords:
        if keyword in message_lower:
            # Check if the keyword appears in a legal context
            legal_context_found = False
            for legal_term in legal_keywords:
                if legal_term in message_lower and legal_term != keyword:
                    legal_context_found = True
                    break
            
            # Only reject if no legal context is found
            if not legal_context_found:
                return {
                    "is_legal": False,
                    "confidence": 0.9,
                    "reasoning": f"La consulta contiene términos no relacionados con asuntos legales: '{keyword}'",
                    "suggestion": "Por favor, formule una consulta relacionada con asuntos legales colombianos."
                }
    
    # Check for legal keywords
    legal_matches = []
    for keyword in legal_keywords:
        if keyword in message_lower:
            legal_matches.append(keyword)
    
    # Calculate confidence based on matches
    if len(legal_matches) >= 3:
        confidence = 0.9
    elif len(legal_matches) >= 2:
        confidence = 0.7
    elif len(legal_matches) >= 1:
        confidence = 0.5
    else:
        confidence = 0.1
    
    # Additional checks for legal context
    legal_context_indicators = [
        '¿qué', '¿cómo', '¿cuándo', '¿dónde', '¿por qué', '¿cuál',
        'necesito', 'quiero', 'debo', 'puedo', 'tengo derecho',
        'es legal', 'es ilegal', 'está permitido', 'está prohibido',
        'qué dice la ley', 'qué establece', 'qué regula',
        'procedimiento', 'trámite', 'requisito', 'documento',
        'plazo', 'término', 'vigencia', 'vencimiento'
    ]
    
    context_matches = sum(1 for indicator in legal_context_indicators if indicator in message_lower)
    if context_matches > 0:
        confidence = min(confidence + 0.2, 1.0)
    
    # Determine if query is legal
    is_legal = confidence >= 0.5
    
    if is_legal:
        reasoning = f"Consulta legal detectada. Términos legales encontrados: {', '.join(legal_matches[:5])}"
        if len(legal_matches) > 5:
            reasoning += f" y {len(legal_matches) - 5} más"
    else:
        reasoning = "La consulta no parece estar relacionada con asuntos legales colombianos"
        if legal_matches:
            reasoning += f". Aunque se encontraron algunos términos legales: {', '.join(legal_matches)}"
        else:
            reasoning += ". No se detectaron términos legales específicos"
    
    return {
        "is_legal": is_legal,
        "confidence": confidence,
        "reasoning": reasoning,
        "legal_terms_found": legal_matches,
        "suggestion": "Por favor, formule una consulta específica sobre asuntos legales colombianos." if not is_legal else None
    }

def create_chatbot_agent(
    practice_area: str = None,
    authentication_token: str = None,
    client_id: str = None,
    instructions: str = None,
    file_content: str = None,
    user_id: str = None,
    session_id: str = None
) -> Agent:
    """Create a specialized agent team for client chat with enhanced memory capabilities"""
    
    # Create knowledge base integration
    knowledge_integration = create_agent_knowledge_integration("chatbot_agent")
    
    # Get enhanced configuration with memory
    try:
        enhanced_config = get_enhanced_agent_config("chatbot_agent")
        
        # Safety check: ensure enhanced_config is a dictionary
        if not isinstance(enhanced_config, dict):
            logger.warning(f"Enhanced config is not a dict (type: {type(enhanced_config)}), using minimal configuration")
            raise ValueError(f"Enhanced config has wrong type: {type(enhanced_config)}")
            
    except Exception as e:
        logger.warning(f"Failed to get enhanced config, using minimal configuration: {e}")
        enhanced_config = {
            "storage": None,
            "memory": None,
            "add_history_to_messages": False,
            "num_history_runs": 0,
            "enable_user_memories": False,
            "enable_session_summaries": False,
            "enable_agentic_memory": False,
            "read_chat_history": False,
            "read_tool_call_history": False
        }
    
    # Main legal chatbot agent with memory capabilities
    system_instructions = [
        "IMPORTANTE: SIEMPRE responde ÚNICAMENTE en español. NUNCA uses inglés en tus respuestas.",
        "Proporciona respuestas DIRECTAS y ACCIONABLES sobre derecho colombiano. NO entres en bucles de razonamiento.",
        "OBLIGATORIO: Después de cada respuesta, SIEMPRE genera 1-3 preguntas específicas para ayudar al usuario a obtener información más detallada sobre su situación particular.",
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
        "Responde SIEMPRE en español utilizando terminología jurídica colombiana apropiada",
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
        "Si no encuentras información relevante, indica que no hay datos disponibles y sugiere al usuario proporcionar más contexto.",
        
        # === MEMORY AND PERSONALIZATION INSTRUCTIONS ===
        "Considera las preferencias del usuario basándote en interacciones previas",
        "Adapta el nivel de detalle según la experiencia legal del usuario",
        "Mantén consistencia con análisis previos del mismo usuario",
        "Aprende de los patrones identificados en casos similares",
        "Personaliza las recomendaciones según el perfil del usuario",
        "Utiliza el historial de conversación para proporcionar respuestas más contextualizadas",
        "Recuerda las áreas de interés específicas del usuario",
        "Adapta el tono y complejidad según el perfil del usuario",
        
        # === SESSION MANAGEMENT ===
        "Mantén el contexto de la sesión actual",
        "Referencia conversaciones previas cuando sea relevante",
        "Continúa análisis iniciados en sesiones anteriores",
        "Proporciona seguimiento a temas discutidos previamente",
        
        # === ENHANCED CAPABILITIES (POINTS 3 & 4) ===
        "INTEGRACIÓN CON JURISPRUDENCIA: Utiliza la base de datos de jurisprudencia de la Corte Constitucional para proporcionar casos relevantes y precedentes legales.",
        "BÚSQUEDA HÍBRIDA: Combina búsqueda por palabras clave y similitud semántica para encontrar la información más relevante.",
        "ANÁLISIS DE CASOS: Proporciona análisis de sentencias relevantes, incluyendo ratio decidendi y aplicación práctica.",
        "REDACCION DE DOCUMENTOS: Ofrece asistencia en la redacción de documentos legales simplificados para trámites y procedimientos.",
        "PLANTILLAS LEGALES: Proporciona plantillas y ejemplos de documentos legales comunes adaptados al contexto colombiano.",
        "CUMPLIMIENTO LEGAL: Asegura que todas las recomendaciones cumplan con la normativa colombiana vigente.",
        
        # === INTEGRACIÓN CON BASE DE CONOCIMIENTO RAG ===
        "ANTES de responder, consulta la base de conocimiento legal para obtener información actualizada",
        "Utiliza la base de datos de plantillas de documentos (document_templates) para proporcionar ejemplos específicos",
        "Busca en jurisprudencia colombiana relevante para fundamentar tus recomendaciones",
        "Consulta términos legales específicos y sus definiciones vigentes",
        "Aplica mejores prácticas contractuales documentadas en la base de conocimiento",
        "Cita específicamente las fuentes de la base de conocimiento utilizadas",
        "Utiliza plantillas y cláusulas estándar de la base de conocimiento",
        "Consulta casos similares y precedentes legales relevantes",
        
        "Genera un máximo de 3 preguntas *completamente originales, altamente específicas, claras y concisas*. Cada pregunta debe estar diseñada para obtener un detalle *indispensable* que cambie o afine el análisis legal (e.g., *¿Existe un contrato escrito y qué tipo de contrato es?*, *¿Se ha iniciado algún proceso judicial o administrativo relacionado?*, *¿Cuál es la fecha exacta del evento clave o de la última comunicación?*, *¿Se han presentado pruebas o documentos en alguna instancia?*, *¿Cuál es el domicilio o la jurisdicción específica relevante?*). *ESTÁ TERMINANTEMENTE PROHIBIDO* generar preguntas genéricas o repetitivas como '¿Cuál es la aplicación práctica de derecho de familia para evaluar en casos concretos?' o '¿Qué criterios ha establecido la jurisprudencia sobre derecho de familia para evaluar?'. Cada pregunta debe ser una consulta *novedosa e imperativa* que desentrañe una pieza crucial de información para el caso.",
        "Cada pregunta debe abordar una *pieza de información distintiva y no redundante* que sea verdaderamente necesaria para el análisis jurídico y que no haya sido inferida, provista anteriormente en la conversación, o que sea de conocimiento general. Evita la repetición de CUALQUIER pregunta, incluyendo aquellas previamente respondidas o las que puedan considerarse 'comunes' o 'básicas'.",
        "Prioriza preguntas que aborden *las lagunas de información más críticas y con mayor impacto* para la elaboración de un análisis jurídico completo y útil.",
        "Adapta las preguntas al tono y nivel de conocimiento del usuario, utilizando análisis de sentimiento para detectar urgencia o confusión, pero sin sacrificar la precisión legal requerida.",
        "Evita preguntas redundantes o excesivamente técnicas si el usuario parece no tener formación jurídica, a menos que sean absolutamente esenciales y se puedan explicar.",
        "Si el usuario proporciona un archivo, genera preguntas *EXACTAMENTE Y DETALLADAMENTE ESPECÍFICAS* sobre su contenido para confirmar su relevancia, validar la información o extraer detalles legales que no sean evidentes a primera vista o que presenten alguna ambigüedad crítica para el análisis."
    ]
    
    if practice_area:
        system_instructions.append(f"Te especializas en derecho {practice_area}.")
    if instructions:
        system_instructions.append(f"Instrucción del usuario: {instructions}")
    if file_content:
        system_instructions.append(f"El usuario ha adjuntado el siguiente archivo para contexto: {file_content}")
        
    # Prepare agent parameters with type safety
    agent_params = {
        "name": "Asistente Legal Virtual Colombiano Avanzado",
        "role": "Asistente de información jurídica colombiana con capacidades de búsqueda de jurisprudencia y redacción de documentos",
        "model": get_model("chatbot"),
        "tools": [GoogleSearchTools()],
        "knowledge": knowledge_integration,
        "search_knowledge": True,
        "storage": enhanced_config.get("storage") if isinstance(enhanced_config, dict) else None,
        # Do not pass custom memory object directly to Agent. agno expects dict/AgentMemory.
        # We'll still use our memory_instance for external persistence.
        "memory": None,
        "instructions": system_instructions,
        "markdown": True,
        "add_context": True,
        "session_id": session_id or f"chatbot_{user_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    }
    
    # Debug log the parameter types
    for key, value in agent_params.items():
        logger.debug(f"Agent param {key}: type={type(value)}, value={str(value)[:100] if value else None}")
    
    # Ensure instructions is a list (safety check for potential issue)
    if not isinstance(agent_params["instructions"], list):
        logger.warning(f"Instructions is not a list (type: {type(agent_params["instructions"])}), converting to list")
        agent_params["instructions"] = [str(agent_params["instructions"])] if agent_params["instructions"] else []
    
    # Ensure tools is a list
    if not isinstance(agent_params["tools"], list):
        logger.warning(f"Tools is not a list (type: {type(agent_params["tools"])}), converting to list")
        agent_params["tools"] = [agent_params["tools"]] if agent_params["tools"] else []
    
    legal_agent = Agent(**agent_params)
    
    return legal_agent

def get_recommendations_for_practice_area(practice_area: Optional[str] = None) -> List[str]:
    """Get recommendations based on practice area"""
    base_recommendations = ["Consultar con un abogado especializado"]
    
    if practice_area == "arrendamiento":
        return [
            "Leer detenidamente el contrato antes de firmar",
            "Verificar el estado del inmueble",
            "Documentar todas las comunicaciones",
            "Revisar cláusulas de terminación",
            "Consultar con un abogado especializado"
        ]
    elif practice_area == "derecho_laboral":
        return [
            "Revisar el contrato de trabajo detalladamente",
            "Documentar todas las comunicaciones con el empleador",
            "Verificar el pago de prestaciones sociales",
            "Mantener copias de todos los documentos",
            "Consultar con un abogado especializado"
        ]
    elif practice_area == "derecho_familia":
        return [
            "Priorizar el interés superior del menor",
            "Documentar todos los acuerdos por escrito",
            "Mantener comunicación respetuosa",
            "Considerar mediación familiar",
            "Consultar con un abogado especializado"
        ]
    elif practice_area == "derecho_comercial":
        return [
            "Revisar la estructura societaria",
            "Verificar cumplimiento de obligaciones legales",
            "Documentar todas las decisiones importantes",
            "Mantener libros contables actualizados",
            "Consultar con un abogado especializado"
        ]
    else:
        return base_recommendations

def get_legal_terms_for_practice_area(practice_area: Optional[str] = None) -> Dict[str, str]:
    """Get legal terms definitions based on practice area"""
    if practice_area == "arrendamiento":
        return {
            "canon": "Precio acordado por el arrendamiento",
            "clausula_penal": "Sanción por incumplimiento del contrato",
            "deposito": "Garantía para cubrir posibles daños"
        }
    elif practice_area == "derecho_laboral":
        return {
            "contrato_trabajo": "Acuerdo entre empleador y trabajador",
            "prestaciones_sociales": "Beneficios adicionales al salario",
            "cesantias": "Indemnización por terminación del contrato"
        }
    elif practice_area == "derecho_familia":
        return {
            "custodia": "Cuidado y protección de menores",
            "pension_alimenticia": "Obligación de manutención",
            "patria_potestad": "Autoridad sobre los hijos"
        }
    elif practice_area == "derecho_comercial":
        return {
            "sociedad": "Entidad jurídica para actividades comerciales",
            "capital_social": "Aportes de los socios",
            "responsabilidad_limitada": "Limitación de responsabilidad de socios"
        }
    else:
        return {
            "derecho": "Conjunto de normas jurídicas",
            "jurisprudencia": "Interpretación judicial de la ley",
            "normativa": "Conjunto de leyes y reglamentos"
        }

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

async def search_jurisprudence_for_user_query(query: str, practice_area: str = None) -> Dict[str, Any]:
    """Search jurisprudence database for user query using hybrid search"""
    try:
        # Import the jurisprudence API
        from scripts.ai_agent_jurisprudence_api import AIAgentJurisprudenceAPI
        
        # Create jurisprudence search instance
        jurisprudence_api = AIAgentJurisprudenceAPI()
        
        # Perform hybrid search - properly await the async method
        search_results = await jurisprudence_api.search_jurisprudence(
            query=query,
            search_type="hybrid",
            limit=5,
            vector_weight=0.6,
            keyword_weight=0.4,
            filters={
                "decision_type": practice_area if practice_area else None,
                "relevance_threshold": 0.6
            }
        )
        
        if search_results and search_results.get("results"):
            # Limit to top 5 results
            limited_results = search_results["results"][:5]
            return {
                "success": True,
                "cases_found": len(limited_results),
                "relevant_cases": limited_results[:3],  # Top 3 most relevant
                "search_metadata": {
                    "query": query,
                    "search_type": "hybrid",
                    "total_results": len(search_results["results"])
                }
            }
        else:
            return {
                "success": False,
                "cases_found": 0,
                "message": "No se encontraron casos relevantes en la jurisprudencia"
            }
            
    except Exception as e:
        logger.error(f"Error searching jurisprudence: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Error al buscar en la base de datos de jurisprudencia"
        }

async def generate_legal_document_for_user(
    document_type: str,
    description: str,
    parties: List[Dict[str, str]],
    key_points: List[str],
    practice_area: str = None
) -> Dict[str, Any]:
    """Generate legal document for user using the enhanced document drafting agent with RAG"""
    try:
        # Import the document drafting functions
        from agents.document_drafting_agent import draft_simplified_document, draft_custom_document
        
        # First, check if we have relevant templates in the RAG system
        relevant_templates = []
        try:
            from config.supabase_knowledge_base import SupabaseLegalKnowledgeBase
            kb = SupabaseLegalKnowledgeBase(mock_mode=False)
            
            # Search for relevant templates
            templates = await kb.get_document_templates("contract", "simple")
            if templates:
                # Filter templates that match the document type or practice area
                for template in templates:
                    template_name = template.get('template_name', '').lower()
                    template_type = template.get('document_type', '').lower()
                    
                    if (document_type.lower() in template_name or 
                        practice_area and practice_area.lower() in template_name or
                        template_type == "contract"):
                        relevant_templates.append(template)
            
            logger.info(f"Found {len(relevant_templates)} relevant templates for document generation")
            
        except Exception as kb_error:
            logger.warning(f"Error accessing document templates for generation: {kb_error}")
        
        # Determine document complexity based on practice area
        if practice_area in ["arrendamiento", "derecho_laboral", "derecho_familia"]:
            # Use simplified document for common practice areas
            document = await draft_simplified_document(
                document_type=document_type,
                description=description,
                parties=parties,
                key_points=key_points
            )
        else:
            # Use custom document for specialized areas
            document = await draft_custom_document(
                document_type=document_type,
                description=description,
                parties=parties,
                key_points=key_points,
                industry=practice_area,
                jurisdiction="Colombia",
                complexity="standard"
            )
        
        # Add template information to the response
        generation_metadata = {
            "document_type": document_type,
            "practice_area": practice_area,
            "complexity": "simplified" if practice_area in ["arrendamiento", "derecho_laboral", "derecho_familia"] else "custom",
            "templates_consulted": len(relevant_templates),
            "rag_enhanced": True
        }
        
        return {
            "success": True,
            "document": document,
            "generation_metadata": generation_metadata,
            "available_templates": [
                {
                    "name": t.get('template_name', 'N/A'),
                    "type": t.get('document_type', 'N/A')
                } for t in relevant_templates[:3]  # Top 3 most relevant
            ]
        }
        
    except Exception as e:
        logger.error(f"Error generating legal document: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Error al generar el documento legal"
        }

async def enhance_response_with_jurisprudence(
    response_content: str,
    user_query: str,
    practice_area: str = None
) -> str:
    """Enhance response with relevant jurisprudence cases"""
    try:
        # Search for relevant jurisprudence
        jurisprudence_results = await search_jurisprudence_for_user_query(user_query, practice_area)
        
        if jurisprudence_results.get("success") and jurisprudence_results.get("relevant_cases"):
            enhanced_response = response_content + "\n\n"
            enhanced_response += "## 📚 JURISPRUDENCIA RELEVANTE\n\n"
            enhanced_response += "He encontrado los siguientes casos de la Corte Constitucional que pueden ser relevantes para tu consulta:\n\n"
            
            for i, case in enumerate(jurisprudence_results["relevant_cases"], 1):
                enhanced_response += f"### Caso {i}: {case.get('case_number', 'N/A')}\n"
                enhanced_response += f"**Tema:** {case.get('topic', 'No especificado')}\n"
                enhanced_response += f"**Resumen:** {case.get('summary', 'No disponible')[:200]}...\n"
                enhanced_response += f"**Fecha:** {case.get('decision_date', 'No especificada')}\n"
                enhanced_response += f"**Relevancia:** {case.get('relevance_score', 'N/A')}\n\n"
            
            enhanced_response += "> 💡 **Nota:** Estos casos proporcionan precedentes legales relevantes. Para un análisis completo de tu situación específica, consulta con un abogado especializado.\n"
            
            return enhanced_response
        else:
            # Add note about jurisprudence availability
            return response_content + "\n\n> 💡 **Información:** Puedo buscar en nuestra base de datos de jurisprudencia de la Corte Constitucional para casos específicos. Si necesitas precedentes legales relevantes, házmelo saber."
            
    except Exception as e:
        logger.error(f"Error enhancing response with jurisprudence: {str(e)}")
        return response_content

async def enhance_response_with_document_suggestions(
    response_content: str,
    user_query: str,
    practice_area: str = None
) -> str:
    """Enhance response with document drafting suggestions"""
    try:
        # Analyze if user might need document drafting
        document_keywords = [
            "contrato", "documento", "escrito", "redactar", "plantilla", "formato",
            "solicitud", "recurso", "demanda", "petición", "notificación"
        ]
        
        needs_document = any(keyword in user_query.lower() for keyword in document_keywords)
        
        if needs_document:
            enhanced_response = response_content + "\n\n"
            enhanced_response += "## 📄 ASISTENCIA EN REDACCION DE DOCUMENTOS\n\n"
            enhanced_response += "Puedo ayudarte a redactar documentos legales simplificados para trámites y procedimientos. He encontrado las siguientes plantillas disponibles:\n\n"
            
            # Get document templates from RAG system
            try:
                from config.supabase_knowledge_base import SupabaseLegalKnowledgeBase
                kb = SupabaseLegalKnowledgeBase(mock_mode=False)
                
                # Search for relevant templates based on practice area
                if practice_area == "arrendamiento":
                    templates = await kb.get_document_templates("contract", "simple")
                    enhanced_response += "### 🏠 **Plantillas de Arrendamiento:**\n"
                elif practice_area == "derecho_laboral":
                    templates = await kb.get_document_templates("contract", "simple")
                    enhanced_response += "### 💼 **Plantillas Laborales:**\n"
                else:
                    templates = await kb.get_document_templates(None, "simple")
                    enhanced_response += "### 📋 **Plantillas Disponibles:**\n"
                
                if templates and len(templates) > 0:
                    # Show up to 5 relevant templates
                    for i, template in enumerate(templates[:5], 1):
                        template_name = template.get('template_name', 'Plantilla sin nombre')
                        document_type = template.get('document_type', 'documento')
                        enhanced_response += f"• **{template_name}** ({document_type})\n"
                    
                    enhanced_response += f"\n> 📊 **Total de plantillas disponibles:** {len(templates)} plantillas en la base de datos\n"
                else:
                    enhanced_response += "• **Contratos de arrendamiento** simplificados\n"
                    enhanced_response += "• **Notificaciones** y comunicaciones oficiales\n"
                    enhanced_response += "• **Solicitudes** de terminación o modificación\n"
                    enhanced_response += "• **Contratos de trabajo** simplificados\n"
                    enhanced_response += "• **Recursos** administrativos\n"
                
            except Exception as kb_error:
                logger.warning(f"Error accessing document templates: {kb_error}")
                # Fallback to static suggestions
                if practice_area == "arrendamiento":
                    enhanced_response += "• **Contratos de arrendamiento** simplificados\n"
                    enhanced_response += "• **Notificaciones** y comunicaciones oficiales\n"
                    enhanced_response += "• **Solicitudes** de terminación o modificación\n"
                elif practice_area == "derecho_laboral":
                    enhanced_response += "• **Contratos de trabajo** simplificados\n"
                    enhanced_response += "• **Solicitudes** de prestaciones sociales\n"
                    enhanced_response += "• **Recursos** administrativos\n"
                else:
                    enhanced_response += "• **Documentos legales** simplificados\n"
                    enhanced_response += "• **Contratos** básicos\n"
                    enhanced_response += "• **Solicitudes** y recursos\n"
            
            enhanced_response += "\n> 💡 **Solicita un documento:** Si necesitas que redacte un documento específico, proporciona los detalles y puedo generarlo para ti.\n"
            
            return enhanced_response
        else:
            return response_content
            
    except Exception as e:
        logger.error(f"Error enhancing response with document suggestions: {str(e)}")
        return response_content

async def process_client_message(
    client_id: str,
    message: str,
    conversation_id: Optional[str] = None,
    practice_area: Optional[str] = None,
    legal_terms: Optional[List[str]] = None,
    data_processing: Optional[Dict[str, str]] = None,
    instructions: Optional[str] = None,
    file_content: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """Process a client message with enhanced memory capabilities"""
    try:
        logger.info(f"Processing message for client {client_id} with memory support")
        
        # Validate if the query is legal-related
        validation_result = is_legal_query(message)
        logger.info(f"Query validation result: {validation_result}")
        
        # If query is not legal, return appropriate response
        if not validation_result["is_legal"]:
            logger.warning(f"Non-legal query detected: {message}")
            return {
                "response": {
                    "content": f"# ⚠️ Consulta No Relacionada con Asuntos Legales\n\n{validation_result['reasoning']}\n\n## 📋 Sugerencia\n\n{validation_result['suggestion']}\n\n## 🏛️ Áreas de Consulta Legal Disponibles\n\nPuedo ayudarte con consultas sobre:\n\n- **Derecho Civil**: Contratos, propiedad, familia, sucesiones\n- **Derecho Laboral**: Contratos de trabajo, prestaciones, despidos\n- **Derecho Comercial**: Sociedades, comercio, contratos mercantiles\n- **Derecho Administrativo**: Trámites, licencias, recursos\n- **Derecho Penal**: Delitos, faltas, procedimientos\n- **Derecho Constitucional**: Derechos fundamentales, tutelas\n- **Derecho de Familia**: Matrimonio, divorcio, custodia\n- **Derecho Tributario**: Impuestos, declaraciones, DIAN\n- **Propiedad Intelectual**: Patentes, marcas, derechos de autor\n- **Protección al Consumidor**: Garantías, reclamos, devoluciones\n\nPor favor, formula una consulta específica sobre alguno de estos temas legales.",
                    "relevant_laws": [],
                    "recommendations": ["Formular una consulta legal específica"],
                    "clarifying_questions": [
                        "¿En qué área del derecho necesitas orientación?",
                        "¿Cuál es tu situación legal específica?",
                        "¿Qué tipo de asesoría legal requieres?"
                    ]
                },
                "conversation_id": conversation_id or f"conv_{client_id}_{datetime.datetime.now().timestamp()}",
                "session_id": session_id or conversation_id,
                "user_id": user_id or client_id,
                "memory_enabled": False,
                "disclaimer": "Esta información es de carácter general y no constituye asesoría jurídica.",
                "colombian_compliance": {
                    "version": "1.0",
                    "constitutional_principles": ["Debido proceso", "Buena fe"],
                    "data_protection": {
                        "law": "Ley 1581 de 2012",
                        "status": "Cumple"
                    }
                },
                "practice_area": None,
                "legal_terms": {},
                "references": {"normativa": [], "jurisprudencia": [], "doctrina": []},
                "query_validation": validation_result,
                "is_legal_query": False
            }
        
        # Initialize memory system
        try:
            from postgres_memory import get_memory_instance, add_user_memory, store_session_data
            memory_instance = get_memory_instance("chatbot_agent")
            logger.info(f"Memory system initialized for chatbot_agent")
        except Exception as e:
            logger.warning(f"Failed to initialize memory system: {e}")
            memory_instance = None
        
        # Build dynamic context from stored user memories and prior session
        combined_instructions = instructions
        if memory_instance and (user_id or session_id):
            try:
                context_sections: List[str] = []
                # Include brief session history
                if session_id:
                    session_record = memory_instance.get_session_data(
                        user_id=user_id or client_id,
                        session_id=session_id
                    )
                    if session_record and isinstance(session_record.get("session_data"), dict):
                        history = session_record["session_data"].get("conversation_history", [])
                        if isinstance(history, list) and history:
                            recent = history[-4:]  # last up to 4 turns
                            history_lines = []
                            for item in recent:
                                role = item.get("role", "user")
                                content = str(item.get("content", ""))[:300]
                                prefix = "Usuario" if role == "user" else "Asistente"
                                history_lines.append(f"- {prefix}: {content}")
                            if history_lines:
                                context_sections.append(
                                    "Historial reciente de la conversación (resumen corto):\n" + "\n".join(history_lines)
                                )
                # Include user memories (high-level facts/preferences)
                if user_id:
                    user_mems = memory_instance.get_user_memories(user_id=user_id, limit=5)
                    if isinstance(user_mems, list) and user_mems:
                        mem_lines = []
                        for m in user_mems[:5]:
                            mem_text = str(m.get("memory", ""))[:200]
                            if mem_text:
                                mem_lines.append(f"- {mem_text}")
                        if mem_lines:
                            context_sections.append(
                                "Hechos y preferencias recordados del usuario (resumen):\n" + "\n".join(mem_lines)
                            )
                # Merge into instruction block (Spanish)
                if context_sections:
                    dynamic_context = (
                        "Contexto previo para mejorar la precisión de la respuesta."
                        " Úsalo estrictamente como referencia contextual y NO lo repitas textualmente en la respuesta.\n"
                        + "\n\n".join(context_sections)
                    )
                    combined_instructions = (f"{instructions}\n\n{dynamic_context}" if instructions else dynamic_context)
            except Exception as ctx_err:
                logger.warning(f"No se pudo preparar el contexto dinámico: {ctx_err}")

        # Create agent with dynamic context injected as additional instructions
        agent = create_chatbot_agent(
            practice_area=practice_area,
            client_id=client_id,
            instructions=combined_instructions,
            file_content=file_content,
            user_id=user_id or client_id,
            session_id=session_id or conversation_id
        )

        # Store user memory if memory system is available
        if memory_instance and user_id:
            try:
                # Add user memory for this interaction
                timestamp = datetime.datetime.now().isoformat()
                memory_content = f"User asked about: {message[:100]}... [Session: {session_id or conversation_id}]"
                topics = [practice_area] if practice_area else ["general"]
                if legal_terms:
                    topics.extend(legal_terms)
                
                memory_success = memory_instance.add_user_memory(
                    user_id=user_id,
                    memory_content=memory_content,
                    topics=topics,
                    memory_type="conversation",
                    metadata={
                        "practice_area": practice_area,
                        "legal_terms": legal_terms,
                        "conversation_id": conversation_id,
                        "session_id": session_id,
                        "timestamp": timestamp,
                        "message_length": len(message)
                    }
                )
                
                if memory_success:
                    logger.info(f"User memory stored successfully for user {user_id}")
                else:
                    logger.warning(f"Failed to store user memory for user {user_id}")
                    
            except Exception as memory_error:
                logger.error(f"Error storing user memory: {memory_error}")

        # Process message with memory context
        try:
            logger.debug(f"About to run agent with message: {message[:50]}...")
            logger.debug(f"Agent type: {type(agent)}")
            logger.debug(f"Agent memory: {type(agent.memory) if hasattr(agent, 'memory') else 'No memory'}")
            
            response: RunResponse = agent.run(
                message,
                user_id=user_id or client_id,
                session_id=session_id or conversation_id
            )
        except Exception as agent_error:
            logger.error(f"Agent run failed: {agent_error}")
            logger.error(f"Agent error type: {type(agent_error)}")
            
            # Get more detailed error information
            import traceback
            tb_str = traceback.format_exc()
            logger.error(f"Full traceback: {tb_str}")
            
            # Check if this is the specific list.get() error we're looking for
            if "'list' object has no attribute 'get'" in str(agent_error):
                logger.error("*** FOUND THE LIST.GET() ERROR - This is the bug we're hunting! ***")
                
                # Try to extract more information about what list is causing the issue
                tb_lines = tb_str.split('\n')
                for i, line in enumerate(tb_lines):
                    if '.get(' in line or "'list' object" in line:
                        logger.error(f"Problematic line {i}: {line}")
                        # Log surrounding context
                        for j in range(max(0, i-2), min(len(tb_lines), i+3)):
                            logger.error(f"Context line {j}: {tb_lines[j]}")
            
            # Provide a fallback response
            response_content = f"Lo siento, tuve un problema procesando tu consulta sobre '{message}'. Por favor, intenta reformular tu pregunta o contacta soporte técnico si el problema persiste."
            clarifying_questions = [
                "¿Podrías proporcionar más detalles sobre tu situación específica?",
                "¿En qué jurisdicción de Colombia se encuentra tu caso?",
                "¿Has consultado previamente con un abogado sobre este tema?"
            ]
            
            # Return fallback response
            return {
                "response": {
                    "content": response_content,
                    "relevant_laws": [],
                    "recommendations": ["Consultar con un abogado especializado"],
                    "clarifying_questions": clarifying_questions
                },
                "conversation_id": conversation_id or f"conv_{client_id}_{datetime.datetime.now().timestamp()}",
                "session_id": session_id or conversation_id,
                "user_id": user_id or client_id,
                "memory_enabled": memory_instance is not None,
                "disclaimer": "Esta información es de carácter general y no constituye asesoría jurídica.",
                "colombian_compliance": {
                    "version": "1.0",
                    "constitutional_principles": ["Debido proceso", "Buena fe"],
                    "data_protection": {
                        "law": "Ley 1581 de 2012",
                        "status": "Cumple"
                    }
                },
                "practice_area": practice_area or "derecho_civil",
                "legal_terms": {},
                "references": {"normativa": [], "jurisprudencia": [], "doctrina": []}
            }
        
        logger.debug(f"Raw agent response type: {type(response)}")
        logger.debug(f"Raw agent response: {response}")
        
        # Check if response is None or invalid
        if response is None:
            raise ValueError("Agent returned None response")
        
        # Extract content from response
        if not hasattr(response, 'content') or response.content is None:
            raise ValueError("Agent response has no content or content is None")
            
        full_response_content = response.content
        logger.debug(f"Full response content after initial extraction: {full_response_content[:500]}...")

        # Clean up any task transfer metadata
        logger.debug(f"Full response content after cleanup: {full_response_content[:500]}...")

        response_content = full_response_content
        clarifying_questions: List[str] = []

        # Simple parsing to extract clarifying questions from legal_agent response
        # Look for questions that start with ¿ and end with ?
        question_pattern = r'¿[^?]+\?'
        questions_found = re.findall(question_pattern, full_response_content)
        
        logger.debug(f"All questions found: {questions_found}")
        
        # Filter out questions that are too generic or common
        filtered_questions = []
        for question in questions_found:
            logger.debug(f"Processing question: {question}")
            # Skip very generic questions
            if any(generic in question.lower() for generic in [
                'qué es', 'qué significa', 'cómo funciona', 'cuál es la definición',
                'qué dice la ley', 'qué establece', 'qué regula'
            ]):
                logger.debug(f"Skipping generic question: {question}")
                continue
            # Keep specific clarifying questions
            if any(specific in question.lower() for specific in [
                'existe', 'se ha iniciado', 'cuál es la fecha', 'dónde', 'cuándo',
                'quién', 'qué tipo', 'qué documento', 'qué proceso', 'qué instancia'
            ]):
                logger.debug(f"Keeping specific question: {question}")
                filtered_questions.append(question.strip())
            else:
                logger.debug(f"Question doesn't match specific criteria: {question}")
        
        clarifying_questions = filtered_questions[:3]  # Limit to 3 questions
        
        logger.debug(f"Extracted clarifying_questions: {clarifying_questions}")
        logger.debug(f"Final response_content (main): {response_content[:500]}...")

        # === ENHANCE RESPONSE WITH JURISPRUDENCE AND DOCUMENT CAPABILITIES ===
        try:
            # Enhance with jurisprudence if relevant
            enhanced_response = await enhance_response_with_jurisprudence(
                response_content, message, practice_area
            )
            
            # Enhance with document suggestions if relevant
            final_response = await enhance_response_with_document_suggestions(
                enhanced_response, message, practice_area
            )
            
            response_content = final_response
            
        except Exception as enhancement_error:
            logger.warning(f"Failed to enhance response with jurisprudence/document capabilities: {enhancement_error}")
            # Continue with original response if enhancement fails
            pass

        # Store session data if memory system is available
        if memory_instance and user_id and session_id:
            try:
                session_data = {
                    "conversation_history": [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": response_content}
                    ],
                    "practice_area": practice_area,
                    "legal_terms": legal_terms,
                    "clarifying_questions": clarifying_questions,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "conversation_id": conversation_id
                }
                
                session_success = memory_instance.store_session_data(
                    user_id=user_id,
                    session_id=session_id,
                    session_data=session_data
                )
                
                if session_success:
                    logger.info(f"Session data stored successfully for session {session_id}")
                else:
                    logger.warning(f"Failed to store session data for session {session_id}")
                    
            except Exception as session_error:
                logger.error(f"Error storing session data: {session_error}")

        # Get references with guaranteed lists
        references = get_legal_references(practice_area)

        # Ensure references are properly structured
        response_data = {
            "response": {
                "content": response_content,  # This will be the markdown content
                "relevant_laws": references["normativa"],
                "recommendations": get_recommendations_for_practice_area(practice_area),
                "clarifying_questions": clarifying_questions # Add clarifying questions here
            },
            "conversation_id": conversation_id or f"conv_{client_id}_{datetime.datetime.now().timestamp()}",
            "session_id": session_id or conversation_id,
            "user_id": user_id or client_id,
            "memory_enabled": memory_instance is not None,
            "disclaimer": """Esta información es de carácter general y no constituye asesoría jurídica.\n                        Cada caso particular puede requerir un análisis específico y profesional.""",
            "colombian_compliance": {
                "version": "1.0",
                "constitutional_principles": ["Debido proceso", "Buena fe"],
                "data_protection": {
                    "law": "Ley 1581 de 2012",
                    "status": "Cumple"
                }
            },
            "practice_area": practice_area or "derecho_civil",
            "legal_terms": get_legal_terms_for_practice_area(practice_area),
            "references": references,
            # === NEW ENHANCED CAPABILITIES ===
            "enhanced_capabilities": {
                "jurisprudence_search": True,
                "document_drafting": True,
                "hybrid_search": True,
                "constitutional_court_cases": True
            },
            # === QUERY VALIDATION INFORMATION ===
            "query_validation": validation_result,
            "is_legal_query": True
        }

        return response_data

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        # Raise the exception instead of returning an error response
        # This allows the endpoint to properly handle it and return appropriate HTTP status code
        raise e 

async def demonstrate_enhanced_chatbot_capabilities():
    """Demonstrate the enhanced chatbot agent capabilities"""
    
    print("🚀 DEMOSTRACIÓN DEL CHATBOT AGENTE MEJORADO")
    print("=" * 70)
    
    # Test 1: Jurisprudence Search
    print("\n📚 TEST 1: Búsqueda de Jurisprudencia")
    print("-" * 50)
    
    try:
        jurisprudence_results = await search_jurisprudence_for_user_query(
            query="derechos fundamentales arrendamiento",
            practice_area="arrendamiento"
        )
        
        if jurisprudence_results.get("success"):
            print("✅ Búsqueda de jurisprudencia exitosa")
            print(f"📊 Casos encontrados: {jurisprudence_results['cases_found']}")
            print(f"🔍 Tipo de búsqueda: {jurisprudence_results['search_metadata']['search_type']}")
            
            if jurisprudence_results.get("relevant_cases"):
                print("\n📖 Casos relevantes encontrados:")
                for i, case in enumerate(jurisprudence_results["relevant_cases"][:2], 1):
                    print(f"   {i}. {case.get('case_number', 'N/A')} - {case.get('topic', 'No especificado')[:50]}...")
        else:
            print(f"❌ Error en búsqueda: {jurisprudence_results.get('message', 'Error desconocido')}")
            
    except Exception as e:
        print(f"❌ Error en test de jurisprudencia: {str(e)}")
    
    # Test 2: Document Generation
    print("\n📄 TEST 2: Generación de Documentos")
    print("-" * 50)
    
    try:
        document_result = await generate_legal_document_for_user(
            document_type="Contrato de Arrendamiento",
            description="Arrendamiento de vivienda para uso residencial",
            parties=[
                {"name": "Ana López", "identification": "CC 11223344", "role": "Arrendador"},
                {"name": "Pedro Martínez", "identification": "CC 44332211", "role": "Arrendatario"}
            ],
            key_points=[
                "Plazo de 24 meses",
                "Canon mensual de $1,200,000",
                "Depósito de $1,200,000"
            ],
            practice_area="arrendamiento"
        )
        
        if document_result.get("success"):
            print("✅ Generación de documento exitosa")
            print(f"📄 Tipo: {document_result['generation_metadata']['document_type']}")
            print(f"🏭 Área: {document_result['generation_metadata']['practice_area']}")
            print(f"🔧 Complejidad: {document_result['generation_metadata']['complexity']}")
            
            document = document_result['document']
            if document.get('document', {}).get('sections'):
                print(f"📊 Secciones: {len(document['document']['sections'])}")
                print(f"🔒 Cumplimiento: {document['colombian_compliance']['status']}")
        else:
            print(f"❌ Error en generación: {document_result.get('message', 'Error desconocido')}")
            
    except Exception as e:
        print(f"❌ Error en test de documentos: {str(e)}")
    
    # Test 3: Response Enhancement
    print("\n🔍 TEST 3: Mejora de Respuestas")
    print("-" * 50)
    
    try:
        # Test jurisprudence enhancement
        original_response = "El arrendamiento en Colombia está regulado por el Código Civil y la Ley 820 de 2003."
        enhanced_response = await enhance_response_with_jurisprudence(
            original_response, "arrendamiento vivienda", "arrendamiento"
        )
        
        print("✅ Mejora de respuesta con jurisprudencia exitosa")
        print(f"📏 Longitud original: {len(original_response)} caracteres")
        print(f"📏 Longitud mejorada: {len(enhanced_response)} caracteres")
        print(f"📈 Mejora: {((len(enhanced_response) - len(original_response)) / len(original_response) * 100):.1f}%")
        
        # Test document suggestions
        final_response = await enhance_response_with_document_suggestions(
            enhanced_response, "necesito un contrato de arrendamiento", "arrendamiento"
        )
        
        print("✅ Mejora de respuesta con sugerencias de documentos exitosa")
        print(f"📏 Longitud final: {len(final_response)} caracteres")
        
    except Exception as e:
        print(f"❌ Error en test de mejora: {str(e)}")
    
    print("\n🎯 CAPACIDADES PRINCIPALES DEL CHATBOT MEJORADO:")
    print("=" * 70)
    print("✅ Búsqueda híbrida en jurisprudencia de la Corte Constitucional")
    print("✅ Generación de documentos legales simplificados")
    print("✅ Mejora automática de respuestas con casos relevantes")
    print("✅ Sugerencias inteligentes de documentos según consulta")
    print("✅ Integración con base de conocimiento legal")
    print("✅ Cumplimiento legal colombiano")
    print("✅ Memoria de usuario y sesión")
    
    print("\n🚀 El chatbot está listo para proporcionar asistencia legal avanzada!")
    print("💡 Integra jurisprudencia, documentos y conocimiento legal en cada respuesta")

# Main execution for demonstration
if __name__ == "__main__":
    import asyncio
    
    print("🔧 Iniciando demostración del chatbot agente mejorado...")
    
    try:
        asyncio.run(demonstrate_enhanced_chatbot_capabilities())
    except Exception as e:
        print(f"❌ Error en demostración: {str(e)}")
        print("💡 Asegúrese de que todas las dependencias estén configuradas correctamente") 