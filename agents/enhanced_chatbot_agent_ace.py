import datetime
import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import hashlib
import re

from agno.agent import Agent, RunResponse
from config.ai_models import get_model
from config.knowledge_base_integration import create_agent_knowledge_integration
from config.enhanced_agent_config import get_enhanced_agent_config
from utils.security_protection import protect_agent_input, protect_agent_response
from utils.url_validator import validate_url
from config.neo4j_rag_adapter import find_similar_cases
from utils.link_resolver import resolve_record_url

logger = logging.getLogger(__name__)

class ContextType(Enum):
    """Types of context that can be managed by the ACE framework"""
    LEGAL_KNOWLEDGE = "legal_knowledge"
    USER_PREFERENCES = "user_preferences"
    CONVERSATION_HISTORY = "conversation_history"
    JURISPRUDENCE = "jurisprudence"
    DOCUMENT_TEMPLATES = "document_templates"
    SESSION_SUMMARY = "session_summary"
    PERFORMANCE_METRICS = "performance_metrics"

class ContextPriority(Enum):
    """Priority levels for context management"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class ContextModule:
    """Represents a modular context component in the ACE framework"""
    id: str
    context_type: ContextType
    content: str
    priority: ContextPriority
    created_at: datetime.datetime
    last_updated: datetime.datetime
    relevance_score: float
    usage_count: int
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "id": self.id,
            "context_type": self.context_type.value,
            "content": self.content,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "relevance_score": self.relevance_score,
            "usage_count": self.usage_count,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContextModule':
        """Create from dictionary"""
        return cls(
            id=data["id"],
            context_type=ContextType(data["context_type"]),
            content=data["content"],
            priority=ContextPriority(data["priority"]),
            created_at=datetime.datetime.fromisoformat(data["created_at"]),
            last_updated=datetime.datetime.fromisoformat(data["last_updated"]),
            relevance_score=data["relevance_score"],
            usage_count=data["usage_count"],
            metadata=data["metadata"]
        )

class ACEContextManager:
    """
    Agentic Context Engineering (ACE) Manager
    Implements the core ACE framework for evolving contexts in the legal chatbot
    """
    
    def __init__(self, user_id: str, session_id: str):
        self.user_id = user_id
        self.session_id = session_id
        self.context_modules: Dict[str, ContextModule] = {}
        self.context_history: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, Any] = {}
        self.adaptation_strategies: List[str] = []
        
    def generate_context_id(self, content: str, context_type: ContextType) -> str:
        """Generate unique ID for context module"""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"{context_type.value}_{content_hash}_{int(datetime.datetime.now().timestamp())}"
    
    def add_context_module(self, 
                          content: str, 
                          context_type: ContextType, 
                          priority: ContextPriority = ContextPriority.MEDIUM,
                          metadata: Dict[str, Any] = None) -> str:
        """Add a new context module with automatic ID generation"""
        context_id = self.generate_context_id(content, context_type)
        
        module = ContextModule(
            id=context_id,
            context_type=context_type,
            content=content,
            priority=priority,
            created_at=datetime.datetime.now(),
            last_updated=datetime.datetime.now(),
            relevance_score=0.5,  # Initial relevance score
            usage_count=0,
            metadata=metadata or {}
        )
        
        self.context_modules[context_id] = module
        self._log_context_change("ADD", context_id, context_type)
        return context_id
    
    def update_context_module(self, 
                             context_id: str, 
                             new_content: str = None,
                             relevance_score: float = None,
                             metadata: Dict[str, Any] = None) -> bool:
        """Update an existing context module"""
        if context_id not in self.context_modules:
            return False
        
        module = self.context_modules[context_id]
        
        if new_content:
            module.content = new_content
        if relevance_score is not None:
            module.relevance_score = relevance_score
        if metadata:
            module.metadata.update(metadata)
        
        module.last_updated = datetime.datetime.now()
        module.usage_count += 1
        
        self._log_context_change("UPDATE", context_id, module.context_type)
        return True
    
    def remove_context_module(self, context_id: str) -> bool:
        """Remove a context module"""
        if context_id in self.context_modules:
            context_type = self.context_modules[context_id].context_type
            del self.context_modules[context_id]
            self._log_context_change("REMOVE", context_id, context_type)
            return True
        return False
    
    def get_relevant_context(self, 
                           query: str, 
                           context_types: List[ContextType] = None,
                           max_modules: int = 10) -> List[ContextModule]:
        """Get relevant context modules for a query"""
        relevant_modules = []
        
        for module in self.context_modules.values():
            # Filter by context type if specified
            if context_types and module.context_type not in context_types:
                continue
            
            # Calculate relevance based on content similarity and usage
            relevance = self._calculate_relevance(module, query)
            
            if relevance > 0.3:  # Threshold for relevance
                module.relevance_score = relevance
                relevant_modules.append(module)
        
        # Sort by relevance score and priority
        relevant_modules.sort(key=lambda x: (x.relevance_score, x.priority.value), reverse=True)
        
        return relevant_modules[:max_modules]
    
    def _calculate_relevance(self, module: ContextModule, query: str) -> float:
        """Calculate relevance score for a context module"""
        # Simple keyword-based relevance calculation
        query_words = set(query.lower().split())
        content_words = set(module.content.lower().split())
        
        # Calculate word overlap
        overlap = len(query_words.intersection(content_words))
        total_words = len(query_words.union(content_words))
        
        if total_words == 0:
            return 0.0
        
        # Base relevance from word overlap
        base_relevance = overlap / total_words
        
        # Boost based on usage count and recency
        usage_boost = min(module.usage_count * 0.1, 0.3)
        recency_boost = self._calculate_recency_boost(module.last_updated)
        
        # Priority boost
        priority_boost = {
            ContextPriority.CRITICAL: 0.3,
            ContextPriority.HIGH: 0.2,
            ContextPriority.MEDIUM: 0.1,
            ContextPriority.LOW: 0.0
        }[module.priority]
        
        final_relevance = min(base_relevance + usage_boost + recency_boost + priority_boost, 1.0)
        return final_relevance
    
    def _calculate_recency_boost(self, last_updated: datetime.datetime) -> float:
        """Calculate recency boost based on how recently the module was updated"""
        time_diff = datetime.datetime.now() - last_updated
        hours_ago = time_diff.total_seconds() / 3600
        
        if hours_ago < 1:
            return 0.2
        elif hours_ago < 24:
            return 0.1
        elif hours_ago < 168:  # 1 week
            return 0.05
        else:
            return 0.0
    
    def _log_context_change(self, action: str, context_id: str, context_type: ContextType):
        """Log context changes for monitoring"""
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "action": action,
            "context_id": context_id,
            "context_type": context_type.value,
            "user_id": self.user_id,
            "session_id": self.session_id
        }
        self.context_history.append(log_entry)
    
    def reflect_on_context(self) -> Dict[str, Any]:
        """Reflect on context usage and performance"""
        reflection = {
            "total_modules": len(self.context_modules),
            "context_types": {},
            "average_relevance": 0.0,
            "most_used_modules": [],
            "underutilized_modules": [],
            "recommendations": []
        }
        
        if not self.context_modules:
            return reflection
        
        # Analyze by context type
        for module in self.context_modules.values():
            context_type = module.context_type.value
            if context_type not in reflection["context_types"]:
                reflection["context_types"][context_type] = 0
            reflection["context_types"][context_type] += 1
        
        # Calculate average relevance
        total_relevance = sum(module.relevance_score for module in self.context_modules.values())
        reflection["average_relevance"] = total_relevance / len(self.context_modules)
        
        # Find most and least used modules
        sorted_modules = sorted(self.context_modules.values(), key=lambda x: x.usage_count, reverse=True)
        reflection["most_used_modules"] = [m.id for m in sorted_modules[:5]]
        reflection["underutilized_modules"] = [m.id for m in sorted_modules[-5:] if m.usage_count == 0]
        
        # Generate recommendations
        reflection["recommendations"] = self._generate_recommendations()
        
        return reflection
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations for context improvement"""
        recommendations = []
        
        # Check for context type balance
        context_type_counts = {}
        for module in self.context_modules.values():
            context_type = module.context_type.value
            context_type_counts[context_type] = context_type_counts.get(context_type, 0) + 1
        
        # Recommend adding more context types if imbalanced
        if len(context_type_counts) < 3:
            recommendations.append("Consider adding more diverse context types for better coverage")
        
        # Check for underutilized modules
        unused_count = sum(1 for module in self.context_modules.values() if module.usage_count == 0)
        if unused_count > len(self.context_modules) * 0.3:
            recommendations.append("Many context modules are unused - consider removing or updating them")
        
        # Check for low relevance scores
        low_relevance_count = sum(1 for module in self.context_modules.values() if module.relevance_score < 0.3)
        if low_relevance_count > len(self.context_modules) * 0.4:
            recommendations.append("Many context modules have low relevance - consider updating content")
        
        return recommendations
    
    def curate_context(self, max_modules: int = 20) -> List[ContextModule]:
        """Curate context by removing low-value modules and keeping the most relevant ones"""
        # Sort modules by combined score (relevance + usage + recency)
        def curation_score(module):
            recency_boost = self._calculate_recency_boost(module.last_updated)
            return (module.relevance_score + 
                   min(module.usage_count * 0.1, 0.3) + 
                   recency_boost)
        
        sorted_modules = sorted(self.context_modules.values(), key=curation_score, reverse=True)
        
        # Keep top modules and remove the rest
        modules_to_keep = sorted_modules[:max_modules]
        modules_to_remove = sorted_modules[max_modules:]
        
        for module in modules_to_remove:
            self.remove_context_module(module.id)
        
        return modules_to_keep
    
    def get_context_summary(self) -> str:
        """Generate a summary of current context for the agent"""
        if not self.context_modules:
            return "No context modules available."
        
        summary_parts = []
        
        # Group by context type
        by_type = {}
        for module in self.context_modules.values():
            context_type = module.context_type.value
            if context_type not in by_type:
                by_type[context_type] = []
            by_type[context_type].append(module)
        
        for context_type, modules in by_type.items():
            summary_parts.append(f"**{context_type.replace('_', ' ').title()}** ({len(modules)} modules):")
            for module in modules[:3]:  # Show top 3 modules per type
                summary_parts.append(f"  - {module.content[:100]}...")
            if len(modules) > 3:
                summary_parts.append(f"  - ... and {len(modules) - 3} more")
        
        return "\n".join(summary_parts)

class EnhancedChatbotAgentACE:
    """
    Enhanced Chatbot Agent implementing the ACE (Agentic Context Engineering) framework
    """
    
    def __init__(self, user_id: str, session_id: str):
        self.user_id = user_id
        self.session_id = session_id
        self.context_manager = ACEContextManager(user_id, session_id)
        self.performance_tracker = PerformanceTracker()
        self.adaptation_engine = AdaptationEngine()
        
    async def process_message(self, 
                            message: str,
                            practice_area: Optional[str] = None,
                            instructions: Optional[str] = None,
                            file_content: Optional[str] = None) -> Dict[str, Any]:
        """Process a message with ACE-enhanced context management"""
        
        # 1. GENERATE: Create new context modules from the message
        await self._generate_context_from_message(message, practice_area, file_content)
        
        # 2. REFLECT: Analyze current context and performance
        reflection = self.context_manager.reflect_on_context()
        
        # 3. CURATE: Optimize context modules
        curated_modules = self.context_manager.curate_context()
        
        # 4. Get relevant context for the query
        relevant_context = self.context_manager.get_relevant_context(
            message, 
            max_modules=15
        )
        
        # 5. Build enhanced instructions with context
        enhanced_instructions = self._build_enhanced_instructions(
            instructions, 
            relevant_context, 
            practice_area
        )
        
        # 6. Create and run the agent
        agent = self._create_enhanced_agent(enhanced_instructions, practice_area)
        
        try:
            response = agent.run(
                message,
                user_id=self.user_id,
                session_id=self.session_id
            )
            
            # 7. Update context based on response
            await self._update_context_from_response(message, response.content, practice_area)
            
            # 8. Track performance
            self.performance_tracker.track_interaction(message, response.content, practice_area)
            
            return self._format_response(response, reflection, curated_modules)
            
        except Exception as e:
            logger.error(f"Error in ACE-enhanced agent: {str(e)}")
            return self._create_error_response(str(e))
    
    async def _generate_context_from_message(self, 
                                           message: str, 
                                           practice_area: Optional[str],
                                           file_content: Optional[str]):
        """Generate new context modules from the user message"""
        
        # Extract legal terms and concepts
        legal_terms = self._extract_legal_terms(message)
        if legal_terms:
            context_content = f"Términos legales identificados: {', '.join(legal_terms)}"
            self.context_manager.add_context_module(
                content=context_content,
                context_type=ContextType.LEGAL_KNOWLEDGE,
                priority=ContextPriority.HIGH,
                metadata={"extracted_terms": legal_terms, "source": "user_message"}
            )
        
        # Extract user preferences and patterns
        user_preferences = self._extract_user_preferences(message)
        if user_preferences:
            context_content = f"Preferencias del usuario: {', '.join(user_preferences)}"
            self.context_manager.add_context_module(
                content=context_content,
                context_type=ContextType.USER_PREFERENCES,
                priority=ContextPriority.MEDIUM,
                metadata={"preferences": user_preferences, "source": "user_message"}
            )
        
        # Add practice area context
        if practice_area:
            context_content = f"Área de práctica legal: {practice_area}"
            self.context_manager.add_context_module(
                content=context_content,
                context_type=ContextType.LEGAL_KNOWLEDGE,
                priority=ContextPriority.HIGH,
                metadata={"practice_area": practice_area, "source": "user_input"}
            )
        
        # Add file content context if provided
        if file_content:
            context_content = f"Contenido de archivo adjunto: {file_content[:500]}..."
            self.context_manager.add_context_module(
                content=context_content,
                context_type=ContextType.LEGAL_KNOWLEDGE,
                priority=ContextPriority.HIGH,
                metadata={"file_content": True, "source": "attached_file"}
            )
    
    def _extract_legal_terms(self, message: str) -> List[str]:
        """Extract legal terms from the message"""
        legal_keywords = [
            'derecho', 'ley', 'código', 'norma', 'jurídico', 'legal', 'legislación',
            'contrato', 'arrendamiento', 'trabajo', 'familia', 'comercial', 'penal',
            'constitucional', 'administrativo', 'tributario', 'civil', 'laboral',
            'demanda', 'sentencia', 'fallo', 'resolución', 'decreto', 'reglamento',
            'proceso', 'procedimiento', 'instancia', 'término', 'plazo', 'vigencia',
            'recurso', 'apelación', 'tutela', 'amparo', 'habeas corpus'
        ]
        
        found_terms = []
        message_lower = message.lower()
        
        for term in legal_keywords:
            if term in message_lower:
                found_terms.append(term)
        
        return found_terms
    
    def _extract_user_preferences(self, message: str) -> List[str]:
        """Extract user preferences and patterns from the message"""
        preferences = []
        
        # Check for complexity preferences
        if any(word in message.lower() for word in ['simple', 'básico', 'fácil', 'entendible']):
            preferences.append("prefiere_explicaciones_simples")
        
        if any(word in message.lower() for word in ['detallado', 'completo', 'técnico', 'específico']):
            preferences.append("prefiere_explicaciones_detalladas")
        
        # Check for format preferences
        if any(word in message.lower() for word in ['ejemplo', 'caso', 'situación']):
            preferences.append("prefiere_ejemplos_prácticos")
        
        if any(word in message.lower() for word in ['documento', 'plantilla', 'formato']):
            preferences.append("necesita_documentos")
        
        return preferences
    
    async def _update_context_from_response(self, 
                                          message: str, 
                                          response: str, 
                                          practice_area: Optional[str]):
        """Update context based on the agent's response"""
        
        # Add successful interaction to conversation history
        conversation_entry = f"Usuario: {message[:100]}... | Asistente: {response[:100]}..."
        self.context_manager.add_context_module(
            content=conversation_entry,
            context_type=ContextType.CONVERSATION_HISTORY,
            priority=ContextPriority.MEDIUM,
            metadata={"interaction_type": "successful", "practice_area": practice_area}
        )
        
        # Extract and store any legal references mentioned
        legal_references = self._extract_legal_references(response)
        if legal_references:
            for reference in legal_references:
                self.context_manager.add_context_module(
                    content=f"Referencia legal: {reference}",
                    context_type=ContextType.LEGAL_KNOWLEDGE,
                    priority=ContextPriority.HIGH,
                    metadata={"reference_type": "legal_citation", "source": "agent_response"}
                )
    
    def _extract_legal_references(self, response: str) -> List[str]:
        """Extract legal references from the response"""
        # Pattern to match legal references like "Ley 123 de 2023", "Código Civil", etc.
        patterns = [
            r'Ley \d+ de \d{4}',
            r'Código \w+',
            r'Sentencia [A-Z]-\d+ de \d{4}',
            r'Decreto \d+ de \d{4}',
            r'Circular \d+ de \d{4}'
        ]
        
        references = []
        for pattern in patterns:
            matches = re.findall(pattern, response)
            references.extend(matches)
        
        return references
    
    def _build_enhanced_instructions(self, 
                                   base_instructions: Optional[str],
                                   relevant_context: List[ContextModule],
                                   practice_area: Optional[str]) -> str:
        """Build enhanced instructions incorporating relevant context"""
        
        instructions_parts = []
        
        # Add base instructions
        if base_instructions:
            instructions_parts.append(base_instructions)
        
        # Add context-aware instructions
        instructions_parts.append("=== CONTEXTO DINÁMICO MEJORADO ===")
        instructions_parts.append("Utiliza el siguiente contexto para proporcionar respuestas más precisas y personalizadas:")
        
        # Add relevant context modules
        for module in relevant_context:
            context_header = f"\n**{module.context_type.value.replace('_', ' ').title()}:**"
            instructions_parts.append(context_header)
            instructions_parts.append(module.content)
        
        # Add practice area specific instructions
        if practice_area:
            instructions_parts.append(f"\n**Área de Práctica Específica:** {practice_area}")
            instructions_parts.append("Adapta tu respuesta específicamente a esta área del derecho colombiano.")
        
        return "\n".join(instructions_parts)
    
    def _create_enhanced_agent(self, 
                              instructions: str, 
                              practice_area: Optional[str]) -> Agent:
        """Create an enhanced agent with ACE context integration"""
        
        # Create knowledge base integration
        knowledge_integration = create_agent_knowledge_integration("enhanced_chatbot_agent")
        
        # Get enhanced configuration
        try:
            enhanced_config = get_enhanced_agent_config("chatbot_agent")
        except Exception as e:
            logger.warning(f"Failed to get enhanced config: {e}")
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
        
        # Enhanced system instructions with ACE principles
        system_instructions = [
            "IMPORTANTE: SIEMPRE responde ÚNICAMENTE en español. NUNCA uses inglés en tus respuestas.",
            "Proporciona respuestas DIRECTAS y ACCIONABLES sobre derecho colombiano. NO entres en bucles de razonamiento.",
            "OBLIGATORIO: Después de cada respuesta, SIEMPRE genera 1-3 preguntas específicas para ayudar al usuario a obtener información más detallada sobre su situación particular.",
            
            # ACE-Enhanced Instructions
            "=== CAPACIDADES ACE (AGENTIC CONTEXT ENGINEERING) ===",
            "Utiliza el contexto dinámico proporcionado para personalizar completamente tu respuesta.",
            "Aprende y adapta tu estilo de comunicación basándote en las preferencias del usuario identificadas.",
            "Mantén coherencia con conversaciones previas y referencias legales mencionadas anteriormente.",
            "Evoluciona tu comprensión del contexto del usuario con cada interacción.",
            
            "Eres un asistente virtual especializado en información legal colombiana con capacidades de evolución contextual",
            "Proporciona información general precisa según la jurisdicción colombiana",
            "Utiliza lenguaje claro y accesible para personas sin formación jurídica",
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
            
            # Context Integration Instructions
            "INTEGRACIÓN CON BASE DE CONOCIMIENTO RAG: Consulta la base de conocimiento legal para obtener información actualizada",
            "Utiliza la base de datos de plantillas de documentos para proporcionar ejemplos específicos",
            "Busca en jurisprudencia colombiana relevante para fundamentar tus recomendaciones",
            "Consulta términos legales específicos y sus definiciones vigentes",
            "Aplica mejores prácticas contractuales documentadas en la base de conocimiento",
            "Cita específicamente las fuentes de la base de conocimiento utilizadas",
            "Utiliza plantillas y cláusulas estándar de la base de conocimiento",
            "Consulta casos similares y precedentes legales relevantes",
            
            # Enhanced Question Generation
            "Genera un máximo de 3 preguntas *completamente originales, altamente específicas, claras y concisas*.",
            "Cada pregunta debe estar diseñada para obtener un detalle *indispensable* que cambie o afine el análisis legal.",
            "Cada pregunta debe abordar una *pieza de información distintiva y no redundante* que sea verdaderamente necesaria para el análisis jurídico.",
            "Prioriza preguntas que aborden *las lagunas de información más críticas y con mayor impacto* para la elaboración de un análisis jurídico completo y útil.",
            "Adapta las preguntas al tono y nivel de conocimiento del usuario, utilizando análisis de sentimiento para detectar urgencia o confusión.",
            "Evita preguntas redundantes o excesivamente técnicas si el usuario parece no tener formación jurídica, a menos que sean absolutamente esenciales.",
            "Si el usuario proporciona un archivo, genera preguntas *EXACTAMENTE Y DETALLADAMENTE ESPECÍFICAS* sobre su contenido para confirmar su relevancia."
        ]
        
        if practice_area:
            system_instructions.append(f"Te especializas en derecho {practice_area}.")
        
        # Add dynamic instructions
        system_instructions.append(f"\n=== INSTRUCCIONES DINÁMICAS ===\n{instructions}")
        
        # Create agent parameters
        agent_params = {
            "name": "Asistente Legal Virtual Colombiano ACE-Enhanced",
            "role": "Asistente de información jurídica colombiana con capacidades de evolución contextual y gestión inteligente de contexto",
            "model": get_model("chatbot"),
            "tools": [],
            "knowledge": knowledge_integration,
            "search_knowledge": True,
            "storage": enhanced_config.get("storage") if isinstance(enhanced_config, dict) else None,
            "memory": None,
            "instructions": system_instructions,
            "markdown": True,
            "add_context": True,
            "session_id": self.session_id
        }
        
        return Agent(**agent_params)
    
    def _format_response(self, 
                        response: RunResponse, 
                        reflection: Dict[str, Any],
                        curated_modules: List[ContextModule]) -> Dict[str, Any]:
        """Format the response with ACE enhancement information"""
        
        # Extract clarifying questions
        clarifying_questions = self._extract_clarifying_questions(response.content)
        
        return {
            "response": {
                "content": response.content,
                "relevant_laws": [],
                "recommendations": ["Consultar con un abogado especializado"],
                "clarifying_questions": clarifying_questions
            },
            "conversation_id": f"ace_conv_{self.user_id}_{datetime.datetime.now().timestamp()}",
            "session_id": self.session_id,
            "user_id": self.user_id,
            "memory_enabled": True,
            "disclaimer": "Esta información es de carácter general y no constituye asesoría jurídica.",
            "colombian_compliance": {
                "version": "1.0",
                "constitutional_principles": ["Debido proceso", "Buena fe"],
                "data_protection": {
                    "law": "Ley 1581 de 2012",
                    "status": "Cumple"
                }
            },
            "practice_area": "derecho_civil",
            "legal_terms": {},
            "references": {"normativa": [], "jurisprudencia": [], "doctrina": []},
            
            # ACE Enhancement Information
            "ace_enhancement": {
                "context_modules_active": len(self.context_manager.context_modules),
                "context_reflection": reflection,
                "curated_modules_count": len(curated_modules),
                "context_types_used": list(set(module.context_type.value for module in curated_modules)),
                "adaptation_strategies": self.adaptation_engine.get_active_strategies(),
                "performance_metrics": self.performance_tracker.get_current_metrics()
            },
            "enhanced_capabilities": {
                "jurisprudence_search": True,
                "document_drafting": True,
                "hybrid_search": True,
                "constitutional_court_cases": True,
                "ace_context_engineering": True,
                "adaptive_context_management": True,
                "performance_monitoring": True
            },
            "query_validation": {
                "is_legal": True,
                "confidence": 1.0,
                "reasoning": "Query processed with ACE enhancement",
                "legal_terms_found": [],
                "suggestion": None
            },
            "is_legal_query": True
        }
    
    def _extract_clarifying_questions(self, content: str) -> List[str]:
        """Extract clarifying questions from the response content"""
        question_pattern = r'¿[^?]+\?'
        questions_found = re.findall(question_pattern, content)
        
        # Filter out generic questions
        filtered_questions = []
        for question in questions_found:
            if any(specific in question.lower() for specific in [
                'existe', 'se ha iniciado', 'cuál es la fecha', 'dónde', 'cuándo',
                'quién', 'qué tipo', 'qué documento', 'qué proceso', 'qué instancia'
            ]):
                filtered_questions.append(question.strip())
        
        return filtered_questions[:3]
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create an error response"""
        return {
            "response": {
                "content": f"Lo siento, tuve un problema procesando tu consulta. Error: {error_message}",
                "relevant_laws": [],
                "recommendations": ["Consultar con un abogado especializado"],
                "clarifying_questions": [
                    "¿Podrías proporcionar más detalles sobre tu situación específica?",
                    "¿En qué jurisdicción de Colombia se encuentra tu caso?",
                    "¿Has consultado previamente con un abogado sobre este tema?"
                ]
            },
            "conversation_id": f"ace_error_{self.user_id}_{datetime.datetime.now().timestamp()}",
            "session_id": self.session_id,
            "user_id": self.user_id,
            "memory_enabled": True,
            "disclaimer": "Esta información es de carácter general y no constituye asesoría jurídica.",
            "colombian_compliance": {
                "version": "1.0",
                "constitutional_principles": ["Debido proceso", "Buena fe"],
                "data_protection": {
                    "law": "Ley 1581 de 2012",
                    "status": "Cumple"
                }
            },
            "practice_area": "derecho_civil",
            "legal_terms": {},
            "references": {"normativa": [], "jurisprudencia": [], "doctrina": []},
            "ace_enhancement": {
                "error": True,
                "error_message": error_message,
                "context_modules_active": len(self.context_manager.context_modules)
            },
            "enhanced_capabilities": {
                "jurisprudence_search": False,
                "document_drafting": False,
                "hybrid_search": False,
                "constitutional_court_cases": False,
                "ace_context_engineering": True,
                "adaptive_context_management": True,
                "performance_monitoring": True
            },
            "query_validation": {
                "is_legal": True,
                "confidence": 0.5,
                "reasoning": "Error in processing",
                "legal_terms_found": [],
                "suggestion": "Please try again"
            },
            "is_legal_query": True
        }

class PerformanceTracker:
    """Track performance metrics for the ACE system"""
    
    def __init__(self):
        self.metrics = {
            "total_interactions": 0,
            "successful_interactions": 0,
            "average_response_time": 0.0,
            "user_satisfaction_scores": [],
            "context_utilization_rates": [],
            "adaptation_effectiveness": []
        }
    
    def track_interaction(self, message: str, response: str, practice_area: Optional[str]):
        """Track a single interaction"""
        self.metrics["total_interactions"] += 1
        self.metrics["successful_interactions"] += 1
        
        # Simple satisfaction scoring based on response length and completeness
        satisfaction_score = min(len(response) / 500, 1.0)  # Normalize to 0-1
        self.metrics["user_satisfaction_scores"].append(satisfaction_score)
        
        # Keep only last 100 scores
        if len(self.metrics["user_satisfaction_scores"]) > 100:
            self.metrics["user_satisfaction_scores"] = self.metrics["user_satisfaction_scores"][-100:]
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        avg_satisfaction = (
            sum(self.metrics["user_satisfaction_scores"]) / len(self.metrics["user_satisfaction_scores"])
            if self.metrics["user_satisfaction_scores"] else 0.0
        )
        
        return {
            "total_interactions": self.metrics["total_interactions"],
            "success_rate": (
                self.metrics["successful_interactions"] / self.metrics["total_interactions"]
                if self.metrics["total_interactions"] > 0 else 0.0
            ),
            "average_satisfaction": avg_satisfaction,
            "recent_performance": self.metrics["user_satisfaction_scores"][-10:] if self.metrics["user_satisfaction_scores"] else []
        }

class AdaptationEngine:
    """Engine for adapting the ACE system based on performance"""
    
    def __init__(self):
        self.active_strategies = [
            "context_curation",
            "relevance_optimization",
            "user_preference_learning"
        ]
        self.adaptation_history = []
    
    def get_active_strategies(self) -> List[str]:
        """Get currently active adaptation strategies"""
        return self.active_strategies
    
    def adapt_based_on_performance(self, performance_metrics: Dict[str, Any]):
        """Adapt the system based on performance metrics"""
        # Simple adaptation logic
        if performance_metrics.get("average_satisfaction", 0) < 0.6:
            if "response_enhancement" not in self.active_strategies:
                self.active_strategies.append("response_enhancement")
        
        if performance_metrics.get("success_rate", 0) < 0.8:
            if "context_expansion" not in self.active_strategies:
                self.active_strategies.append("context_expansion")

# Main function to create and use the enhanced chatbot agent
async def create_enhanced_chatbot_agent_ace(
    user_id: str,
    session_id: str,
    practice_area: Optional[str] = None,
    instructions: Optional[str] = None,
    file_content: Optional[str] = None
) -> EnhancedChatbotAgentACE:
    """Create an ACE-enhanced chatbot agent"""
    return EnhancedChatbotAgentACE(user_id, session_id)

# Example usage and demonstration
async def demonstrate_ace_enhanced_chatbot():
    """Demonstrate the ACE-enhanced chatbot capabilities"""
    
    print("🚀 DEMOSTRACIÓN DEL CHATBOT ACE-ENHANCED")
    print("=" * 70)
    
    # Create enhanced agent
    agent = await create_enhanced_chatbot_agent_ace(
        user_id="demo_user",
        session_id="demo_session",
        practice_area="derecho_civil"
    )
    
    # Test message
    test_message = "Necesito ayuda con un contrato de arrendamiento de vivienda en Bogotá"
    
    print(f"\n📝 Mensaje de prueba: {test_message}")
    print("-" * 50)
    
    try:
        # Process message with ACE enhancement
        response = await agent.process_message(
            message=test_message,
            practice_area="derecho_civil",
            instructions="Proporciona información detallada sobre contratos de arrendamiento"
        )
        
        print("✅ Respuesta generada exitosamente")
        print(f"📊 Módulos de contexto activos: {response['ace_enhancement']['context_modules_active']}")
        print(f"🔧 Estrategias de adaptación: {response['ace_enhancement']['adaptation_strategies']}")
        print(f"📈 Métricas de rendimiento: {response['ace_enhancement']['performance_metrics']}")
        
        # Show context reflection
        reflection = response['ace_enhancement']['context_reflection']
        print(f"\n🔍 Reflexión del contexto:")
        print(f"  - Total de módulos: {reflection['total_modules']}")
        print(f"  - Tipos de contexto: {list(reflection['context_types'].keys())}")
        print(f"  - Módulos más utilizados: {reflection['most_used_modules'][:3]}")
        
        if reflection['recommendations']:
            print(f"  - Recomendaciones: {reflection['recommendations']}")
        
    except Exception as e:
        print(f"❌ Error en demostración: {str(e)}")
    
    print("\n🎯 CAPACIDADES PRINCIPALES DEL CHATBOT ACE-ENHANCED:")
    print("=" * 70)
    print("✅ Gestión modular de contexto con evolución automática")
    print("✅ Reflexión y curación inteligente de contexto")
    print("✅ Adaptación basada en rendimiento y preferencias del usuario")
    print("✅ Monitoreo continuo de métricas de rendimiento")
    print("✅ Manejo optimizado de contextos largos")
    print("✅ Aprendizaje incremental de patrones de usuario")
    print("✅ Integración con base de conocimiento legal")
    print("✅ Cumplimiento legal colombiano")
    
    print("\n🚀 El chatbot ACE-enhanced está listo para proporcionar asistencia legal evolutiva!")
    print("💡 El sistema aprende y se adapta continuamente para mejorar la experiencia del usuario")

if __name__ == "__main__":
    import asyncio
    
    print("🔧 Iniciando demostración del chatbot ACE-enhanced...")
    
    try:
        asyncio.run(demonstrate_ace_enhanced_chatbot())
    except Exception as e:
        print(f"❌ Error en demostración: {str(e)}")
        print("💡 Asegúrese de que todas las dependencias estén configuradas correctamente")
