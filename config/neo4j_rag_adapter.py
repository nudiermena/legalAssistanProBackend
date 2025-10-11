"""
Neo4j RAG adapter: thin wrapper that exposes simple functions for agents
to retrieve graph-based context in a consistent, failure-tolerant shape.
"""

from typing import List, Dict, Any, Optional

def _safe_list(value: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    return value or []

def find_similar_cases(
    legal_concepts: List[str],
    legal_area: Optional[str] = None,
    procedure_type: Optional[str] = None,
    court_id: Optional[str] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    try:
        from config.neo4j_http_client import get_neo4j_http_client
        client = get_neo4j_http_client()
        results = client.find_similar_cases(
            legal_concepts=legal_concepts or [],
            legal_area=legal_area,
            procedure_type=procedure_type,
            limit=limit,
        )
        return _safe_list(results)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Neo4j similar cases lookup failed: {e}")
        return []

def get_precedents_for_concepts(
    legal_concepts: List[str],
    jurisdiction: Optional[str] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    try:
        from config.neo4j_http_client import get_neo4j_http_client
        client = get_neo4j_http_client()
        results = client.get_precedents_for_concepts(
            legal_concepts=legal_concepts or [],
            jurisdiction=jurisdiction or "Colombia",
            limit=limit,
        )
        return _safe_list(results)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Neo4j precedents lookup failed: {e}")
        return []



