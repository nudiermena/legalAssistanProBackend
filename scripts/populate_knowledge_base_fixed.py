#!/usr/bin/env python3
"""
Fixed Knowledge Base Population Script
Populates Supabase with processed Colombian legal documents
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

from config.supabase_knowledge_base import (
    SupabaseLegalKnowledgeBase, 
    KnowledgeType
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FixedKnowledgePopulator:
    """Fixed knowledge base population with processed legal documents"""
    
    def __init__(self, mock_mode: bool = False):
        self.kb = SupabaseLegalKnowledgeBase(mock_mode=mock_mode)
        self.population_stats = {
            "total_added": 0,
            "errors": 0,
            "by_type": {}
        }
    
    def load_processed_documents(self, filename: str) -> List[Dict[str, Any]]:
        """Load processed documents from JSON file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Loaded {len(data)} processed documents from {filename}")
            return data
            
        except Exception as e:
            logger.error(f"Error loading processed documents: {e}")
            return []
    
    def map_document_type_to_knowledge_type(self, doc_type: str, legal_area: str) -> KnowledgeType:
        """Map document type to knowledge base type"""
        mapping = {
            "law": KnowledgeType.LEGAL_DOCUMENTS,
            "decree": KnowledgeType.LEGAL_DOCUMENTS,
            "resolution": KnowledgeType.REGULATORY_FRAMEWORKS,
            "constitutional_decision": KnowledgeType.JURISPRUDENCE,
            "supreme_decision": KnowledgeType.JURISPRUDENCE,
            "administrative_decision": KnowledgeType.JURISPRUDENCE
        }
        
        # Special mappings based on legal area
        if legal_area == "intellectual_property":
            return KnowledgeType.PATENT_KNOWLEDGE
        elif legal_area == "civil" and "contrato" in doc_type.lower():
            return KnowledgeType.CONTRACT_KNOWLEDGE
        elif legal_area == "administrative":
            return KnowledgeType.COMPLIANCE_KNOWLEDGE
        
        return mapping.get(doc_type, KnowledgeType.LEGAL_DOCUMENTS)
    
    def prepare_metadata(self, processed_doc: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare metadata for database insertion"""
        original_doc = processed_doc.get("original_doc", {})
        structured_data = processed_doc.get("structured_data", {})
        
        metadata = {
            "title": original_doc.get("title", ""),
            "source_url": original_doc.get("source_url", ""),
            "document_number": structured_data.get("document_number"),
            "year": structured_data.get("year"),
            "document_type": structured_data.get("document_type"),
            "legal_area": structured_data.get("legal_area"),
            "authority": original_doc.get("authority"),
            "quality_score": processed_doc.get("quality_score", 0.0),
            "processing_status": processed_doc.get("processing_status"),
            "document_hash": processed_doc.get("document_hash"),
            "articles": structured_data.get("articles", []),
            "dates": structured_data.get("dates", []),
            "scraped_date": original_doc.get("metadata", {}).get("scraped_date"),
            "word_count": len(processed_doc.get("processed_content", "").split())
        }
        
        # Remove None values
        metadata = {k: v for k, v in metadata.items() if v is not None}
        
        return metadata
    
    def prepare_content_for_insertion(self, processed_doc: Dict[str, Any]) -> str:
        """Prepare content for knowledge base insertion"""
        content = processed_doc.get("processed_content", "")
        title = processed_doc.get("original_doc", {}).get("title", "")
        
        # Combine title and content for better searchability
        if title and content:
            return f"Título: {title}\n\nContenido:\n{content}"
        elif title:
            return title
        else:
            return content
    
    async def add_document_to_knowledge_base(self, processed_doc: Dict[str, Any]) -> bool:
        """Add a single processed document to the knowledge base"""
        try:
            # Prepare content and metadata
            content = self.prepare_content_for_insertion(processed_doc)
            metadata = self.prepare_metadata(processed_doc)
            
            # Determine knowledge type
            doc_type = metadata.get("document_type", "unknown")
            legal_area = metadata.get("legal_area", "general")
            knowledge_type = self.map_document_type_to_knowledge_type(doc_type, legal_area)
            
            # Add to knowledge base
            success = await self.kb.add_custom_knowledge(
                content=content,
                metadata=metadata,
                knowledge_type=knowledge_type
            )
            
            if success:
                self.population_stats["total_added"] += 1
                knowledge_type_str = knowledge_type.value
                self.population_stats["by_type"][knowledge_type_str] = self.population_stats["by_type"].get(knowledge_type_str, 0) + 1
                logger.info(f"Successfully added document: {metadata.get('title', 'Unknown')}")
                return True
            else:
                logger.error(f"Failed to add document: {metadata.get('title', 'Unknown')}")
                self.population_stats["errors"] += 1
                return False
                
        except Exception as e:
            logger.error(f"Error adding document {processed_doc.get('original_doc', {}).get('title', 'Unknown')}: {e}")
            self.population_stats["errors"] += 1
            return False
    
    async def populate_knowledge_base(self, processed_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Populate knowledge base with all processed documents"""
        logger.info(f"Starting knowledge base population with {len(processed_documents)} documents...")
        
        # Filter out failed documents
        valid_documents = [doc for doc in processed_documents if doc.get("processing_status") != "failed"]
        logger.info(f"Found {len(valid_documents)} valid documents for population")
        
        # Process documents in batches
        batch_size = 10
        total_batches = (len(valid_documents) + batch_size - 1) // batch_size
        
        for i in range(0, len(valid_documents), batch_size):
            batch = valid_documents[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} documents)")
            
            # Process batch concurrently
            tasks = [self.add_document_to_knowledge_base(doc) for doc in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log batch results
            successful = sum(1 for r in results if r is True)
            failed = len(batch) - successful
            logger.info(f"Batch {batch_num}: {successful} successful, {failed} failed")
            
            # Small delay between batches to avoid overwhelming the database
            if batch_num < total_batches:
                await asyncio.sleep(1)
        
        logger.info("Knowledge base population completed")
        return self.population_stats
    
    def generate_population_report(self) -> Dict[str, Any]:
        """Generate population statistics report"""
        report = {
            "population_timestamp": datetime.now().isoformat(),
            "total_documents_processed": self.population_stats["total_added"] + self.population_stats["errors"],
            "successfully_added": self.population_stats["total_added"],
            "errors": self.population_stats["errors"],
            "success_rate": self.population_stats["total_added"] / (self.population_stats["total_added"] + self.population_stats["errors"]) if (self.population_stats["total_added"] + self.population_stats["errors"]) > 0 else 0,
            "by_knowledge_type": self.population_stats["by_type"]
        }
        
        return report

async def main():
    """Main population function"""
    # Initialize populator
    populator = FixedKnowledgePopulator(mock_mode=False)
    
    # Load processed documents
    input_file = "data_pipeline_output/processed_legal_documents_fixed.json"
    
    if not os.path.exists(input_file):
        logger.error(f"Processed documents file not found: {input_file}")
        return
    
    processed_documents = populator.load_processed_documents(input_file)
    if not processed_documents:
        logger.error("No processed documents to populate")
        return
    
    # Populate knowledge base
    population_stats = await populator.populate_knowledge_base(processed_documents)
    
    # Generate and display report
    report = populator.generate_population_report()
    
    print("\n" + "="*60)
    print("KNOWLEDGE BASE POPULATION REPORT")
    print("="*60)
    print(f"Total documents processed: {report['total_documents_processed']}")
    print(f"Successfully added: {report['successfully_added']}")
    print(f"Errors: {report['errors']}")
    print(f"Success rate: {report['success_rate']:.2%}")
    
    if report['by_knowledge_type']:
        print("\nDocuments by Knowledge Type:")
        for knowledge_type, count in report['by_knowledge_type'].items():
            print(f"  {knowledge_type}: {count}")
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"data_pipeline_output/knowledge_base_population_report_{timestamp}.json"
    
    os.makedirs(os.path.dirname(report_filename), exist_ok=True)
    with open(report_filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\nReport saved to: {report_filename}")

if __name__ == "__main__":
    asyncio.run(main())
