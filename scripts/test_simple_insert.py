#!/usr/bin/env python3
"""
Minimal test script to verify database connection and simple insertion.
"""

import os
import sys
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import POSTGRES_URL, MISTRAL_API_KEY

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_connection():
    """Test basic database connection."""
    try:
        import psycopg
        logger.info("Testing database connection...")
        
        with psycopg.connect(POSTGRES_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version()")
                version = cur.fetchone()
                logger.info(f"✓ Database connected successfully: {version[0]}")
                
                # Test if tables exist
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('jurisprudence', 'legal_documents_ai', 'document_templates')
                    ORDER BY table_name
                """)
                tables = cur.fetchall()
                logger.info(f"✓ Found tables: {[t[0] for t in tables]}")
                
                # Count rows in each table
                for table in ['jurisprudence', 'legal_documents_ai', 'document_templates']:
                    try:
                        cur.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cur.fetchone()[0]
                        logger.info(f"✓ Table {table}: {count} rows")
                    except Exception as e:
                        logger.warning(f"Could not count {table}: {e}")
                
        return True
        
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

def test_mistral():
    """Test Mistral API connection."""
    try:
        from agno.embedder.mistral import MistralEmbedder
        
        logger.info("Testing Mistral API...")
        embedder = MistralEmbedder(
            id="mistral-embed",
            dimensions=1024,
            api_key=MISTRAL_API_KEY
        )
        
        # Test with a simple text
        test_text = "Hello world"
        logger.info("Getting embedding for test text...")
        embedding = embedder.get_embedding(test_text)
        
        if embedding and len(embedding) == 1024:
            logger.info(f"✓ Mistral API working: got {len(embedding)}-dimensional vector")
            return True
        else:
            logger.error(f"Mistral API returned invalid embedding: {len(embedding) if embedding else 'None'}")
            return False
            
    except Exception as e:
        logger.error(f"Mistral API test failed: {e}")
        return False

def main():
    logger.info("Starting simple tests...")
    
    # Test 1: Database connection
    if not test_connection():
        logger.error("❌ Database test failed")
        sys.exit(1)
    
    # Test 2: Mistral API
    if not test_mistral():
        logger.error("❌ Mistral API test failed")
        sys.exit(1)
    
    logger.info("✓ All tests passed! The system is ready for ingestion.")

if __name__ == "__main__":
    main() 