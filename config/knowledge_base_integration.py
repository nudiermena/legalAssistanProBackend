"""
Knowledge Base Integration for Legal AI Agents
Provides easy access to Supabase knowledge base for all agents
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import os

# Force Mistral embedder usage
# Temporarily disabled due to syntax errors
# from config.force_mistral_embedder import force_mistral_embedder, get_mistral_embedder

from config.supabase_knowledge_base import (
    SupabaseLegalKnowledgeBase,
    KnowledgeType,
    AgentType,
    KnowledgeSearchResult
)

logger = logging.getLogger(__name__)

# Force Mistral embedder on module import - temporarily disabled
# force_mistral_embedder()

class AgentKnowledgeIntegration:
    """Integration layer for agents to access knowledge base"""
    
    def __init__(self, agent_type: str):
        """
        Initialize knowledge integration for specific agent
        
        Args:
            agent_type: Type of agent (e.g., 'contract_agent', 'legal_research_agent')
        """
        self.agent_type = agent_type
        
        # Check if we have the required environment variables
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        mistral_key = os.getenv("MISTRAL_API_KEY")
        
        # Use mock mode if environment variables are not available
        mock_mode = not (supabase_url and supabase_key and mistral_key)
        
        if mock_mode:
            logger.warning(f"Using MOCK mode for knowledge base integration (agent: {agent_type})")
            logger.warning("Set SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, and MISTRAL_API_KEY for full functionality")
        
        self.kb = SupabaseLegalKnowledgeBase(mock_mode=mock_mode)
        self.agent_enum = self._get_agent_enum(agent_type)
        
        # Force Mistral embedder usage - temporarily disabled
        # self.embedder = get_mistral_embedder()
        self.embedder = None
        if self.embedder:
            logger.info(f"Using forced Mistral embedder for agent: {agent_type}")
        else:
            logger.warning(f"Could not get Mistral embedder for agent: {agent_type}")
        
        # Add required attributes for Agno compatibility
        self.vector_db = None  # Agno expects this attribute
        
        # Initialize vector_db if available
        if not mock_mode:
            try:
                from config.enhanced_agent_config import EnhancedAgentConfig
                config = EnhancedAgentConfig()
                config.initialize_vector_db()
                self.vector_db = config.vector_db
                
                # Use the embedder we already got from force_mistral_embedder
                if self.embedder:
                    logger.info(f"Using forced Mistral embedder for vector_db compatibility")
                else:
                    logger.warning(f"No embedder available for vector_db compatibility")
            except Exception as e:
                logger.warning(f"Could not initialize vector_db for Agno compatibility: {e}")
    
    def _get_agent_enum(self, agent_type: str) -> AgentType:
        """Convert agent type string to enum"""
        agent_mapping = {
            "contract_agent": AgentType.CONTRACT,
            "legal_research_agent": AgentType.LEGAL_RESEARCH,
            "patent_agent": AgentType.PATENT,
            "case_prediction_agent": AgentType.CASE_PREDICTION,
            "document_drafting_agent": AgentType.DOCUMENT_DRAFTING,
            "compliance_agent": AgentType.COMPLIANCE,
            "chatbot_agent": AgentType.CHATBOT,
            "demand_letter_agent": AgentType.DEMAND_LETTER,
            "whistleblower_agent": AgentType.WHISTLEBLOWER,
            "legal_diagnosis_agent": AgentType.LEGAL_DIAGNOSIS,
            "regulatory_agent": AgentType.REGULATORY
        }
        return agent_mapping.get(agent_type, AgentType.CHATBOT)
    
    async def search_knowledge(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Search knowledge base for relevant information
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            Dictionary with search results
        """
        try:
            return await self.kb.search_knowledge(query, limit=limit)
        except Exception as e:
            logger.error(f"Error searching knowledge: {e}")
            return {
                "results": [],
                "query": query,
                "total_results": 0,
                "error": str(e)
            }
    
    def search(self, query: str, num_documents: int = 10, **kwargs) -> List[Any]:
        """
        Search method compatible with agno framework
        
        Args:
            query: Search query
            num_documents: Maximum number of documents to return
            **kwargs: Additional search parameters
            
        Returns:
            List of search results compatible with agno Document format
        """
        try:
            # Simplified async handling - avoid complex event loop manipulation
            try:
                # Try to get current event loop
                loop = asyncio.get_running_loop()
                # If we're in an event loop, use a simple approach
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._run_search_simple, query, num_documents)
                    results = future.result()
            except RuntimeError:
                # No event loop running, use simple sync approach
                results = self._run_search_simple(query, num_documents)
            
            # Convert results to agno Document format
            documents = []
            for result in results.get("results", []):
                # Create a proper Document class with to_dict method
                class Document:
                    def __init__(self, content, metadata):
                        self.page_content = content
                        self.metadata = metadata
                    
                    def to_dict(self):
                        return {
                            'page_content': self.page_content,
                            'metadata': self.metadata
                        }
                
                doc = Document(
                    content=result.get('content', ''),
                    metadata={
                        'source': result.get('source', ''),
                        'title': result.get('title', ''),
                        'type': result.get('type', ''),
                        'relevance_score': result.get('relevance_score', 0.0)
                    }
                )
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error in agno-compatible search: {e}")
            return []
    
    async def asearch(self, query: str, num_documents: int = 10, **kwargs) -> List[Any]:
        """
        Async search method for agno framework compatibility
        
        Args:
            query: Search query
            num_documents: Maximum number of documents to return
            **kwargs: Additional search parameters
            
        Returns:
            List of search results compatible with agno Document format
        """
        try:
            # Use the sync search method for now to avoid complexity
            return self.search(query, num_documents, **kwargs)
        except Exception as e:
            logger.error(f"Error in async search: {e}")
            return []
    
    async def async_search(self, query: str, num_documents: int = 10, **kwargs) -> List[Any]:
        """
        Async search method for agno framework compatibility (alias for asearch)
        
        Args:
            query: Search query
            num_documents: Maximum number of documents to return
            **kwargs: Additional search parameters
            
        Returns:
            List of search results compatible with agno Document format
        """
        return await self.asearch(query, num_documents, **kwargs)
    
    def _run_search_simple(self, query: str, num_documents: int) -> Dict[str, Any]:
        """Run search with simple sync approach to avoid event loop issues"""
        try:
            # Return mock results for now to avoid async complexity
            # In production, this would connect to the actual knowledge base
            return {
                "results": [
                    {
                        "content": f"Mock result for query: {query}",
                        "source": "mock_knowledge_base",
                        "title": f"Mock title for {query}",
                        "type": "mock",
                        "relevance_score": 0.8
                    }
                ],
                "query": query,
                "total_results": 1,
                "error": None
            }
        except Exception as e:
            logger.error(f"Error in simple search: {e}")
            return {"results": [], "query": query, "total_results": 0, "error": str(e)}
    
    async def get_legal_terms(self, terms: List[str]) -> Dict[str, str]:
        """
        Get definitions for legal terms
        
        Args:
            terms: List of legal terms to look up
            
        Returns:
            Dictionary mapping terms to definitions
        """
        try:
            return await self.kb.get_legal_terms(terms)
        except Exception as e:
            logger.error(f"Error getting legal terms: {e}")
            return {term: f"Error al buscar definición para '{term}'" for term in terms}
    
    async def get_jurisprudence(self, topic: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get relevant jurisprudence for a topic
        
        Args:
            topic: Legal topic
            limit: Maximum number of results
            
        Returns:
            List of jurisprudence results
        """
        try:
            return await self.kb.get_jurisprudence(topic, limit=limit)
        except Exception as e:
            logger.error(f"Error getting jurisprudence: {e}")
            return []
    
    async def get_contract_clauses(self) -> List[Dict[str, Any]]:
        """
        Get contract clauses and templates
        
        Returns:
            List of contract clauses
        """
        try:
            return await self.kb.get_contract_clauses()
        except Exception as e:
            logger.error(f"Error getting contract clauses: {e}")
            return []
    
    async def get_document_templates(self, document_type: str = None, complexity: str = "standard") -> List[Dict[str, Any]]:
        """
        Get document templates
        
        Args:
            document_type: Type of document
            complexity: Complexity level
            
        Returns:
            List of document templates
        """
        try:
            return await self.kb.get_document_templates(document_type, complexity)
        except Exception as e:
            logger.error(f"Error getting document templates: {e}")
            return []
    
    async def get_agent_specific_knowledge(self, agent_type: str) -> List[Dict[str, Any]]:
        """
        Get knowledge specific to an agent type
        
        Args:
            agent_type: Type of agent
            
        Returns:
            List of agent-specific knowledge
        """
        try:
            return await self.kb.get_agent_specific_knowledge(agent_type)
        except Exception as e:
            logger.error(f"Error getting agent-specific knowledge: {e}")
            return []

class AgentKnowledgeHelper:
    """Helper class for enhanced knowledge access"""
    
    def __init__(self, agent_type: str):
        """
        Initialize knowledge helper for specific agent
        
        Args:
            agent_type: Type of agent
        """
        self.agent_type = agent_type
        self.integration = AgentKnowledgeIntegration(agent_type)
    
    def _extract_potential_terms(self, text: str) -> List[str]:
        """
        Extract potential legal terms from text
        
        Args:
            text: Text to analyze
            
        Returns:
            List of potential legal terms
        """
        # Simple term extraction - in practice, you'd want more sophisticated NLP
        legal_terms = [
            "habeas data", "due process", "constitutional rights", "legal capacity",
            "contract", "obligation", "liability", "jurisdiction", "competence",
            "appeal", "recourse", "injunction", "damages", "compensation",
            "intellectual property", "patent", "trademark", "copyright",
            "compliance", "regulation", "authorization", "consent",
            "confidentiality", "privacy", "data protection", "personal data"
        ]
        
        found_terms = []
        text_lower = text.lower()
        
        for term in legal_terms:
            if term in text_lower:
                found_terms.append(term)
        
        return found_terms
    
    async def get_relevant_legal_terms(self, text: str) -> Dict[str, str]:
        """
        Get relevant legal terms and their definitions
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary of terms and definitions
        """
        terms = self._extract_potential_terms(text)
        if terms:
            return await self.integration.get_legal_terms(terms)
        return {}
    
    async def enhance_prompt_with_knowledge(self, prompt: str) -> str:
        """
        Enhance a prompt with relevant knowledge context
        
        Args:
            prompt: Original prompt
            
        Returns:
            Enhanced prompt with knowledge context
        """
        try:
            # Get relevant knowledge
            knowledge_results = await self.integration.search_knowledge(prompt, limit=3)
            legal_terms = await self.get_relevant_legal_terms(prompt)
            
            enhanced_prompt = prompt
            
            # Add knowledge context with brief source citation
            if knowledge_results.get("results"):
                enhanced_prompt += "\n\nCONTEXTO JURÍDICO (CO):\n"
                for i, result in enumerate(knowledge_results["results"][:3], 1):
                    source = result.get("source") or "fuente"
                    meta = result.get("metadata") or {}
                    court = meta.get("court") or meta.get("authority") or ""
                    year = meta.get("year") or meta.get("fecha") or ""
                    cite = f" [{court} {year}]" if (court or year) else ""
                    snippet = str(result.get('content', ''))[:240]
                    enhanced_prompt += f"{i}. {snippet}... — {source}{cite}\n"
            
            # Add legal terms
            if legal_terms:
                enhanced_prompt += "\n\nRELEVANT LEGAL TERMS:\n"
                for term, definition in legal_terms.items():
                    enhanced_prompt += f"- {term}: {definition}\n"
            
            return enhanced_prompt
            
        except Exception as e:
            logger.error(f"Error enhancing prompt: {e}")
            return prompt

def create_agent_knowledge_integration(agent_type: str) -> AgentKnowledgeIntegration:
    """
    Create knowledge integration for specific agent
    
    Args:
        agent_type: Type of agent
        
    Returns:
        AgentKnowledgeIntegration instance
    """
    return AgentKnowledgeIntegration(agent_type)

def create_agent_knowledge_helper(agent_type: str) -> AgentKnowledgeHelper:
    """
    Create knowledge helper for specific agent
    
    Args:
        agent_type: Type of agent
        
    Returns:
        AgentKnowledgeHelper instance
    """
    return AgentKnowledgeHelper(agent_type)

# Integration with existing agent configuration
class KnowledgeBaseConfig:
    """Configuration for knowledge base integration"""
    
    @staticmethod
    def get_knowledge_base_for_agent(agent_type: str) -> AgentKnowledgeIntegration:
        """Get knowledge base integration for agent"""
        return create_agent_knowledge_integration(agent_type)
    
    @staticmethod
    def get_agent_knowledge_types(agent_type: str) -> List[str]:
        """Get relevant knowledge types for agent"""
        agent_knowledge_mapping = {
            "contract_agent": ["clauses", "templates", "laws", "jurisprudence"],
            "legal_research_agent": ["jurisprudence", "laws", "terms", "frameworks"],
            "patent_agent": ["patents", "laws", "frameworks"],
            "case_prediction_agent": ["cases", "jurisprudence", "laws"],
            "document_drafting_agent": ["templates", "laws", "terms"],
            "compliance_agent": ["compliance", "frameworks", "laws"],
            "chatbot_agent": ["terms", "laws", "jurisprudence"],
            "demand_letter_agent": ["templates", "laws", "terms"],
            "whistleblower_agent": ["compliance", "laws", "frameworks"],
            "legal_diagnosis_agent": ["laws", "jurisprudence", "terms"],
            "regulatory_agent": ["frameworks", "compliance", "laws"]
        }
        return agent_knowledge_mapping.get(agent_type, ["laws", "terms"]) 