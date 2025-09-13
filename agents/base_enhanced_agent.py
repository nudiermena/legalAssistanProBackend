"""
Base Enhanced Agent Class
Provides reasoning, knowledge, storage, and memory capabilities for all agents
"""

from abc import ABC, abstractmethod
from agno.agent import Agent
from config.enhanced_agent_config import (
    get_enhanced_agent_config,
    get_agent_memory,
    update_agent_memory
)
from config.ai_models import get_model
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import logging
import re

logger = logging.getLogger(__name__)

class BaseEnhancedAgent(ABC):
    """Base class for enhanced agents with reasoning, knowledge, storage, and memory"""
    
    def __init__(self, agent_name: str, user_id: str = None):
        self.agent_name = agent_name
        self.user_id = user_id
        self.agent = None
        self.memory = get_agent_memory(self.agent_name)
        self.initialize_agent()
    
    def initialize_agent(self):
        """Initialize the enhanced agent with all capabilities"""
        try:
            # Get enhanced configuration
            config = get_enhanced_agent_config(self.agent_name)
            
            # Create agent with enhanced capabilities
            self.agent = Agent(
                name=self.get_agent_name(),
                role=self.get_agent_role(),
                model=get_model(self.get_model_name()),
                tools=self.get_tools(),
                knowledge=config["knowledge"],
                search_knowledge=config["search_knowledge"],
                storage=config["storage"],
                reasoning=config["reasoning"],
                show_tool_calls=config["show_tool_calls"],
                debug_mode=config["debug_mode"],
                instructions=self.get_enhanced_instructions(),
                markdown=True
            )
            
            logger.info(f"Enhanced {self.agent_name} agent initialized for user: {self.user_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize enhanced {self.agent_name} agent: {e}")
            raise
    
    @abstractmethod
    def get_agent_name(self) -> str:
        """Get the display name for the agent"""
        pass
    
    @abstractmethod
    def get_agent_role(self) -> str:
        """Get the role description for the agent"""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Get the model name for the agent"""
        pass
    
    @abstractmethod
    def get_tools(self) -> List:
        """Get the tools for the agent"""
        pass
    
    @abstractmethod
    def get_base_instructions(self) -> List[str]:
        """Get the base instructions for the agent"""
        pass
    
    def get_enhanced_instructions(self) -> List[str]:
        """Get enhanced instructions with reasoning and memory capabilities"""
        base_instructions = self.get_base_instructions()
        
        enhanced_instructions = [
            # === REASONING CAPABILITIES ===
            "Antes de responder, analiza el contexto completo y la situación del usuario",
            "Evalúa múltiples perspectivas legales antes de llegar a conclusiones",
            "Considera el historial de interacciones previas con el usuario",
            "Aplica razonamiento deductivo para identificar riesgos y oportunidades",
            "Utiliza el conocimiento legal almacenado para fundamentar tus análisis",
            "Explica tu proceso de razonamiento paso a paso",
            
            # === MEMORY AND PERSONALIZATION ===
            "Considera las preferencias del usuario basándote en interacciones previas",
            "Adapta el nivel de detalle según la experiencia legal del usuario",
            "Mantén consistencia con análisis previos del mismo usuario",
            "Aprende de los patrones identificados en casos similares",
            "Personaliza las recomendaciones según el perfil del usuario",
            
            # === KNOWLEDGE INTEGRATION ===
            "Busca en la base de conocimiento legal para obtener información actualizada",
            "Cita fuentes específicas y referencias normativas",
            "Utiliza jurisprudencia relevante para fundamentar tus análisis",
            "Incorpora mejores prácticas del sector legal",
            
            # === STORAGE AND PERSISTENCE ===
            "Mantén un registro estructurado de todas las interacciones",
            "Guarda el contexto de la sesión para continuidad",
            "Preserva el estado de análisis en curso",
            "Almacena preferencias y configuraciones del usuario",
        ]
        
        return enhanced_instructions + base_instructions
    
    def _get_context_from_memory(self) -> str:
        """Get relevant context from agent memory"""
        context_parts = []
        
        # Add user preferences
        if self.memory.get("user_preferences"):
            prefs = self.memory["user_preferences"]
            context_parts.append(f"Preferencias del usuario: {json.dumps(prefs, ensure_ascii=False)}")
        
        # Add recent conversation history
        if self.memory.get("conversation_history"):
            recent_history = self.memory["conversation_history"][-3:]  # Last 3 interactions
            context_parts.append(f"Historial reciente: {json.dumps(recent_history, ensure_ascii=False)}")
        
        # Add case context
        if self.memory.get("case_context"):
            context_parts.append(f"Contexto del caso: {json.dumps(self.memory['case_context'], ensure_ascii=False)}")
        
        # Add legal terms cache
        if self.memory.get("legal_terms_cache"):
            terms = self.memory["legal_terms_cache"]
            context_parts.append(f"Términos legales utilizados: {json.dumps(terms, ensure_ascii=False)}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def _update_memory(self, interaction_data: Dict[str, Any]):
        """Update agent memory with new interaction data"""
        try:
            # Update conversation history
            if "conversation_history" not in self.memory:
                self.memory["conversation_history"] = []
            
            self.memory["conversation_history"].append({
                "timestamp": datetime.now().isoformat(),
                "user_id": self.user_id,
                "agent_name": self.agent_name,
                "interaction_type": interaction_data.get("type", "general_analysis"),
                "key_data": interaction_data.get("key_data", {}),
                "outcome": interaction_data.get("outcome", "success")
            })
            
            # Keep only last 10 interactions
            if len(self.memory["conversation_history"]) > 10:
                self.memory["conversation_history"] = self.memory["conversation_history"][-10:]
            
            # Update case context
            if "case_context" not in self.memory:
                self.memory["case_context"] = {}
            
            self.memory["case_context"].update({
                "last_interaction_type": interaction_data.get("type"),
                "total_interactions": self.memory["case_context"].get("total_interactions", 0) + 1,
                "last_update": datetime.now().isoformat()
            })
            
            # Update legal terms cache
            if "legal_terms" in interaction_data:
                if "legal_terms_cache" not in self.memory:
                    self.memory["legal_terms_cache"] = {}
                self.memory["legal_terms_cache"].update(interaction_data["legal_terms"])
            
            # Update memory in the system
            update_agent_memory(self.agent_name, self.memory)
            
            logger.info(f"Memory updated for {self.agent_name} agent, user {self.user_id}")
            
        except Exception as e:
            logger.error(f"Failed to update memory for {self.agent_name}: {e}")
    
    def _extract_structured_data(self, content: str) -> Dict[str, Any]:
        """Extract structured JSON data from agent response"""
        try:
            # Look for JSON block in the response
            json_match = re.search(r"```json\s*([\s\S]+?)```", content)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
            return {}
        except Exception as e:
            logger.warning(f"Failed to extract structured data from {self.agent_name}: {e}")
            return {}
    
    def _build_enhanced_prompt(self, base_prompt: str, additional_context: str = "") -> str:
        """Build enhanced prompt with memory context and reasoning instructions"""
        memory_context = self._get_context_from_memory()
        
        enhanced_prompt = f"""Analizar con capacidades avanzadas:

CONTEXTO DEL USUARIO:
{memory_context}

{base_prompt}

{additional_context}

REASONING: Explica tu proceso de análisis paso a paso, incluyendo:
1. Qué información busqué en la base de conocimiento
2. Cómo evalué las diferentes opciones
3. Qué factores consideré para llegar a mis conclusiones
4. Qué alternativas exploré
5. Mi nivel de confianza en las recomendaciones

MEMORY: Considera las interacciones previas con este usuario para personalizar la respuesta.
"""
        
        return enhanced_prompt
    
    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request with enhanced capabilities"""
        try:
            # Build enhanced prompt
            base_prompt = self._build_base_prompt(request_data)
            additional_context = self._get_additional_context(request_data)
            enhanced_prompt = self._build_enhanced_prompt(base_prompt, additional_context)
            
            # Run analysis with enhanced agent
            response = await self.agent.arun(enhanced_prompt)
            
            # Extract structured data
            structured_result = self._extract_structured_data(response.content)
            
            # Build result
            result = {
                "summary": response.content,
                "structured_analysis": structured_result,
                "agent_name": self.agent_name,
                "user_id": self.user_id,
                "timestamp": datetime.now().isoformat(),
                "enhanced_features": {
                    "reasoning_used": True,
                    "knowledge_searched": True,
                    "memory_accessed": bool(self._get_context_from_memory()),
                    "storage_persisted": True
                }
            }
            
            # Update memory with this interaction
            self._update_memory({
                "type": request_data.get("type", "general_analysis"),
                "key_data": request_data,
                "outcome": "success",
                "legal_terms": self._extract_legal_terms(response.content)
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error in {self.agent_name} processing: {e}")
            raise
    
    @abstractmethod
    def _build_base_prompt(self, request_data: Dict[str, Any]) -> str:
        """Build the base prompt for the specific agent"""
        pass
    
    def _get_additional_context(self, request_data: Dict[str, Any]) -> str:
        """Get additional context for the request (can be overridden)"""
        return ""
    
    def _extract_legal_terms(self, content: str) -> Dict[str, str]:
        """Extract legal terms from content for caching"""
        # This is a basic implementation - can be enhanced
        legal_terms = {}
        
        # Look for common legal terms
        term_patterns = [
            r'Ley\s+\d+\s+de\s+\d+',
            r'Código\s+[A-Za-z]+',
            r'Decreto\s+\d+\s+de\s+\d+',
            r'Sentencia\s+[A-Z]-\d+\s+de\s+\d+'
        ]
        
        for pattern in term_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                legal_terms[match] = "Referencia legal encontrada"
        
        return legal_terms
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get a summary of the agent's memory"""
        return {
            "agent_name": self.agent_name,
            "user_id": self.user_id,
            "total_interactions": len(self.memory.get("conversation_history", [])),
            "last_interaction": self.memory.get("last_interaction"),
            "case_context": self.memory.get("case_context", {}),
            "legal_terms_count": len(self.memory.get("legal_terms_cache", {})),
            "user_preferences": self.memory.get("user_preferences", {})
        }
    
    def clear_memory(self):
        """Clear the agent's memory"""
        self.memory = {
            "user_preferences": {},
            "conversation_history": [],
            "case_context": {},
            "legal_terms_cache": {},
            "last_interaction": None,
            "preferred_language": "es",
            "expertise_areas": [],
            "risk_tolerance": "medium"
        }
        update_agent_memory(self.agent_name, self.memory)
        logger.info(f"Memory cleared for {self.agent_name} agent") 