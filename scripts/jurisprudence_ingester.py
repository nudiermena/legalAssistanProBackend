#!/usr/bin/env python3
"""
Jurisprudence Ingester
Ingests constitutional court cases into the jurisprudence table with vector embeddings
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.supabase_knowledge_base import SupabaseLegalKnowledgeBase, KnowledgeType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class JurisprudenceIngester:
    """Ingests constitutional court cases into the jurisprudence table"""
    
    def __init__(self, mock_mode: bool = False):
        self.kb = SupabaseLegalKnowledgeBase(mock_mode=mock_mode)
        self.ingestion_stats = {
            "total_processed": 0,
            "successfully_added": 0,
            "errors": 0,
            "by_decision_type": {}
        }
    
    def load_scraped_cases(self, filename: str) -> List[Dict[str, Any]]:
        """Load scraped constitutional court cases from JSON file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Loaded {len(data)} scraped cases from {filename}")
            return data
            
        except Exception as e:
            logger.error(f"Error loading scraped cases: {e}")
            return []
    
    def prepare_jurisprudence_metadata(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare metadata for jurisprudence table insertion"""
        metadata = {
            "case_number": case.get("case_number"),
            "court": case.get("court", "Corte Constitucional"),
            "decision_type": case.get("decision_type"),
            "decision_date": case.get("decision_date"),
            "topic": case.get("topic"),
            "summary": case.get("summary"),
            "key_holdings": case.get("key_holdings", []),
            "legal_principles": case.get("legal_principles", []),
            "cited_laws": case.get("cited_laws", []),
            "cited_precedents": case.get("cited_precedents", []),
            "relevance_score": 0.85,  # Default high relevance for constitutional cases
            "tags": case.get("tags", []),
            "source_url": case.get("source_url"),
            "scraped_date": case.get("scraped_date")
        }
        
        # Remove None values
        metadata = {k: v for k, v in metadata.items() if v is not None}
        
        return metadata
    
    def prepare_content_for_insertion(self, case: Dict[str, Any]) -> str:
        """Prepare content for jurisprudence table insertion"""
        content_parts = []
        
        # Add case header
        if case.get("case_number"):
            content_parts.append(f"CASO: {case['case_number']}")
        
        if case.get("topic"):
            content_parts.append(f"TEMA: {case['topic']}")
        
        if case.get("decision_type"):
            content_parts.append(f"TIPO DE DECISIÓN: {case['decision_type']}")
        
        content_parts.append("")  # Empty line
        
        # Add summary if available
        if case.get("summary"):
            content_parts.append("RESUMEN:")
            content_parts.append(case["summary"])
            content_parts.append("")
        
        # Add key holdings
        if case.get("key_holdings"):
            content_parts.append("PRINCIPIOS JURÍDICOS CLAVE:")
            for holding in case["key_holdings"]:
                content_parts.append(f"• {holding}")
            content_parts.append("")
        
        # Add legal principles
        if case.get("legal_principles"):
            content_parts.append("PRINCIPIOS LEGALES:")
            for principle in case["legal_principles"]:
                content_parts.append(f"• {principle}")
            content_parts.append("")
        
        # Add cited laws
        if case.get("cited_laws"):
            content_parts.append("LEYES CITADAS:")
            for law in case["cited_laws"]:
                content_parts.append(f"• {law}")
            content_parts.append("")
        
        # Add full text
        if case.get("full_text"):
            content_parts.append("TEXTO COMPLETO:")
            content_parts.append(case["full_text"])
        
        return "\n".join(content_parts)
    
    async def add_case_to_jurisprudence_table(self, case: Dict[str, Any]) -> bool:
        """Add a single constitutional court case to the jurisprudence table"""
        try:
            # Prepare content and metadata
            content = self.prepare_content_for_insertion(case)
            metadata = self.prepare_jurisprudence_metadata(case)
            
            # Add to jurisprudence table using the knowledge base
            success = await self.kb.add_custom_knowledge(
                content=content,
                metadata=metadata,
                knowledge_type=KnowledgeType.JURISPRUDENCE
            )
            
            if success:
                self.ingestion_stats["successfully_added"] += 1
                
                # Track by decision type
                decision_type = metadata.get("decision_type", "unknown")
                self.ingestion_stats["by_decision_type"][decision_type] = self.ingestion_stats["by_decision_type"].get(decision_type, 0) + 1
                
                logger.info(f"Successfully added case: {metadata.get('case_number', 'Unknown')}")
                return True
            else:
                logger.error(f"Failed to add case: {metadata.get('case_number', 'Unknown')}")
                self.ingestion_stats["errors"] += 1
                return False
                
        except Exception as e:
            logger.error(f"Error adding case {case.get('case_number', 'Unknown')}: {e}")
            self.ingestion_stats["errors"] += 1
            return False
    
    async def ingest_jurisprudence(self, scraped_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Ingest all scraped constitutional court cases"""
        logger.info(f"Starting jurisprudence ingestion with {len(scraped_cases)} cases...")
        
        # Filter out invalid cases
        valid_cases = [case for case in scraped_cases if case.get("full_text") and len(case.get("full_text", "")) > 100]
        logger.info(f"Found {len(valid_cases)} valid cases for ingestion")
        
        # Process cases in batches
        batch_size = 5  # Smaller batch size for jurisprudence due to complexity
        total_batches = (len(valid_cases) + batch_size - 1) // batch_size
        
        for i in range(0, len(valid_cases), batch_size):
            batch = valid_cases[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} cases)")
            
            # Process batch concurrently
            tasks = [self.add_case_to_jurisprudence_table(case) for case in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log batch results
            successful = sum(1 for r in results if r is True)
            failed = len(batch) - successful
            logger.info(f"Batch {batch_num}: {successful} successful, {failed} failed")
            
            # Small delay between batches to avoid overwhelming the database
            if batch_num < total_batches:
                await asyncio.sleep(2)
        
        self.ingestion_stats["total_processed"] = len(valid_cases)
        logger.info("Jurisprudence ingestion completed")
        return self.ingestion_stats
    
    def generate_ingestion_report(self) -> Dict[str, Any]:
        """Generate ingestion statistics report"""
        report = {
            "ingestion_timestamp": datetime.now().isoformat(),
            "total_cases_processed": self.ingestion_stats["total_processed"],
            "successfully_added": self.ingestion_stats["successfully_added"],
            "errors": self.ingestion_stats["errors"],
            "success_rate": self.ingestion_stats["successfully_added"] / self.ingestion_stats["total_processed"] if self.ingestion_stats["total_processed"] > 0 else 0,
            "by_decision_type": self.ingestion_stats["by_decision_type"]
        }
        
        return report

async def main():
    """Main ingestion function"""
    # Initialize ingester
    ingester = JurisprudenceIngester(mock_mode=False)
    
    # Find the most recent constitutional court cases file
    data_dir = Path("data_pipeline_output")
    case_files = list(data_dir.glob("constitutional_court_cases_*.json"))
    
    if not case_files:
        logger.error("No constitutional court cases files found")
        return
    
    # Sort by modification time and get the most recent
    latest_file = max(case_files, key=lambda f: f.stat().st_mtime)
    logger.info(f"Using latest cases file: {latest_file}")
    
    # Load scraped cases
    scraped_cases = ingester.load_scraped_cases(str(latest_file))
    if not scraped_cases:
        logger.error("No scraped cases to ingest")
        return
    
    # Ingest jurisprudence
    ingestion_stats = await ingester.ingest_jurisprudence(scraped_cases)
    
    # Generate and display report
    report = ingester.generate_ingestion_report()
    
    print("\n" + "="*60)
    print("JURISPRUDENCE INGESTION REPORT")
    print("="*60)
    print(f"Total cases processed: {report['total_cases_processed']}")
    print(f"Successfully added: {report['successfully_added']}")
    print(f"Errors: {report['errors']}")
    print(f"Success rate: {report['success_rate']:.2%}")
    
    if report['by_decision_type']:
        print("\nCases by Decision Type:")
        for decision_type, count in report['by_decision_type'].items():
            print(f"  {decision_type}: {count}")
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"data_pipeline_output/jurisprudence_ingestion_report_{timestamp}.json"
    
    os.makedirs(os.path.dirname(report_filename), exist_ok=True)
    with open(report_filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\nReport saved to: {report_filename}")

if __name__ == "__main__":
    asyncio.run(main())
