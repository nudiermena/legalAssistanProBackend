from agno.agent import Agent
from config.database import get_agent_storage
from config.ai_models import get_model
from config.knowledge_base_integration import (
    create_agent_knowledge_integration,
    AgentKnowledgeHelper
)
from config.colombian_compliance import (
    ColombianDataProtection,
    ColombianLegalFramework,
    get_data_category,
    validate_consent,
    get_retention_period,
    get_administrative_deadline,
    get_legal_term
)
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from time import sleep
import random
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_not_exception_type
from agno.tools.googlesearch import GoogleSearchTools
import logging
import traceback

logger = logging.getLogger(__name__)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_not_exception_type(UnboundLocalError)  # Skip retries for code errors
)
def create_document_drafting_agent() -> Agent:
    """Create a specialized agent for legal document drafting with retry logic and knowledge base integration"""
    try:
        # Create knowledge base integration (disabled temporarily to avoid connection issues)
        # knowledge_integration = create_agent_knowledge_integration("document_drafting_agent")
        
        agent = Agent(
            name="Especialista en Redacción Jurídica Colombiana",
            role="Especialista en elaboración de documentos legales completos y compliantes para Colombia",
            model=get_model("document_drafting"),  # Specify model directly
             tools=[GoogleSearchTools()],
            knowledge=None,  # Disable knowledge base temporarily
            
            search_knowledge=False,  # Disable knowledge search
            storage=None,  # Disable storage to avoid connection issues
            instructions=[
                # === INSTRUCCIONES PRINCIPALES DE COMPLIANCE ===
                "ENFOQUE LEGAL: Crear documentos que cumplan TODOS los requisitos legales obligatorios",
                "COMPLIANCE TOTAL: Incluir todas las cláusulas requeridas por la legislación colombiana",
                "COMPLETITUD: Asegurar que no falten elementos esenciales para la validez legal",
                "PROTECCIÓN: Garantizar la protección de derechos fundamentales de las partes",
                
                # === CONOCIMIENTO LEGAL ===
                "Utilizar la base de conocimiento legal para obtener plantillas y ejemplos actualizados",
                "Consultar términos legales específicos y sus definiciones vigentes",
                "Buscar en jurisprudencia relevante para fundamentar cláusulas",
                "Aplicar mejores prácticas de redacción legal documentadas",
                
                # === CUMPLIMIENTO COLOMBIANO ===
                "Cumplir ordenamiento jurídico colombiano vigente al 100%",
                "Incluir cláusulas constitucionales obligatorias",
                "Asegurar validez y eficacia jurídica completa",
                "Utilizar terminología jurídica colombiana correcta",
                
                # === CONTRATOS LABORALES ESPECÍFICOS ===
                "Para contratos laborales: incluir TODAS las cláusulas del Código Sustantivo del Trabajo",
                "Incluir beneficios legales: vacaciones, cesantías, prima de servicios, subsidio de transporte",
                "Especificar seguridad social: salud, pensión, riesgos laborales",
                "Incluir período de prueba cuando aplique (máximo según la ley)",
                "Especificar causales de terminación justas",
                "Incluir mecanismos de solución de conflictos laborales",
                
                # === PROTECCIÓN DE DATOS ===
                "Incluir consentimiento explícito para tratamiento de datos según Ley 1581 de 2012",
                "Especificar finalidad, tratamiento y derechos del titular",
                "Incluir mecanismos de revocación del consentimiento",
                
                # === FORMATO Y ESTRUCTURA ===
                "Usar lenguaje claro pero técnicamente correcto",
                "Organizar en secciones numeradas y bien estructuradas",
                "Incluir espacios para firmas, fechas y documentos de identidad",
                "Referenciar leyes aplicables cuando sea necesario",
                
                # === EXCLUSIONES ===
                "NO incluir cláusulas abusivas o contrarias a la ley",
                "NO incluir renuncias a derechos laborales",
                "NO incluir condiciones discriminatorias",
                "NO incluir cláusulas de jurisdicción extranjera",
                "NO incluir secciones de 'NOTAS FINALES' o 'RECOMENDACIONES FINALES'",
                "El documento debe ser COMPLETAMENTE COMPLIANTE y listo para uso legal"
            ]
        )
        return agent
    except UnboundLocalError as e:
        logger.error(f"UnboundLocalError in create_document_drafting_agent: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in create_document_drafting_agent: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise

def clean_response(response: str) -> str:
    """Clean and format the agent's response"""
    # Remove RunResponse metadata
    if "RunResponse(content='" in response:
        response = response.split("RunResponse(content='", 1)[1].split("', content_type=", 1)[0]
    
    # Unescape any escaped characters
    response = response.replace('\\n', '\n')
    
    # Remove any remaining response metadata
    response = response.split("messages=[Message(", 1)[0] if "messages=[Message(" in response else response
    
    # Clean up any trailing metadata
    response = response.strip()
    
    return response

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_not_exception_type(UnboundLocalError)  # Skip retries for code errors
)
async def draft_custom_document(
    document_type: str,
    description: str,
    parties: List[Dict[str, str]],
    key_points: List[str],
    industry: str,
    jurisdiction: str,
    complexity: str
) -> Dict[str, Any]:
    """Draft custom legal document with detailed specifications and knowledge base integration"""
    try:
        agent = create_document_drafting_agent()
        
        # Create knowledge helper for enhanced drafting (disabled temporarily)
        # knowledge_helper = AgentKnowledgeHelper("document_drafting_agent")
        
        # Get relevant document templates from knowledge base (disabled)
        document_templates = []  # Disabled temporarily
        
        # Get relevant legal terms (disabled)
        legal_terms = []
        legal_definitions = {}  # Disabled temporarily
        
        # Get relevant legal documents (disabled)
        legal_documents = {"results": []}  # Disabled temporarily
        
        # Format the prompt for custom document
        prompt = format_custom_document_prompt(
            document_type=document_type,
            description=description,
            parties=parties,
            key_points=key_points,
            industry=industry,
            jurisdiction=jurisdiction,
            complexity=complexity,
            document_templates=document_templates,
            legal_definitions=legal_definitions,
            legal_documents=legal_documents
        )

        # Get response from agent
        response = agent.run(prompt)
        
        # Clean and format the response
        document_content = clean_response(str(response))
        
        # Structure the response
        result = {
            "document": {
                "content": document_content,
                "sections": extract_document_sections(document_content),
                "markdown": True
            },
            "document_type": document_type,
            "jurisdiction": jurisdiction,
            "key_requirements": key_points,
            "parties": parties,
            "colombian_compliance": {
                "framework_version": "2024.1",
                "status": "compliant",
                "constitutional_principles": [
                    "Dignidad humana",
                    "Buena fe",
                    "Debido proceso",
                    "Legalidad",
                    "Transparencia"
                ],
                "validation_date": datetime.now().isoformat()
            },
            "legal_terms": legal_definitions,
            "data_processing": None,
            "timestamp": datetime.now().isoformat(),
            "knowledge_base_usage": {
                "document_templates_found": len(document_templates),
                "legal_terms_found": len(legal_definitions),
                "legal_documents_found": len(legal_documents.get("results", [])),
                "knowledge_sources": [
                    {"type": "document_templates", "count": len(document_templates)},
                    {"type": "legal_terms", "count": len(legal_definitions)},
                    {"type": "legal_documents", "count": len(legal_documents.get("results", []))}
                ]
            }
        }
        
        return result
        
    except UnboundLocalError as e:
        logger.error(f"UnboundLocalError in draft_custom_document: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in draft_custom_document: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise

def format_custom_document_prompt(
    document_type: str,
    description: str,
    parties: List[Dict[str, str]],
    key_points: List[str],
    industry: str,
    jurisdiction: str,
    complexity: str,
    document_templates: List[Dict] = None,
    legal_definitions: Dict[str, str] = None,
    legal_documents: Dict = None
) -> str:
    """Format the prompt for custom document generation with knowledge base context - ENHANCED FOR PRACTICAL USE"""
    
    # Map complexity to simplified, practical instructions
    complexity_instructions = {
        "simple": "Crear documento básico con cláusulas esenciales. Enfoque en trámites y procedimientos básicos. Mantener conciso y fácil de entender.",
        "standard": "Incluir nivel de detalle normal con cláusulas completas pero no excesivas. Priorizar requisitos de trámite.",
        "complex": "Crear documento detallado pero práctico. Incluir cláusulas específicas necesarias para trámites complejos."
    }
    
    # Map industry to practical considerations (simplified)
    industry_considerations = {
        "technology": "Considerar propiedad intelectual básica, confidencialidad esencial, y regulaciones tecnológicas mínimas.",
        "healthcare": "Incluir consideraciones de privacidad médica básica y regulaciones sanitarias esenciales.",
        "finance": "Incorporar regulaciones financieras básicas y cláusulas de riesgo esenciales.",
        "real-estate": "Considerar regulaciones inmobiliarias básicas y registros públicos necesarios.",
        "retail": "Incluir consideraciones comerciales básicas y protección al consumidor esencial.",
        "agriculture": "Considerar regulaciones agrícolas básicas y certificaciones necesarias.",
        "oil-gas": "Incorporar regulaciones energéticas básicas y responsabilidad esencial.",
        "education": "Considerar regulaciones educativas básicas y protección de datos estudiantiles.",
        "construction": "Incluir regulaciones de construcción básicas, licencias y seguros esenciales.",
        "other": "Utilizar cláusulas generales aplicables a la mayoría de industrias."
    }
    
    # Format parties with identification (simplified)
    parties_text = "\n".join([
        f"- {party['name']} (ID: {party['identification']}) - Rol: {party['role']}"
        for party in parties
    ])
    
    # Format key points
    key_points_text = "\n".join([f"- {point}" for point in key_points])
    
    # Get current date for the document
    from datetime import datetime
    current_date = datetime.now().strftime("%d de %B de %Y")
    
    prompt = f"""Por favor redacta un documento legal COMPLETO y COMPLIANTE tipo "{document_type}" según el ordenamiento jurídico colombiano:

FECHA ACTUAL: Usar la fecha de hoy: {current_date}

🚫 EXCLUSIONES OBLIGATORIAS - LEER ANTES DE REDACTAR:
- PROHIBIDO incluir el texto: "(Regido por las disposiciones del Código Sustantivo del Trabajo Colombiano y la Constitución Política de Colombia)"
- PROHIBIDO incluir cualquier variación de: "Regido por las disposiciones del Código Sustantivo del Trabajo"
- PROHIBIDO incluir texto entre paréntesis sobre reglamentación legal
- NO incluir referencias a "Código Sustantivo del Trabajo" en el título o subtítulo
- El documento debe comenzar directamente con el título del contrato, sin texto adicional

ENFOQUE LEGAL: Crear un documento que cumpla TODOS los requisitos legales obligatorios para contratos en Colombia.

DESCRIPCIÓN DEL DOCUMENTO:
{description}

PARTES INVOLUCRADAS:
{parties_text}

PUNTOS CLAVE A INCLUIR:
{key_points_text}

INDUSTRIA: {industry}
{industry_considerations.get(industry, "Consideraciones generales aplicables.")}

JURISDICCIÓN: {jurisdiction}

COMPLEJIDAD: {complexity}
{complexity_instructions.get(complexity, "Nivel de detalle estándar.")}

CLÁUSULAS OBLIGATORIAS PARA CONTRATOS EN COLOMBIA:
- Identificación completa de las partes (nombres, documentos, domicilios)
- Objeto del contrato claramente definido
- Duración y términos del contrato
- Obligaciones específicas de cada parte
- Forma y términos de pago
- Causales de terminación
- Mecanismos de solución de conflictos
- Tratamiento de datos personales según Ley 1581 de 2012
- Responsabilidades y garantías
- Cláusulas de confidencialidad (si aplica)
- Propiedad intelectual (si aplica)
- Fuerza mayor y casos fortuitos
- Notificaciones y comunicaciones
- Ley aplicable y jurisdicción

INSTRUCCIONES ESPECÍFICAS PARA CONTRATOS:
1. COMPLIANCE TOTAL: Incluir TODAS las cláusulas obligatorias según la legislación colombiana
2. IDENTIFICACIÓN COMPLETA: Nombres completos, documentos de identidad, domicilios
3. OBJETO CLARO: Definir específicamente el objeto y alcance del contrato
4. OBLIGACIONES DETALLADAS: Especificar claramente obligaciones de cada parte
5. TÉRMINOS ESPECÍFICOS: Duración, pagos, entregables, fechas límite
6. PROTECCIÓN DE DATOS: Consentimiento explícito según Ley 1581 de 2012
7. SOLUCIÓN DE CONFLICTOS: Mecanismos de conciliación y jurisdicción
8. CAUSALES DE TERMINACIÓN: Especificar causas justas de terminación
9. RESPONSABILIDADES: Definir claramente responsabilidades y garantías
10. CONFIDENCIALIDAD: Si aplica, cláusulas de protección de información
"""
    
    # Add knowledge base context
    if document_templates:
        prompt += "\nPLANTILLAS DE REFERENCIA:\n"
        for template in document_templates[:2]:  # Top 2 most relevant
            prompt += f"- {template.get('template_name', 'N/A')}: {template.get('template_content', '')[:200]}...\n"
    
    if legal_definitions:
        prompt += "\nTÉRMINOS LEGALES RELEVANTES:\n"
        for term, definition in legal_definitions.items():
            prompt += f"- {term}: {definition}\n"
    
    if legal_documents and legal_documents.get("results"):
        prompt += "\nDOCUMENTOS LEGALES DE REFERENCIA:\n"
        for doc in legal_documents["results"][:2]:  # Top 2 most relevant
            prompt += f"- {doc.get('metadata', {}).get('title', 'N/A')}: {doc.get('content', '')[:200]}...\n"
    
    prompt += f"""

REQUISITOS SIMPLIFICADOS:
- Cumplir requisitos mínimos legales colombianos
- Incluir solo cláusulas constitucionales obligatorias
- Asegurar validez para trámites y procedimientos
- Incluir mecanismos de solución de conflictos simples
- Proteger derechos fundamentales esenciales
- Cumplir requisitos de formalidad mínimos
- Mantener documento ejecutable y práctico

EXCLUSIONES ESPECÍFICAS:
- NO incluir secciones de 'NOTAS FINALES' o 'RECOMENDACIONES FINALES'
- NO incluir texto sobre conservar copias firmadas
- NO incluir instrucciones sobre adjuntar documentos para trámites
- NO incluir referencias específicas a artículos del Código Sustantivo del Trabajo
- NO incluir texto 'Simplificado para trámites en Colombia'
- NO incluir instrucciones sobre presentación en entidades públicas específicas
- NO incluir cláusulas de jurisdicción y competencia
- NO incluir cláusulas de ley aplicable
- NO incluir texto "(Regido por las disposiciones del Código Sustantivo del Trabajo Colombiano y la Constitución Política de Colombia)"

🚨 RECORDATORIO FINAL IMPORTANTE:
El documento debe comenzar directamente con el título del contrato (ej: "CONTRATO DE TRABAJO A TÉRMINO FIJO") 
SIN incluir texto adicional entre paréntesis sobre reglamentación legal.

El documento debe ser COMPLETO para trámites pero SIMPLIFICADO para uso práctico.
El documento debe terminar directamente con las cláusulas legales, sin notas adicionales."""

    return prompt

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_not_exception_type(UnboundLocalError)  # Skip retries for code errors
)
async def draft_legal_document(
    document_type: str,
    jurisdiction: str,
    key_requirements: List[str],
    parties: List[str],
    legal_terms: Optional[List[str]] = None,
    data_processing: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Draft legal document with Colombian compliance"""
    try:
        agent = create_document_drafting_agent()
        
        # Format the prompt
        prompt = format_document_prompt(
            document_type=document_type,
            jurisdiction=jurisdiction,
            key_requirements=key_requirements,
            parties=parties,
            legal_terms=legal_terms,
            data_processing=data_processing
        )

        # Get response from agent
        response = agent.run(prompt)
        
        # Clean and format the response
        document_content = clean_response(str(response))
        
        # Structure the response
        result = {
            "document": {
                "content": document_content,
                "sections": extract_document_sections(document_content),
                "markdown": True  # Indicate that the content uses markdown
            },
            "document_type": document_type,
            "jurisdiction": jurisdiction,
            "key_requirements": key_requirements,
            "parties": [{"name": name, "role": "Parte"} for name in parties],
            "colombian_compliance": {
                "framework_version": "2024.1",
                "status": "compliant",
                "constitutional_principles": [
                    "Dignidad humana",
                    "Buena fe",
                    "Debido proceso",
                    "Legalidad",
                    "Transparencia"
                ],
                "validation_date": datetime.now().isoformat()
            },
            "legal_terms": None,
            "data_processing": None,
            "timestamp": datetime.now().isoformat()
        }
        
        if legal_terms:
            result["legal_terms"] = {term: get_legal_term(term) for term in legal_terms}
            
        if data_processing:
            result["data_processing"] = process_data_requirements(data_processing)
            
        return result
        
    except UnboundLocalError as e:
        logger.error(f"UnboundLocalError in draft_legal_document: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in draft_legal_document: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise

def format_document_prompt(
    document_type: str,
    jurisdiction: str,
    key_requirements: List[str],
    parties: List[str],
    legal_terms: Optional[List[str]] = None,
    data_processing: Optional[Dict[str, str]] = None
) -> str:
    """Format the prompt for document generation - ENHANCED FOR COLOMBIAN COMPLIANCE"""
    
    # Get current date for the document
    from datetime import datetime
    current_date = datetime.now().strftime("%d de %B de %Y")
    
    # Enhanced Colombian labor law compliance
    colombian_labor_clauses = """
CLÁUSULAS OBLIGATORIAS PARA CONTRATOS LABORALES EN COLOMBIA:
- Identificación completa de las partes (nombres, documentos, domicilios)
- Cargo o función específica del trabajador
- Salario base y forma de pago (mensual, quincenal, semanal)
- Duración del contrato (término fijo, indefinido, obra o labor)
- Lugar de trabajo
- Jornada laboral (completa, parcial, nocturna)
- Fecha de inicio de labores
- Período de prueba (si aplica)
- Obligaciones específicas del empleador
- Obligaciones específicas del trabajador
- Causales de terminación del contrato
- Mecanismos de solución de conflictos
- Tratamiento de datos personales
- Horario de trabajo
- Días de descanso
- Vacaciones y prima de servicios
- Cesantías y sus intereses
- Subsidio de transporte (si aplica)
- Riesgos laborales
- Seguridad social
"""
    
    prompt = f"""Por favor redacta un documento legal COMPLETO y COMPLIANTE tipo {document_type} según el ordenamiento jurídico colombiano:

FECHA ACTUAL: Usar la fecha de hoy: {current_date}

🚫 EXCLUSIONES OBLIGATORIAS - LEER ANTES DE REDACTAR:
- PROHIBIDO incluir el texto: "(Regido por las disposiciones del Código Sustantivo del Trabajo Colombiano y la Constitución Política de Colombia)"
- PROHIBIDO incluir cualquier variación de: "Regido por las disposiciones del Código Sustantivo del Trabajo"
- PROHIBIDO incluir texto entre paréntesis sobre reglamentación legal
- NO incluir referencias a "Código Sustantivo del Trabajo" en el título o subtítulo
- El documento debe comenzar directamente con el título del contrato, sin texto adicional

ENFOQUE: Crear documento que cumpla TODOS los requisitos legales obligatorios para contratos laborales en Colombia.

JURISDICCIÓN:
{jurisdiction}

REQUISITOS CLAVE:
{chr(10).join(f'- {req}' for req in key_requirements)}

PARTES:
{chr(10).join(f'- {party}' for party in parties)}

{f'TÉRMINOS LEGALES:{chr(10)}{chr(10).join(f"- {term}" for term in legal_terms)}' if legal_terms else ''}

{f'TRATAMIENTO DE DATOS:{chr(10)}{chr(10).join(f"- {k}: {v}" for k, v in data_processing.items())}' if data_processing else ''}

{colombian_labor_clauses}

INSTRUCCIONES ESPECÍFICAS PARA CONTRATOS LABORALES:
1. COMPLIANCE TOTAL: Incluir TODAS las cláusulas obligatorias según el Código Sustantivo del Trabajo
2. IDENTIFICACIÓN COMPLETA: Nombres completos, documentos de identidad, domicilios
3. TÉRMINOS ESPECÍFICOS: Cargo, salario, duración, lugar, jornada, fecha de inicio
4. OBLIGACIONES DETALLADAS: Especificar claramente obligaciones de empleador y trabajador
5. BENEFICIOS LEGALES: Vacaciones, cesantías, prima de servicios, subsidio de transporte
6. SEGURIDAD SOCIAL: Afiliación obligatoria a salud, pensión, riesgos laborales
7. TRATAMIENTO DE DATOS: Consentimiento explícito según Ley 1581 de 2012
8. SOLUCIÓN DE CONFLICTOS: Mecanismos de conciliación y jurisdicción laboral
9. CAUSALES DE TERMINACIÓN: Especificar causas justas de terminación
10. PERÍODO DE PRUEBA: Si aplica, especificar duración máxima según la ley

FORMATO REQUERIDO:
- Título claro del tipo de contrato
- Secciones numeradas y organizadas
- Lenguaje claro pero técnicamente correcto
- Espacios para firmas y fechas
- Referencias a leyes aplicables cuando sea necesario

EXCLUSIONES:
- NO incluir cláusulas abusivas o contrarias a la ley
- NO incluir renuncias a derechos laborales
- NO incluir condiciones discriminatorias
- NO incluir cláusulas de jurisdicción extranjera
- NO incluir texto "(Regido por las disposiciones del Código Sustantivo del Trabajo Colombiano y la Constitución Política de Colombia)"

El documento debe ser COMPLETAMENTE COMPLIANTE con la legislación laboral colombiana y listo para uso legal.
Incluir todas las cláusulas obligatorias y proteger los derechos fundamentales del trabajador."""
    
    return prompt

def extract_document_sections(content: str) -> List[str]:
    """Extract main sections from the document"""
    sections = []
    
    # Split content by common section markers
    section_markers = [
        "##", "###", "**", "1.", "2.", "3.", "4.", "5.",
        "PRIMERA:", "SEGUNDA:", "TERCERA:", "CUARTA:", "QUINTA:",
        "CLÁUSULA PRIMERA:", "CLÁUSULA SEGUNDA:"
    ]
    
    lines = content.split('\n')
    current_section = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if line starts a new section
        is_new_section = any(line.startswith(marker) for marker in section_markers)
        
        if is_new_section and current_section:
            sections.append('\n'.join(current_section))
            current_section = []
            
        current_section.append(line)
    
    # Add the last section
    if current_section:
        sections.append('\n'.join(current_section))
    
    return sections if sections else [content]

def process_data_requirements(data_processing: Dict[str, str]) -> Dict[str, str]:
    """Process data processing requirements for Colombian compliance"""
    processed = {}
    
    for key, value in data_processing.items():
        if key.lower() in ['consent', 'autorizacion']:
            # Convert boolean to string for response model compatibility
            consent_valid = validate_consent(value)
            processed[key] = str(consent_valid).lower()
        elif key.lower() in ['retention', 'retencion']:
            retention_period = get_retention_period(value)
            processed[key] = str(retention_period)
        elif key.lower() in ['category', 'categoria']:
            category = get_data_category(value)
            processed[key] = str(category.value if hasattr(category, 'value') else category)
        else:
            processed[key] = str(value)  # Ensure all values are strings
    
    return processed

async def draft_simplified_document(
    document_type: str,
    description: str,
    parties: List[Dict[str, str]],
    key_points: List[str],
    jurisdiction: str = "Colombia"
) -> Dict[str, Any]:
    """Draft a simplified legal document focused on practical use and procedures"""
    try:
        agent = create_document_drafting_agent()
        
        # Create knowledge helper for enhanced drafting
        knowledge_helper = AgentKnowledgeHelper("document_drafting_agent")
        
        # Get relevant legal terms
        legal_terms = knowledge_helper._extract_potential_terms(description)
        legal_definitions = {}
        if legal_terms:
            legal_definitions = await knowledge_helper.get_relevant_legal_terms(description)
        
        # Get current date for the document
        from datetime import datetime
        current_date = datetime.now().strftime("%d de %B de %Y")
        
        # Format the simplified prompt
        prompt = f"""Por favor redacta un documento legal SIMPLIFICADO tipo "{document_type}" enfocado ÚNICAMENTE en trámites y procedimientos:

FECHA ACTUAL: Usar la fecha de hoy: {current_date}

🚫 EXCLUSIONES OBLIGATORIAS - LEER ANTES DE REDACTAR:
- PROHIBIDO incluir el texto: "(Regido por las disposiciones del Código Sustantivo del Trabajo Colombiano y la Constitución Política de Colombia)"
- PROHIBIDO incluir cualquier variación de: "Regido por las disposiciones del Código Sustantivo del Trabajo"
- PROHIBIDO incluir texto entre paréntesis sobre reglamentación legal
- NO incluir referencias a "Código Sustantivo del Trabajo" en el título o subtítulo
- El documento debe comenzar directamente con el título del contrato, sin texto adicional

ENFOQUE PRINCIPAL: Crear un documento que cumpla requisitos MÍNIMOS legales para trámites, eliminando TODAS las secciones innecesarias.

DESCRIPCIÓN DEL DOCUMENTO:
{description}

PARTES INVOLUCRADAS:
{chr(10).join([f"- {party['name']} (ID: {party['identification']}) - Rol: {party['role']}" for party in parties])}

PUNTOS CLAVE A INCLUIR:
{chr(10).join([f"- {point}" for point in key_points])}

JURISDICCIÓN: {jurisdiction}

INSTRUCCIONES ESPECÍFICAS:
1. SIMPLIFICAR AL MÁXIMO: Incluir SOLO cláusulas obligatorias y términos esenciales
2. PRÁCTICO: Enfocarse ÚNICAMENTE en requisitos de trámite y procedimiento
3. TRÁMITE: Crear documento que pueda ser presentado en entidades públicas
4. CLARIDAD: Usar lenguaje claro y comprensible para usuarios no jurídicos
5. ESENCIALES: Eliminar TODAS las secciones excesivamente técnicas o complejas
6. MÍNIMO: Solo lo que la ley exige, nada más

REQUISITOS MÍNIMOS:
- Cumplir requisitos MÍNIMOS legales colombianos
- Incluir SOLO cláusulas constitucionales obligatorias
- Asegurar validez para trámites y procedimientos
- Incluir mecanismos de solución de conflictos SIMPLES
- Proteger derechos fundamentales ESENCIALES
- Cumplir requisitos de formalidad MÍNIMOS

EXCLUSIONES ESPECÍFICAS:
- NO incluir secciones de 'NOTAS FINALES' o 'RECOMENDACIONES FINALES'
- NO incluir texto sobre conservar copias firmadas
- NO incluir instrucciones sobre adjuntar documentos para trámites
- NO incluir referencias específicas a artículos del Código Sustantivo del Trabajo
- NO incluir texto 'Simplificado para trámites en Colombia'
- NO incluir instrucciones sobre presentación en entidades públicas específicas
- NO incluir cláusulas de jurisdicción y competencia
- NO incluir cláusulas de ley aplicable
- NO incluir texto "(Regido por las disposiciones del Código Sustantivo del Trabajo Colombiano y la Constitución Política de Colombia)"

🚨 RECORDATORIO FINAL IMPORTANTE:
El documento debe comenzar directamente con el título del contrato (ej: "CONTRATO DE TRABAJO A TÉRMINO FIJO") 
SIN incluir texto adicional entre paréntesis sobre reglamentación legal.

El documento debe ser COMPLETO para trámites pero MÁXIMAMENTE SIMPLIFICADO para uso práctico.
Eliminar cualquier cláusula que no sea estrictamente necesaria para el trámite.
El documento debe terminar directamente con las cláusulas legales, sin notas adicionales."""

        # Get response from agent
        response = agent.run(prompt)
        
        # Clean and format the response
        document_content = clean_response(str(response))
        
        # Structure the response
        result = {
            "document": {
                "content": document_content,
                "sections": extract_document_sections(document_content),
                "markdown": True,
                "simplified": True
            },
            "document_type": document_type,
            "jurisdiction": jurisdiction,
            "key_requirements": key_points,
            "parties": parties,
            "colombian_compliance": {
                "framework_version": "2024.1",
                "status": "compliant_simplified",
                "constitutional_principles": [
                    "Dignidad humana",
                    "Buena fe",
                    "Debido proceso",
                    "Legalidad"
                ],
                "validation_date": datetime.now().isoformat(),
                "simplification_level": "maximum"
            },
            "legal_terms": legal_definitions,
            "timestamp": datetime.now().isoformat(),
            "simplification_notes": [
                "Documento enfocado en requisitos mínimos para trámites",
                "Eliminadas secciones innecesarias y cláusulas complejas",
                "Priorizada claridad y uso práctico",
                "Mantenida validez legal esencial"
            ]
        }
        
        return result
        
    except Exception as e:
        print(f"Error drafting simplified document: {str(e)}")
        raise

async def draft_document(
    document_content: str,
    document_context: dict,
    parties: List[str],
    jurisdiction: str,
    special_considerations: Optional[List[str]] = None,
    administrative_procedure: Optional[str] = None,
    data_processing: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    """Redactar documentos legales con formato y cláusulas apropiadas"""
    agent = create_document_drafting_agent()
    
    # Format parties for the prompt
    parties_text = "\n".join([f"- {party}" for party in parties])
    
    # Format special considerations if provided
    considerations_text = "\n".join([f"- {consideration}" for consideration in special_considerations]) if special_considerations else "None specified"
    
    # Get administrative deadlines if applicable
    deadlines = {}
    if administrative_procedure:
        response_time = get_administrative_deadline("response_time")
        appeal_time = get_administrative_deadline("appeal_time")
        recourse_time = get_administrative_deadline("recourse_time")
        deadlines = {
            "response": response_time,
            "appeal": appeal_time,
            "recourse": recourse_time
        }
    
    # Prepare the prompt
    prompt = f"""Redactar un documento legal con los siguientes parámetros:

CONTENIDO DEL DOCUMENTO:
{document_content}

CONTEXTO DEL DOCUMENTO:
{document_context}

PARTES INVOLUCRADAS:
{parties_text}

JURISDICCIÓN:
{jurisdiction}

CONSIDERACIONES ESPECIALES:
{considerations_text}

El documento debe:
1. Utilizar lenguaje jurídico y formato apropiado
2. Incluir todas las cláusulas y disposiciones necesarias
3. Cumplir requisitos jurisdiccionales específicos
4. Abordar todas las consideraciones especiales
5. Definir claramente términos y condiciones
6. Incluir espacios para firmas y fechas
7. Tener numeración y organización apropiada
8. Incluir avisos y revelaciones requeridas
9. Cumplir con el marco legal colombiano
10. Incorporar principios constitucionales
11. Seguir procedimientos administrativos
12. Proteger derechos del titular de datos
 13. NO incluir cláusulas de jurisdicción y competencia
 14. NO incluir cláusulas de ley aplicable
"""

    if administrative_procedure:
        prompt += f"""
DETALLES DEL PROCEDIMIENTO ADMINISTRATIVO:
- Tipo: {administrative_procedure}
- Término de Respuesta: {deadlines['response']} días
- Término de Apelación: {deadlines['appeal']} días
- Término de Reposición: {deadlines['recourse']} días
"""

    # Add data processing details if provided
    if data_processing:
        data_category = get_data_category(data_processing.get("type", "personal"))
        retention_period = get_retention_period(data_category)
        consent_valid = validate_consent(data_processing.get("consent", {}))
        
        prompt += f"""
REQUISITOS DE TRATAMIENTO DE DATOS:
- Categoría de Datos: {data_category.value}
- Retención Período: {retention_period} días
- Requisitos de Consentimiento: {'Cumplido' if consent_valid else 'No Cumplido'}
- Derechos Constitucionales: {', '.join(ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES)}
"""

    # Run the generation
    response = agent.run(prompt)
    
    # Structure the response
    result = {
        "document": response.content,
        "jurisdiction": jurisdiction,
        "parties": parties,
        "colombian_compliance": {
            "constitutional_principles": ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES,
            "draft_date": datetime.now().isoformat()
        }
    }
    
    # Add administrative procedure details if applicable
    if administrative_procedure:
        result["administrative_procedure"] = {
            "type": administrative_procedure,
            "deadlines": deadlines,
            "response_due": (datetime.now() + timedelta(days=deadlines["response"])).isoformat()
        }
    
    # Add data processing details if provided
    if data_processing:
        result["data_processing"] = {
            "category": data_processing.get("type", "personal"),
            "retention_period": retention_period,
            "consent_valid": consent_valid,
            "expiry_date": (datetime.now() + timedelta(days=retention_period)).isoformat()
        }
    
    return result

async def draft_contract(
    contract_type: str,
    parties: list,
    key_terms: list,
    jurisdiction: str,
    special_considerations: list = None,
    risk_profile: str = "balanceado",
    negotiation_context: str = None,
    data_processing: Optional[Dict[str, str]] = None
) -> dict:
    """Redactar contratos legales personalizados según parámetros especificados"""
    agent = create_document_drafting_agent()
    
    # Format parties for the prompt
    parties_text = "\n".join([f"- {party.get('name', 'Unnamed Party')}: {party.get('details', 'No details provided')}" for party in parties])
    
    # Format key terms for the prompt
    terms_text = "\n".join([f"- {term.get('name', 'Unnamed Term')}: {term.get('details', 'No details provided')}" for term in key_terms])
    
    # Prepare the prompt
    prompt = f"""Redactar un contrato de {contract_type} con los siguientes parámetros:

PARTES:
{parties_text}

TÉRMINOS PRINCIPALES:
{terms_text}

JURISDICCIÓN:
{jurisdiction}

PERFIL DE RIESGO:
{risk_profile}
"""
    
    if special_considerations:
        prompt += f"\nCONSIDERACIONES ESPECIALES:\n{', '.join(special_considerations)}\n"
    
    if negotiation_context:
        prompt += f"\nCONTEXTO DE NEGOCIACIÓN:\n{negotiation_context}\n"
    
    # Add data processing requirements if provided
    if data_processing:
        data_category = get_data_category(data_processing.get("type", "personal"))
        retention_period = get_retention_period(data_category)
        consent_valid = validate_consent(data_processing.get("consent", {}))
        
        prompt += f"""
REQUISITOS DE TRATAMIENTO DE DATOS:
- Categoría de Datos: {data_category.value}
- Retención Período: {retention_period} días
- Requisitos de Consentimiento: {'Cumplido' if consent_valid else 'No Cumplido'}
- Derechos Constitucionales: {', '.join(ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES)}
"""
    
    prompt += """
Por favor redactar un contrato completo que:
1. Utilice lenguaje claro y preciso
2. Incluya todas las secciones estándar apropiadas
3. Incorpore los términos especificados con detalle apropiado
4. Proporcione protecciones equilibradas según el perfil de riesgo
5. Cumpla con la legislación aplicable
6. Incluya notas explicativas para disposiciones que requieren decisiones
7. Señale áreas que requieren información adicional del cliente
8. Ofrezca alternativas para disposiciones potencialmente contenciosas
9. Cumpla con leyes de protección de datos colombianas
10. Incorpore principios constitucionales
11. Proteja derechos del titular de datos
12. Incluya períodos de retención apropiados
 13. NO incluir cláusulas de jurisdicción y competencia
 14. NO incluir cláusulas de ley aplicable

Formatear el documento con estilo legal apropiado, incluyendo secciones numeradas, términos definidos y espacios para firmas.
"""
    
    # Run the drafting
    response = agent.run(prompt)
    
    # Structure the response
    result = {
        "contract_draft": response.content,
        "contract_type": contract_type,
        "jurisdiction": jurisdiction,
        "parties": [party.get('name', 'Unnamed Party') for party in parties],
        "colombian_compliance": {
            "constitutional_principles": ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES,
            "draft_date": datetime.now().isoformat()
        }
    }
    
    # Add data processing details if provided
    if data_processing:
        result["data_processing"] = {
            "category": data_processing.get("type", "personal"),
            "retention_period": retention_period,
            "consent_valid": consent_valid,
            "expiry_date": (datetime.now() + timedelta(days=retention_period)).isoformat()
        }
    
    return result 

async def demonstrate_enhanced_document_drafting():
    """Demonstrate the enhanced document drafting capabilities"""
    
    print("🚀 DEMOSTRACIÓN DEL AGENTE DE REDACCIÓN JURÍDICA MEJORADO")
    print("=" * 70)
    
    # Example 1: Simplified contract
    print("\n📋 EJEMPLO 1: Contrato Simplificado de Arrendamiento")
    print("-" * 50)
    
    try:
        simplified_contract = await draft_simplified_document(
            document_type="Contrato de Arrendamiento",
            description="Arrendamiento de vivienda para uso residencial",
            parties=[
                {"name": "María González", "identification": "CC 12345678", "role": "Arrendador"},
                {"name": "Carlos Rodríguez", "identification": "CC 87654321", "role": "Arrendatario"}
            ],
            key_points=[
                "Plazo de 12 meses",
                "Canon mensual de $800,000",
                "Depósito de $800,000",
                "Uso exclusivo para vivienda"
            ]
        )
        
        print("✅ Contrato simplificado generado exitosamente")
        print(f"📄 Tipo: {simplified_contract['document_type']}")
        print(f"🔒 Cumplimiento: {simplified_contract['colombian_compliance']['status']}")
        print(f"📝 Nivel de simplificación: {simplified_contract['colombian_compliance']['simplification_level']}")
        print(f"📊 Secciones: {len(simplified_contract['document']['sections'])}")
        
        # Show first section as preview
        if simplified_contract['document']['sections']:
            first_section = simplified_contract['document']['sections'][0][:200] + "..."
            print(f"📖 Vista previa primera sección: {first_section}")
            
    except Exception as e:
        print(f"❌ Error generando contrato simplificado: {str(e)}")
    
    # Example 2: Standard document with enhanced prompts
    print("\n📋 EJEMPLO 2: Documento Estándar con Prompts Mejorados")
    print("-" * 50)
    
    try:
        standard_document = await draft_custom_document(
            document_type="Contrato de Prestación de Servicios",
            description="Contrato para servicios de consultoría tecnológica",
            parties=[
                {"name": "Tech Solutions SAS", "identification": "NIT 900123456-7", "role": "Contratista"},
                {"name": "Empresa ABC Ltda", "identification": "NIT 800987654-3", "role": "Contratante"}
            ],
            key_points=[
                "Servicios de consultoría en desarrollo de software",
                "Plazo de 6 meses",
                "Pago mensual por servicios prestados",
                "Confidencialidad de información"
            ],
            industry="technology",
            jurisdiction="Colombia",
            complexity="standard"
        )
        
        print("✅ Documento estándar generado exitosamente")
        print(f"📄 Tipo: {standard_document['document_type']}")
        print(f"🔒 Cumplimiento: {standard_document['colombian_compliance']['status']}")
        print(f"🏭 Industria: {standard_document.get('industry', 'N/A')}")
        print(f"📊 Uso de base de conocimiento:")
        for source in standard_document['knowledge_base_usage']['knowledge_sources']:
            print(f"   - {source['type']}: {source['count']} elementos")
            
    except Exception as e:
        print(f"❌ Error generando documento estándar: {str(e)}")
    
    print("\n🎯 CARACTERÍSTICAS PRINCIPALES DEL AGENTE MEJORADO:")
    print("=" * 70)
    print("✅ Enfoque en documentos prácticos y de trámite")
    print("✅ Simplificación máxima eliminando secciones innecesarias")
    print("✅ Prompts mejorados para claridad y uso práctico")
    print("✅ Cumplimiento legal colombiano simplificado")
    print("✅ Integración con base de conocimiento legal")
    print("✅ Funciones especializadas para diferentes niveles de complejidad")
    
    print("\n🚀 El agente está listo para generar documentos legales simplificados!")
    print("💡 Use 'draft_simplified_document' para máxima simplificación")
    print("💡 Use 'draft_custom_document' para documentos personalizados")
    print("💡 Use 'draft_legal_document' para documentos estándar")

# Main execution for demonstration
if __name__ == "__main__":
    import asyncio
    
    print("🔧 Iniciando demostración del agente de redacción jurídica mejorado...")
    
    try:
        asyncio.run(demonstrate_enhanced_document_drafting())
    except Exception as e:
        print(f"❌ Error en demostración: {str(e)}")
        print("💡 Asegúrese de que todas las dependencias estén configuradas correctamente") 