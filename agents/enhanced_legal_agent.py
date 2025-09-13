#!/usr/bin/env python3
"""
Enhanced Legal Agent Template
Demonstrates best practices for using vector database, storage, memory, and knowledge systems
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from agno import Agent
from config.enhanced_agent_config import get_enhanced_agent_config
from config.ai_models import get_model

logger = logging.getLogger(__name__)

class EnhancedLegalAgent:
    """Enhanced Legal Agent with full vector database, storage, memory, and knowledge capabilities"""
    
    def __init__(self, agent_type: str, user_id: str = None):
        """
        Initialize enhanced legal agent
        
        Args:
            agent_type: Type of agent (e.g., 'legal_research_agent', 'contract_agent')
            user_id: User identifier for personalization
        """
        self.agent_type = agent_type
        self.user_id = user_id
        self.session_id = f"{agent_type}_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Get enhanced configuration
        self.config = get_enhanced_agent_config(agent_type)
        
        # Initialize AI model
        self.model = get_model(agent_type)
        
        # Initialize systems
        self.knowledge_base = self.config.get("knowledge")
        self.storage = self.config.get("storage")
        self.memory = self.config.get("memory")
        
        logger.info(f"Enhanced Legal Agent initialized: {agent_type}")
        logger.info(f"Knowledge base: {'✅ Available' if self.knowledge_base else '❌ Not available'}")
        logger.info(f"Storage: {'✅ Available' if self.storage else '❌ Not available'}")
        logger.info(f"Memory: {'✅ Available' if self.memory else '❌ Not available'}")
    
    async def process_legal_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process legal query with full system integration
        
        Args:
            query: Legal query from user
            context: Additional context (case details, user preferences, etc.)
            
        Returns:
            Enhanced response with knowledge base insights
        """
        try:
            # Step 1: Search knowledge base for relevant information
            knowledge_results = await self._search_knowledge_base(query)
            
            # Step 2: Retrieve user memory and preferences
            user_memory = await self._get_user_memory()
            
            # Step 3: Build enhanced prompt with context
            enhanced_prompt = self._build_enhanced_prompt(query, knowledge_results, user_memory, context)
            
            # Step 4: Generate response using AI model
            response = await self._generate_response(enhanced_prompt)
            
            # Step 5: Store interaction in memory and storage
            await self._store_interaction(query, response, knowledge_results)
            
            return {
                "response": response,
                "knowledge_sources": knowledge_results.get("sources", []),
                "confidence_score": knowledge_results.get("confidence", 0.0),
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing legal query: {e}")
            return {
                "error": str(e),
                "response": "Lo siento, hubo un error procesando su consulta legal.",
                "session_id": self.session_id
            }
    
    async def _search_knowledge_base(self, query: str) -> Dict[str, Any]:
        """Search knowledge base for relevant legal information"""
        if not self.knowledge_base:
            return {"sources": [], "confidence": 0.0}
        
        try:
            # Search for relevant legal documents, jurisprudence, and regulations
            results = await self.knowledge_base.asearch(query, limit=5)
            
            # Extract and format relevant information
            sources = []
            for result in results:
                sources.append({
                    "content": result.content[:200] + "..." if len(result.content) > 200 else result.content,
                    "source": result.source,
                    "score": result.score,
                    "type": "legal_document"
                })
            
            # Calculate confidence based on search results
            confidence = max([r.score for r in results]) if results else 0.0
            
            return {
                "sources": sources,
                "confidence": confidence,
                "total_results": len(results)
            }
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return {"sources": [], "confidence": 0.0}
    
    async def _get_user_memory(self) -> Dict[str, Any]:
        """Retrieve user memory and preferences"""
        if not self.memory or not self.user_id:
            return {}
        
        try:
            # Get user memories (preferences, past cases, expertise level)
            user_memories = await self.memory.get_user_memories(self.user_id)
            
            # Get recent session history
            session_history = await self.memory.get_session_history(self.user_id, limit=5)
            
            return {
                "preferences": user_memories.get("preferences", {}),
                "expertise_level": user_memories.get("expertise_level", "general"),
                "practice_areas": user_memories.get("practice_areas", []),
                "recent_cases": session_history
            }
            
        except Exception as e:
            logger.error(f"Error retrieving user memory: {e}")
            return {}
    
    def _build_enhanced_prompt(self, query: str, knowledge_results: Dict, user_memory: Dict, context: Dict) -> str:
        """Build enhanced prompt with all available context"""
        
        prompt_parts = []
        
        # Base query
        prompt_parts.append(f"Consulta legal: {query}")
        
        # Add knowledge base insights
        if knowledge_results.get("sources"):
            prompt_parts.append("\nInformación relevante de la base de conocimiento:")
            for i, source in enumerate(knowledge_results["sources"][:3], 1):
                prompt_parts.append(f"{i}. {source['content']}")
                prompt_parts.append(f"   Fuente: {source['source']}")
        
        # Add user context
        if user_memory:
            prompt_parts.append(f"\nContexto del usuario:")
            if user_memory.get("expertise_level"):
                prompt_parts.append(f"- Nivel de experiencia: {user_memory['expertise_level']}")
            if user_memory.get("practice_areas"):
                prompt_parts.append(f"- Áreas de práctica: {', '.join(user_memory['practice_areas'])}")
        
        # Add additional context
        if context:
            prompt_parts.append(f"\nContexto adicional:")
            for key, value in context.items():
                prompt_parts.append(f"- {key}: {value}")
        
        # Add agent-specific instructions
        agent_instructions = self._get_agent_instructions()
        prompt_parts.append(f"\nInstrucciones específicas del agente: {agent_instructions}")
        
        return "\n".join(prompt_parts)
    
    def _get_agent_instructions(self) -> str:
        """Get agent-specific instructions based on agent type"""
        instructions = {
            "legal_research_agent": "Proporciona investigación legal detallada con referencias a jurisprudencia y normativa colombiana.",
            "contract_agent": "Analiza contratos y proporciona recomendaciones sobre cláusulas, riesgos y cumplimiento legal.",
            "compliance_agent": "Evalúa el cumplimiento normativo y proporciona recomendaciones de compliance.",
            "case_prediction_agent": "Analiza casos y proporciona predicciones sobre probabilidad de éxito basadas en jurisprudencia.",
            "document_drafting_agent": "Ayuda a redactar documentos legales con plantillas y mejores prácticas."
        }
        return instructions.get(self.agent_type, "Proporciona asistencia legal general.")
    
    async def _generate_response(self, prompt: str) -> str:
        """Generate response using AI model"""
        try:
            # Use the AI model to generate response
            response = await self.model.agenerate(prompt)
            return response
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "Lo siento, hubo un error generando la respuesta."
    
    async def _store_interaction(self, query: str, response: str, knowledge_results: Dict):
        """Store interaction in memory and storage systems"""
        try:
            # Store in memory system
            if self.memory and self.user_id:
                await self.memory.add_user_memory(
                    user_id=self.user_id,
                    memory_type="interaction",
                    content={
                        "query": query,
                        "response": response[:500],  # Limit response length
                        "knowledge_sources": knowledge_results.get("sources", []),
                        "timestamp": datetime.now().isoformat()
                    }
                )
            
            # Store in storage system
            if self.storage:
                await self.storage.add(
                    session_id=self.session_id,
                    user_id=self.user_id,
                    agent_type=self.agent_type,
                    query=query,
                    response=response,
                    metadata={
                        "knowledge_sources": knowledge_results.get("sources", []),
                        "confidence": knowledge_results.get("confidence", 0.0)
                    }
                )
                
        except Exception as e:
            logger.error(f"Error storing interaction: {e}")
    
    async def get_legal_terms(self, terms: List[str]) -> Dict[str, str]:
        """Get definitions for legal terms"""
        if not self.knowledge_base:
            return {term: "Definición no disponible" for term in terms}
        
        try:
            definitions = {}
            for term in terms:
                results = await self.knowledge_base.asearch(f"definición {term}", limit=1)
                if results:
                    definitions[term] = results[0].content[:200] + "..."
                else:
                    definitions[term] = f"Definición no encontrada para '{term}'"
            
            return definitions
            
        except Exception as e:
            logger.error(f"Error getting legal terms: {e}")
            return {term: "Error al buscar definición" for term in terms}
    
    async def get_jurisprudence(self, topic: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get relevant jurisprudence for a topic"""
        if not self.knowledge_base:
            return []
        
        try:
            results = await self.knowledge_base.asearch(f"jurisprudencia {topic}", limit=limit)
            
            jurisprudence = []
            for result in results:
                jurisprudence.append({
                    "content": result.content,
                    "source": result.source,
                    "score": result.score,
                    "topic": topic
                })
            
            return jurisprudence
            
        except Exception as e:
            logger.error(f"Error getting jurisprudence: {e}")
            return []
    
    async def get_contract_analysis(self, contract_text: str) -> Dict[str, Any]:
        """Analyze contract and provide recommendations"""
        if not self.knowledge_base:
            return {"analysis": "Análisis no disponible", "recommendations": []}
        
        try:
            # Search for contract-related knowledge
            results = await self.knowledge_base.asearch("cláusulas contractuales obligaciones", limit=3)
            
            # Build analysis prompt
            analysis_prompt = f"""
            Analiza el siguiente contrato y proporciona recomendaciones:
            
            Contrato:
            {contract_text[:1000]}...
            
            Información relevante:
            {chr(10).join([r.content for r in results])}
            
            Proporciona:
            1. Análisis de riesgos
            2. Cláusulas problemáticas
            3. Recomendaciones de mejora
            4. Cumplimiento normativo
            """
            
            analysis = await self._generate_response(analysis_prompt)
            
            return {
                "analysis": analysis,
                "knowledge_sources": [r.source for r in results],
                "confidence": max([r.score for r in results]) if results else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error analyzing contract: {e}")
            return {"analysis": "Error en el análisis", "recommendations": []}

# Usage example
async def main():
    """Example usage of enhanced legal agent"""
    
    # Initialize agent
    agent = EnhancedLegalAgent("legal_research_agent", user_id="user123")
    
    # Process legal query
    result = await agent.process_legal_query(
        query="¿Cuáles son los requisitos para un recurso de casación en Colombia?",
        context={
            "case_type": "civil",
            "urgency": "high"
        }
    )
    
    print("Response:", result["response"])
    print("Knowledge sources:", len(result["knowledge_sources"]))
    print("Confidence:", result["confidence_score"])

if __name__ == "__main__":
    asyncio.run(main()) 