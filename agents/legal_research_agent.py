from agno.agent import Agent
from agno.tools.googlesearch import GoogleSearchTools
from config.database import get_agent_storage
from config.ai_models import get_model
from config.knowledge_base_integration import (
    create_agent_knowledge_integration,
    AgentKnowledgeHelper
)
from config.enhanced_agent_config import get_enhanced_agent_config
from config.colombian_compliance import (
    ColombianLegalFramework,
    get_legal_term
)
# Force Mistral embedder usage
# Temporarily disabled due to syntax errors
# from config.force_mistral_embedder import force_mistral_embedder
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import asyncio
import json
import re
import logging
from enum import Enum

logger = logging.getLogger(__name__)

# Force Mistral embedder on module import - temporarily disabled
# force_mistral_embedder()

class ResearchMethodology(Enum):
    """Legal research methodologies"""
    DOCTRINAL = "doctrinal"
    COMPARATIVE = "comparative"
    EMPIRICAL = "empirical"
    INTERDISCIPLINARY = "interdisciplinary"
    CRITICAL = "critical"

class LegalResearchAgent:
    """Enhanced Legal Research Agent with professional capabilities"""
    
    def __init__(self, user_id: str = None, session_id: str = None):
        self.user_id = user_id
        self.session_id = session_id or f"research_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.agent = None
        self.knowledge_helper = None
        self.research_history = []
        self.citation_style = "colombian_legal"
        self.initialize_agent()
    
    def initialize_agent(self):
        """Initialize the enhanced legal research agent"""
        try:
            # Create knowledge base integration
            knowledge_integration = create_agent_knowledge_integration("legal_research_agent")
            self.knowledge_helper = AgentKnowledgeHelper("legal_research_agent")
            
            # Get enhanced configuration with memory
            enhanced_config = get_enhanced_agent_config("legal_research_agent")
            
            # Get memory instance for this agent
            memory_instance = enhanced_config.get("memory_instance")
            
            # Configure memory properly for agno framework
            memory_config = None
            if memory_instance:
                if hasattr(memory_instance, 'runs') and hasattr(memory_instance, 'add_run'):
                    memory_config = memory_instance
                    logger.info(f"Legal research agent memory system configured with external memory: {type(memory_instance).__name__}")
                else:
                    logger.warning(f"Memory instance missing required interface, using agno default memory")
            
            self.agent = Agent(
                name="Investigador Jurídico Profesional",
                role="Especialista en investigación jurídica avanzada con metodologías profesionales y acceso a bases de conocimiento legal colombiano e internacional",
                model=get_model("legal_research"),
                knowledge=knowledge_integration,
                search_knowledge=True,
                tools=[GoogleSearchTools()],
                storage=enhanced_config["storage"],
                memory=memory_config,
                session_id=self.session_id,
                #show_tool_calls=True,
                #debug_mode=True,
                #reasoning=False,  # Disable reasoning mode for Mistral API compatibility
                description="""
                    Un agente especializado en realizar investigaciones jurídicas exhaustivas y profesionales 
                    dentro del marco legal colombiano e internacional. Utiliza metodologías de investigación 
                    legal avanzadas, analiza jurisprudencia, autos, legislación y artículos académicos, 
                    proporcionando citas precisas siguiendo estándares profesionales y sintetizando hallazgos 
                    en un formato estructurado para profesionales del derecho. Integra múltiples fuentes de 
                    conocimiento legal actualizadas para proporcionar información precisa, relevante y 
                    metodológicamente sólida.
                """,
                instructions=self._get_enhanced_instructions(),
                markdown=True
            )
            
            logger.info(f"Enhanced Legal Research Agent initialized for user: {self.user_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize enhanced legal research agent: {e}")
            raise
    
    def _get_enhanced_instructions(self) -> List[str]:
        """Get enhanced professional instructions"""
        return [
            # === PROFESSIONAL RESEARCH METHODOLOGY ===
            "Utiliza metodologías de investigación legal profesionales y sistemáticas",
            "Aplica el método doctrinal para análisis de normas y jurisprudencia",
            "Implementa análisis comparativo cuando sea relevante para el derecho colombiano",
            "Considera enfoques interdisciplinarios para temas complejos",
            "Evalúa críticamente las fuentes y su confiabilidad",
            "Mantén objetividad y neutralidad en el análisis legal",
            
            # === ADVANCED MEMORY AND CONTEXT MANAGEMENT ===
            "Gestiona el contexto de investigación de manera inteligente y eficiente",
            "Mantén un historial estructurado de investigaciones previas",
            "Aprende de patrones de investigación exitosos",
            "Adapta la profundidad del análisis según el perfil del usuario",
            "Personaliza las recomendaciones basándote en el historial de investigación",
            "Optimiza las búsquedas basándote en resultados previos",
            
            # === ENHANCED KNOWLEDGE BASE INTEGRATION ===
            "Utiliza la base de conocimiento legal de manera estratégica y eficiente",
            "Consulta múltiples fuentes de conocimiento para validación cruzada",
            "Prioriza fuentes primarias sobre secundarias",
            "Verifica la vigencia y aplicabilidad de todas las fuentes",
            "Integra información de diferentes jurisdicciones cuando sea relevante",
            "Aplica mejores prácticas de investigación legal documentadas",
            
            # === PROFESSIONAL LEGAL RESEARCH STANDARDS ===
            "Realiza investigaciones jurídicas exhaustivas siguiendo estándares académicos",
            "Busca y analiza jurisprudencia de las Altas Cortes de Colombia sistemáticamente",
            "Identifica precedentes vinculantes y doctrina probable con precisión",
            "Examina la legislación vigente incluyendo su evolución histórica",
            "Verifica la vigencia y aplicabilidad de las normas legales",
            "Identifica derogaciones, modificaciones y vacíos legales",
            
            # === ADVANCED ANALYSIS CAPABILITIES ===
            "Evalúa principios constitucionales y su aplicación práctica",
            "Analiza conceptos e interpretaciones administrativas",
            "Considera el derecho comparado de manera crítica y contextualizada",
            "Evalúa el impacto del control constitucional en el tema",
            "Identifica reformas legislativas recientes y sus implicaciones",
            "Analiza tendencias jurisprudenciales y doctrinales",
            
            # === PROFESSIONAL CITATION AND FORMATTING ===
            "Cita las fuentes jurídicas siguiendo estándares profesionales colombianos",
            "Utiliza el sistema de citación legal colombiano (Corte Constitucional, etc.)",
            "Incluye referencias completas y precisas a todas las fuentes",
            "Formatea las respuestas siguiendo estándares académicos",
            "Estructura la información de manera lógica y coherente",
            "Utiliza terminología legal precisa y consistente",
            
            # === ENHANCED OUTPUT STRUCTURE ===
            "Devuelve resultados en formato markdown profesional con estructura clara",
            "Incluye un bloque JSON estructurado con análisis detallado",
            "Proporciona de 5 a 7 resultados por sección con justificación",
            "Incluye análisis de relevancia y confiabilidad de fuentes",
            "Proporciona síntesis ejecutiva y recomendaciones profesionales",
            "Incluye estadísticas de investigación y metodología utilizada",
            
            # === ERROR HANDLING AND QUALITY ASSURANCE ===
            "Maneja errores de manera profesional y proporciona alternativas",
            "Valida la calidad y confiabilidad de todas las fuentes",
            "Indica limitaciones y sugiere enfoques alternativos cuando sea necesario",
            "Evita interpretaciones especulativas y mantén rigor académico",
            "Asegura el uso ético de las fuentes respetando derechos de autor",
            "Proporciona advertencias sobre información desactualizada o controvertida",
            
            # === MULTI-JURISDICTIONAL SUPPORT ===
            "Considera el derecho internacional cuando sea relevante",
            "Analiza tratados y convenciones internacionales aplicables",
            "Evalúa la influencia del derecho comparado en el contexto colombiano",
            "Considera decisiones de tribunales internacionales relevantes",
            "Integra perspectivas de derecho supranacional cuando sea apropiado",
            
            # === PROFESSIONAL COMMUNICATION ===
            "Adapta el nivel de complejidad según el perfil del usuario",
            "Utiliza un tono profesional y académico apropiado",
            "Proporciona explicaciones claras de conceptos técnicos",
            "Ofrece recomendaciones prácticas y aplicables",
            "Mantén consistencia en la terminología y enfoque",
            "Proporciona contexto histórico y evolutivo cuando sea relevante"
        ]
    
    async def conduct_comprehensive_research(
        self,
        research_topic: str,
        jurisdiction: str = "Colombia",
        methodology: ResearchMethodology = ResearchMethodology.DOCTRINAL,
        specific_areas: Optional[List[str]] = None,
        legal_terms: Optional[List[str]] = None,
        timeframe: Optional[str] = None,
        case_law_only: bool = False,
        include_comparative: bool = False,
        include_international: bool = False,
        depth_level: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Conduct comprehensive legal research with professional methodology
        
        Args:
            research_topic: Main research topic
            jurisdiction: Legal jurisdiction (default: Colombia)
            methodology: Research methodology to apply
            specific_areas: Specific legal areas to focus on
            legal_terms: Legal terms to analyze
            timeframe: Time period for analysis
            case_law_only: Focus only on case law
            include_comparative: Include comparative law analysis
            include_international: Include international law
            depth_level: Research depth (basic, intermediate, comprehensive)
            
        Returns:
            Comprehensive research results
        """
        try:
            # Initialize research session
            research_session = {
                "topic": research_topic,
                "jurisdiction": jurisdiction,
                "methodology": methodology.value,
                "timestamp": datetime.now().isoformat(),
                "user_id": self.user_id,
                "session_id": self.session_id
            }
            
            # Build enhanced research prompt
            prompt = self._build_research_prompt(
                research_topic, jurisdiction, methodology, specific_areas,
                legal_terms, timeframe, case_law_only, include_comparative,
                include_international, depth_level
            )
            
            # Execute research
            response = await self.agent.arun(prompt)
            
            # Process and structure results
            results = self._process_research_results(response, research_session)
            
            # Store research memory in database
            self._store_research_memory(research_session, results)
            
            # Update research history
            self.research_history.append(research_session)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in comprehensive research: {e}")
            return self._create_error_response(str(e), research_topic)
    
    def _build_research_prompt(
        self,
        research_topic: str,
        jurisdiction: str,
        methodology: ResearchMethodology,
        specific_areas: Optional[List[str]] = None,
        legal_terms: Optional[List[str]] = None,
        timeframe: Optional[str] = None,
        case_law_only: bool = False,
        include_comparative: bool = False,
        include_international: bool = False,
        depth_level: str = "comprehensive"
    ) -> str:
        """Build comprehensive research prompt"""
        
        prompt = f"""Realizar investigación jurídica profesional y exhaustiva siguiendo metodología {methodology.value}:

TEMA DE INVESTIGACIÓN: {research_topic}
JURISDICCIÓN: {jurisdiction}
METODOLOGÍA: {methodology.value.upper()}
NIVEL DE PROFUNDIDAD: {depth_level.upper()}
"""

        if specific_areas:
            prompt += f"ÁREAS ESPECÍFICAS: {', '.join(specific_areas)}\n"
        
        if timeframe:
            prompt += f"PERÍODO DE ANÁLISIS: {timeframe}\n"
        
        if case_law_only:
            prompt += "ENFOQUE: Exclusivamente jurisprudencia\n"
        
        if include_comparative:
            prompt += "INCLUIR: Análisis de derecho comparado\n"
        
        if include_international:
            prompt += "INCLUIR: Derecho internacional y tratados\n"
        
        prompt += f"""
MARCO METODOLÓGICO:
- Aplicar metodología {methodology.value} de manera sistemática
- Validar fuentes primarias y secundarias
- Analizar evolución histórica y tendencias actuales
- Evaluar impacto práctico y aplicabilidad
- Considerar críticas y perspectivas alternativas

MARCO JURÍDICO {jurisdiction.upper()}:
- Principios Constitucionales: {', '.join(ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES)}
- Fuentes del Derecho:
  * Constitución Política
  * Leyes y Decretos
  * Jurisprudencia de Altas Cortes
  * Doctrina Autorizada
  * Conceptos Vinculantes
  * Tratados Internacionales (si aplica)
"""
        
        # Add legal terms context
        if legal_terms:
            legal_terms_dict = {}
            for term in legal_terms:
                definition = get_legal_term(term)
                if definition:
                    legal_terms_dict[term] = definition
            
            if legal_terms_dict:
                prompt += "\nTÉRMINOS JURÍDICOS RELEVANTES:\n"
                for term, definition in legal_terms_dict.items():
                    prompt += f"- {term}: {definition}\n"
        
        # Add knowledge base context
        try:
            if self.knowledge_helper:
                # Get relevant jurisprudence
                jurisprudence = asyncio.run(self.knowledge_helper.integration.get_jurisprudence(research_topic, limit=5))
                if jurisprudence:
                    prompt += "\nJURISPRUDENCIA RELEVANTE DE LA BASE DE CONOCIMIENTO:\n"
                    for jur in jurisprudence[:3]:
                        prompt += f"- {jur.get('topic', 'N/A')}: {jur.get('summary', '')[:200]}...\n"
                
                # Get relevant legal documents
                legal_docs = asyncio.run(self.knowledge_helper.integration.search_knowledge(research_topic, limit=3))
                if legal_docs.get("results"):
                    prompt += "\nDOCUMENTOS LEGALES RELEVANTES:\n"
                    for doc in legal_docs["results"][:3]:
                        prompt += f"- {doc.get('metadata', {}).get('title', 'N/A')}: {doc.get('content', '')[:200]}...\n"
        except Exception as e:
            logger.warning(f"Could not retrieve knowledge base context: {e}")
        
        prompt += """
ESTRUCTURA DE RESPUESTA REQUERIDA:
1. RESUMEN EJECUTIVO (al menos 900 palabras)
2. METODOLOGÍA APLICADA
3. ANÁLISIS NORMATIVO
4. JURISPRUDENCIA RELEVANTE
5. DOCTRINA APLICABLE
6. ANÁLISIS COMPARATIVO (si aplica)
7. RECOMENDACIONES PROFESIONALES
8. FUENTES Y CITACIONES
9. LIMITACIONES Y CONSIDERACIONES

FORMATO JSON ESTRUCTURADO:
{
  "executive_summary": "Resumen ejecutivo profesional",
  "methodology": "Metodología aplicada",
  "cases": [{"title", "court", "date", "jurisdiction", "summary", "tags", "relevance", "url", "key_holdings", "impact"}],
  "legislation": [{"title", "type", "date", "jurisdiction", "summary", "tags", "url", "status", "amendments"}],
  "doctrine": [{"title", "author", "date", "source", "summary", "tags", "url", "relevance"}],
  "comparative_analysis": [{"jurisdiction", "approach", "similarities", "differences", "lessons"}],
  "recommendations": [{"type", "description", "priority", "implementation"}],
  "statistics": {"sources_found", "search_time", "relevance_distribution", "methodology_used"},
  "limitations": ["limitación1", "limitación2"],
  "future_research": ["área1", "área2"]
}

Asegúrate de:
- Seguir estándares de citación legal colombianos
- Validar todas las fuentes
- Proporcionar análisis crítico
- Incluir perspectivas alternativas
- Mantener rigor académico
- Ofrecer recomendaciones prácticas
"""
        
        return prompt
    
    def _process_research_results(self, response: Any, research_session: Dict[str, Any]) -> Dict[str, Any]:
        """Process and structure research results"""
        try:
            # Try to extract JSON from response
            json_data = self._extract_json_from_response(response.content)
            
            if json_data:
                # Validate and enhance JSON structure
                enhanced_results = self._enhance_json_structure(json_data)
            else:
                # Fallback to parsing text response
                enhanced_results = self._parse_text_response(response.content)
            
            # Add metadata
            enhanced_results.update({
                "research_session": research_session,
                "response_metadata": {
                    "response_length": len(response.content),
                    "processing_timestamp": datetime.now().isoformat(),
                    "agent_version": "2.0_enhanced",
                    "methodology_applied": research_session.get("methodology", "doctrinal")
                }
            })
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Error processing research results: {e}")
            return self._create_error_response(str(e), research_session.get("topic", "Unknown"))
    
    def _extract_json_from_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from response content"""
        try:
            # Look for JSON blocks in the response
            json_patterns = [
                r'```json\s*(.*?)\s*```',
                r'```\s*(.*?)\s*```',
                r'\{.*\}'
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, content, re.DOTALL)
                for match in matches:
                    try:
                        return json.loads(match)
                    except json.JSONDecodeError:
                        continue
            
            return None
            
        except Exception as e:
            logger.warning(f"Could not extract JSON from response: {e}")
            return None
    
    def _enhance_json_structure(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance and validate JSON structure"""
        enhanced = {
            "executive_summary": json_data.get("executive_summary", ""),
            "methodology": json_data.get("methodology", "doctrinal"),
            "cases": self._validate_cases(json_data.get("cases", [])),
            "legislation": self._validate_legislation(json_data.get("legislation", [])),
            "doctrine": self._validate_doctrine(json_data.get("doctrine", [])),
            "comparative_analysis": json_data.get("comparative_analysis", []),
            "recommendations": self._validate_recommendations(json_data.get("recommendations", [])),
            "statistics": self._validate_statistics(json_data.get("statistics", {})),
            "limitations": json_data.get("limitations", []),
            "future_research": json_data.get("future_research", [])
        }
        
        return enhanced
    
    def _validate_cases(self, cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and enhance case data"""
        validated = []
        for case in cases:
            # Safely convert relevance to float
            relevance = case.get("relevance", 0.5)
            try:
                if isinstance(relevance, str):
                    # Try to extract numeric value from string like "Alta (establece precedentes...)"
                    import re
                    numeric_match = re.search(r'(\d+\.?\d*)', relevance)
                    if numeric_match:
                        relevance = float(numeric_match.group(1)) / 100.0  # Convert percentage to decimal
                    else:
                        relevance = 0.5  # Default value
                else:
                    relevance = float(relevance)
                relevance = min(1.0, max(0.0, relevance))
            except (ValueError, TypeError):
                relevance = 0.5  # Default value if conversion fails
            
            validated_case = {
                "title": case.get("title", "N/A"),
                "court": case.get("court", "N/A"),
                "date": case.get("date", "N/A"),
                "jurisdiction": case.get("jurisdiction", "Colombia"),
                "summary": case.get("summary", ""),
                "tags": case.get("tags", []),
                "relevance": relevance,
                "url": case.get("url", ""),
                "key_holdings": case.get("key_holdings", ""),
                "impact": case.get("impact", "")
            }
            validated.append(validated_case)
        return validated
    
    def _validate_legislation(self, legislation: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and enhance legislation data"""
        validated = []
        for leg in legislation:
            validated_leg = {
                "title": leg.get("title", "N/A"),
                "type": leg.get("type", "N/A"),
                "date": leg.get("date", "N/A"),
                "jurisdiction": leg.get("jurisdiction", "Colombia"),
                "summary": leg.get("summary", ""),
                "tags": leg.get("tags", []),
                "url": leg.get("url", ""),
                "status": leg.get("status", "vigente"),
                "amendments": leg.get("amendments", [])
            }
            validated.append(validated_leg)
        return validated
    
    def _validate_doctrine(self, doctrine: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and enhance doctrine data"""
        validated = []
        for doc in doctrine:
            # Safely convert relevance to float
            relevance = doc.get("relevance", 0.5)
            try:
                if isinstance(relevance, str):
                    # Try to extract numeric value from string
                    import re
                    numeric_match = re.search(r'(\d+\.?\d*)', relevance)
                    if numeric_match:
                        relevance = float(numeric_match.group(1)) / 100.0  # Convert percentage to decimal
                    else:
                        relevance = 0.5  # Default value
                else:
                    relevance = float(relevance)
                relevance = min(1.0, max(0.0, relevance))
            except (ValueError, TypeError):
                relevance = 0.5  # Default value if conversion fails
            
            validated_doc = {
                "title": doc.get("title", "N/A"),
                "author": doc.get("author", "N/A"),
                "date": doc.get("date", "N/A"),
                "source": doc.get("source", "N/A"),
                "summary": doc.get("summary", ""),
                "tags": doc.get("tags", []),
                "url": doc.get("url", ""),
                "relevance": relevance
            }
            validated.append(validated_doc)
        return validated
    
    def _validate_recommendations(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and enhance recommendations"""
        validated = []
        for rec in recommendations:
            validated_rec = {
                "type": rec.get("type", "general"),
                "description": rec.get("description", ""),
                "priority": rec.get("priority", "medium"),
                "implementation": rec.get("implementation", "")
            }
            validated.append(validated_rec)
        return validated
    
    def _validate_statistics(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance statistics"""
        return {
            "sources_found": stats.get("sources_found", 0),
            "search_time": stats.get("search_time", "N/A"),
            "relevance_distribution": stats.get("relevance_distribution", {}),
            "methodology_used": stats.get("methodology_used", "doctrinal")
        }
    
    def _parse_text_response(self, content: str) -> Dict[str, Any]:
        """Parse text response when JSON extraction fails"""
        return {
            "executive_summary": "Análisis basado en respuesta textual del agente",
            "methodology": "doctrinal",
            "raw_response": content,
            "cases": [],
            "legislation": [],
            "doctrine": [],
            "comparative_analysis": [],
            "recommendations": [],
            "statistics": {"sources_found": 0, "search_time": "N/A"},
            "limitations": ["Respuesta no estructurada en JSON"],
            "future_research": []
        }
    
    def _create_error_response(self, error_message: str, topic: str) -> Dict[str, Any]:
        """Create error response structure"""
        return {
            "executive_summary": f"Error en la investigación sobre '{topic}': {error_message}",
            "methodology": "error",
            "cases": [],
            "legislation": [],
            "doctrine": [],
            "comparative_analysis": [],
            "recommendations": [
                {
                    "type": "error_recovery",
                    "description": "Verificar conectividad y configuración del sistema",
                    "priority": "high",
                    "implementation": "Contactar soporte técnico"
                }
            ],
            "statistics": {"sources_found": 0, "search_time": "N/A"},
            "limitations": [f"Error técnico: {error_message}"],
            "future_research": [],
            "error": error_message
        }
    
    async def get_research_history(self) -> List[Dict[str, Any]]:
        """Get research history for the user"""
        return self.research_history
    
    def set_citation_style(self, style: str):
        """Set citation style for research"""
        self.citation_style = style
    
    def _store_research_memory(self, research_session: Dict[str, Any], results: Dict[str, Any]):
        """Store research memory in the database"""
        try:
            if not self.user_id:
                logger.warning("No user_id provided, skipping memory storage")
                return
            
            # Get memory instance from enhanced config
            enhanced_config = get_enhanced_agent_config("legal_research_agent")
            memory_instance = enhanced_config.get("memory_instance")
            
            if not memory_instance:
                logger.warning("No memory instance available, skipping memory storage")
                return
            
            # Extract research topics from results
            research_topics = []
            if results.get("cases"):
                for case in results["cases"]:
                    if case.get("tags"):
                        research_topics.extend(case["tags"])
            
            if results.get("legislation"):
                for leg in results["legislation"]:
                    if leg.get("tags"):
                        research_topics.extend(leg["tags"])
            
            # Remove duplicates
            research_topics = list(set(research_topics))
            
            # Extract legal sources
            legal_sources = []
            if results.get("cases"):
                for case in results["cases"]:
                    if case.get("court"):
                        legal_sources.append(f"Court: {case['court']}")
            
            if results.get("legislation"):
                for leg in results["legislation"]:
                    if leg.get("type"):
                        legal_sources.append(f"Legislation: {leg['type']}")
            
            # Create research summary
            research_summary = results.get("executive_summary", "")
            if not research_summary and results.get("raw_response"):
                research_summary = results["raw_response"][:500] + "..." if len(results["raw_response"]) > 500 else results["raw_response"]
            
            # Store memory using the memory instance
            if hasattr(memory_instance, 'store_legal_research_memory'):
                success = memory_instance.store_legal_research_memory(
                    user_id=self.user_id,
                    session_id=self.session_id,
                    research_topic=research_session.get("topic", ""),
                    research_summary=research_summary,
                    research_topics=research_topics,
                    legal_sources=legal_sources,
                    jurisdiction=research_session.get("jurisdiction", "Colombia")
                )
                
                if success:
                    logger.info(f"Research memory stored successfully for user {self.user_id}")
                else:
                    logger.warning(f"Failed to store research memory for user {self.user_id}")
            else:
                logger.warning("Memory instance does not have store_legal_research_memory method")
                
        except Exception as e:
            logger.error(f"Error storing research memory: {e}")
    
    def get_research_statistics(self) -> Dict[str, Any]:
        """Get research statistics"""
        return {
            "total_research_sessions": len(self.research_history),
            "user_id": self.user_id,
            "session_id": self.session_id,
            "citation_style": self.citation_style,
            "agent_version": "2.0_enhanced"
        }

# Backward compatibility function
def create_legal_research_agent(user_id: str = None, session_id: str = None) -> Agent:
    """Create a specialized agent for legal research with enhanced memory capabilities"""
    # Create knowledge base integration
    knowledge_integration = create_agent_knowledge_integration("legal_research_agent")
    
    # Get enhanced configuration with memory
    enhanced_config = get_enhanced_agent_config("legal_research_agent")
    
    # Get memory instance for this agent
    memory_instance = enhanced_config.get("memory_instance")
    
    # Configure memory properly for agno framework
    memory_config = None
    if memory_instance:
        if hasattr(memory_instance, 'runs') and hasattr(memory_instance, 'add_run'):
            memory_config = memory_instance
            logger.info(f"Legal research agent memory system configured with external memory: {type(memory_instance).__name__}")
        else:
            logger.warning(f"Memory instance missing required interface, using agno default memory")
    
    return Agent(
        name="Investigador Jurídico",
        role="Especialista en investigación jurídica con acceso a base de conocimiento legal colombiano",
        model=get_model("legal_research"),
        knowledge=knowledge_integration,
        search_knowledge=True,
        tools=[GoogleSearchTools()],
        storage=enhanced_config["storage"],
        memory=memory_config,
        session_id=session_id or f"research_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        show_tool_calls=True,
        debug_mode=True,
        reasoning=False,  # Disable reasoning mode temporarily to fix Mistral API compatibility
       description="""
            Un agente especializado en realizar investigaciones jurídicas exhaustivas dentro del marco legal colombiano e internacional.
            Analiza jurisprudencia, autos, legislación y artículos académicos, proporcionando citas precisas y sintetizando hallazgos en un formato estructurado para profesionales del derecho.
            Utiliza una base de conocimiento legal actualizada para proporcionar información precisa y relevante.
        """,
        instructions=[
            # === MEMORY AND PERSONALIZATION ===
            "Considera las preferencias del usuario basándote en investigaciones previas",
            "Adapta el nivel de detalle según la experiencia legal del usuario",
            "Mantén consistencia con investigaciones previas del mismo usuario",
            "Aprende de los patrones identificados en temas de investigación similares",
            "Personaliza las recomendaciones según el perfil del usuario",
            "Utiliza el historial de investigación para proporcionar insights más precisos",
            "Recuerda las áreas de interés específicas del usuario",
            "Adapta el tono y complejidad según el perfil del usuario",
            
            # === SESSION MANAGEMENT ===
            "Mantén el contexto de la sesión actual de investigación",
            "Referencia investigaciones previas cuando sea relevante",
            "Continúa investigaciones iniciadas en sesiones anteriores",
            "Proporciona seguimiento a temas investigados previamente",
            
            # === KNOWLEDGE BASE INTEGRATION ===
            "Utiliza la base de conocimiento legal para obtener información actualizada sobre jurisprudencia colombiana",
            "Consulta términos legales específicos y sus definiciones de la base de conocimiento",
            "Busca en documentos legales, sentencias y marcos regulatorios almacenados",
            "Cita fuentes específicas y referencias normativas de la base de conocimiento",
            "Aplica mejores prácticas de investigación legal documentadas en el sistema",
            
            # Instrucciones de Investigación
            "Realiza investigaciones jurídicas exhaustivas enfocándote exclusivamente en el marco legal colombiano e internacional.",
            "Busca y analiza jurisprudencia de las Altas Cortes de Colombia (Corte Constitucional, Corte Suprema, Consejo de Estado).",
            "Identifica precedentes vinculantes y doctrina probable.",
            "Examina la legislación vigente, incluyendo su evolución histórica y modificaciones.",
            "Verifica la vigencia y aplicabilidad de las normas legales, indicando cualquier derogación o modificación.",

            # Instrucciones de Análisis
            "Evalúa los principios constitucionales relevantes y su aplicación al tema de investigación.",
            "Analiza conceptos e interpretaciones administrativas emitidas por autoridades colombianas.",
            "Considera el derecho comparado solo cuando enriquezca la comprensión del derecho colombiano.",
            "Evalúa el impacto del control constitucional (por ejemplo, sentencias de la Corte Constitucional) en el tema.",
            "Identifica reformas legislativas recientes y sus implicaciones.",

            # Instrucciones de Fuentes y Citación
            "Cita las fuentes jurídicas con precisión técnica, siguiendo los estándares de citación legales colombianos.",
            "Utiliza fuentes autorizadas como diarios oficiales, bases de datos de cortes y revistas jurídicas de prestigio.",
            "Verifica la confiabilidad y relevancia de todas las fuentes, priorizando fuentes primarias.",

            # Instrucciones de Salida
            "Devuelve los resultados en formato markdown, estructurados con encabezados claros para casos, legislación, artículos y resumen.",
            "Incluye un bloque JSON al final de la respuesta con los siguientes campos: cases, legislation, articles, summary, statistics, knowledge_sources.",
            "Para cada sección (casos, legislación, artículos), proporciona de 3 a 5 resultados si están disponibles; si hay menos, explica por qué.",
            "Cada caso debe incluir: título, corte, fecha, jurisdicción, resumen, etiquetas, relevancia (escala 0–1), url.",
            "Cada legislación debe incluir: título, tipo (por ejemplo, ley, decreto), fecha, jurisdicción, resumen, etiquetas, url.",
            "Cada artículo debe incluir: título, autor, fecha, fuente, resumen, etiquetas, url.",
            "El campo resumen en JSON debe ser una síntesis detallada y bien redactada que conecte los hallazgos clave de todas las secciones.",
            "El campo estadísticas debe incluir: número de fuentes encontradas, tiempo de búsqueda y distribución de relevancia de los resultados.",
            "El campo knowledge_sources debe listar las fuentes de conocimiento utilizadas del sistema con su relevancia.",

            # Manejo de Errores y Ética
            "Si los datos encontrados son insuficientes, indica claramente las limitaciones y sugiere enfoques de investigación alternativos.",
            "Evita interpretaciones especulativas de normas o jurisprudencia; confía en datos verificados.",
            "Asegura el uso ético de las fuentes, respetando los derechos de autor y la propiedad intelectual."
        ],
        markdown=True
    )

async def conduct_legal_research(
    research_topic: str,
    jurisdiction: str,
    specific_areas: Optional[List[str]] = None,
    data_processing: Optional[Dict[str, str]] = None,
    legal_terms: Optional[List[str]] = None,
    timeframe: str = None,
    case_law_only: bool = False,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """Realizar investigación jurídica exhaustiva sobre un tema específico con integración de base de conocimiento"""
    agent = create_legal_research_agent(user_id=user_id, session_id=session_id)
    
    # Create knowledge helper for enhanced research
    knowledge_helper = AgentKnowledgeHelper("legal_research_agent")
    
    # Get Colombian legal terms if provided
    legal_terms_dict = {}
    if legal_terms:
        legal_terms_dict = {term: get_legal_term(term) for term in legal_terms if get_legal_term(term)}
    
    # Get additional legal terms from knowledge base
    additional_terms = knowledge_helper._extract_potential_terms(research_topic)
    if additional_terms:
        additional_definitions = await knowledge_helper.get_relevant_legal_terms(research_topic)
        legal_terms_dict.update(additional_definitions)
    
    # Get relevant jurisprudence from knowledge base
    jurisprudence = await knowledge_helper.integration.get_jurisprudence(
        topic=research_topic,
        limit=10
    )
    
    # Get relevant legal documents from knowledge base
    legal_documents = await knowledge_helper.integration.search_knowledge(
        query=research_topic,
        limit=5
    )
    
    # Update prompt in Spanish with knowledge base context
    prompt = f"""Realizar investigación jurídica exhaustiva sobre el siguiente tema:

TEMA: {research_topic}
JURISDICCIÓN: {jurisdiction}
"""

    if specific_areas:
        prompt += f"ÁREAS ESPECÍFICAS: {', '.join(specific_areas)}\n"
    
    if timeframe:
        prompt += f"PERÍODO DE ANÁLISIS: {timeframe}\n"
    
    if case_law_only:
        prompt += "Enfocarse únicamente en jurisprudencia, no en normatividad.\n"
    
    prompt += f"""
MARCO JURÍDICO COLOMBIANO:
- Principios Constitucionales: {', '.join(ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES)}
- Fuentes del Derecho:
  * Constitución Política
  * Leyes y Decretos
  * Jurisprudencia de Altas Cortes
  * Doctrina Autorizada
  * Conceptos Vinculantes
"""
    
    # Add knowledge base context
    if legal_terms_dict:
        prompt += "\nTÉRMINOS JURÍDICOS RELEVANTES:\n"
        for term, definition in legal_terms_dict.items():
            prompt += f"- {term}: {definition}\n"
    
    if jurisprudence:
        prompt += "\nJURISPRUDENCIA RELEVANTE DE LA BASE DE CONOCIMIENTO:\n"
        for jur in jurisprudence[:3]:  # Top 3 most relevant
            prompt += f"- {jur.get('topic', 'N/A')}: {jur.get('summary', '')[:200]}...\n"
    
    if legal_documents.get("results"):
        prompt += "\nDOCUMENTOS LEGALES RELEVANTES:\n"
        for doc in legal_documents["results"][:3]:  # Top 3 most relevant
            prompt += f"- {doc.get('metadata', {}).get('title', 'N/A')}: {doc.get('content', '')[:200]}...\n"
    
    prompt += ("\nDevuelve los resultados en formato JSON estructurado con los siguientes campos: "
               "cases, legislation, articles, summary, statistics, knowledge_sources. "
               "Cada caso debe incluir: title, court, date, jurisdiction, summary, tags, relevance, url. "
               "Cada legislación debe incluir: title, type, date, jurisdiction, summary, tags, url. "
               "Cada artículo debe incluir: title, author, date, source, summary, tags, url. "
               "Incluye también un resumen ejecutivo, estadísticas de la búsqueda y fuentes de conocimiento utilizadas.")
    
    # Run the research
    response = await agent.arun(prompt)
    
    def clean_json_string(json_str: str) -> str:
        """Clean JSON string by removing invalid control characters and fixing common issues"""
        import re
        
        # Remove invalid control characters (except newlines and tabs)
        cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', json_str)
        
        # Fix common JSON issues
        # Replace smart quotes with regular quotes
        cleaned = cleaned.replace('"', '"').replace('"', '"')
        cleaned = cleaned.replace(''', "'").replace(''', "'")
        
        # Fix escaped quotes that might be malformed
        cleaned = re.sub(r'\\"', '"', cleaned)
        cleaned = re.sub(r'\\"', '"', cleaned)
        
        # Remove any trailing commas before closing braces/brackets
        cleaned = re.sub(r',(\s*[}\]])', r'\1', cleaned)
        
        # Fix any double-escaped characters
        cleaned = re.sub(r'\\\\([^"\\])', r'\\\1', cleaned)
        
        return cleaned
    
    # Parse response.content as JSON and map to new response structure
    parsed_data = None
    try:
        # Try to extract JSON from the response
        import json
        import re
        
        # Look for JSON blocks in the response
        json_patterns = [
            r'```json\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```',
            r'\{.*\}'
        ]
        
        # If no JSON blocks found, try to parse the entire response
        if not any(re.findall(pattern, response.content, re.DOTALL) for pattern in json_patterns):
            logger.info("No JSON blocks found, trying to parse entire response content")
            try:
                parsed_data = json.loads(response.content)
                logger.info("Successfully parsed entire response as JSON")
            except json.JSONDecodeError:
                logger.warning("Failed to parse entire response as JSON")
                parsed_data = None
        
        for pattern in json_patterns:
            matches = re.findall(pattern, response.content, re.DOTALL)
            logger.info(f"Found {len(matches)} matches for pattern: {pattern}")
            for i, match in enumerate(matches):
                logger.info(f"Trying to parse match {i+1} (length: {len(match)})")
                
                # Clean the JSON string to remove invalid control characters
                cleaned_match = clean_json_string(match)
                
                try:
                    parsed_data = json.loads(cleaned_match)
                    logger.info("Successfully parsed JSON from legal research response")
                    logger.info(f"Parsed data type: {type(parsed_data)}")
                    break
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON decode error for match {i+1}: {e}")
                    continue
            if parsed_data:
                break
                
    except Exception as e:
        logger.warning(f"Failed to parse JSON from response: {e}")
        parsed_data = None
    
    # Build the result structure
    if parsed_data:
        # Debug logging
        logger.info(f"Parsed data keys: {list(parsed_data.keys())}")
        logger.info(f"Cases found: {len(parsed_data.get('cases', []))}")
        logger.info(f"Legislation found: {len(parsed_data.get('legislation', []))}")
        logger.info(f"Articles found: {len(parsed_data.get('articles', []))}")
        
        # Use parsed data to populate structured fields
    result = {
            "cases": parsed_data.get("cases", []),
            "legislation": parsed_data.get("legislation", []),
            "articles": parsed_data.get("articles", []),
            "summary": parsed_data.get("summary", response.content),
            "statistics": parsed_data.get("statistics", {}),
            "research_topic": research_topic,
            "jurisdiction": jurisdiction,
            "colombian_compliance": {
                "framework_version": ColombianLegalFramework.FRAMEWORK_VERSION,
                "constitutional_principles": ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES,
                "research_date": datetime.now().isoformat()
            },
            "legal_framework": {
                "leyes": [],
                "decretos": [],
                "resoluciones": []
            },
            "jurisprudence": jurisprudence,
            "knowledge_base_usage": {
                "legal_terms_found": len(legal_terms_dict),
                "jurisprudence_found": len(jurisprudence),
                "legal_documents_found": len(legal_documents.get("results", [])),
                "knowledge_sources": [
                    {"type": "legal_terms", "count": len(legal_terms_dict)},
                    {"type": "jurisprudence", "count": len(jurisprudence)},
                    {"type": "legal_documents", "count": len(legal_documents.get("results", []))}
                ]
            }
        }
    else:
        # Fallback to old structure if parsing fails
        result = {
            "cases": [],
            "legislation": [],
            "articles": [],
            "summary": response.content,
            "statistics": {},
            "research_topic": research_topic,
            "jurisdiction": jurisdiction,
            "colombian_compliance": {
                "framework_version": ColombianLegalFramework.FRAMEWORK_VERSION,
                "constitutional_principles": ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES,
                "research_date": datetime.now().isoformat()
            },
            "legal_framework": {
                "leyes": [],
                "decretos": [],
                "resoluciones": []
            },
            "jurisprudence": jurisprudence,
            "knowledge_base_usage": {
                "legal_terms_found": len(legal_terms_dict),
                "jurisprudence_found": len(jurisprudence),
                "legal_documents_found": len(legal_documents.get("results", [])),
                "knowledge_sources": [
                    {"type": "legal_terms", "count": len(legal_terms_dict)},
                    {"type": "jurisprudence", "count": len(jurisprudence)},
                    {"type": "legal_documents", "count": len(legal_documents.get("results", []))}
                ]
            }
    }
    
    if specific_areas:
        result["specific_areas"] = specific_areas
    
    if data_processing:
        result["data_processing"] = data_processing
    
    if legal_terms_dict:
        result["legal_terms"] = legal_terms_dict
    
    # Store research memory if user_id is provided
    if user_id:
        try:
            # Get memory instance
            from postgres_memory import get_memory_instance
            memory_instance = get_memory_instance("legal_research_agent")
            
            if memory_instance and hasattr(memory_instance, 'store_legal_research_memory'):
                # Extract research topics and sources
                research_topics = []
                legal_sources = []
                
                # Add specific areas as topics
                if specific_areas:
                    research_topics.extend(specific_areas)
                
                # Add legal terms as topics
                if legal_terms:
                    research_topics.extend(legal_terms)
                
                # Add jurisprudence sources
                if jurisprudence:
                    legal_sources.append("Jurisprudence Database")
                
                # Add legal documents sources
                if legal_documents.get("results"):
                    legal_sources.append("Legal Documents Database")
                
                # Create research summary
                research_summary = response.content[:500] + "..." if len(response.content) > 500 else response.content
                
                # Store memory
                success = memory_instance.store_legal_research_memory(
                    user_id=user_id,
                    session_id=session_id or f"research_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    research_topic=research_topic,
                    research_summary=research_summary,
                    research_topics=research_topics,
                    legal_sources=legal_sources,
                    jurisdiction=jurisdiction
                )
                
                if success:
                    logger.info(f"Research memory stored successfully for user {user_id}")
                else:
                    logger.warning(f"Failed to store research memory for user {user_id}")
            else:
                logger.warning("Memory instance not available for storing research memory")
                
        except Exception as e:
            logger.error(f"Error storing research memory: {e}")
    
    return result 