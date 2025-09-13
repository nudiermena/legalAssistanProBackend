#!/usr/bin/env python3
"""
Hybrid Jurisprudence Search System
Combines vector similarity search with keyword matching for optimal results
"""

import asyncio
import logging
import sys
import os
from typing import List, Dict, Any, Tuple
import psycopg
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

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

class HybridJurisprudenceSearch:
    """Hybrid search system combining vector similarity and keyword matching"""
    
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
                'input': text[:8000]  # Limit text length for API
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
        
        # Remove brackets and split by comma
        vector_str = vector_str.strip('[]')
        return [float(x.strip()) for x in vector_str.split(',')]
    
    async def keyword_search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Perform keyword-based search using PostgreSQL text search"""
        try:
            with psycopg.connect(self.postgres_url) as conn:
                with conn.cursor() as cur:
                    # Enhanced keyword search with ranking
                    sql = """
                        SELECT 
                            case_number, court, decision_type, topic, summary, 
                            full_text, tags, source_url,
                            -- Calculate keyword relevance score
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
                            "keyword_score": row[8]
                        })
                    
                    return results
                    
        except Exception as e:
            logger.error(f"Error in keyword search: {e}")
            return []
    
    async def vector_similarity_search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Perform vector similarity search using stored embeddings"""
        try:
            # Get query embedding
            query_embedding = self.get_mistral_embedding(query)
            if not query_embedding:
                logger.warning("Could not get query embedding, falling back to keyword search")
                return await self.keyword_search(query, limit)
            
            with psycopg.connect(self.postgres_url) as conn:
                with conn.cursor() as cur:
                    # Get all cases with their vector embeddings
                    sql = """
                        SELECT 
                            case_number, court, decision_type, topic, summary, 
                            full_text, tags, source_url, vector_embedding
                        FROM ai.jurisprudence 
                        WHERE vector_embedding IS NOT NULL
                    """
                    cur.execute(sql)
                    
                    cases = []
                    similarities = []
                    
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
                            "vector_embedding": row[8]
                        }
                        
                        # Parse vector string and calculate similarity
                        case_vector = self.parse_vector_string(case['vector_embedding'])
                        if case_vector:
                            # Calculate cosine similarity
                            similarity = cosine_similarity(
                                [query_embedding], [case_vector]
                            )[0][0]
                            
                            cases.append(case)
                            similarities.append(similarity)
                    
                    # Sort by similarity and return top results
                    if cases:
                        sorted_indices = np.argsort(similarities)[::-1]  # Descending order
                        top_cases = []
                        
                        for i in sorted_indices[:limit]:
                            case = cases[i].copy()
                            case['vector_score'] = float(similarities[i])
                            top_cases.append(case)
                        
                        return top_cases
                    
                    return []
                    
        except Exception as e:
            logger.error(f"Error in vector similarity search: {e}")
            return []
    
    async def hybrid_search(self, query: str, limit: int = 20, 
                           vector_weight: float = 0.6, keyword_weight: float = 0.4) -> List[Dict[str, Any]]:
        """Perform hybrid search combining vector similarity and keyword matching"""
        try:
            logger.info(f"Performing hybrid search for: '{query}'")
            
            # Get results from both search methods
            keyword_results = await self.keyword_search(query, limit * 2)
            vector_results = await self.vector_similarity_search(query, limit * 2)
            
            # Create lookup dictionaries for scoring
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
                    all_cases[case_case]['vector_score'] = case['vector_score']
            
            # Calculate hybrid scores
            for case_number, case in all_cases.items():
                # Normalize scores to 0-1 range
                keyword_norm = min(case['keyword_score'] / 8.0, 1.0)  # Max possible keyword score is 8
                vector_norm = max(0, case['vector_score'])  # Vector scores are already 0-1
                
                # Calculate weighted hybrid score
                hybrid_score = (keyword_weight * keyword_norm) + (vector_weight * vector_norm)
                case['hybrid_score'] = hybrid_score
                
                # Add explanation of scoring
                case['score_breakdown'] = {
                    'keyword_score': case['keyword_score'],
                    'keyword_normalized': keyword_norm,
                    'vector_score': case['vector_score'],
                    'vector_normalized': vector_norm,
                    'hybrid_score': hybrid_score,
                    'weights': {'keyword': keyword_weight, 'vector': vector_weight}
                }
            
            # Sort by hybrid score and return top results
            sorted_cases = sorted(
                all_cases.values(), 
                key=lambda x: x['hybrid_score'], 
                reverse=True
            )
            
            return sorted_cases[:limit]
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            # Fallback to keyword search
            return await self.keyword_search(query, limit)
    
    async def semantic_search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Semantic search using vector similarity with enhanced context"""
        try:
            # Enhance query with legal context
            enhanced_query = self.enhance_legal_query(query)
            
            # Perform vector search with enhanced query
            results = await self.vector_similarity_search(enhanced_query, limit)
            
            # Add semantic context to results
            for result in results:
                result['semantic_context'] = self.extract_semantic_context(query, result)
                result['search_type'] = 'semantic'
            
            return results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def enhance_legal_query(self, query: str) -> str:
        """Enhance legal query with relevant context"""
        # Add common legal terms that might be related
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
        
        # Calculate relevance scores
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
    
    def print_search_results(self, results: List[Dict[str, Any]], search_type: str, query: str):
        """Print search results with scoring information"""
        print(f"\n{'='*80}")
        print(f"{search_type.upper()} SEARCH RESULTS FOR: '{query}'")
        print(f"{'='*80}")
        
        if not results:
            print("No results found.")
            return
        
        print(f"Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Case: {result['case_number']}")
            print(f"   Court: {result['court']}")
            print(f"   Type: {result['decision_type']}")
            print(f"   Topic: {result['topic'][:80]}...")
            print(f"   Summary: {result['summary'][:120]}...")
            
            # Show scoring information
            if 'hybrid_score' in result:
                print(f"   Hybrid Score: {result['hybrid_score']:.3f}")
                if 'score_breakdown' in result:
                    breakdown = result['score_breakdown']
                    print(f"   - Keyword: {breakdown['keyword_score']} (norm: {breakdown['keyword_normalized']:.3f})")
                    print(f"   - Vector: {breakdown['vector_score']:.3f} (norm: {breakdown['vector_normalized']:.3f})")
            
            elif 'vector_score' in result:
                print(f"   Vector Score: {result['vector_score']:.3f}")
            
            elif 'keyword_score' in result:
                print(f"   Keyword Score: {result['keyword_score']}")
            
            if result['tags']:
                print(f"   Tags: {', '.join(result['tags'][:5])}")
    
    async def demonstrate_hybrid_search(self):
        """Demonstrate the hybrid search capabilities"""
        print("HYBRID JURISPRUDENCE SEARCH SYSTEM - DEMONSTRATION")
        print("="*80)
        
        # Test queries
        test_queries = [
            "derechos fundamentales",
            "control constitucional",
            "debido proceso",
            "libertad de expresión"
        ]
        
        for query in test_queries:
            print(f"\n{'='*60}")
            print(f"TESTING QUERY: '{query}'")
            print(f"{'='*60}")
            
            # 1. Keyword-only search
            print("\n1. KEYWORD-ONLY SEARCH:")
            keyword_results = await self.keyword_search(query, 5)
            self.print_search_results(keyword_results, "Keyword", query)
            
            # 2. Vector similarity search
            print("\n2. VECTOR SIMILARITY SEARCH:")
            vector_results = await self.vector_similarity_search(query, 5)
            self.print_search_results(vector_results, "Vector", query)
            
            # 3. Hybrid search
            print("\n3. HYBRID SEARCH (60% vector, 40% keyword):")
            hybrid_results = await self.hybrid_search(query, 5, 0.6, 0.4)
            self.print_search_results(hybrid_results, "Hybrid", query)
            
            # 4. Semantic search
            print("\n4. SEMANTIC SEARCH:")
            semantic_results = await self.semantic_search(query, 5)
            self.print_search_results(semantic_results, "Semantic", query)
        
        print(f"\n{'='*80}")
        print("HYBRID SEARCH DEMONSTRATION COMPLETED!")
        print(f"{'='*80}")
        print("\nAI agents can now use:")
        print("✅ Keyword-based search with relevance scoring")
        print("✅ Vector similarity search for semantic understanding")
        print("✅ Hybrid search combining both approaches")
        print("✅ Semantic search with legal context enhancement")
        print("✅ Detailed scoring breakdowns for result ranking")
        print("\nThe hybrid search system provides the most accurate and relevant results!")

async def main():
    """Main demonstration function"""
    try:
        hybrid_search = HybridJurisprudenceSearch()
        await hybrid_search.demonstrate_hybrid_search()
        
    except Exception as e:
        print(f"Error during demonstration: {e}")

if __name__ == "__main__":
    asyncio.run(main())
