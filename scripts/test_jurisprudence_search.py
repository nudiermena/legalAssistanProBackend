#!/usr/bin/env python3
"""
Test Jurisprudence Search
Verifies ingested data and demonstrates search functionality for AI agents
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

class JurisprudenceSearchTester:
    """Test class for jurisprudence search functionality"""
    
    def __init__(self):
        self.postgres_url = POSTGRES_URL
    
    async def test_database_connection(self) -> bool:
        """Test database connection"""
        try:
            with psycopg.connect(self.postgres_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT version()")
                    version = cur.fetchone()
                    logger.info(f"Database connection successful: {version[0]}")
                    return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    async def verify_ingested_data(self) -> Dict[str, Any]:
        """Verify that the jurisprudence data was properly ingested"""
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
                    
                    # Sample case data
                    cur.execute("""
                        SELECT case_number, court, decision_type, topic, summary, tags
                        FROM jurisprudence 
                        LIMIT 5
                    """)
                    sample_cases = cur.fetchall()
                    
                    verification_results = {
                        "total_cases": total_cases,
                        "by_decision_type": by_decision_type,
                        "by_court": by_court,
                        "with_vectors": with_vectors,
                        "sample_cases": sample_cases
                    }
                    
                    return verification_results
                    
        except Exception as e:
            logger.error(f"Error verifying ingested data: {e}")
            return {}
    
    async def test_text_search(self, query: str) -> List[Dict[str, Any]]:
        """Test text search functionality"""
        try:
            with psycopg.connect(self.postgres_url) as conn:
                with conn.cursor() as cur:
                    # Search in topic, summary, and full_text
                    sql = """
                        SELECT case_number, court, decision_type, topic, summary, tags
                        FROM jurisprudence 
                        WHERE 
                            topic ILIKE %s OR 
                            summary ILIKE %s OR 
                            full_text ILIKE %s
                        LIMIT 10
                    """
                    search_pattern = f"%{query}%"
                    cur.execute(sql, (search_pattern, search_pattern, search_pattern))
                    
                    results = []
                    for row in cur.fetchall():
                        results.append({
                            "case_number": row[0],
                            "court": row[1],
                            "decision_type": row[2],
                            "topic": row[3],
                            "summary": row[4],
                            "tags": row[5]
                        })
                    
                    return results
                    
        except Exception as e:
            logger.error(f"Error in text search: {e}")
            return []
    
    async def test_tag_search(self, tag: str) -> List[Dict[str, Any]]:
        """Test tag-based search functionality"""
        try:
            with psycopg.connect(self.postgres_url) as conn:
                with conn.cursor() as cur:
                    # Search by tag
                    sql = """
                        SELECT case_number, court, decision_type, topic, summary, tags
                        FROM jurisprudence 
                        WHERE %s = ANY(tags)
                        LIMIT 10
                    """
                    cur.execute(sql, (tag,))
                    
                    results = []
                    for row in cur.fetchall():
                        results.append({
                            "case_number": row[0],
                            "court": row[1],
                            "decision_type": row[2],
                            "topic": row[3],
                            "summary": row[4],
                            "tags": row[5]
                        })
                    
                    return results
                    
        except Exception as e:
            logger.error(f"Error in tag search: {e}")
            return []
    
    async def test_decision_type_search(self, decision_type: str) -> List[Dict[str, Any]]:
        """Test decision type search functionality"""
        try:
            with psycopg.connect(self.postgres_url) as conn:
                with conn.cursor() as cur:
                    # Search by decision type
                    sql = """
                        SELECT case_number, court, decision_type, topic, summary, tags
                        FROM jurisprudence 
                        WHERE decision_type = %s
                        LIMIT 10
                    """
                    cur.execute(sql, (decision_type,))
                    
                    results = []
                    for row in cur.fetchall():
                        results.append({
                            "case_number": row[0],
                            "court": row[1],
                            "decision_type": row[2],
                            "topic": row[3],
                            "summary": row[4],
                            "tags": row[5]
                        })
                    
                    return results
                    
        except Exception as e:
            logger.error(f"Error in decision type search: {e}")
            return []
    
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
            if result['topic']:
                print(f"   Topic: {result['topic'][:100]}...")
            if result['summary']:
                print(f"   Summary: {result['summary'][:150]}...")
            if result['tags']:
                print(f"   Tags: {', '.join(result['tags'][:5])}")
    
    async def run_comprehensive_test(self):
        """Run comprehensive tests of the jurisprudence search functionality"""
        print("JURISPRUDENCE SEARCH FUNCTIONALITY TEST")
        print("="*60)
        
        # Test database connection
        print("\n1. Testing database connection...")
        if not await self.test_database_connection():
            print("❌ Database connection failed!")
            return
        print("✅ Database connection successful!")
        
        # Verify ingested data
        print("\n2. Verifying ingested data...")
        verification = await self.verify_ingested_data()
        if verification:
            print("✅ Data verification successful!")
            print(f"   Total cases: {verification['total_cases']}")
            print(f"   By decision type: {verification['by_decision_type']}")
            print(f"   By court: {verification['by_court']}")
            print(f"   Cases with vectors: {verification['with_vectors']}")
            
            print("\n   Sample cases:")
            for i, case in enumerate(verification['sample_cases'][:3], 1):
                print(f"   {i}. {case[0]} - {case[2]} - {case[3][:50]}...")
        else:
            print("❌ Data verification failed!")
            return
        
        # Test text search
        print("\n3. Testing text search functionality...")
        text_search_queries = [
            "derechos fundamentales",
            "control constitucional",
            "debido proceso"
        ]
        
        for query in text_search_queries:
            results = await self.test_text_search(query)
            self.print_search_results(results, "Text", query)
        
        # Test tag search
        print("\n4. Testing tag search functionality...")
        tag_search_queries = [
            "tutela",
            "sentencia",
            "derechos_fundamentales"
        ]
        
        for tag in tag_search_queries:
            results = await self.test_tag_search(tag)
            self.print_search_results(results, "Tag", tag)
        
        # Test decision type search
        print("\n5. Testing decision type search functionality...")
        decision_types = ["tutela", "sentencia"]
        
        for decision_type in decision_types:
            results = await self.test_decision_type_search(decision_type)
            self.print_search_results(results, "Decision Type", decision_type)
        
        print("\n" + "="*60)
        print("JURISPRUDENCE SEARCH TESTING COMPLETED!")
        print("="*60)
        print("\nThe jurisprudence table is now ready for AI agents to search!")
        print("AI agents can use:")
        print("- Text search in topic, summary, and full_text fields")
        print("- Tag-based filtering")
        print("- Decision type filtering")
        print("- Vector similarity search (when needed)")

async def main():
    """Main test function"""
    try:
        tester = JurisprudenceSearchTester()
        await tester.run_comprehensive_test()
        
    except Exception as e:
        print(f"Error during testing: {e}")

if __name__ == "__main__":
    asyncio.run(main())
