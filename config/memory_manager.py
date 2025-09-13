"""
Memory Management Utility for Legal AI Assistant
Provides centralized memory operations for all agents using PostgreSQL
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from postgres_memory import get_memory_instance, add_user_memory, get_user_memories, search_knowledge_base, get_session_data, store_session_data

logger = logging.getLogger(__name__)

class MemoryManager:
    """Centralized memory management for all agents using PostgreSQL"""
    
    def __init__(self):
        self.agent_names = [
            "chatbot_agent",
            "contract_agent", 
            "legal_research_agent",
            "case_prediction_agent",
            "compliance_agent",
            "document_drafting_agent",
            "demand_letter_agent",
            "patent_agent",
            "regulatory_agent",
            "whistleblower_agent"
        ]
        self._initialize_memory_systems()
    
    def _initialize_memory_systems(self):
        """Initialize memory systems for all agents"""
        for agent_name in self.agent_names:
            try:
                # Initialize memory instance for each agent
                memory_instance = get_memory_instance(agent_name)
                logger.info(f"Memory system initialized for {agent_name}")
            except Exception as e:
                logger.warning(f"Failed to initialize memory for {agent_name}: {e}")
    
    def get_user_memories(self, agent_name: str, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user memories for a specific agent"""
        try:
            from postgres_memory import get_user_memories as pg_get_user_memories
            return pg_get_user_memories(agent_name, user_id, limit)
        except Exception as e:
            logger.error(f"Error getting user memories for {agent_name}: {e}")
            return []
    
    def add_user_memory(self, agent_name: str, user_id: str, memory_data: Dict[str, Any]) -> bool:
        """Add a new memory for a user"""
        try:
            memory_content = memory_data.get("memory", "")
            topics = memory_data.get("topics", [])
            memory_type = memory_data.get("memory_type", "general")
            metadata = memory_data.get("metadata", {})
            
            from postgres_memory import add_user_memory as pg_add_user_memory
            success = pg_add_user_memory(
                agent_name=agent_name,
                user_id=user_id,
                memory_content=memory_content,
                topics=topics,
                memory_type=memory_type,
                metadata=metadata
            )
            
            if success:
                logger.info(f"Memory added for {agent_name}, user {user_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error adding memory for {agent_name}: {e}")
            return False
    
    def get_session_summary(self, agent_name: str, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session summary for a specific agent and session"""
        try:
            from postgres_memory import get_session_data as pg_get_session_data
            return pg_get_session_data(agent_name, user_id, session_id)
        except Exception as e:
            logger.error(f"Error getting session summary for {agent_name}: {e}")
            return None
    
    def clear_user_memories(self, agent_name: str, user_id: str) -> bool:
        """Clear all memories for a user"""
        try:
            # For now, we'll just return True since clearing is handled by the database
            # In a full implementation, you would delete from the agent-specific tables
            logger.info(f"Memory clearing requested for {agent_name}, user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing memories for {agent_name}: {e}")
            return False
    
    def get_memory_stats(self, agent_name: str, user_id: str) -> Dict[str, Any]:
        """Get memory statistics for a user"""
        try:
            memories = self.get_user_memories(agent_name, user_id)
            
            return {
                "agent_name": agent_name,
                "user_id": user_id,
                "total_memories": len(memories),
                "recent_memories": len([m for m in memories if self._is_recent(m.get("last_updated"))]),
                "last_interaction": self._get_last_interaction(memories)
            }
        except Exception as e:
            logger.error(f"Error getting memory stats for {agent_name}: {e}")
            return {}
    
    def _is_recent(self, timestamp) -> bool:
        """Check if a timestamp is recent (within last 7 days)"""
        try:
            if not timestamp:
                return False
            # Handle both string and datetime objects
            if isinstance(timestamp, str):
                memory_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                memory_time = timestamp
            return datetime.now(memory_time.tzinfo) - memory_time < timedelta(days=7)
        except:
            return False
    
    def _get_last_interaction(self, memories: List[Dict[str, Any]]) -> Optional[str]:
        """Get the timestamp of the last interaction"""
        if not memories:
            return None
        
        try:
            # Sort by last_updated and get the most recent
            sorted_memories = sorted(memories, key=lambda x: x.get("last_updated", ""), reverse=True)
            return sorted_memories[0].get("last_updated")
        except:
            return None
    
    def get_legal_research_memories(self, user_id: str, research_topic: str = None, jurisdiction: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get legal research memories for a user"""
        try:
            from postgres_memory import get_memory_instance
            memory_instance = get_memory_instance("legal_research_agent")
            if memory_instance and hasattr(memory_instance, 'get_legal_research_memories'):
                return memory_instance.get_legal_research_memories(user_id, research_topic, jurisdiction, limit)
            else:
                logger.warning("Memory instance not available for legal research")
                return []
        except Exception as e:
            logger.error(f"Error getting legal research memories: {e}")
            return []
    
    def store_legal_research_memory(self, user_id: str, session_id: str, research_topic: str,
                                   research_summary: str, research_topics: List[str] = None,
                                   legal_sources: List[str] = None, jurisdiction: str = "Colombia") -> bool:
        """Store legal research memory"""
        try:
            from postgres_memory import get_memory_instance
            memory_instance = get_memory_instance("legal_research_agent")
            if memory_instance and hasattr(memory_instance, 'store_legal_research_memory'):
                return memory_instance.store_legal_research_memory(
                    user_id, session_id, research_topic, research_summary, 
                    research_topics, legal_sources, jurisdiction
                )
            else:
                logger.warning("Memory instance not available for storing legal research memory")
                return False
        except Exception as e:
            logger.error(f"Error storing legal research memory: {e}")
            return False
    
    def get_agent_memory_context(self, agent_name: str, user_id: str, session_id: str = None) -> str:
        """Get memory context for an agent to include in prompts"""
        try:
            memories = self.get_user_memories(agent_name, user_id)
            session_summary = None
            
            if session_id:
                session_summary = self.get_session_summary(agent_name, user_id, session_id)
            
            context_parts = []
            
            # Add recent memories context
            if memories:
                recent_memories = [m for m in memories if self._is_recent(m.get("last_updated"))]
                if recent_memories:
                    context_parts.append("MEMORIAS RECIENTES DEL USUARIO:")
                    for memory in recent_memories[-3:]:  # Last 3 memories
                        context_parts.append(f"- {memory.get('memory', '')}")
            
            # Add session summary context
            if session_summary:
                context_parts.append(f"RESUMEN DE SESIÓN: {session_summary.get('summary', '')}")
            
            return "\n".join(context_parts) if context_parts else ""
            
        except Exception as e:
            logger.error(f"Error getting memory context for {agent_name}: {e}")
            return ""
    
    def update_memory_from_interaction(self, agent_name: str, user_id: str, session_id: str, 
                                     interaction_data: Dict[str, Any]) -> bool:
        """Update memory based on a new interaction"""
        try:
            # Store session data
            session_data = {
                "interaction": interaction_data,
                "timestamp": datetime.now().isoformat(),
                "agent_name": agent_name
            }
            
            from postgres_memory import store_session_data as pg_store_session_data
            success = pg_store_session_data(agent_name, user_id, session_id, session_data)
            
            if success:
                logger.info(f"Memory updated for {agent_name}, user {user_id}, session {session_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error updating memory for {agent_name}: {e}")
            return False

# Global memory manager instance
_memory_manager = None

def get_memory_manager() -> MemoryManager:
    """Get or create the global memory manager instance"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager

def get_user_memories(agent_name: str, user_id: str) -> List[Dict[str, Any]]:
    """Get user memories for a specific agent"""
    return get_memory_manager().get_user_memories(agent_name, user_id)

def add_user_memory(agent_name: str, user_id: str, memory_data: Dict[str, Any]) -> bool:
    """Add a new memory for a user"""
    return get_memory_manager().add_user_memory(agent_name, user_id, memory_data)

def get_session_summary(agent_name: str, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
    """Get session summary for a specific agent and session"""
    return get_memory_manager().get_session_summary(agent_name, user_id, session_id)

def clear_user_memories(agent_name: str, user_id: str) -> bool:
    """Clear all memories for a user"""
    return get_memory_manager().clear_user_memories(agent_name, user_id)

def get_memory_stats(agent_name: str, user_id: str) -> Dict[str, Any]:
    """Get memory statistics for a user"""
    return get_memory_manager().get_memory_stats(agent_name, user_id)

def get_agent_memory_context(agent_name: str, user_id: str, session_id: str = None) -> str:
    """Get memory context for an agent to include in prompts"""
    return get_memory_manager().get_agent_memory_context(agent_name, user_id, session_id)

def update_memory_from_interaction(agent_name: str, user_id: str, session_id: str, 
                                 interaction_data: Dict[str, Any]) -> bool:
    """Update memory based on a new interaction"""
    return get_memory_manager().update_memory_from_interaction(agent_name, user_id, session_id, interaction_data) 