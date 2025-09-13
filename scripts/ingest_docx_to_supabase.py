#!/usr/bin/env python3
"""
Ingest local .doc/.docx documents into Supabase document_templates table using Agno DocxKnowledgeBase.

Usage:
  python scripts/ingest_docx_to_supabase.py --path "C:\\Users\\nudie\\OneDrive\\Documentos\\Derecho\\Formatos" --recreate false

Requirements:
  pip install agno textract python-docx
"""

import os
import sys
import time
import random
import logging
import argparse
from pathlib import Path
from typing import List, Optional

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import POSTGRES_URL, MISTRAL_API_KEY
from agno.knowledge.docx import DocxKnowledgeBase
from agno.vectordb.pgvector import PgVector, SearchType
from agno.embedder.mistral import MistralEmbedder

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_docx_files(directory: str) -> List[Path]:
    """Find all .doc and .docx files in the given directory and subdirectories."""
    docx_files = []
    directory_path = Path(directory)
    
    if not directory_path.exists():
        logger.error(f"Directory {directory} does not exist")
        return []
    
    # Search for .doc and .docx files recursively
    for file_path in directory_path.rglob("*.doc*"):
        if file_path.suffix.lower() in ['.doc', '.docx']:
            docx_files.append(file_path)
    
    logger.info(f"Found {len(docx_files)} DOCX files in {directory}")
    return docx_files

def process_documents_manually(docx_files: List[Path], delay: float, recreate: bool = False):
    """Manually process documents with delays between each to avoid rate limits."""
    # Temporarily unset OPENAI_API_KEY to force use of Mistral
    original_openai_key = os.environ.get('OPENAI_API_KEY')
    if original_openai_key:
        logger.info("Temporarily unsetting OPENAI_API_KEY to force use of Mistral")
        del os.environ['OPENAI_API_KEY']
    
    try:
        # Convert POSTGRES_URL to the format expected by PgVector
        db_url = POSTGRES_URL
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
        
        # Create Mistral embedder
        logger.info("Creating Mistral embedder...")
        mistral_embedder = MistralEmbedder(
            id="mistral-embed",
            dimensions=1024,  # mistral-embed default is 1024 dimensions
            api_key=MISTRAL_API_KEY
        )
        logger.info("Mistral embedder created successfully")
        
        # Create PgVector instance for document_templates table with the embedder
        vector_db = PgVector(
            table_name="document_templates",
            db_url=db_url,
            search_type=SearchType.hybrid,
            embedder=mistral_embedder  # Pass the embedder here
        )
        
        if recreate:
            logger.info("Recreating knowledge base table...")
            try:
                vector_db.drop()
                logger.info("Table dropped successfully")
            except Exception as e:
                logger.warning(f"Could not drop table: {e}")
        
        total_files = len(docx_files)
        processed_count = 0
        failed_count = 0
        
        logger.info(f"Starting manual processing of {total_files} documents with {delay}s delay between each...")
        
        for i, file_path in enumerate(docx_files):
            try:
                logger.info(f"Processing document {i+1}/{total_files}: {file_path.name}")
                
                # Create a single document knowledge instance
                single_kb = DocxKnowledgeBase(
                    path=str(file_path),
                    vector_db=vector_db
                )
                
                # Load this single document
                single_kb.load(recreate=False, upsert=True)
                
                processed_count += 1
                logger.info(f"Successfully processed: {file_path.name}")
                
                # Add delay between documents (except for the last one)
                if i < total_files - 1:
                    logger.info(f"Waiting {delay}s before next document...")
                    time.sleep(delay)
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to process {file_path.name}: {e}")
                
                # If it's a rate limit error, wait longer
                if "rate limit" in str(e).lower() or "429" in str(e):
                    logger.warning("Rate limit detected, waiting 30 seconds before continuing...")
                    time.sleep(30)
                elif "dimensions" in str(e).lower():
                    logger.error(f"Dimension error with {file_path.name}: {e}")
                    continue
                else:
                    logger.error(f"Unexpected error with {file_path.name}: {e}")
                    continue
        
        logger.info(f"Processing complete. Successfully processed: {processed_count}, Failed: {failed_count}")
        return processed_count, failed_count
        
    finally:
        # Restore OPENAI_API_KEY if it was set
        if original_openai_key:
            logger.info("Restoring OPENAI_API_KEY")
            os.environ['OPENAI_API_KEY'] = original_openai_key

def main():
    parser = argparse.ArgumentParser(description="Ingest DOCX into Supabase document_templates table")
    parser.add_argument("--path", default=None, help="Path to directory with .doc/.docx files")
    parser.add_argument("--recreate", default="false", choices=["true", "false"], help="Recreate table before load")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between documents in seconds (default: 2.0)")
    args = parser.parse_args()
    
    # Check if MISTRAL_API_KEY is set
    if not MISTRAL_API_KEY:
        logger.error("MISTRAL_API_KEY not found in environment variables")
        sys.exit(1)
    
    # Check if POSTGRES_URL is set
    if not POSTGRES_URL:
        logger.error("POSTGRES_URL not found in environment variables")
        sys.exit(1)
    
    # Parse arguments
    recreate = args.recreate.lower() == "true"
    delay = args.delay
    
    # Find DOCX files
    if args.path:
        docx_files = find_docx_files(args.path)
        if not docx_files:
            logger.error("No DOCX files found in the specified directory")
            sys.exit(1)
    else:
        logger.error("Please specify a path to the directory containing DOCX files")
        sys.exit(1)
    
    logger.info(f"Found {len(docx_files)} DOCX files to process")
    logger.info(f"Configuration: recreate={recreate}, delay={delay}s")
    
    try:
        # Process documents manually with delays
        processed, failed = process_documents_manually(docx_files, delay, recreate)
        
        if failed > 0:
            logger.warning(f"Completed with {failed} failures. Check logs for details.")
            sys.exit(1)
        else:
            logger.info("All documents processed successfully!")
            
    except Exception as e:
        logger.error(f"Error during document processing: {e}")
        if "rate limit" in str(e).lower() or "429" in str(e):
            logger.info("Rate limit hit. Consider waiting a few minutes and running the script again.")
            logger.info("You can also try running with --delay 5.0 to add longer delays between documents.")
        sys.exit(1)

if __name__ == "__main__":
    main()

