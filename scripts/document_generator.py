#!/usr/bin/env python3
"""
Document Generator with Current Date
Generates legal documents using current date and formatos from knowledge base
"""

import os
import sys
import logging
from datetime import datetime, date
from typing import Dict, List, Any, Optional
import argparse

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.supabase_knowledge_base import SupabaseLegalKnowledgeBase, KnowledgeType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DocumentGenerator:
    """Generates legal documents using current date and formatos"""
    
    def __init__(self, mock_mode: bool = False):
        self.kb = SupabaseLegalKnowledgeBase(mock_mode=mock_mode)
        self.current_date = datetime.now()
        self.generation_stats = {
            "templates_found": 0,
            "documents_generated": 0,
            "errors": 0
        }
    
    def get_current_date_formatted(self, format_type: str = "standard") -> str:
        """Get current date in various formats for legal documents"""
        today = date.today()
        
        date_formats = {
            "standard": today.strftime("%d de %B de %Y"),  # 19 de agosto de 2025
            "short": today.strftime("%d/%m/%Y"),           # 19/08/2025
            "long": today.strftime("%A, %d de %B de %Y"), # martes, 19 de agosto de 2025
            "legal": today.strftime("%d de %B del año %Y"), # 19 de agosto del año 2025
            "iso": today.isoformat(),                      # 2025-08-19
            "spanish_short": today.strftime("%d-%m-%Y"),   # 19-08-2025
            "spanish_long": today.strftime("%d de %B de %Y") # 19 de agosto de 2025
        }
        
        return date_formats.get(format_type, date_formats["standard"])
    
    def get_current_time_formatted(self) -> str:
        """Get current time formatted for legal documents"""
        return self.current_date.strftime("%H:%M horas")
    
    def get_current_datetime_legal(self) -> str:
        """Get current date and time in legal format"""
        return f"{self.get_current_date_formatted('legal')} a las {self.get_current_time_formatted()}"
    
    async def search_document_templates(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for document templates in the knowledge base"""
        try:
            results = await self.kb.search_knowledge(query, limit=limit)
            if results and "results" in results:
                return results["results"]
            return []
        except Exception as e:
            logger.error(f"Error searching for templates: {e}")
            return []
    
    async def get_template_by_category(self, category: str, document_type: str = None) -> List[Dict[str, Any]]:
        """Get templates by legal category and document type"""
        try:
            # Search for templates in the specific category
            query = f"template legal {category}"
            if document_type:
                query += f" {document_type}"
            
            results = await self.search_document_templates(query, limit=10)
            
            # Filter by category if available
            if results:
                filtered_results = []
                for result in results:
                    metadata = result.get("metadata", {})
                    if metadata.get("legal_area", "").lower() == category.lower():
                        filtered_results.append(result)
                return filtered_results
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting templates by category: {e}")
            return []
    
    def generate_document_with_date(self, template_content: str, template_name: str, 
                                  document_type: str, legal_area: str) -> Dict[str, Any]:
        """Generate a document using template content and current date"""
        try:
            # Replace date placeholders in template
            processed_content = template_content
            
            # Common date replacements
            date_replacements = {
                "[FECHA]": self.get_current_date_formatted("standard"),
                "[FECHA_ACTUAL]": self.get_current_date_formatted("legal"),
                "[FECHA_CORTA]": self.get_current_date_formatted("short"),
                "[FECHA_LARGA]": self.get_current_date_formatted("long"),
                "[FECHA_ISO]": self.get_current_date_formatted("iso"),
                "[FECHA_HORA]": self.get_current_datetime_legal(),
                "[HORA]": self.get_current_time_formatted(),
                "[AÑO]": str(self.current_date.year),
                "[MES]": self.current_date.strftime("%B"),
                "[DIA]": str(self.current_date.day),
                "[DIA_SEMANA]": self.current_date.strftime("%A")
            }
            
            # Apply date replacements
            for placeholder, value in date_replacements.items():
                processed_content = processed_content.replace(placeholder, value)
            
            # Generate document metadata
            generated_document = {
                "template_used": template_name,
                "document_type": document_type,
                "legal_area": legal_area,
                "generation_date": self.current_date.isoformat(),
                "generated_content": processed_content,
                "original_template": template_content,
                "date_placeholders_replaced": list(date_replacements.keys()),
                "document_title": f"{template_name} - Generado el {self.get_current_date_formatted('standard')}"
            }
            
            return generated_document
            
        except Exception as e:
            logger.error(f"Error generating document: {e}")
            return None
    
    async def generate_document_from_template(self, template_name: str, 
                                           document_type: str = None, 
                                           legal_area: str = None) -> Optional[Dict[str, Any]]:
        """Generate a document from a specific template"""
        try:
            # Search for the specific template
            query = f"template {template_name}"
            results = await self.search_document_templates(query, limit=1)
            
            if not results:
                logger.error(f"Template not found: {template_name}")
                return None
            
            template = results[0]
            content = template.get("content", "")
            metadata = template.get("metadata", {})
            
            # Use provided parameters or extract from template
            doc_type = document_type or metadata.get("document_type", "legal_document")
            area = legal_area or metadata.get("legal_area", "general")
            
            # Generate document
            generated_doc = self.generate_document_with_date(
                content, template_name, doc_type, area
            )
            
            if generated_doc:
                self.generation_stats["documents_generated"] += 1
                logger.info(f"Successfully generated document from template: {template_name}")
                return generated_doc
            else:
                logger.error(f"Failed to generate document from template: {template_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating document from template: {e}")
            self.generation_stats["errors"] += 1
            return None
    
    async def generate_documents_by_category(self, category: str, 
                                          document_type: str = None, 
                                          limit: int = 5) -> List[Dict[str, Any]]:
        """Generate multiple documents from templates in a specific category"""
        try:
            # Get templates for the category
            templates = await self.get_template_by_category(category, document_type)
            
            if not templates:
                logger.warning(f"No templates found for category: {category}")
                return []
            
            self.generation_stats["templates_found"] = len(templates)
            
            generated_documents = []
            
            # Generate documents from each template (up to limit)
            for i, template in enumerate(templates[:limit]):
                try:
                    content = template.get("content", "")
                    metadata = template.get("metadata", {})
                    template_name = metadata.get("template_name", f"Template_{i+1}")
                    
                    doc_type = document_type or metadata.get("document_type", "legal_document")
                    area = metadata.get("legal_area", category)
                    
                    generated_doc = self.generate_document_with_date(
                        content, template_name, doc_type, area
                    )
                    
                    if generated_doc:
                        generated_documents.append(generated_doc)
                        logger.info(f"Generated document {i+1}/{min(len(templates), limit)}: {template_name}")
                    
                except Exception as e:
                    logger.error(f"Error generating document {i+1}: {e}")
                    self.generation_stats["errors"] += 1
                    continue
            
            return generated_documents
            
        except Exception as e:
            logger.error(f"Error generating documents by category: {e}")
            return []
    
    def print_generation_report(self):
        """Print document generation statistics report"""
        print("\n" + "="*60)
        print("DOCUMENT GENERATION REPORT")
        print("="*60)
        print(f"Generation Date: {self.get_current_date_formatted('legal')}")
        print(f"Templates found: {self.generation_stats['templates_found']}")
        print(f"Documents generated: {self.generation_stats['documents_generated']}")
        print(f"Errors encountered: {self.generation_stats['errors']}")
        
        if self.generation_stats['templates_found'] > 0:
            success_rate = (self.generation_stats['documents_generated'] / self.generation_stats['templates_found']) * 100
            print(f"Success rate: {success_rate:.1f}%")
        
        print("\nCurrent Date Formats Available:")
        print(f"  Standard: {self.get_current_date_formatted('standard')}")
        print(f"  Legal: {self.get_current_date_formatted('legal')}")
        print(f"  Short: {self.get_current_date_formatted('short')}")
        print(f"  Long: {self.get_current_date_formatted('long')}")
        print(f"  ISO: {self.get_current_date_formatted('iso')}")
        print(f"  Date & Time: {self.get_current_datetime_legal()}")
        
        print("="*60)

async def main():
    """Main document generation function"""
    parser = argparse.ArgumentParser(description="Generate legal documents with current date")
    parser.add_argument("--category", help="Legal category to generate documents for")
    parser.add_argument("--template", help="Specific template name to use")
    parser.add_argument("--type", help="Document type to filter by")
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of documents to generate")
    parser.add_argument("--mock", action="store_true", help="Use mock mode for testing")
    args = parser.parse_args()
    
    logger.info("Starting document generation...")
    
    # Initialize generator
    generator = DocumentGenerator(mock_mode=args.mock)
    
    try:
        if args.template:
            # Generate from specific template
            logger.info(f"Generating document from template: {args.template}")
            result = await generator.generate_document_from_template(
                args.template, args.type, args.category
            )
            
            if result:
                print(f"\nGenerated Document:")
                print(f"Title: {result['document_title']}")
                print(f"Type: {result['document_type']}")
                print(f"Legal Area: {result['legal_area']}")
                print(f"Generation Date: {result['generation_date']}")
                print(f"\nContent Preview:")
                print(result['generated_content'][:500] + "..." if len(result['generated_content']) > 500 else result['generated_content'])
            else:
                logger.error("Failed to generate document")
        
        elif args.category:
            # Generate documents by category
            logger.info(f"Generating documents for category: {args.category}")
            results = await generator.generate_documents_by_category(
                args.category, args.type, args.limit
            )
            
            if results:
                print(f"\nGenerated {len(results)} documents for category: {args.category}")
                for i, doc in enumerate(results, 1):
                    print(f"\nDocument {i}:")
                    print(f"  Title: {doc['document_title']}")
                    print(f"  Type: {doc['document_type']}")
                    print(f"  Template: {doc['template_used']}")
            else:
                logger.warning(f"No documents generated for category: {args.category}")
        
        else:
            # Show available options
            print("Document Generator - Available Options:")
            print("  --category <category>  : Generate documents for a legal category")
            print("  --template <name>      : Generate document from specific template")
            print("  --type <type>          : Filter by document type")
            print("  --limit <number>       : Maximum documents to generate")
            print("\nExample usage:")
            print("  python document_generator.py --category civil --type contract")
            print("  python document_generator.py --template 'Contrato Arrendamiento'")
        
        # Print generation report
        generator.print_generation_report()
        
    except Exception as e:
        logger.error(f"Error during document generation: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
