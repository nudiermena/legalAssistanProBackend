#!/usr/bin/env python3
"""
Enhanced Formatos Ingestion Script
Ingests only today's formatos (document templates) into the knowledge base
Uses current date to filter and integrates with existing Supabase knowledge base
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.supabase_knowledge_base import SupabaseLegalKnowledgeBase, KnowledgeType
from config.settings import DOCX_KB_PATH

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedFormatosIngester:
    """Enhanced formatos ingestion with date filtering and knowledge base integration"""
    
    def __init__(self, mock_mode: bool = False):
        self.kb = SupabaseLegalKnowledgeBase(mock_mode=mock_mode)
        self.ingestion_stats = {
            "total_found": 0,
            "total_processed": 0,
            "errors": 0,
            "by_category": {}
        }
    
    def get_today_folders(self, base_path: str) -> List[Path]:
        """Get folders modified today from the formatos directory"""
        today = date.today()
        today_folders = []
        
        base_path_obj = Path(base_path)
        if not base_path_obj.exists():
            logger.error(f"Base path does not exist: {base_path}")
            return []
        
        logger.info(f"Scanning for folders modified on {today.strftime('%Y-%m-%d')}")
        
        for folder in base_path_obj.iterdir():
            if folder.is_dir():
                # Get the modification time of the folder
                try:
                    mtime = datetime.fromtimestamp(folder.stat().st_mtime).date()
                    if mtime == today:
                        today_folders.append(folder)
                        logger.info(f"Found today's folder: {folder.name} (modified: {mtime})")
                except Exception as e:
                    logger.warning(f"Could not get modification time for {folder.name}: {e}")
        
        logger.info(f"Found {len(today_folders)} folders modified today")
        return today_folders
    
    def find_docx_files_in_folders(self, folders: List[Path]) -> List[Path]:
        """Find all .doc and .docx files in the specified folders"""
        docx_files = []
        
        for folder in folders:
            try:
                # Search for .doc and .docx files recursively in this folder
                for file_path in folder.rglob("*.doc*"):
                    if file_path.suffix.lower() in ['.doc', '.docx']:
                        docx_files.append(file_path)
                        logger.debug(f"Found DOCX file: {file_path}")
            except Exception as e:
                logger.error(f"Error scanning folder {folder}: {e}")
        
        logger.info(f"Found {len(docx_files)} DOCX files in today's folders")
        return docx_files
    
    def extract_document_content(self, file_path: Path) -> Dict[str, Any]:
        """Extract content and metadata from a DOCX file"""
        try:
            # Read the file content (basic text extraction)
            import docx
            
            doc = docx.Document(file_path)
            content = []
            
            # Extract text from paragraphs
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    content.append(paragraph.text.strip())
            
            # Extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            content.append(cell.text.strip())
            
            full_content = "\n\n".join(content)
            
            # Determine document category from folder structure
            category = self._determine_category(file_path)
            
            # Extract metadata - only use allowed fields for document_templates table
            metadata = {
                "template_name": file_path.stem,
                "document_type": self._get_document_type(file_path),
                "template_content": full_content,
                "complexity_level": "standard",
                "jurisdiction": "Colombia",
                "industry_specific": False,
                "industry": "legal"
            }
            
            return {
                "content": full_content,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error extracting content from {file_path}: {e}")
            return None
    
    def _determine_category(self, file_path: Path) -> str:
        """Determine the legal category based on folder structure"""
        folder_name = file_path.parent.name.lower()
        
        category_mapping = {
            "civil": "civil",
            "comercial": "commercial",
            "laboral": "labor",
            "penal": "criminal",
            "tributario": "tax",
            "propiedad": "property",
            "intellectual": "intellectual_property",
            "familia": "family",
            "sucesiones": "succession",
            "bonos": "pensions",
            "pensiones": "pensions",
            "tutelas": "constitutional",
            "emprendedores": "entrepreneurship",
            "consumidor": "consumer_protection",
            "animales": "animal_rights",
            "multas": "fines",
            "insolvencias": "insolvency",
            "arrandamientos": "leases",
            "notariales": "notarial"
        }
        
        for key, value in category_mapping.items():
            if key in folder_name:
                return value
        
        return "general"
    
    def _get_document_type(self, file_path: Path) -> str:
        """Determine document type based on file name and content"""
        file_name = file_path.stem.lower()
        
        if any(word in file_name for word in ["demanda", "demand"]):
            return "lawsuit"
        elif any(word in file_name for word in ["contrato", "contract"]):
            return "contract"
        elif any(word in file_name for word in ["carta", "letter"]):
            return "letter"
        elif any(word in file_path.parent.name.lower() for word in ["actas", "minutes"]):
            return "minutes"
        elif any(word in file_name for word in ["formato", "template"]):
            return "template"
        else:
            return "legal_document"
    
    async def ingest_document(self, file_path: Path) -> bool:
        """Ingest a single document into the knowledge base"""
        try:
            logger.info(f"Processing: {file_path.name}")
            
            # Extract content and metadata
            doc_data = self.extract_document_content(file_path)
            if not doc_data:
                logger.error(f"Failed to extract content from {file_path}")
                return False
            
            # Add to knowledge base
            success = await self.kb.add_custom_knowledge(
                content=doc_data["content"],
                metadata=doc_data["metadata"],
                knowledge_type=KnowledgeType.DOCUMENT_TEMPLATES
            )
            
            if success:
                self.ingestion_stats["total_processed"] += 1
                # Get category from folder name for statistics
                category = self._determine_category(file_path)
                self.ingestion_stats["by_category"][category] = \
                    self.ingestion_stats["by_category"].get(category, 0) + 1
                logger.info(f"Successfully ingested: {file_path.name}")
                return True
            else:
                logger.error(f"Failed to add to knowledge base: {file_path.name}")
                self.ingestion_stats["errors"] += 1
                return False
                
        except Exception as e:
            logger.error(f"Error ingesting {file_path}: {e}")
            self.ingestion_stats["errors"] += 1
            return False
    
    async def ingest_today_formatos(self, base_path: str = None, delay: float = 1.0) -> bool:
        """Ingest all formatos modified today"""
        if base_path is None:
            base_path = DOCX_KB_PATH
        
        logger.info(f"Starting ingestion of today's formatos from: {base_path}")
        
        # Get today's folders
        today_folders = self.get_today_folders(base_path)
        if not today_folders:
            logger.warning("No folders modified today found")
            return False
        
        # Find DOCX files in today's folders
        docx_files = self.find_docx_files_in_folders(today_folders)
        if not docx_files:
            logger.warning("No DOCX files found in today's folders")
            return False
        
        self.ingestion_stats["total_found"] = len(docx_files)
        
        # Process each document
        for i, file_path in enumerate(docx_files):
            try:
                await self.ingest_document(file_path)
                
                # Add delay between documents (except for the last one)
                if i < len(docx_files) - 1 and delay > 0:
                    logger.info(f"Waiting {delay}s before next document...")
                    time.sleep(delay)
                    
            except Exception as e:
                logger.error(f"Unexpected error processing {file_path}: {e}")
                self.ingestion_stats["errors"] += 1
        
        logger.info("Formatos ingestion completed")
        return True
    
    def print_ingestion_report(self):
        """Print ingestion statistics report"""
        print("\n" + "="*60)
        print("TODAY'S FORMATOS INGESTION REPORT")
        print("="*60)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total files found: {self.ingestion_stats['total_found']}")
        print(f"Successfully processed: {self.ingestion_stats['total_processed']}")
        print(f"Errors encountered: {self.ingestion_stats['errors']}")
        
        if self.ingestion_stats['total_found'] > 0:
            success_rate = (self.ingestion_stats['total_processed'] / self.ingestion_stats['total_found']) * 100
            print(f"Success rate: {success_rate:.1f}%")
        
        if self.ingestion_stats['by_category']:
            print("\nDocuments by legal category:")
            for category, count in self.ingestion_stats["by_category"].items():
                print(f"  {category}: {count} documents")
        
        print("="*60)

async def main():
    """Main ingestion function"""
    parser = argparse.ArgumentParser(description="Ingest today's formatos into knowledge base")
    parser.add_argument("--path", default=None, help="Path to formatos directory (default: from settings)")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between documents in seconds")
    parser.add_argument("--mock", action="store_true", help="Use mock mode for testing")
    args = parser.parse_args()
    
    logger.info("Starting enhanced formatos ingestion...")
    
    # Initialize ingester
    ingester = EnhancedFormatosIngester(mock_mode=args.mock)
    
    # Ingest today's formatos
    success = await ingester.ingest_today_formatos(
        base_path=args.path,
        delay=args.delay
    )
    
    # Print report
    ingester.print_ingestion_report()
    
    if success:
        logger.info("Formatos ingestion completed successfully")
    else:
        logger.warning("Formatos ingestion completed with issues")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
