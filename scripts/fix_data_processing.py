#!/usr/bin/env python3
"""
Fixed Data Processing Pipeline for Colombian Legal Database
Handles document parsing, structuring, and quality validation
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import os
import sys
import re
from dataclasses import dataclass
from enum import Enum
import hashlib
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.supabase_knowledge_base import KnowledgeType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProcessingStatus(Enum):
    """Document processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    VALIDATED = "validated"

@dataclass
class ProcessedDocument:
    """Processed legal document with enhanced metadata"""
    original_doc: Dict[str, Any]
    processed_content: str
    structured_data: Dict[str, Any]
    quality_score: float
    processing_status: ProcessingStatus
    validation_errors: List[str]
    document_hash: str
    processing_timestamp: str

class LegalDocumentProcessor:
    """Processes and validates legal documents"""
    
    def __init__(self):
        # Legal document patterns
        self.legal_patterns = {
            "law": r"(?:Ley|LEY)\s+(\d+)\s+de\s+(\d{4})",
            "decree": r"(?:Decreto|DECRETO)\s+(\d+)\s+de\s+(\d{4})",
            "resolution": r"(?:Resolución|RESOLUCIÓN)\s+(\d+)\s+de\s+(\d{4})",
            "constitutional_court": r"(?:Sentencia|SENTENCIA)\s+([CT]-\d+/\d{4})",
            "supreme_court": r"(?:Sentencia|SENTENCIA)\s+([A-Z]+-\d+/\d{4})",
            "date": r"(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})",
            "article": r"(?:Artículo|ARTÍCULO)\s+(\d+)",
            "paragraph": r"(?:Parágrafo|PARÁGRAFO)\s+(\d+)"
        }
        
        # Quality thresholds
        self.quality_thresholds = {
            "min_content_length": 100,
            "min_title_length": 10,
            "max_content_length": 50000,
            "min_quality_score": 0.6
        }
    
    def calculate_document_hash(self, content: str, title: str) -> str:
        """Calculate unique hash for document"""
        combined = f"{title}:{content}"
        return hashlib.md5(combined.encode('utf-8')).hexdigest()
    
    def extract_legal_metadata(self, content: str, title: str) -> Dict[str, Any]:
        """Extract legal metadata from document content"""
        metadata = {
            "document_type": "unknown",
            "document_number": None,
            "year": None,
            "articles": [],
            "dates": [],
            "authority": None,
            "legal_area": None
        }
        
        # Determine document type
        if re.search(self.legal_patterns["law"], title + " " + content):
            metadata["document_type"] = "law"
            match = re.search(self.legal_patterns["law"], title + " " + content)
            if match:
                metadata["document_number"] = match.group(1)
                metadata["year"] = match.group(2)
        elif re.search(self.legal_patterns["decree"], title + " " + content):
            metadata["document_type"] = "decree"
            match = re.search(self.legal_patterns["decree"], title + " " + content)
            if match:
                metadata["document_number"] = match.group(1)
                metadata["year"] = match.group(2)
        elif re.search(self.legal_patterns["resolution"], title + " " + content):
            metadata["document_type"] = "resolution"
            match = re.search(self.legal_patterns["resolution"], title + " " + content)
            if match:
                metadata["document_number"] = match.group(1)
                metadata["year"] = match.group(2)
        elif re.search(self.legal_patterns["constitutional_court"], title + " " + content):
            metadata["document_type"] = "constitutional_decision"
            match = re.search(self.legal_patterns["constitutional_court"], title + " " + content)
            if match:
                metadata["document_number"] = match.group(1)
        elif re.search(self.legal_patterns["supreme_court"], title + " " + content):
            metadata["document_type"] = "supreme_decision"
            match = re.search(self.legal_patterns["supreme_court"], title + " " + content)
            if match:
                metadata["document_number"] = match.group(1)
        
        # Extract dates
        date_matches = re.findall(self.legal_patterns["date"], content)
        for match in date_matches:
            metadata["dates"].append(f"{match[0]} de {match[1]} de {match[2]}")
        
        # Extract articles
        article_matches = re.findall(self.legal_patterns["article"], content)
        metadata["articles"] = [f"Artículo {match}" for match in article_matches]
        
        # Determine legal area based on content keywords
        content_lower = content.lower()
        if any(word in content_lower for word in ["contrato", "obligación", "responsabilidad"]):
            metadata["legal_area"] = "civil"
        elif any(word in content_lower for word in ["administrativo", "funcionario", "estado"]):
            metadata["legal_area"] = "administrative"
        elif any(word in content_lower for word in ["patente", "marca", "propiedad intelectual"]):
            metadata["legal_area"] = "intellectual_property"
        elif any(word in content_lower for word in ["constitucional", "derechos", "libertades"]):
            metadata["legal_area"] = "constitutional"
        else:
            metadata["legal_area"] = "general"
        
        return metadata
    
    def clean_and_structure_content(self, content: str) -> str:
        """Clean and structure document content"""
        if not content:
            return ""
        
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content.strip())
        
        # Remove HTML tags if present
        content = re.sub(r'<[^>]+>', '', content)
        
        # Remove special characters but keep Spanish accents
        content = re.sub(r'[^\w\sáéíóúñÁÉÍÓÚÑ.,;:!?()\-]', '', content)
        
        return content
    
    def calculate_quality_score(self, doc: Dict[str, Any], processed_content: str) -> float:
        """Calculate quality score for document"""
        score = 0.0
        
        # Content length score
        content_length = len(processed_content)
        if content_length >= self.quality_thresholds["min_content_length"]:
            score += 0.3
            if content_length <= self.quality_thresholds["max_content_length"]:
                score += 0.2
        
        # Title quality score
        title = doc.get("title", "")
        if len(title) >= self.quality_thresholds["min_title_length"]:
            score += 0.2
        
        # Source URL score
        if doc.get("source_url"):
            score += 0.1
        
        # Content structure score
        if any(word in processed_content.lower() for word in ["artículo", "parágrafo", "capítulo"]):
            score += 0.2
        
        return min(score, 1.0)
    
    def validate_document(self, doc: Dict[str, Any], processed_content: str) -> Tuple[bool, List[str]]:
        """Validate document quality"""
        errors = []
        
        # Check content length
        if len(processed_content) < self.quality_thresholds["min_content_length"]:
            errors.append(f"Content too short: {len(processed_content)} characters")
        
        if len(processed_content) > self.quality_thresholds["max_content_length"]:
            errors.append(f"Content too long: {len(processed_content)} characters")
        
        # Check title
        title = doc.get("title", "")
        if len(title) < self.quality_thresholds["min_title_length"]:
            errors.append(f"Title too short: {len(title)} characters")
        
        # Check required fields
        if not doc.get("source_url"):
            errors.append("Missing source URL")
        
        return len(errors) == 0, errors
    
    def process_document(self, doc: Dict[str, Any]) -> ProcessedDocument:
        """Process a single legal document"""
        try:
            # Extract content
            content = doc.get("content", "")
            title = doc.get("title", "")
            
            # Clean and structure content
            processed_content = self.clean_and_structure_content(content)
            
            # Extract legal metadata
            structured_data = self.extract_legal_metadata(processed_content, title)
            
            # Calculate quality score
            quality_score = self.calculate_quality_score(doc, processed_content)
            
            # Validate document
            is_valid, validation_errors = self.validate_document(doc, processed_content)
            
            # Determine processing status
            if is_valid and quality_score >= self.quality_thresholds["min_quality_score"]:
                status = ProcessingStatus.COMPLETED
            elif is_valid:
                status = ProcessingStatus.VALIDATED
            else:
                status = ProcessingStatus.FAILED
            
            # Calculate document hash
            document_hash = self.calculate_document_hash(processed_content, title)
            
            return ProcessedDocument(
                original_doc=doc,
                processed_content=processed_content,
                structured_data=structured_data,
                quality_score=quality_score,
                processing_status=status,
                validation_errors=validation_errors,
                document_hash=document_hash,
                processing_timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error processing document {doc.get('title', 'Unknown')}: {e}")
            return ProcessedDocument(
                original_doc=doc,
                processed_content="",
                structured_data={},
                quality_score=0.0,
                processing_status=ProcessingStatus.FAILED,
                validation_errors=[str(e)],
                document_hash="",
                processing_timestamp=datetime.now().isoformat()
            )

class DataProcessingPipeline:
    """Processes and validates legal documents"""
    
    def __init__(self):
        self.processor = LegalDocumentProcessor()
        self.duplicates_removed = 0
        self.quality_filtered = 0
    
    def load_scraped_documents(self, filename: str) -> List[Dict[str, Any]]:
        """Load scraped documents from JSON file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Loaded {len(data)} documents from {filename}")
            return data
            
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
            return []
    
    def remove_duplicates(self, documents: List[ProcessedDocument]) -> List[ProcessedDocument]:
        """Remove duplicate documents based on hash"""
        seen_hashes = set()
        unique_docs = []
        
        for doc in documents:
            if doc.document_hash and doc.document_hash not in seen_hashes:
                seen_hashes.add(doc.document_hash)
                unique_docs.append(doc)
            else:
                self.duplicates_removed += 1
        
        logger.info(f"Removed {self.duplicates_removed} duplicate documents")
        return unique_docs
    
    def filter_by_quality(self, documents: List[ProcessedDocument]) -> List[ProcessedDocument]:
        """Filter documents by quality score"""
        high_quality = []
        
        for doc in documents:
            if doc.quality_score >= self.processor.quality_thresholds["min_quality_score"]:
                high_quality.append(doc)
            else:
                self.quality_filtered += 1
        
        logger.info(f"Filtered out {self.quality_filtered} low-quality documents")
        return high_quality
    
    def process_documents(self, documents: List[Dict[str, Any]]) -> List[ProcessedDocument]:
        """Process all documents through the pipeline"""
        logger.info(f"Processing {len(documents)} documents...")
        
        processed_docs = []
        for i, doc in enumerate(documents):
            if i % 10 == 0:
                logger.info(f"Processed {i}/{len(documents)} documents...")
            
            processed_doc = self.processor.process_document(doc)
            processed_docs.append(processed_doc)
        
        logger.info(f"Completed processing {len(processed_docs)} documents")
        return processed_docs
    
    def save_processed_documents(self, documents: List[ProcessedDocument], filename: str = None):
        """Save processed documents to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data_pipeline_output/processed_legal_documents_{timestamp}.json"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        documents_data = []
        for doc in documents:
            doc_dict = {
                "original_doc": doc.original_doc,
                "processed_content": doc.processed_content,
                "structured_data": doc.structured_data,
                "quality_score": doc.quality_score,
                "processing_status": doc.processing_status.value,
                "validation_errors": doc.validation_errors,
                "document_hash": doc.document_hash,
                "processing_timestamp": doc.processing_timestamp
            }
            documents_data.append(doc_dict)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(documents_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(documents_data)} processed documents to {filename}")
        return filename
    
    def generate_processing_report(self, documents: List[ProcessedDocument]) -> Dict[str, Any]:
        """Generate processing statistics report"""
        total_docs = len(documents)
        status_counts = {}
        quality_scores = []
        legal_areas = {}
        document_types = {}
        
        for doc in documents:
            # Status counts
            status = doc.processing_status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Quality scores
            quality_scores.append(doc.quality_score)
            
            # Legal areas
            area = doc.structured_data.get("legal_area", "unknown")
            legal_areas[area] = legal_areas.get(area, 0) + 1
            
            # Document types
            doc_type = doc.structured_data.get("document_type", "unknown")
            document_types[doc_type] = document_types.get(doc_type, 0) + 1
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        report = {
            "total_documents": total_docs,
            "duplicates_removed": self.duplicates_removed,
            "quality_filtered": self.quality_filtered,
            "final_documents": len(documents),
            "status_distribution": status_counts,
            "average_quality_score": avg_quality,
            "legal_area_distribution": legal_areas,
            "document_type_distribution": document_types,
            "processing_timestamp": datetime.now().isoformat()
        }
        
        return report
    
    def run_pipeline(self, input_filename: str, output_filename: str = None) -> Tuple[List[ProcessedDocument], Dict[str, Any]]:
        """Run the complete data processing pipeline"""
        logger.info("Starting data processing pipeline...")
        
        # Load documents
        documents = self.load_scraped_documents(input_filename)
        if not documents:
            logger.error("No documents to process")
            return [], {}
        
        # Process documents
        processed_docs = self.process_documents(documents)
        
        # Remove duplicates
        unique_docs = self.remove_duplicates(processed_docs)
        
        # Filter by quality
        high_quality_docs = self.filter_by_quality(unique_docs)
        
        # Save processed documents
        if output_filename:
            self.save_processed_documents(high_quality_docs, output_filename)
        
        # Generate report
        report = self.generate_processing_report(high_quality_docs)
        
        logger.info("Data processing pipeline completed successfully")
        return high_quality_docs, report

async def main():
    """Main processing function"""
    # Example usage
    pipeline = DataProcessingPipeline()
    
    # Use the specific scraped file from data_pipeline_output
    input_file = "data_pipeline_output/scraped_legal_documents_20250727_220248.json"
    output_file = "data_pipeline_output/processed_legal_documents_fixed.json"
    
    if os.path.exists(input_file):
        logger.info(f"Processing file: {input_file}")
        documents, report = pipeline.run_pipeline(input_file, output_file)
        
        # Print report
        print("\n" + "="*50)
        print("PROCESSING REPORT")
        print("="*50)
        print(f"Total documents processed: {report.get('total_documents', 0)}")
        print(f"Duplicates removed: {report.get('duplicates_removed', 0)}")
        print(f"Quality filtered: {report.get('quality_filtered', 0)}")
        print(f"Final documents: {report.get('final_documents', 0)}")
        print(f"Average quality score: {report.get('average_quality_score', 0):.2f}")
        
        if report.get('status_distribution'):
            print("\nStatus Distribution:")
            for status, count in report['status_distribution'].items():
                print(f"  {status}: {count}")
        
        if report.get('legal_area_distribution'):
            print("\nLegal Area Distribution:")
            for area, count in report['legal_area_distribution'].items():
                print(f"  {area}: {count}")
        
        if report.get('document_type_distribution'):
            print("\nDocument Type Distribution:")
            for doc_type, count in report['document_type_distribution'].items():
                print(f"  {doc_type}: {count}")
        
    else:
        logger.error(f"Input file {input_file} not found")

if __name__ == "__main__":
    asyncio.run(main()) 