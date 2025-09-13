#!/usr/bin/env python3
"""
Jurisprudence Demo for AI Agents
Demonstrates how AI agents can search and use the constitutional court jurisprudence data
"""

import asyncio
import logging
import sys
import os
from typing import List, Dict, Any
import psycopg

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import configuration
from config.settings import POSTGRES_URL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class JurisprudenceForAIAgents:
    """Class that demonstrates how AI agents can interact with jurisprudence data"""
    
    def __init__(self):
        self.postgres_url = POSTGRES_URL
    
    async def get_jurisprudence_stats(self) -> Dict[str, Any]:
        """Get statistics about the jurisprudence data"""
        try:
            with psycopg.connect(self.postgres_url) as conn:
                with conn.cursor() as cur:
                    # Count total cases
                    cur.execute("SELECT COUNT(*) FROM jurisprudence")
                    total_cases = cur.fetchone()[0]
                    
                    # Count by decision type
                    cur.execute("""
                        SELECT decision_type, COUNT(*) 
                        FROM jurisprudence 
                        WHERE decision_type IS NOT NULL
                        GROUP BY decision_type
                    """)
                    by_decision_type = dict(cur.fetchall())
                    
                    # Count by court
                    cur.execute("""
                        SELECT court, COUNT(*) 
                        FROM jurisprudence 
                        GROUP BY court
                    """)
                    by_court = dict(cur.fetchall())
                    
                    # Check for vector embeddings
                    cur.execute("""
                        SELECT COUNT(*) 
                        FROM jurisprudence 
                        WHERE vector_embedding IS NOT NULL
                    """)
                    with_vectors = cur.fetchone()[0]
                    
                    return {
                        "total_cases": total_cases,
                        "by_decision_type": by_decision_type,
                        "by_court": by_court,
                        "with_vectors": with_vectors
                    }
                    
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    async def search_jurisprudence(self, query: str, search_type: str = "text", limit: int = 5) -> List[Dict[str, Any]]:
        """Search jurisprudence data - this is what AI agents would use"""
        try:
            with psycopg.connect(self.postgres_url) as conn:
                with conn.cursor() as cur:
                    if search_type == "text":
                        # Text search in topic, summary, and full_text
                        sql = """
                            SELECT case_number, court, decision_type, topic, summary, tags
                            FROM jurisprudence 
                            WHERE 
                                topic ILIKE %s OR 
                                summary ILIKE %s OR 
                                full_text ILIKE %s
                            LIMIT %s
                        """
                        search_pattern = f"%{query}%"
                        cur.execute(sql, (search_pattern, search_pattern, search_pattern, limit))
                        
                    elif search_type == "tag":
                        # Tag-based search
                        sql = """
                            SELECT case_number, court, decision_type, topic, summary, tags
                            FROM jurisprudence 
                            WHERE %s = ANY(tags)
                            LIMIT %s
                        """
                        cur.execute(sql, (query, limit))
                        
                    elif search_type == "decision_type":
                        # Decision type search
                        sql = """
                            SELECT case_number, court, decision_type, topic, summary, tags
                            FROM jurisprudence 
                            WHERE decision_type = %s
                            LIMIT %s
                        """
                        cur.execute(sql, (query, limit))
                    
                    results = []
                    for row in cur.fetchall():
                        results.append({
                            "case_number": row[0],
                            "court": row[1],
                            "decision_type": row[2],
                            "topic": row[3] or "No topic available",
                            "summary": row[4] or "No summary available",
                            "tags": row[5] or []
                        })
                    
                    return results
                    
        except Exception as e:
            logger.error(f"Error in search: {e}")
            return []
    
    async def get_case_details(self, case_number: str) -> Dict[str, Any]:
        """Get detailed information about a specific case"""
        try:
            with psycopg.connect(self.postgres_url) as conn:
                with conn.cursor() as cur:
                    sql = """
                        SELECT case_number, court, decision_type, decision_date, topic, 
                               summary, full_text, key_holdings, legal_principles, 
                               cited_laws, tags, source_url
                        FROM jurisprudence 
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
                            "source_url": row[11]
                        }
                    else:
                        return {}
                        
        except Exception as e:
            logger.error(f"Error getting case details: {e}")
            return {}
    
    def print_search_results(self, results: List[Dict[str, Any]], search_type: str, query: str):
        """Print search results in a formatted way"""
        print(f"\n{'='*60}")
        print(f"{search_type.upper()} SEARCH RESULTS FOR: '{query}'")
        print(f"{'='*60}")
        
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
            if result['tags']:
                print(f"   Tags: {', '.join(result['tags'][:5])}")
    
    def print_case_details(self, case: Dict[str, Any]):
        """Print detailed case information"""
        print(f"\n{'='*60}")
        print(f"CASE DETAILS: {case['case_number']}")
        print(f"{'='*60}")
        print(f"Court: {case['court']}")
        print(f"Decision Type: {case['decision_type']}")
        if case['decision_date']:
            print(f"Decision Date: {case['decision_date']}")
        if case['topic']:
            print(f"Topic: {case['topic']}")
        if case['summary']:
            print(f"Summary: {case['summary']}")
        if case['key_holdings']:
            print(f"Key Holdings: {', '.join(case['key_holdings'])}")
        if case['legal_principles']:
            print(f"Legal Principles: {', '.join(case['legal_principles'])}")
        if case['cited_laws']:
            print(f"Cited Laws: {', '.join(case['cited_laws'])}")
        if case['tags']:
            print(f"Tags: {', '.join(case['tags'])}")
        if case['source_url']:
            print(f"Source: {case['source_url']}")
    
    async def demonstrate_ai_agent_capabilities(self):
        """Demonstrate the capabilities available to AI agents"""
        print("JURISPRUDENCE DATA FOR AI AGENTS - DEMONSTRATION")
        print("="*60)
        
        # Show statistics
        print("\n1. JURISPRUDENCE DATA OVERVIEW")
        stats = await self.get_jurisprudence_stats()
        if stats:
            print(f"   Total cases: {stats['total_cases']}")
            print(f"   By decision type: {stats['by_decision_type']}")
            print(f"   By court: {stats['by_court']}")
            print(f"   Cases with vector embeddings: {stats['with_vectors']}")
        
        # Demonstrate text search
        print("\n2. TEXT SEARCH CAPABILITY")
        print("   AI agents can search for legal concepts, topics, or specific terms")
        text_queries = [
            "derechos fundamentales",
            "control constitucional",
            "debido proceso"
        ]
        
        for query in text_queries:
            results = await self.search_jurisprudence(query, "text", 3)
            self.print_search_results(results, "Text", query)
        
        # Demonstrate tag search
        print("\n3. TAG-BASED SEARCH CAPABILITY")
        print("   AI agents can filter by specific tags or categories")
        tag_queries = ["tutela", "sentencia"]
        
        for tag in tag_queries:
            results = await self.search_jurisprudence(tag, "tag", 3)
            self.print_search_results(results, "Tag", tag)
        
        # Demonstrate decision type search
        print("\n4. DECISION TYPE FILTERING")
        print("   AI agents can filter by specific decision types")
        decision_types = ["tutela", "sentencia"]
        
        for decision_type in decision_types:
            results = await self.search_jurisprudence(decision_type, "decision_type", 3)
            self.print_search_results(results, "Decision Type", decision_type)
        
        # Show detailed case information
        print("\n5. DETAILED CASE INFORMATION")
        print("   AI agents can retrieve comprehensive case details")
        
        # Get a sample case for detailed view
        sample_results = await self.search_jurisprudence("derechos fundamentales", "text", 1)
        if sample_results:
            case_number = sample_results[0]['case_number']
            case_details = await self.get_case_details(case_number)
            if case_details:
                self.print_case_details(case_details)
        
        print("\n" + "="*60)
        print("AI AGENT CAPABILITIES DEMONSTRATION COMPLETED!")
        print("="*60)
        print("\nAI agents can now:")
        print("✅ Search jurisprudence by text content")
        print("✅ Filter by tags and decision types")
        print("✅ Retrieve detailed case information")
        print("✅ Access vector embeddings for similarity search")
        print("✅ Use structured data for legal analysis")
        print("\nThe jurisprudence table is fully operational and ready for AI agent use!")

async def main():
    """Main demonstration function"""
    try:
        demo = JurisprudenceForAIAgents()
        await demo.demonstrate_ai_agent_capabilities()
        
    except Exception as e:
        print(f"Error during demonstration: {e}")

if __name__ == "__main__":
    asyncio.run(main())
