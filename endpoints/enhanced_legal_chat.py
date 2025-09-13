#!/usr/bin/env python3
"""
Enhanced Legal Chat Endpoint
Demonstrates integration of vector database, storage, memory, and knowledge systems
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import asyncio
import logging
from datetime import datetime

from agents.enhanced_legal_agent import EnhancedLegalAgent
from config.enhanced_agent_config import get_enhanced_agent_config
from middleware.security import verify_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/enhanced-legal", tags=["Enhanced Legal Chat"])

# Request/Response Models
class LegalQueryRequest(BaseModel):
    query: str
    agent_type: str = "legal_research_agent"
    context: Optional[Dict[str, Any]] = None
    user_preferences: Optional[Dict[str, Any]] = None

class LegalQueryResponse(BaseModel):
    response: str
    knowledge_sources: List[Dict[str, Any]]
    confidence_score: float
    session_id: str
    timestamp: str
    agent_type: str
    user_id: str

class LegalTermsRequest(BaseModel):
    terms: List[str]
    user_id: str

class JurisprudenceRequest(BaseModel):
    topic: str
    court: Optional[str] = None
    limit: int = 5
    user_id: str

class ContractAnalysisRequest(BaseModel):
    contract_text: str
    user_id: str
    analysis_type: str = "comprehensive"  # comprehensive, risk, compliance

# Global agent instances (in production, use proper session management)
_agents = {}

def get_enhanced_agent(agent_type: str, user_id: str) -> EnhancedLegalAgent:
    """Get or create enhanced agent instance"""
    agent_key = f"{agent_type}_{user_id}"
    
    if agent_key not in _agents:
        _agents[agent_key] = EnhancedLegalAgent(agent_type, user_id)
    
    return _agents[agent_key]

@router.post("/query", response_model=LegalQueryResponse)
async def process_legal_query(
    request: LegalQueryRequest,
    current_user: Dict = Depends(verify_token)
):
    """
    Process legal query with full system integration
    
    This endpoint demonstrates the complete integration of:
    - Vector database for semantic search
    - Knowledge base for legal documents
    - Memory system for user preferences
    - Storage system for session data
    """
    try:
        user_id = current_user.get("user_id", "anonymous")
        
        # Get enhanced agent
        agent = get_enhanced_agent(request.agent_type, user_id)
        
        # Update user preferences if provided
        if request.user_preferences:
            await agent._update_user_preferences(user_id, request.user_preferences)
        
        # Process the legal query
        result = await agent.process_legal_query(
            query=request.query,
            context=request.context
        )
        
        return LegalQueryResponse(
            response=result["response"],
            knowledge_sources=result.get("knowledge_sources", []),
            confidence_score=result.get("confidence_score", 0.0),
            session_id=result.get("session_id", ""),
            timestamp=result.get("timestamp", datetime.now().isoformat()),
            agent_type=request.agent_type,
            user_id=user_id
        )
        
    except Exception as e:
        logger.error(f"Error processing legal query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/legal-terms")
async def get_legal_terms(
    request: LegalTermsRequest,
    current_user: Dict = Depends(verify_token)
):
    """
    Get definitions for legal terms using knowledge base
    """
    try:
        user_id = request.user_id or current_user.get("user_id", "anonymous")
        agent = get_enhanced_agent("legal_research_agent", user_id)
        
        definitions = await agent.get_legal_terms(request.terms)
        
        return {
            "definitions": definitions,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting legal terms: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/jurisprudence")
async def get_jurisprudence(
    request: JurisprudenceRequest,
    current_user: Dict = Depends(verify_token)
):
    """
    Search for relevant jurisprudence using vector database
    """
    try:
        user_id = request.user_id or current_user.get("user_id", "anonymous")
        agent = get_enhanced_agent("legal_research_agent", user_id)
        
        jurisprudence = await agent.get_jurisprudence(
            topic=request.topic,
            limit=request.limit
        )
        
        return {
            "jurisprudence": jurisprudence,
            "topic": request.topic,
            "court": request.court,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting jurisprudence: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/contract-analysis")
async def analyze_contract(
    request: ContractAnalysisRequest,
    current_user: Dict = Depends(verify_token)
):
    """
    Analyze contract using knowledge base and AI model
    """
    try:
        user_id = request.user_id or current_user.get("user_id", "anonymous")
        agent = get_enhanced_agent("contract_agent", user_id)
        
        analysis = await agent.get_contract_analysis(request.contract_text)
        
        return {
            "analysis": analysis.get("analysis", ""),
            "knowledge_sources": analysis.get("knowledge_sources", []),
            "confidence": analysis.get("confidence", 0.0),
            "analysis_type": request.analysis_type,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error analyzing contract: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user-history/{user_id}")
async def get_user_history(
    user_id: str,
    limit: int = 10,
    current_user: Dict = Depends(verify_token)
):
    """
    Get user interaction history from storage system
    """
    try:
        # Verify user can access this history
        if current_user.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        agent = get_enhanced_agent("legal_research_agent", user_id)
        
        # Get session history from storage
        history = await agent._get_session_history(user_id, limit)
        
        return {
            "history": history,
            "user_id": user_id,
            "limit": limit,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting user history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user-preferences/{user_id}")
async def get_user_preferences(
    user_id: str,
    current_user: Dict = Depends(verify_token)
):
    """
    Get user preferences from memory system
    """
    try:
        # Verify user can access preferences
        if current_user.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        agent = get_enhanced_agent("legal_research_agent", user_id)
        
        preferences = await agent._get_user_memory()
        
        return {
            "preferences": preferences,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting user preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-preferences/{user_id}")
async def update_user_preferences(
    user_id: str,
    preferences: Dict[str, Any],
    current_user: Dict = Depends(verify_token)
):
    """
    Update user preferences in memory system
    """
    try:
        # Verify user can update preferences
        if current_user.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        agent = get_enhanced_agent("legal_research_agent", user_id)
        
        # Update user preferences
        await agent._update_user_preferences(user_id, preferences)
        
        return {
            "message": "Preferences updated successfully",
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error updating user preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge-stats")
async def get_knowledge_stats(
    current_user: Dict = Depends(verify_token)
):
    """
    Get statistics about knowledge base usage
    """
    try:
        user_id = current_user.get("user_id", "anonymous")
        agent = get_enhanced_agent("legal_research_agent", user_id)
        
        # Get knowledge base statistics
        stats = {
            "knowledge_base_available": agent.knowledge_base is not None,
            "storage_available": agent.storage is not None,
            "memory_available": agent.memory is not None,
            "vector_db_available": agent.config.get("search_knowledge", False),
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting knowledge stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Batch processing endpoint
@router.post("/batch-query")
async def batch_process_queries(
    queries: List[LegalQueryRequest],
    current_user: Dict = Depends(verify_token)
):
    """
    Process multiple legal queries efficiently
    """
    try:
        user_id = current_user.get("user_id", "anonymous")
        agent = get_enhanced_agent("legal_research_agent", user_id)
        
        results = []
        
        # Process queries in parallel
        tasks = []
        for query_request in queries:
            task = agent.process_legal_query(
                query=query_request.query,
                context=query_request.context
            )
            tasks.append(task)
        
        # Wait for all queries to complete
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(batch_results):
            if isinstance(result, Exception):
                results.append({
                    "error": str(result),
                    "query": queries[i].query,
                    "success": False
                })
            else:
                results.append({
                    "response": result["response"],
                    "knowledge_sources": result.get("knowledge_sources", []),
                    "confidence_score": result.get("confidence_score", 0.0),
                    "query": queries[i].query,
                    "success": True
                })
        
        return {
            "results": results,
            "total_queries": len(queries),
            "successful_queries": len([r for r in results if r["success"]]),
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in batch processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@router.get("/health")
async def health_check():
    """
    Health check for enhanced legal chat system
    """
    try:
        # Test basic agent creation
        test_agent = get_enhanced_agent("legal_research_agent", "test_user")
        
        health_status = {
            "status": "healthy",
            "knowledge_base": test_agent.knowledge_base is not None,
            "storage": test_agent.storage is not None,
            "memory": test_agent.memory is not None,
            "vector_db": test_agent.config.get("search_knowledge", False),
            "timestamp": datetime.now().isoformat()
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        } 