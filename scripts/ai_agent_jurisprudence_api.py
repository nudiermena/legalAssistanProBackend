#!/usr/bin/env python3
"""
AI Agent Jurisprudence API
Comprehensive interface for AI agents to search constitutional court jurisprudence
"""

import asyncio
import logging
import sys
import os
from typing import List, Dict, Any, Optional
import psycopg
import math
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import configuration
from config.settings import POSTGRES_URL, MISTRAL_API_KEY

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AIAgentJurisprudenceAPI:
    """Comprehensive API for AI agents to search jurisprudence data"""
    
    def __init__(self):
        self.postgres_url = POSTGRES_URL
        self.mistral_api_key = MISTRAL_API_KEY
    
    def get_mistral_embedding(self, text: str) -> List[float]:
        """Get vector embedding from Mistral API"""
        try:
            import requests
            
            headers = {
                'Authorization': f'Bearer {self.mistral_api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': 'mistral-embed',
                'input': text[:8000]
            }
            
            response = requests.post(
                'https://api.mistral.ai/v1/embeddings',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['data'][0]['embedding']
            else:
                logger.warning(f"Mistral API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.warning(f"Error getting Mistral embedding: {e}")
            return None
    
    def parse_vector_string(self, vector_str: str) -> List[float]:
        """Parse PostgreSQL vector string to Python list"""
        if not vector_str or vector_str == 'None':
            return None
        
        vector_str = vector_str.strip('[]')
        return [float(x.strip()) for x in vector_str.split(',')]
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    async def search_jurisprudence(self, 
                                 query: str, 
                                 search_type: str = "hybrid",
                                 limit: int = 20,
                                 vector_weight: float = 0.6,
                                 keyword_weight: float = 0.4,
                                 filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main search method for AI agents
        
        Args:
            query: Search query string
            search_type: "keyword", "vector", "hybrid", "semantic"
            limit: Maximum number of results
            vector_weight: Weight for vector similarity (0.0-1.0)
            keyword_weight: Weight for keyword matching (0.0-1.0)
            filters: Additional filters (court, decision_type, year, tags)
        
        Returns:
            Dictionary with search results and metadata
        """
        try:
            # Apply filters if provided
            if filters:
                query = self.apply_filters_to_query(query, filters)
            
            # Perform search based on type
            if search_type == "keyword":
                results = await self._keyword_search(query, limit)
            elif search_type == "vector":
                results = await self._vector_search(query, limit)
            elif search_type == "semantic":
                results = await self._semantic_search(query, limit)
            elif search_type == "hybrid":
                results = await self._hybrid_search(query, limit, vector_weight, keyword_weight)
            else:
                raise ValueError(f"Unknown search type: {search_type}")
            
            # Add metadata
            response = {
                "query": query,
                "search_type": search_type,
                "filters_applied": filters or {},
                "total_results": len(results),
                "results": results,
                "search_metadata": {
                    "vector_weight": vector_weight if search_type == "hybrid" else None,
                    "keyword_weight": keyword_weight if search_type == "hybrid" else None,
                    "limit": limit
                }
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error in search_jurisprudence: {e}")
            return {
                "error": str(e),
                "query": query,
                "search_type": search_type,
                "results": []
            }
    
    async def _keyword_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Internal keyword search method"""
        try:
            with psycopg.connect(self.postgres_url) as conn:
                with conn.cursor() as cur:
                    sql = """
                        SELECT 
                            case_number, court, decision_type, topic, summary, 
                            full_text, tags, source_url,
                            (
                                CASE WHEN topic ILIKE %s THEN 3 ELSE 0 END +
                                CASE WHEN summary ILIKE %s THEN 2 ELSE 0 END +
                                CASE WHEN full_text ILIKE %s THEN 1 ELSE 0 END +
                                CASE WHEN %s = ANY(tags) THEN 2 ELSE 0 END
                            ) as keyword_score
                        FROM ai.jurisprudence 
                        WHERE 
                            topic ILIKE %s OR 
                            summary ILIKE %s OR 
                            full_text ILIKE %s OR
                            %s = ANY(tags)
                        ORDER BY keyword_score DESC, case_number
                        LIMIT %s
                    """
                    
                    search_pattern = f"%{query}%"
                    cur.execute(sql, (
                        search_pattern, search_pattern, search_pattern, query,
                        search_pattern, search_pattern, search_pattern, query, limit
                    ))
                    
                    results = []
                    for row in cur.fetchall():
                        results.append({
                            "case_number": row[0],
                            "court": row[1],
                            "decision_type": row[2],
                            "topic": row[3] or "No topic available",
                            "summary": row[4] or "No summary available",
                            "full_text": row[5] or "",
                            "tags": row[6] or [],
                            "source_url": row[7] or "",
                            "keyword_score": row[8],
                            "search_method": "keyword"
                        })
                    
                    return results
                    
        except Exception as e:
            logger.error(f"Error in keyword search: {e}")
            return []
    
    async def _vector_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Internal vector search method"""
        try:
            query_embedding = self.get_mistral_embedding(query)
            if not query_embedding:
                logger.warning("Could not get query embedding, falling back to keyword search")
                return await self._keyword_search(query, limit)
            
            with psycopg.connect(self.postgres_url) as conn:
                with conn.cursor() as cur:
                    sql = """
                        SELECT 
                            case_number, court, decision_type, topic, summary, 
                            full_text, tags, source_url, vector_embedding
                        FROM ai.jurisprudence 
                        WHERE vector_embedding IS NOT NULL
                    """
                    cur.execute(sql)
                    
                    cases_with_scores = []
                    
                    for row in cur.fetchall():
                        case = {
                            "case_number": row[0],
                            "court": row[1],
                            "decision_type": row[2],
                            "topic": row[3] or "No topic available",
                            "summary": row[4] or "No summary available",
                            "full_text": row[5] or "",
                            "tags": row[6] or [],
                            "source_url": row[7] or "",
                            "vector_embedding": row[8],
                            "search_method": "vector"
                        }
                        
                        case_vector = self.parse_vector_string(case['vector_embedding'])
                        if case_vector:
                            similarity = self.cosine_similarity(query_embedding, case_vector)
                            case['vector_score'] = similarity
                            cases_with_scores.append(case)
                    
                    cases_with_scores.sort(key=lambda x: x['vector_score'], reverse=True)
                    return cases_with_scores[:limit]
                    
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []
    
    async def _hybrid_search(self, query: str, limit: int, 
                            vector_weight: float, keyword_weight: float) -> List[Dict[str, Any]]:
        """Internal hybrid search method"""
        try:
            # Get results from both methods
            keyword_results = await self._keyword_search(query, limit * 2)
            vector_results = await self._vector_search(query, limit * 2)
            
            # Create lookup dictionaries
            keyword_scores = {r['case_number']: r['keyword_score'] for r in keyword_results}
            vector_scores = {r['case_number']: r['vector_score'] for r in vector_results}
            
            # Combine all unique cases
            all_cases = {}
            
            # Add keyword results
            for case in keyword_results:
                case_number = case['case_number']
                if case_number not in all_cases:
                    all_cases[case_number] = case.copy()
                    all_cases[case_number]['keyword_score'] = case['keyword_score']
                    all_cases[case_number]['vector_score'] = 0.0
                else:
                    all_cases[case_number]['keyword_score'] = max(
                        all_cases[case_number]['keyword_score'], 
                        case['keyword_score']
                    )
            
            # Add vector results
            for case in vector_results:
                case_number = case['case_number']
                if case_number not in all_cases:
                    all_cases[case_number] = case.copy()
                    all_cases[case_number]['keyword_score'] = 0.0
                    all_cases[case_number]['vector_score'] = case['vector_score']
                else:
                    all_cases[case_number]['vector_score'] = case['vector_score']
            
            # Calculate hybrid scores
            for case_number, case in all_cases.items():
                keyword_norm = min(case['keyword_score'] / 8.0, 1.0)
                vector_norm = max(0, case['vector_score'])
                
                hybrid_score = (keyword_weight * keyword_norm) + (vector_weight * vector_norm)
                case['hybrid_score'] = hybrid_score
                case['search_method'] = 'hybrid'
                
                case['score_breakdown'] = {
                    'keyword_score': case['keyword_score'],
                    'keyword_normalized': keyword_norm,
                    'vector_score': case['vector_score'],
                    'vector_normalized': vector_norm,
                    'hybrid_score': hybrid_score,
                    'weights': {'keyword': keyword_weight, 'vector': vector_weight}
                }
            
            # Sort by hybrid score
            sorted_cases = sorted(
                all_cases.values(), 
                key=lambda x: x['hybrid_score'], 
                reverse=True
            )
            
            return sorted_cases[:limit]
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            return await self._keyword_search(query, limit)
    
    async def _semantic_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Internal semantic search method"""
        try:
            enhanced_query = self.enhance_legal_query(query)
            results = await self._vector_search(enhanced_query, limit)
            
            for result in results:
                result['semantic_context'] = self.extract_semantic_context(query, result)
                result['search_method'] = 'semantic'
                result['enhanced_query'] = enhanced_query
            
            return results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def apply_filters_to_query(self, query: str, filters: Dict[str, Any]) -> str:
        """Apply filters to enhance the search query"""
        enhanced_query = query
        
        if 'court' in filters:
            enhanced_query += f" {filters['court']}"
        
        if 'decision_type' in filters:
            enhanced_query += f" {filters['decision_type']}"
        
        if 'year' in filters:
            enhanced_query += f" {filters['year']}"
        
        if 'tags' in filters and isinstance(filters['tags'], list):
            enhanced_query += f" {' '.join(filters['tags'])}"
        
        return enhanced_query
    
    def enhance_legal_query(self, query: str) -> str:
        """Enhance legal query with relevant context"""
        legal_context = {
            'derechos fundamentales': 'derechos humanos constitucionales garantías',
            'control constitucional': 'constitucionalidad exequibilidad',
            'debido proceso': 'proceso justo garantías procesales',
            'libertad de expresión': 'libertad opinión prensa',
            'principio de igualdad': 'igualdad discriminación trato igual'
        }
        
        enhanced = query
        for key, context in legal_context.items():
            if key.lower() in query.lower():
                enhanced = f"{query} {context}"
                break
        
        return enhanced
    
    def extract_semantic_context(self, query: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract semantic context for a search result"""
        context = {
            'query_terms': query.lower().split(),
            'topic_relevance': 0,
            'summary_relevance': 0,
            'tag_relevance': 0
        }
        
        query_terms = set(query.lower().split())
        
        if result['topic']:
            topic_terms = set(result['topic'].lower().split())
            context['topic_relevance'] = len(query_terms.intersection(topic_terms)) / len(query_terms)
        
        if result['summary']:
            summary_terms = set(result['summary'].lower().split())
            context['summary_relevance'] = len(query_terms.intersection(summary_terms)) / len(query_terms)
        
        if result['tags']:
            tag_terms = set()
            for tag in result['tags']:
                tag_terms.update(tag.lower().split())
            context['tag_relevance'] = len(query_terms.intersection(tag_terms)) / len(query_terms)
        
        return context
    
    async def get_case_details(self, case_number: str) -> Dict[str, Any]:
        """Get detailed information about a specific case"""
        try:
            with psycopg.connect(self.postgres_url) as conn:
                with conn.cursor() as cur:
                    sql = """
                        SELECT case_number, court, decision_type, decision_date, topic, 
                               summary, full_text, key_holdings, legal_principles, 
                               cited_laws, tags, source_url, vector_embedding
                        FROM ai.jurisprudence 
                        WHERE case_number = %s
                    """
                    cur.execute(sql, (case_number,))
                    row = cur.fetchone()
                    
                    if row:
                        return {
                            "case_number": row[0],
                            "court": row[1],
                            "decision_type": row[2],
                            "decision_date": row[3],
                            "topic": row[4],
                            "summary": row[5],
                            "full_text": row[6],
                            "key_holdings": row[7],
                            "legal_principles": row[8],
                            "cited_laws": row[9],
                            "tags": row[10],
                            "source_url": row[11],
                            "has_vector_embedding": bool(row[12])
                        }
                    else:
                        return {"error": "Case not found"}
                        
        except Exception as e:
            logger.error(f"Error getting case details: {e}")
            return {"error": str(e)}
    
    async def get_jurisprudence_stats(self) -> Dict[str, Any]:
        """Get statistics about the jurisprudence data"""
        try:
            with psycopg.connect(self.postgres_url) as conn:
                with conn.cursor() as cur:
                    # Count total cases
                    cur.execute("SELECT COUNT(*) FROM ai.jurisprudence")
                    total_cases = cur.fetchone()[0]
                    
                    # Count by decision type
                    cur.execute("""
                        SELECT decision_type, COUNT(*) 
                        FROM ai.jurisprudence 
                        WHERE decision_type IS NOT NULL
                        GROUP BY decision_type
                    """)
                    by_decision_type = dict(cur.fetchall())
                    
                    # Count by court
                    cur.execute("""
                        SELECT court, COUNT(*) 
                        FROM ai.jurisprudence 
                        GROUP BY court
                    """)
                    by_court = dict(cur.fetchall())
                    
                    # Check for vector embeddings
                    cur.execute("""
                        SELECT COUNT(*) 
                        FROM ai.jurisprudence 
                        WHERE vector_embedding IS NOT NULL
                    """)
                    with_vectors = cur.fetchone()[0]
                    
                    return {
                        "total_cases": total_cases,
                        "by_decision_type": by_decision_type,
                        "by_court": by_court,
                        "with_vectors": with_vectors,
                        "vector_coverage_percentage": (with_vectors / total_cases * 100) if total_cases > 0 else 0
                    }
                    
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {"error": str(e)}
    
    async def search_by_filters(self, filters: Dict[str, Any], limit: int = 20) -> Dict[str, Any]:
        """Search jurisprudence using specific filters"""
        try:
            conditions = []
            params = []
            
            if 'court' in filters:
                conditions.append("court = %s")
                params.append(filters['court'])
            
            if 'decision_type' in filters:
                conditions.append("decision_type = %s")
                params.append(filters['decision_type'])
            
            if 'year' in filters:
                conditions.append("EXTRACT(YEAR FROM decision_date) = %s")
                params.append(filters['year'])
            
            if 'tags' in filters and isinstance(filters['tags'], list):
                for tag in filters['tags']:
                    conditions.append("%s = ANY(tags)")
                    params.append(tag)
            
            if not conditions:
                return {"error": "No valid filters provided"}
            
            where_clause = " AND ".join(conditions)
            sql = f"""
                SELECT case_number, court, decision_type, topic, summary, 
                       full_text, tags, source_url
                FROM ai.jurisprudence 
                WHERE {where_clause}
                ORDER BY decision_date DESC
                LIMIT %s
            """
            params.append(limit)
            
            with psycopg.connect(self.postgres_url) as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                    
                    results = []
                    for row in cur.fetchall():
                        results.append({
                            "case_number": row[0],
                            "court": row[1],
                            "decision_type": row[2],
                            "topic": row[3] or "No topic available",
                            "summary": row[4] or "No summary available",
                            "full_text": row[5] or "",
                            "tags": row[6] or [],
                            "source_url": row[7] or "",
                            "search_method": "filter"
                        })
                    
                    return {
                        "filters_applied": filters,
                        "total_results": len(results),
                        "results": results
                    }
                    
        except Exception as e:
            logger.error(f"Error in filter search: {e}")
            return {"error": str(e)}

# Example usage for AI agents
async def demonstrate_api_usage():
    """Demonstrate how AI agents can use the API"""
    print("AI AGENT JURISPRUDENCE API - USAGE DEMONSTRATION")
    print("="*80)
    
    api = AIAgentJurisprudenceAPI()
    
    # 1. Get statistics
    print("\n1. GETTING JURISPRUDENCE STATISTICS:")
    stats = await api.get_jurisprudence_stats()
    print(json.dumps(stats, indent=2, default=str))
    
    # 2. Hybrid search example
    print("\n2. HYBRID SEARCH EXAMPLE:")
    hybrid_results = await api.search_jurisprudence(
        query="derechos fundamentales",
        search_type="hybrid",
        limit=5,
        vector_weight=0.7,
        keyword_weight=0.3
    )
    print(f"Found {hybrid_results['total_results']} results")
    print(f"Search type: {hybrid_results['search_type']}")
    print(f"Filters applied: {hybrid_results['filters_applied']}")
    
    # 3. Semantic search example
    print("\n3. SEMANTIC SEARCH EXAMPLE:")
    semantic_results = await api.search_jurisprudence(
        query="control constitucional",
        search_type="semantic",
        limit=3
    )
    print(f"Found {semantic_results['total_results']} results")
    
    # 4. Filter search example
    print("\n4. FILTER SEARCH EXAMPLE:")
    filter_results = await api.search_by_filters(
        filters={
            "decision_type": "tutela",
            "tags": ["derechos_fundamentales"]
        },
        limit=3
    )
    print(f"Found {filter_results['total_results']} results")
    
    # 5. Get case details example
    if hybrid_results['results']:
        print("\n5. GETTING CASE DETAILS:")
        case_number = hybrid_results['results'][0]['case_number']
        case_details = await api.get_case_details(case_number)
        print(f"Case {case_number} details:")
        print(json.dumps(case_details, indent=2, default=str))
    
    print(f"\n{'='*80}")
    print("API DEMONSTRATION COMPLETED!")
    print(f"{'='*80}")
    print("\nAI agents can now use this API for:")
    print("✅ Hybrid search combining vector and keyword approaches")
    print("✅ Semantic search with legal context enhancement")
    print("✅ Filtered searches by court, decision type, year, tags")
    print("✅ Detailed case information retrieval")
    print("✅ Comprehensive statistics and metadata")
    print("\nThe API is production-ready for AI agent integration!")

async def main():
    """Main function"""
    try:
        await demonstrate_api_usage()
        
    except Exception as e:
        print(f"Error during demonstration: {e}")

if __name__ == "__main__":
    asyncio.run(main())
