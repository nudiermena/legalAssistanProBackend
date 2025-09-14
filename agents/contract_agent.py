# Conditional import for agno
try:
    from agno.agent import Agent
    AGNO_AVAILABLE = True
except ImportError:
    AGNO_AVAILABLE = False
    Agent = None

from config.database import get_agent_storage
from config.ai_models import get_model
from config.knowledge_base_integration import (
    create_agent_knowledge_integration,
    AgentKnowledgeHelper
)
from config.enhanced_agent_config import get_enhanced_agent_config
from config.colombian_compliance import (
    ColombianDataProtection,
    ColombianLegalFramework,
    get_data_category,
    validate_consent,
    get_retention_period
)
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import os as os_module
import json
import logging
import asyncio
from fastapi import HTTPException
# Conditional import for agno tools
try:
    from agno.tools.googlesearch import GoogleSearchTools
    GOOGLE_SEARCH_AVAILABLE = True
except ImportError:
    GOOGLE_SEARCH_AVAILABLE = False
    GoogleSearchTools = None
import re

logger = logging.getLogger(__name__)

def create_contract_agent(user_id: str = None, session_id: str = None):
    """Create a specialized agent for contract review with enhanced memory capabilities"""
    # If agno is not available, return a simple fallback object
    if not AGNO_AVAILABLE:
        logger.warning("agno not available, returning fallback contract agent")
        return SimpleContractAgent()
    
    # Create knowledge base integration
    knowledge_integration = create_agent_knowledge_integration("contract_agent")
    
    # Get enhanced configuration with memory
    enhanced_config = get_enhanced_agent_config("contract_agent")
    
    # Get memory instance for this agent
    memory_instance = enhanced_config.get("memory_instance")
    
    # Configure memory properly for agno framework
    # agno expects either a memory object or None, not a dict
    memory_config = None
    if memory_instance:
        # Use the memory instance directly if it has the required interface
        if hasattr(memory_instance, 'runs') and hasattr(memory_instance, 'add_run'):
            memory_config = memory_instance
            logger.info(f"Contract agent memory system configured with external memory: {type(memory_instance).__name__}")
        else:
            logger.warning(f"Memory instance missing required interface, using agno default memory")
    
    # Prepare tools list
    tools = []
    if GOOGLE_SEARCH_AVAILABLE:
        tools.append(GoogleSearchTools())
    
    return Agent(
        name="Analista de Contratos Avanzado con IA",
        role="Especialista en análisis contractual inteligente con capacidades avanzadas de memoria, base de conocimiento legal y cumplimiento colombiano",
        model=get_model("contract_review"),
        tools=tools,
        knowledge=knowledge_integration,
        search_knowledge=True,
        storage=enhanced_config["storage"],
        add_context=True,
        # Use the memory instance directly if available, otherwise let agno handle it
        memory=memory_config,
        session_id=session_id or f"contract_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        instructions=[
            # === CAPACIDADES AVANZADAS DE IA ===
            "Eres un analista de contratos con capacidades avanzadas de IA que combina análisis legal tradicional con inteligencia artificial",
            "Utiliza técnicas de procesamiento de lenguaje natural para identificar patrones y riesgos ocultos en contratos",
            "Aplica machine learning para detectar anomalías contractuales y cláusulas no estándar",
            "Genera insights predictivos sobre posibles conflictos futuros basados en análisis histórico",
            
            # === INTEGRACIÓN CON MEMORIA Y BASE DE CONOCIMIENTO ===
            "ANTES de cada análisis, consulta la base de conocimiento legal para obtener información actualizada",
            "Utiliza la memoria del usuario para personalizar análisis y recordar preferencias previas",
            "Busca en jurisprudencia colombiana relevante para fundamentar tus recomendaciones",
            "Consulta plantillas y cláusulas estándar de la base de conocimiento",
            "Aplica el historial de análisis previos para mejorar la precisión de tus evaluaciones",
            
            # === REASONING CAPABILITIES ===
            "Antes de responder, analiza el contexto completo del contrato y la situación del usuario",
            "Evalúa múltiples perspectivas legales antes de llegar a conclusiones",
            "Considera el historial de interacciones previas con el usuario",
            "Aplica razonamiento deductivo para identificar riesgos ocultos",
            "Utiliza el conocimiento legal almacenado para fundamentar tus análisis",
            "Aplica lógica difusa para evaluar niveles de riesgo y cumplimiento",
            
            # === MEMORY AND PERSONALIZATION ===
            "Considera las preferencias del usuario basándote en análisis previos de contratos",
            "Adapta el nivel de detalle según la experiencia legal del usuario",
            "Mantén consistencia con análisis previos del mismo usuario",
            "Aprende de los patrones identificados en contratos similares",
            "Personaliza las recomendaciones según el perfil del usuario",
            "Utiliza el historial de análisis contractual para proporcionar insights más precisos",
            "Recuerda las áreas de riesgo específicas que el usuario ha mencionado previamente",
            "Adapta el tono y complejidad según el perfil del usuario",
            "Referencia análisis previos cuando sea relevante para el contexto actual",
            
            # === SESSION MANAGEMENT ===
            "Mantén el contexto de la sesión actual de análisis",
            "Referencia análisis previos cuando sea relevante",
            "Continúa análisis iniciados en sesiones anteriores",
            "Proporciona seguimiento a temas discutidos previamente",
            "Mantén coherencia entre sesiones de análisis del mismo usuario",
            
            # === KNOWLEDGE BASE INTEGRATION ===
            "SIEMPRE busca en la base de conocimiento legal antes de responder",
            "Utiliza jurisprudencia relevante de la Corte Constitucional y otras altas cortes",
            "Consulta términos legales específicos y sus definiciones",
            "Aplica mejores prácticas contractuales documentadas en la base de conocimiento",
            "Cita fuentes específicas y referencias normativas de la base de conocimiento",
            "Utiliza plantillas y cláusulas estándar de la base de conocimiento",
            "Consulta casos similares y precedentes legales relevantes",
            
            # === MARCO NORMATIVO Y LEGAL COLOMBIANO ===
            "Analizar contratos aplicando la normativa colombiana vigente (Código Civil, Código de Comercio, Código General del Proceso)",
            "Verificar cumplimiento de la Ley 80 de 1993 (Estatuto General de Contratación Pública) cuando aplique",
            "Evaluar conformidad con el régimen de protección de datos (Ley 1581 de 2012 - Habeas Data)",
            "Aplicar jurisprudencia vinculante de la Corte Suprema de Justicia, Consejo de Estado y Corte Constitucional",
            "Considerar la Ley 1480 de 2011 (Estatuto del Consumidor) para contratos de consumo",
            "Evaluar cumplimiento de la Ley 1429 de 2010 (Ley de Emprendimiento) cuando aplique",
            
            # === ESTRUCTURA CONTRACTUAL AVANZADA ===
            "Verificar la presencia y validez de elementos esenciales: consentimiento, objeto, causa y solemnidades",
            "Evaluar la capacidad jurídica de las partes contratantes y posibles limitaciones",
            "Analizar la descripción del objeto contractual verificando su determinación, posibilidad y licitud",
            "Examinar la causa del contrato asegurando su existencia, veracidad y licitud",
            "Identificar cláusulas abusivas o desequilibradas según jurisprudencia colombiana",
            "Evaluar la validez de cláusulas de limitación de responsabilidad según normativa vigente",
            
            # === CLÁUSULAS Y CONDICIONES INTELIGENTES ===
            "Revisar exhaustivamente obligaciones, derechos y responsabilidades de cada parte",
            "Evaluar cláusulas de penalización, multas y apremios por incumplimiento",
            "Analizar términos de duración, renovación, prórroga y terminación del contrato",
            "Verificar cláusulas de fuerza mayor, caso fortuito y teoría de la imprevisión",
            "Examinar mecanismos de garantías (pólizas, fiducias, cartas de crédito)",
            "Identificar cláusulas de resolución automática y sus efectos legales",
            "Evaluar cláusulas de confidencialidad y protección de información",
            
            # === ASPECTOS PROCEDIMENTALES AVANZADOS ===
            "Verificar cumplimiento de requisitos de forma según el tipo contractual",
            "Evaluar cláusulas de competencia, jurisdicción y ley aplicable",
            "Analizar mecanismos alternativos de solución de conflictos (arbitraje, conciliación, amigable composición)",
            "Revisar procedimientos de notificación, comunicaciones y entrega de documentos",
            "Evaluar cláusulas de modificación y adición contractual",
            "Analizar mecanismos de cesión y subcontratación",
            
            # === CUMPLIMIENTO REGULATORIO INTELIGENTE ===
            "Verificar cumplimiento de normativa sectorial específica (financiera, salud, educación, etc.)",
            "Evaluar conformidad con regulaciones laborales cuando aplique",
            "Analizar aspectos tributarios y fiscales del contrato",
            "Verificar cumplimiento de normas ambientales y de sostenibilidad",
            "Evaluar cumplimiento de normativas de comercio electrónico (Ley 527 de 1999)",
            "Analizar cumplimiento de normativas de protección al consumidor",
            
            # === GESTIÓN DE RIESGOS AVANZADA ===
            "Identificar y evaluar riesgos legales, operacionales y financieros",
            "Analizar cláusulas de indemnidad, exoneración y limitación de responsabilidad",
            "Verificar coherencia entre el clausulado y los anexos del contrato",
            "Evaluar mecanismos de modificación, adición y cesión contractual",
            "Identificar riesgos de cumplimiento regulatorio y sus consecuencias",
            "Evaluar riesgos de reputación y compliance corporativo",
            "Analizar riesgos de continuidad del negocio y planes de contingencia",
            
            # === ANÁLISIS INTELIGENTE Y REPORTE ===
            "Generar informes estructurados con hallazgos, observaciones y recomendaciones",
            "Clasificar observaciones por nivel de riesgo (alto, medio, bajo) con justificación",
            "Proponer redacciones alternativas para cláusulas deficientes",
            "Incluir referencias normativas y jurisprudenciales específicas",
            "Sugerir acciones correctivas y medidas de mitigación de riesgos",
            "Proporcionar análisis comparativo con contratos similares del usuario",
            "Generar recomendaciones personalizadas basadas en el historial del usuario",
            
            # === FORMATO DE RESPUESTA ESTRUCTURADA ===
            (
                "Al final de tu análisis, SIEMPRE incluye un bloque de código JSON con la siguiente estructura:\n"
                "```json\n"
                "{\n"
                '  "risk_level": "alto|medio|bajo",\n'
                '  "risk_score": 85,\n'
                '  "critical_clauses": ["lista de cláusulas críticas"],\n'
                '  "obligations": ["lista de obligaciones identificadas"],\n'
                '  "risks": ["lista de riesgos identificados"],\n'
                '  "impact": "alto|medio|bajo",\n'
                '  "recommendations": ["lista de recomendaciones"],\n'
                '  "compliance_status": "cumple|no_cumple|parcial",\n'
                '  "compliance_score": 75,\n'
                '  "legal_terms": {"término": "definición"},\n'
                '  "jurisprudence_references": ["referencias jurisprudenciales"],\n'
                '  "memory_insights": "insights basados en análisis previos del usuario",\n'
                '  "knowledge_sources": ["fuentes de la base de conocimiento utilizadas"]\n'
                "}\n"
                "```"
            ),
            
            # === INSTRUCCIONES ESPECÍFICAS DE MEMORIA ===
            "ANTES de analizar, consulta la memoria del usuario para obtener contexto previo",
            "Utiliza análisis previos para identificar patrones de riesgo específicos del usuario",
            "Referencia contratos similares analizados anteriormente cuando sea relevante",
            "Adapta tus recomendaciones basándote en las preferencias previas del usuario",
            "Mantén consistencia con evaluaciones previas de cumplimiento y riesgo",
            
            # === INSTRUCCIONES ESPECÍFICAS DE BASE DE CONOCIMIENTO ===
            "SIEMPRE inicia tu análisis consultando la base de conocimiento legal",
            "Busca jurisprudencia relevante para el tipo de contrato específico",
            "Consulta plantillas y cláusulas estándar para comparar con el contrato analizado",
            "Utiliza definiciones legales de la base de conocimiento para términos técnicos",
            "Cita específicamente las fuentes de la base de conocimiento utilizadas"
        ],
        markdown=True
    )

async def analyze_contract(
    contract_text: str,
    contract_type: str,
    parties: List[str],
    specific_concerns: Optional[List[str]] = None,
    relevant_regulations: Optional[List[str]] = None,
    data_processing: Optional[Dict[str, str]] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None
) -> Dict[str, str]:
    """Analyze a contract and provide detailed insights with Colombian compliance and knowledge base integration"""
    agent = create_contract_agent(user_id=user_id, session_id=session_id)
    
    # Create knowledge helper for enhanced analysis
    knowledge_helper = AgentKnowledgeHelper("contract_agent")
    
    # Extract potential legal terms from contract
    legal_terms = knowledge_helper._extract_potential_terms(contract_text)
    
    # Get relevant legal definitions
    legal_definitions = {}
    if legal_terms:
        legal_definitions = await knowledge_helper.get_relevant_legal_terms(contract_text)
    
    # Get relevant contract clauses from knowledge base
    contract_clauses = await knowledge_helper.integration.get_contract_clauses()
    
    # Get relevant jurisprudence
    jurisprudence = await knowledge_helper.integration.get_jurisprudence(
        topic="contratos",
        limit=5
    )
    
    # Get user's contract analysis history for personalized insights
    user_memories = []
    if user_id:
        try:
            user_memories = await get_contract_memories(user_id, contract_type, limit=5)
            logger.info(f"Retrieved {len(user_memories)} previous contract memories for user {user_id}")
        except Exception as e:
            logger.warning(f"Could not retrieve user memories: {e}")
    
    # Enhanced prompt with memory and knowledge base integration
    contract_type_display = contract_type.upper() if contract_type else "CONTRATO GENERAL"
    prompt = f"""ANÁLISIS INTELIGENTE DE CONTRATO - {contract_type_display}

CONTRATO A ANALIZAR:
{contract_text}

PARTES INVOLUCRADAS: {', '.join(parties)}

=== INSTRUCCIONES DE ANÁLISIS ===
Utiliza TODAS las capacidades de memoria y base de conocimiento para proporcionar un análisis personalizado y fundamentado.

=== ANÁLISIS REQUERIDO ===
1. RESUMEN EJECUTIVO INTELIGENTE (máximo 500 palabras)
   - Síntesis ejecutiva del contrato
   - Puntos críticos identificados
   - Nivel general de riesgo

2. ANÁLISIS LEGAL FUNDAMENTADO
   - Obligaciones principales de cada parte con referencia a cláusulas específicas
   - Validez legal según normativa colombiana
   - Cumplimiento de requisitos formales y sustanciales

3. EVALUACIÓN DE RIESGOS INTELIGENTE
   - Riesgos potenciales por cláusula con nivel de severidad (Bajo/Medio/Alto)
   - Análisis de impacto financiero y legal
   - Identificación de cláusulas abusivas o desequilibradas

4. CUMPLIMIENTO REGULATORIO
   - Evaluación de cumplimiento legal colombiano
   - Cumplimiento de protección de datos (Ley 1581 de 2012)
   - Alineación con principios constitucionales
   - Cumplimiento de normativas sectoriales aplicables

5. ASPECTOS PROCEDIMENTALES
   - Fechas críticas y plazos
   - Mecanismos de resolución de conflictos
   - Causales de terminación y efectos
   - Régimen de responsabilidad aplicable

6. GARANTÍAS Y PROTECCIONES
   - Garantías y seguros requeridos
   - Mecanismos de protección para las partes
   - Cláusulas de indemnidad y limitación de responsabilidad

7. JURISDICCIÓN Y COMPETENCIA
   - Ley aplicable y jurisdicción competente
   - Mecanismos alternativos de solución de conflictos
   - Procedimientos de notificación y comunicación

=== INTEGRACIÓN CON MEMORIA Y BASE DE CONOCIMIENTO ===
"""
    
    # Add specific concerns and regulations
    if specific_concerns:
        prompt += f"\n=== ENFOQUE ESPECÍFICO ===\nEnfocarse particularmente en cláusulas relacionadas con: {', '.join(specific_concerns)}"
    
    if relevant_regulations:
        prompt += f"\n\n=== REGULACIONES A EVALUAR ===\nEvaluar cumplimiento de las siguientes regulaciones: {', '.join(relevant_regulations)}"
    
    # Add knowledge base context with enhanced formatting
    if legal_definitions:
        prompt += "\n\n=== TÉRMINOS LEGALES DE LA BASE DE CONOCIMIENTO ===\n"
        for term, definition in legal_definitions.items():
            prompt += f"📚 {term}: {definition}\n"
    
    if contract_clauses:
        prompt += "\n\n=== CLÁUSULAS ESTÁNDAR DE REFERENCIA ===\n"
        for i, clause in enumerate(contract_clauses[:3], 1):  # Top 3 most relevant
            prompt += f"📋 Cláusula {i} - {clause.get('clause_type', 'N/A')}:\n   {clause.get('standard_clause', '')[:200]}...\n\n"
    
    if jurisprudence:
        prompt += "\n\n=== JURISPRUDENCIA COLOMBIANA RELEVANTE ===\n"
        for i, jur in enumerate(jurisprudence[:2], 1):  # Top 2 most relevant
            prompt += f"⚖️ Precedente {i} - {jur.get('topic', 'N/A')}:\n   {jur.get('summary', '')[:200]}...\n\n"
    
    # Add user memory context for personalized analysis
    if user_memories:
        prompt += "\n=== HISTORIAL DE ANÁLISIS PREVIOS DEL USUARIO ===\n"
        prompt += f"Se han identificado {len(user_memories)} análisis previos de contratos similares.\n"
        
        # Add insights from previous analyses
        risk_patterns = []
        compliance_issues = []
        for memory in user_memories:
            if memory.get('risk_patterns'):
                risk_patterns.extend(memory.get('risk_patterns', []))
            if memory.get('compliance_issues'):
                compliance_issues.extend(memory.get('compliance_issues', []))
        
        if risk_patterns:
            unique_risks = list(set(risk_patterns))
            prompt += f"\n🔍 PATRONES DE RIESGO IDENTIFICADOS PREVIAMENTE:\n"
            for risk in unique_risks[:5]:  # Top 5 unique risks
                prompt += f"   • {risk}\n"
        
        if compliance_issues:
            unique_compliance = list(set(compliance_issues))
            prompt += f"\n⚠️ PROBLEMAS DE CUMPLIMIENTO PREVIOS:\n"
            for issue in unique_compliance[:5]:  # Top 5 unique issues
                prompt += f"   • {issue}\n"
        
        prompt += "\n💡 UTILIZA ESTE HISTORIAL para:\n"
        prompt += "   • Identificar patrones de riesgo específicos del usuario\n"
        prompt += "   • Adaptar recomendaciones basadas en experiencias previas\n"
        prompt += "   • Mantener consistencia con análisis anteriores\n"
        prompt += "   • Proporcionar insights personalizados\n"
    
    # Add final instructions for enhanced analysis
    prompt += """

=== INSTRUCCIONES FINALES ===
1. SIEMPRE consulta la base de conocimiento antes de responder
2. Utiliza la memoria del usuario para personalizar el análisis
3. Cita específicamente las fuentes de la base de conocimiento utilizadas
4. Proporciona recomendaciones basadas en el historial del usuario
5. Incluye el bloque JSON estructurado al final del análisis
6. Mantén consistencia con análisis previos del mismo usuario

=== FORMATO DE RESPUESTA ===
Proporciona un análisis completo, estructurado y fundamentado que demuestre el uso de:
- Base de conocimiento legal
- Memoria del usuario
- Jurisprudencia colombiana
- Análisis de riesgos inteligente
- Recomendaciones personalizadas

Al final, incluye SIEMPRE el bloque JSON con la estructura especificada en las instrucciones.
"""
    
    if data_processing:
        data_category = get_data_category(data_processing.get("type", "personal"))
        retention_period = get_retention_period(data_category)
        consent_valid = validate_consent(data_processing.get("consent", {}))
        
        prompt += f"""

=== EVALUACIÓN DE PROTECCIÓN DE DATOS PERSONALES ===
📊 Categoría de datos: {data_category}
⏰ Período de retención: {retention_period}
✅ Consentimiento válido: {'Sí' if consent_valid else 'No'}
🔒 Cumplimiento Ley 1581 de 2012: {'Cumple' if consent_valid else 'No cumple'}

⚠️ CONSIDERACIONES ESPECIALES:
- Verificar cláusulas de protección de datos personales
- Evaluar mecanismos de ejercicio de derechos ARCO
- Revisar procedimientos de seguridad de la información
- Verificar cumplimiento de principios de finalidad y proporcionalidad
"""
    
    # Log the enhanced prompt for debugging
    logger.info(f"Enhanced prompt created for contract analysis - Type: {contract_type}, User: {user_id}")
    logger.info(f"Knowledge base integration: {len(legal_definitions)} terms, {len(contract_clauses)} clauses, {len(jurisprudence)} jurisprudence")
    logger.info(f"Memory integration: {len(user_memories)} previous memories retrieved")
    
    # Run analysis with enhanced memory and knowledge base context
    logger.info("Starting contract analysis with enhanced agent capabilities...")
    response = await agent.arun(
        prompt,
        user_id=user_id,
        session_id=session_id
    )
    
    logger.info(f"Contract analysis completed successfully - Response length: {len(response.content)} characters")
    
    # Extract structured data from response
    structured_data = extract_json_from_markdown(response.content)
    if structured_data:
        structured_data = sanitize_structured_analysis(structured_data, response.content)
    
    # Store contract analysis memory
    if user_id and session_id:
        try:
            # Extract risk patterns and compliance issues from structured data
            risk_patterns = []
            compliance_issues = []
            
            if structured_data:
                if isinstance(structured_data, dict):
                    # Extract risks - handle both simple lists and complex objects
                    raw_risks = structured_data.get('risks', [])
                    if isinstance(raw_risks, list):
                        # Convert complex risk objects to simple strings
                        for risk in raw_risks:
                            if isinstance(risk, dict):
                                # Extract key information from risk object
                                risk_text = f"{risk.get('risk', '')} - {risk.get('severity', '')} - {risk.get('impact', '')}"
                                risk_patterns.append(risk_text)
                            elif isinstance(risk, str):
                                risk_patterns.append(risk)
                            else:
                                risk_patterns.append(str(risk))
                    
                    # Extract compliance issues
                    raw_compliance = structured_data.get('incumplimientos', [])
                    if isinstance(raw_compliance, list):
                        for issue in raw_compliance:
                            if isinstance(issue, dict):
                                # Extract key information from compliance object
                                issue_text = f"{issue.get('issue', '')} - {issue.get('severity', '')}"
                                compliance_issues.append(issue_text)
                            elif isinstance(issue, str):
                                compliance_issues.append(issue)
                            else:
                                compliance_issues.append(str(issue))
            
            # Store memory
            await store_contract_memory(
                user_id=user_id,
                session_id=session_id,
                contract_type=contract_type,
                analysis_summary=response.content[:500],  # First 500 chars
                risk_patterns=risk_patterns,
                compliance_issues=compliance_issues
            )
        except Exception as e:
            logger.warning(f"Failed to store contract memory: {e}")
    
    # Build comprehensive result with enhanced memory and knowledge base information
    result = {
        "summary": response.content,
        "structured_analysis": structured_data,
        "contract_type": contract_type,
        "parties": parties,
        "analysis_timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "session_id": session_id,
        
        # Memory system information
        "memory_enabled": True,
        "memory_utilization": {
            "previous_analyses_retrieved": len(user_memories),
            "risk_patterns_identified": len(set([risk for memory in user_memories for risk in memory.get('risk_patterns', [])])),
            "compliance_issues_identified": len(set([issue for memory in user_memories for issue in memory.get('compliance_issues', [])])),
            "personalization_applied": len(user_memories) > 0
        },
        
        # Knowledge base integration information
        "knowledge_base_utilization": {
            "legal_terms_consulted": len(legal_definitions),
            "contract_clauses_referenced": len(contract_clauses) if contract_clauses else 0,
            "jurisprudence_cited": len(jurisprudence) if jurisprudence else 0,
            "knowledge_sources_used": [
                "legal_definitions",
                "contract_clauses", 
                "jurisprudence"
            ]
        },
        
        # Detailed knowledge sources
        "legal_definitions": legal_definitions,
        "contract_clauses_sample": [clause.get('clause_type', 'N/A') for clause in (contract_clauses[:3] if contract_clauses else [])],
        "jurisprudence_sample": [jur.get('topic', 'N/A') for jur in (jurisprudence[:2] if jurisprudence else [])],
        
        # Analysis metadata
        "analysis_metadata": {
            "enhanced_prompt_length": len(prompt),
            "response_length": len(response.content),
            "knowledge_integration_level": "high" if legal_definitions or contract_clauses or jurisprudence else "basic",
            "memory_integration_level": "high" if user_memories else "none",
            "personalization_level": "high" if user_memories else "standard"
        }
    }
    
    return result

async def store_contract_memory(
    user_id: str,
    session_id: str,
    contract_type: str,
    analysis_summary: str,
    risk_patterns: List[str] = None,
    compliance_issues: List[str] = None
) -> bool:
    """Store contract analysis memory in the database"""
    try:
        from postgres_memory import get_memory_instance
        
        # Get memory instance for contract agent
        memory = get_memory_instance("contract_agent")
        
        if memory and hasattr(memory, 'store_contract_memory'):
            # Store in the memory system
            memory.store_contract_memory(
                user_id=user_id,
                session_id=session_id,
                contract_type=contract_type,
                analysis_summary=analysis_summary,
                risk_patterns=risk_patterns or [],
                compliance_issues=compliance_issues or []
            )
            logger.info(f"Contract memory stored for user {user_id}, session {session_id}")
            return True
        else:
            logger.warning("Memory system not available for storing contract memories")
            return False
            
    except Exception as e:
        logger.error(f"Error storing contract memory: {e}")
        return False

async def get_contract_memories(
    user_id: str,
    contract_type: str = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Retrieve contract analysis memories for a user"""
    try:
        from postgres_memory import get_memory_instance
        
        # Get memory instance for contract agent
        memory = get_memory_instance("contract_agent")
        
        if memory and hasattr(memory, 'get_contract_memories'):
            # Retrieve memories from the memory system
            memories = memory.get_contract_memories(
                user_id=user_id,
                contract_type=contract_type,
                limit=limit
            )
            logger.info(f"Retrieved {len(memories)} contract memories for user {user_id}")
            return memories
        else:
            logger.warning("Memory system not available for retrieving contract memories")
            return []
            
    except Exception as e:
        logger.error(f"Error retrieving contract memories: {e}")
        return []

def extract_json_from_markdown(text: str) -> Optional[Dict[str, Any]]:
    """Extract JSON from markdown text, handling various formats and errors"""
    try:
        # First, try to find JSON blocks
        json_patterns = [
            r'```json\s*(\{[\s\S]*?\})\s*```',  # ```json { ... } ```
            r'```\s*(\{[\s\S]*?\})\s*```',      # ``` { ... } ```
            r'`(\{[\s\S]*?\})`',                 # `{ ... }`
        ]

        def _clean_json_string(s: str) -> str:
            cleaned = s.strip()
            # Remove trailing commas before closing braces/brackets
            cleaned = re.sub(r',\s*(\})', r'\1', cleaned)
            cleaned = re.sub(r',\s*(\])', r'\1', cleaned)
            # Normalize quotes (only if keys appear unquoted later; avoid touching keys blindly)
            # Convert single quotes to double quotes to support JSON-like outputs
            cleaned = cleaned.replace("'", '"')
            # Remove control chars
            cleaned = ''.join(ch for ch in cleaned if ord(ch) >= 32 or ch in '\n\r\t')
            return cleaned

        for pattern in json_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            if matches:
                for match in matches:
                    try:
                        json_str = _clean_json_string(match)
                        parsed = json.loads(json_str)
                        logger.info("Successfully extracted and parsed JSON from response")
                        return parsed
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse JSON match: {e}")
                        logger.debug(f"Problematic JSON string: {json_str[:200]}...")
                        continue

        # Brace-balancing fallback: find first balanced top-level {...}
        start = text.find('{')
        if start != -1:
            brace_count = 0
            end_index = -1
            for idx in range(start, len(text)):
                ch = text[idx]
                if ch == '{':
                    brace_count += 1
                elif ch == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_index = idx + 1
                        break
            if end_index != -1:
                candidate = _clean_json_string(text[start:end_index])
                try:
                    parsed = json.loads(candidate)
                    logger.info("Parsed JSON using brace-balancing fallback")
                    return parsed
                except json.JSONDecodeError as e:
                    logger.warning(f"Brace-balanced JSON parse failed: {e}")

        # If no JSON found, try to extract structured data from the text
        logger.warning("No valid JSON found in response, attempting to extract structured data")
        return extract_structured_data_from_text(text)

    except Exception as e:
        logger.error(f"Error extracting JSON from markdown: {e}")
        return None

def extract_structured_data_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Extract structured data from text when JSON parsing fails"""
    try:
        # Create a basic structured response based on text content
        structured_data = {
            "risk_level": "medio",  # Default values
            "compliance_status": "parcial",
            "critical_clauses": [],
            "risks": [],
            "recommendations": []
        }
        
        # Try to extract information from the text
        if "alto" in text.lower() or "high" in text.lower():
            structured_data["risk_level"] = "alto"
        elif "bajo" in text.lower() or "low" in text.lower():
            structured_data["risk_level"] = "bajo"
            
        if "cumple" in text.lower() or "compliance" in text.lower():
            structured_data["compliance_status"] = "cumple"
        elif "no cumple" in text.lower() or "non-compliance" in text.lower():
            structured_data["compliance_status"] = "no cumple"
            
        # Extract risks and recommendations from text
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                if any(word in line.lower() for word in ['riesgo', 'risk', 'problema', 'issue']):
                    structured_data["risks"].append(line)
                elif any(word in line.lower() for word in ['recomendación', 'recommendation', 'sugerencia']):
                    structured_data["recommendations"].append(line)
        
        logger.info("Extracted structured data from text when JSON parsing failed")
        return structured_data
        
    except Exception as e:
        logger.error(f"Error extracting structured data from text: {e}")
        return None


def _strip_markdown_links(text: str) -> str:
	"""Convert markdown links [text](url) to plain text."""
	return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)


def _clean_list_item(text: str) -> str:
	"""Clean a single list item by removing markdown bullets and emphasis."""
	if not isinstance(text, str):
		text = str(text)
	# Remove leading bullets and whitespace
	text = re.sub(r"^\s*[•\-\*]+\s*", "", text)
	# Strip markdown emphasis
	text = text.replace("**", "").replace("__", "").replace("`", "")
	# Convert markdown links to plain text
	text = _strip_markdown_links(text)
	# Collapse whitespace
	text = re.sub(r"\s+", " ", text).strip()
	return text


def _deduplicate_preserve_order(items: List[str]) -> List[str]:
	seen = set()
	result: List[str] = []
	for item in items:
		if item not in seen and item:
			seen.add(item)
			result.append(item)
	return result


def _extract_clauses_from_text(text: str, limit: int = 5) -> List[str]:
	"""Heuristic extraction of clause titles from Spanish legal text."""
	patterns = [
		r"Cl[aá]usula\s+[A-Za-zÁÉÍÓÚáéíóúñÑ0-9]+[^:\n]*",
		r"(PRIMERA|SEGUNDA|TERCERA|CUARTA|QUINTA|SEXTA|SÉPTIMA|OCTAVA|NOVENA|D[ÉE]CIMA)[:\s][^\n]*",
	]
	matches: List[str] = []
	for pat in patterns:
		for m in re.findall(pat, text, flags=re.IGNORECASE):
			cleaned = _clean_list_item(m)
			if cleaned:
				matches.append(cleaned)
	if not matches:
		return []
	return _deduplicate_preserve_order(matches)[:limit]


def sanitize_structured_analysis(structured: Dict[str, Any], source_text: str) -> Dict[str, Any]:
	"""Sanitize LLM-provided structured analysis fields to be UI-safe and consistent."""
	if not isinstance(structured, dict):
		return structured

	result = dict(structured)

	for key in ["critical_clauses", "risks", "recommendations"]:
		items = result.get(key, [])
		if isinstance(items, list):
			cleaned: List[str] = []
			for item in items:
				text = _clean_list_item(item)
				# Drop empty placeholders like "Recomendación:" with nothing else
				if re.fullmatch(r"(?i)recomendaci[oó]n:?\s*", text):
					continue
				# Minimal length filter
				if len(text) < 5:
					continue
				cleaned.append(text)
			result[key] = _deduplicate_preserve_order(cleaned)

	# If no critical clauses provided, try to infer from the text
	if not result.get("critical_clauses") and isinstance(source_text, str):
		inferred = _extract_clauses_from_text(source_text, limit=5)
		if inferred:
			result["critical_clauses"] = inferred

	# Normalize categorical fields
	if "risk_level" in result and isinstance(result["risk_level"], str):
		lvl = result["risk_level"].strip().lower()
		if lvl not in {"alto", "medio", "bajo"}:
			result["risk_level"] = "medio"
	if "compliance_status" in result and isinstance(result["compliance_status"], str):
		cs = result["compliance_status"].strip().lower().replace(" ", "_")
		if cs not in {"cumple", "no_cumple", "parcial"}:
			result["compliance_status"] = "parcial"

	return result

async def analyze_contract_file(
    file_path: Optional[str] = None,
    text: Optional[str] = None,
    file_type: Optional[str] = None,
    contract_type: Optional[str] = None,
    language: str = "es",
    jurisdiction: str = "Colombia",
    analysis_options: Optional[dict] = None,
    instructions: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    upload_to_r2: bool = False
) -> Dict[str, Any]:
    """
    Analyze a contract file or text and provide legal insights.
    
    This function supports files from the 'contract-analisys' Cloudflare R2 bucket
    via file_url parameter in the contract analysis endpoint.
    
    Args:
        file_path: Path to the contract file
        text: Contract text content
        file_type: MIME type of the file
        contract_type: Type of the contract
        language: Language of the contract
        jurisdiction: Jurisdiction of the contract
        analysis_options: Additional options for analysis (supports frontend format)
        instructions: Optional instructions for analysis
        user_id: User ID for personalization and R2 upload
        session_id: Session ID for tracking
        upload_to_r2: Whether to upload analysis results to R2 storage
        
    Returns:
        Dict containing analysis results
    """
    try:
        if not file_path and not text:
            raise ValueError("Either file_path or text must be provided")
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            content = text

        # Process analysis options from frontend format
        specific_concerns = []
        relevant_regulations = []
        data_processing = None
        
        if analysis_options:
            # Handle the new frontend format
            if analysis_options.get("riskFinancial") or analysis_options.get("riskLegal") or analysis_options.get("riskCompliance"):
                specific_concerns.append("evaluación_de_riesgos")
            
            if analysis_options.get("clauseImportant") or analysis_options.get("clauseObligations") or analysis_options.get("clauseTermination"):
                specific_concerns.append("análisis_de_cláusulas")
            
            if analysis_options.get("complianceRegulatory") or analysis_options.get("complianceInternal") or analysis_options.get("complianceIndustry"):
                specific_concerns.append("cumplimiento_regulatorio")
                relevant_regulations.extend([
                    "Código Civil",
                    "Código de Comercio", 
                    "Ley 1581 de 2012 (Habeas Data)",
                    "Ley 80 de 1993 (Contratación Pública)"
                ])
            
            # Handle legacy format if present
            if analysis_options.get("specificConcerns"):
                specific_concerns.extend(analysis_options.get("specificConcerns"))
            if analysis_options.get("relevantRegulations"):
                relevant_regulations.extend(analysis_options.get("relevantRegulations"))
            if analysis_options.get("dataProcessing"):
                data_processing = analysis_options.get("dataProcessing")

        # Determine contract type if not provided
        if not contract_type:
            # Try to infer contract type from content
            content_lower = content.lower()
            if any(keyword in content_lower for keyword in ['servicio', 'servicios', 'prestación']):
                contract_type = "contrato_de_servicios"
            elif any(keyword in content_lower for keyword in ['compra', 'venta', 'comercial']):
                contract_type = "contrato_de_compraventa"
            elif any(keyword in content_lower for keyword in ['arrendamiento', 'alquiler', 'renta']):
                contract_type = "contrato_de_arrendamiento"
            elif any(keyword in content_lower for keyword in ['laboral', 'trabajo', 'empleado']):
                contract_type = "contrato_laboral"
            elif any(keyword in content_lower for keyword in ['confidencialidad', 'secreto', 'nda']):
                contract_type = "acuerdo_de_confidencialidad"
            else:
                contract_type = "contrato_general"

        # Call the real analysis function
        analysis_response = await analyze_contract(
            contract_text=content,
            contract_type=contract_type,
            parties=[],  # Add parties if you have them
            specific_concerns=specific_concerns if specific_concerns else None,
            relevant_regulations=relevant_regulations if relevant_regulations else None,
            data_processing=data_processing,
            user_id=user_id,
            session_id=session_id
        )

        # Try to extract structured JSON from the agent's response
        source_text = analysis_response["summary"] if isinstance(analysis_response, dict) and "summary" in analysis_response else analysis_response
        structured = extract_json_from_markdown(source_text)
        if structured:
            structured = sanitize_structured_analysis(structured, source_text)
        
        # Add structured analysis to the response data
        if isinstance(analysis_response, dict):
            analysis_response["structured_analysis"] = structured
        # Upload to R2 if requested
        if upload_to_r2 and user_id and session_id:
            try:
                from utils.r2_storage import upload_contract_analysis_pdf_to_r2
                
                # Create analysis data for upload
                analysis_data = {
                    "summary": analysis_response.get("summary", ""),
                    "structured_analysis": structured,
                    "contract_type": contract_type,
                    "language": language,
                    "jurisdiction": jurisdiction,
                    "analysis_timestamp": datetime.now().isoformat(),
                    "user_id": user_id,
                    "session_id": session_id
                }
                
                # Upload to R2
                pdf_url = await upload_contract_analysis_pdf_to_r2(
                    analysis_data=analysis_data,
                    user_id=user_id,
                    session_id=session_id,
                    contract_type=contract_type or "contract_analysis"
                )
                
                # Add R2 URL to response
                if isinstance(analysis_response, dict):
                    analysis_response["r2_pdf_url"] = pdf_url
                    analysis_response["uploaded_to_r2"] = True
                else:
                    # If analysis_response is not a dict, wrap it
                    analysis_response = {
                        "summary": analysis_response,
                        "r2_pdf_url": pdf_url,
                        "uploaded_to_r2": True
                    }
                
                logger.info(f"Contract analysis uploaded to R2: {pdf_url}")
                
            except Exception as upload_error:
                logger.warning(f"Failed to upload analysis to R2: {upload_error}")
                # Continue without failing the analysis
        
        # Generate and upload summary PDF
        pdf_url = None
        try:
            from utils.r2_storage import upload_contract_analysis_summary_pdf
            
            # Upload summary PDF to Supabase S3
            pdf_url = await upload_contract_analysis_summary_pdf(
                analysis_data=analysis_response,
                user_id=user_id,
                session_id=session_id,
                contract_type=contract_type
            )
            
            logger.info(f"Contract analysis summary PDF uploaded successfully: {pdf_url}")
            
        except Exception as pdf_error:
            logger.warning(f"Failed to upload summary PDF: {pdf_error}")
            # Continue without failing the analysis
        
        # Return simplified response with only essential data
        if isinstance(analysis_response, dict) and "structured_analysis" in analysis_response:
            # Return structured analysis directly (this is what the frontend expects)
            structured = analysis_response["structured_analysis"]
            if structured:
                # Add PDF URL and status info to structured response
                structured["summary_pdf_url"] = pdf_url
                structured["status"] = "success"
                structured["message"] = "Análisis completado exitosamente"
                structured["pdf_uploaded"] = (pdf_url is not None)
                return structured
        
        # Fallback: return minimal response
        return {
            "status": "success",
            "message": "Análisis completado exitosamente",
            "risk_level": "medio",
            "compliance_status": "parcial",
            "critical_clauses": [],
            "risks": [],
            "recommendations": [],
            "summary_pdf_url": pdf_url,
            "pdf_uploaded": (pdf_url is not None)
        }
    except Exception as e:
        logger.error(f"Error analyzing contract: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing contract: {str(e)}"
        )

async def analyze_risks(
    contract_text: str,
    include_financial: bool = True,
    include_legal: bool = True,
    include_compliance: bool = True
) -> Dict[str, Any]:
    """Analyze contract risks based on selected options"""
    agent = create_contract_agent()
    
    # Build the prompt based on selected risk types
    risk_types = []
    if include_financial:
        risk_types.append("financieros")
    if include_legal:
        risk_types.append("legales")
    if include_compliance:
        risk_types.append("de cumplimiento")
    
    risk_prompt = f"""Analiza el siguiente contrato y evalúa los riesgos {', '.join(risk_types)}.
    
Contrato:
{contract_text}

Proporciona:
1. Nivel general de riesgo (bajo, medio, alto)
2. Lista de riesgos identificados
3. Impacto potencial de cada riesgo

Responde en formato JSON exactamente así:
{{
    "nivel_riesgo": "bajo/medio/alto",
    "riesgos_identificados": ["riesgo 1", "riesgo 2", ...],
    "impacto_potencial": "descripción del impacto"
}}
"""

    try:
        response = await agent.arun(risk_prompt)
        return eval(response.content)
    except Exception as e:
        print(f"Error in risk analysis: {str(e)}")
        return {
            "nivel_riesgo": "no determinado",
            "riesgos_identificados": [],
            "impacto_potencial": "No se pudo determinar"
        }

async def extract_clauses(
    contract_text: str,
    extract_important: bool = True,
    extract_obligations: bool = True,
    extract_termination: bool = True
) -> Dict[str, List[str]]:
    """Extract relevant clauses based on selected options"""
    agent = create_contract_agent()
    
    clause_types = []
    if extract_important:
        clause_types.append("importantes")
    if extract_obligations:
        clause_types.append("obligaciones")
    if extract_termination:
        clause_types.append("términos de finalización")
    
    clause_prompt = f"""Analiza el siguiente contrato y extrae las cláusulas {', '.join(clause_types)}.

Contrato:
{contract_text}

Proporciona las cláusulas en formato JSON exactamente así:
{{
    "clausulas_criticas": ["cláusula 1", "cláusula 2", ...],
    "obligaciones": ["obligación 1", "obligación 2", ...],
    "terminos_finalizacion": ["término 1", "término 2", ...]
}}
"""

    try:
        response = await agent.arun(clause_prompt)
        return eval(response.content)
    except Exception as e:
        print(f"Error in clause extraction: {str(e)}")
        return {
            "clausulas_criticas": [],
            "obligaciones": [],
            "terminos_finalizacion": []
        }

async def check_compliance(
    contract_text: str,
    check_regulatory: bool = True,
    check_internal: bool = True,
    check_industry: bool = True
) -> Dict[str, Any]:
    """Check contract compliance based on selected options"""
    agent = create_contract_agent()
    
    compliance_types = []
    if check_regulatory:
        compliance_types.append("normativa regulatoria")
    if check_internal:
        compliance_types.append("políticas internas")
    if check_industry:
        compliance_types.append("estándares de la industria")
    
    compliance_prompt = f"""Analiza el cumplimiento del siguiente contrato respecto a {', '.join(compliance_types)}.

Contrato:
{contract_text}

Proporciona el análisis en formato JSON exactamente así:
{{
    "status": "compliant/non_compliant",
    "framework_version": "2024.1",
    "incumplimientos": ["incumplimiento 1", "incumplimiento 2", ...],
    "recomendaciones": ["recomendación 1", "recomendación 2", ...]
}}
"""

    try:
        response = await agent.arun(compliance_prompt)
        return eval(response.content)
    except Exception as e:
        print(f"Error in compliance check: {str(e)}")
        return {
            "status": "unknown",
            "framework_version": "2024.1",
            "incumplimientos": [],
            "recomendaciones": []
        }

def extract_critical_clauses(analysis: str) -> List[str]:
    """Extract critical clauses from analysis"""
    # Implementation needed
    return []

def extract_obligations(analysis: str) -> List[str]:
    """Extract main obligations from analysis"""
    # Implementation needed
    return []

def assess_risk_level(analysis: str) -> str:
    """Assess overall risk level"""
    # Implementation needed
    return "medio"

def extract_risks(analysis: str) -> List[str]:
    """Extract identified risks"""
    # Implementation needed
    return []

def assess_impact(analysis: str) -> str:
    """Assess potential impact"""
    # Implementation needed
    return "significativo"

def extract_recommendations(analysis: str) -> List[str]:
    """Extract recommendations"""
    # Implementation needed
    return []

def extract_analysis_metrics(summary: str) -> dict:
    # Extract risk level
    risk_level_match = re.search(r'(?i)riesgo\s*potencial(?:es)?(?:\s*por\s*cl[aá]usula)?[\s\S]*?\*\*(Bajo|Medio|Alto)\*\*', summary)
    risk_level = risk_level_match.group(1) if risk_level_match else "Bajo"
    # Count clauses
    num_clauses = len(re.findall(r'Cl[aá]usula', summary, re.IGNORECASE))
    # Count risks
    num_risks = len(re.findall(r'Riesgo', summary, re.IGNORECASE))
    # Compliance: 100% if "cumple" or "alineadas" found, else 0
    compliance = 100 if re.search(r'cumple|alinead[ao]s?', summary, re.IGNORECASE) else 0
    return {
        "risk_level": risk_level,
        "num_clauses": num_clauses,
        "num_risks": num_risks,
        "compliance": compliance
    }

async def upload_contract_file_to_r2(
    file_content: bytes,
    filename: str,
    user_id: str,
    session_id: str,
    contract_type: str = "contract_analysis"
) -> str:
    """
    Upload a contract file to R2 storage
    
    Args:
        file_content: Binary content of the file
        filename: Original filename
        user_id: User ID for tracking
        session_id: Session ID for tracking
        contract_type: Type of contract
        
    Returns:
        str: Public URL of the uploaded file
    """
    try:
        from utils.r2_storage import upload_contract_file_to_r2 as r2_upload
        
        file_url = await r2_upload(
            file_content=file_content,
            filename=filename,
            user_id=user_id,
            session_id=session_id,
            contract_type=contract_type
        )
        
        logger.info(f"Contract file uploaded to R2: {file_url}")
        return file_url
        
    except Exception as e:
        logger.error(f"Error uploading contract file to R2: {e}")
        raise

async def download_contract_file_from_r2(
    file_url: str,
    user_id: str,
    session_id: str
) -> bytes:
    """
    Download a contract file from R2 storage
    
    Args:
        file_url: URL of the file in R2 storage
        user_id: User ID for tracking
        session_id: Session ID for tracking
        
    Returns:
        bytes: File content
    """
    try:
        from utils.r2_storage import get_contract_analysis_r2_client
        from botocore.exceptions import ClientError
        
        # Extract object key from URL
        # URL format: https://bucket.r2.cloudflarestorage.com/contract-analysis/filename
        # or: https://bucket.r2.cloudflarestorage.com/contract-files/filename
        # or: https://bucket.r2.cloudflarestorage.com/contract-analisys/filename (legacy)
        if '/contract-analysis/' in file_url:
            url_parts = file_url.split('/contract-analysis/')
            if len(url_parts) == 2:
                object_key = f"contract-analysis/{url_parts[1]}"
            else:
                object_key = file_url.split('/')[-1]
        elif '/contract-files/' in file_url:
            url_parts = file_url.split('/contract-files/')
            if len(url_parts) == 2:
                object_key = f"contract-files/{url_parts[1]}"
            else:
                object_key = file_url.split('/')[-1]
        elif '/contract-analisys/' in file_url:
            # Handle legacy contract-analisys URLs - treat as contract files
            url_parts = file_url.split('/contract-analisys/')
            if len(url_parts) == 2:
                object_key = f"contract-files/{url_parts[1]}"
            else:
                object_key = file_url.split('/')[-1]
        else:
            # Fallback: extract just the filename from the URL
            object_key = file_url.split('/')[-1]
        
        # Get R2 client
        r2_client = get_contract_analysis_r2_client()
        
        # Download file
        response = r2_client.get_object(
            Bucket='document-generator',  # Use the main bucket
            Key=object_key
        )
        
        file_content = response['Body'].read()
        logger.info(f"Contract file downloaded from R2: {object_key} ({len(file_content)} bytes)")
        
        return file_content
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"R2 Client error downloading file: {error_code} - {error_message}")
        logger.error(f"Failed to download object: {object_key} from bucket: document-generator")
        
        if error_code == 'AccessDenied':
            raise ValueError(f"Access denied to R2 object '{object_key}'. Please check if the file exists and you have permission to access it.")
        elif error_code == 'NoSuchKey':
            raise ValueError(f"File '{object_key}' not found in R2 storage.")
        else:
            raise ValueError(f"R2 error: {error_code} - {error_message}")
    except Exception as e:
        logger.error(f"Error downloading contract file from R2: {e}")
        raise

async def list_user_contract_files(
    user_id: str,
    contract_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List contract files for a user from R2 storage
    
    Args:
        user_id: User ID to filter files
        contract_type: Optional contract type filter
        
    Returns:
        List of file metadata
    """
    try:
        from utils.r2_storage import list_contract_analysis_documents
        
        documents = await list_contract_analysis_documents(user_id=user_id)
        
        # Filter by contract type if specified
        if contract_type:
            documents = [doc for doc in documents if doc.get('metadata', {}).get('contract_type') == contract_type]
        
        logger.info(f"Found {len(documents)} contract files for user {user_id}")
        return documents
        
    except Exception as e:
        logger.error(f"Error listing contract files: {e}")
        raise

# Add to all agents:
# Implement decision explanation mechanisms
# Add transparency in processing
# Include user consent controls

class SimpleContractAgent:
    """Simple fallback contract agent when agno is not available"""
    
    def __init__(self):
        self.name = "Analista de Contratos Simple"
        self.role = "Analista de contratos básico"
        logger.warning("Using SimpleContractAgent fallback - limited functionality")
    
    async def run(self, message: str, **kwargs):
        """Simple fallback run method"""
        logger.warning("SimpleContractAgent: Limited contract analysis functionality")
        return {
            "response": "Análisis de contrato básico no disponible en este momento. Por favor, contacte al administrador.",
            "status": "limited_functionality"
        }
    
    def __getattr__(self, name):
        """Fallback for any missing methods"""
        logger.warning(f"SimpleContractAgent: Method {name} not available")
        return lambda *args, **kwargs: {
            "response": "Funcionalidad no disponible en modo limitado",
            "status": "limited_functionality"
        }