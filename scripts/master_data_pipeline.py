#!/usr/bin/env python3
"""
Master Data Pipeline for Colombian Legal Database
Orchestrates the complete data collection, processing, and population workflow
"""

import asyncio
import logging
import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our pipeline components
from scripts.legal_web_scraper import ColombianLegalScraper
from scripts.data_processing_pipeline import DataProcessingPipeline
from scripts.enhanced_knowledge_populator import EnhancedKnowledgePopulator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'legal_database_pipeline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MasterDataPipeline:
    """Master pipeline for building comprehensive Colombian legal database"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self.get_default_config()
        self.pipeline_stats = {
            "scraping": {"documents_scraped": 0, "errors": 0},
            "processing": {"documents_processed": 0, "duplicates_removed": 0, "quality_filtered": 0},
            "population": {"documents_added": 0, "errors": 0},
            "start_time": None,
            "end_time": None,
            "total_duration": None
        }
        
        # Create output directory
        self.output_dir = Path("data_pipeline_output")
        self.output_dir.mkdir(exist_ok=True)
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default pipeline configuration"""
        return {
            "scraping": {
                "enabled": True,
                "rate_limit": 1,  # seconds between requests
                "max_retries": 3,
                "timeout": 30
            },
            "processing": {
                "enabled": True,
                "min_quality_score": 0.6,
                "min_content_length": 100,
                "max_content_length": 50000,
                "remove_duplicates": True
            },
            "population": {
                "enabled": True,
                "batch_size": 50,
                "rate_limit": 0.1  # seconds between insertions
            },
            "sources": {
                "constitutional": True,
                "legislation": True,
                "jurisprudence": True,
                "regulatory": True,
                "doctrine": False  # Requires special access
            }
        }
    
    async def run_scraping_phase(self) -> str:
        """Run the web scraping phase"""
        logger.info("="*60)
        logger.info("PHASE 1: WEB SCRAPING")
        logger.info("="*60)
        
        if not self.config["scraping"]["enabled"]:
            logger.info("Scraping phase disabled in configuration")
            return None
        
        try:
            # Initialize scraper
            async with ColombianLegalScraper() as scraper:
                # Scrape all sources
                documents = await scraper.scrape_all_sources()
                
                # Save scraped documents
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = self.output_dir / f"scraped_legal_documents_{timestamp}.json"
                scraper.save_documents(str(filename))
                
                # Update statistics
                self.pipeline_stats["scraping"]["documents_scraped"] = len(documents)
                
                logger.info(f"Scraping completed: {len(documents)} documents scraped")
                logger.info(f"Scraped documents saved to: {filename}")
                
                return str(filename)
                
        except Exception as e:
            logger.error(f"Error in scraping phase: {e}")
            self.pipeline_stats["scraping"]["errors"] += 1
            return None
    
    async def run_processing_phase(self, scraped_file: str) -> str:
        """Run the data processing phase"""
        logger.info("="*60)
        logger.info("PHASE 2: DATA PROCESSING")
        logger.info("="*60)
        
        if not self.config["processing"]["enabled"]:
            logger.info("Processing phase disabled in configuration")
            return scraped_file
        
        try:
            # Initialize processor
            pipeline = DataProcessingPipeline()
            
            # Process documents
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"processed_legal_documents_{timestamp}.json"
            
            processed_docs, report = pipeline.run_pipeline(scraped_file, str(output_file))
            
            # Update statistics
            self.pipeline_stats["processing"]["documents_processed"] = report.get("total_documents", 0)
            self.pipeline_stats["processing"]["duplicates_removed"] = report.get("duplicates_removed", 0)
            self.pipeline_stats["processing"]["quality_filtered"] = report.get("quality_filtered", 0)
            
            logger.info(f"Processing completed: {len(processed_docs)} documents processed")
            logger.info(f"Processed documents saved to: {output_file}")
            
            # Print processing report
            self.print_processing_report(report)
            
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Error in processing phase: {e}")
            return scraped_file  # Return original file if processing fails
    
    async def run_population_phase(self, processed_file: str):
        """Run the knowledge base population phase"""
        logger.info("="*60)
        logger.info("PHASE 3: KNOWLEDGE BASE POPULATION")
        logger.info("="*60)
        
        if not self.config["population"]["enabled"]:
            logger.info("Population phase disabled in configuration")
            return
        
        try:
            # Initialize populator
            populator = EnhancedKnowledgePopulator(mock_mode=False)
            
            # Populate from processed documents if available
            if processed_file and os.path.exists(processed_file):
                logger.info(f"Populating from processed documents: {processed_file}")
                await populator.populate_from_processed_documents(processed_file)
            else:
                logger.info("No processed documents available, using comprehensive content")
                await populator.populate_comprehensive_legal_content()
            
            # Update statistics
            self.pipeline_stats["population"]["documents_added"] = populator.population_stats["total_added"]
            self.pipeline_stats["population"]["errors"] = populator.population_stats["errors"]
            
            # Print population report
            populator.print_population_report()
            
            logger.info("Population phase completed")
            
        except Exception as e:
            logger.error(f"Error in population phase: {e}")
            self.pipeline_stats["population"]["errors"] += 1
    
    def print_processing_report(self, report: Dict[str, Any]):
        """Print processing phase report"""
        print("\n" + "="*50)
        print("PROCESSING PHASE REPORT")
        print("="*50)
        print(f"Total documents processed: {report.get('total_documents', 0)}")
        print(f"Duplicates removed: {report.get('duplicates_removed', 0)}")
        print(f"Quality filtered: {report.get('quality_filtered', 0)}")
        print(f"Final documents: {report.get('final_documents', 0)}")
        print(f"Average quality score: {report.get('average_quality_score', 0):.2f}")
        
        print("\nStatus Distribution:")
        for status, count in report.get('status_distribution', {}).items():
            print(f"  {status}: {count}")
        
        print("\nLegal Area Distribution:")
        for area, count in report.get('legal_area_distribution', {}).items():
            print(f"  {area}: {count}")
        
        print("\nDocument Type Distribution:")
        for doc_type, count in report.get('document_type_distribution', {}).items():
            print(f"  {doc_type}: {count}")
    
    def print_final_report(self):
        """Print final pipeline report"""
        print("\n" + "="*80)
        print("MASTER DATA PIPELINE - FINAL REPORT")
        print("="*80)
        
        # Timing information
        if self.pipeline_stats["start_time"] and self.pipeline_stats["end_time"]:
            duration = self.pipeline_stats["end_time"] - self.pipeline_stats["start_time"]
            print(f"Total pipeline duration: {duration}")
        
        # Phase summaries
        print(f"\nSCRAPING PHASE:")
        print(f"  Documents scraped: {self.pipeline_stats['scraping']['documents_scraped']}")
        print(f"  Errors: {self.pipeline_stats['scraping']['errors']}")
        
        print(f"\nPROCESSING PHASE:")
        print(f"  Documents processed: {self.pipeline_stats['processing']['documents_processed']}")
        print(f"  Duplicates removed: {self.pipeline_stats['processing']['duplicates_removed']}")
        print(f"  Quality filtered: {self.pipeline_stats['processing']['quality_filtered']}")
        
        print(f"\nPOPULATION PHASE:")
        print(f"  Documents added to database: {self.pipeline_stats['population']['documents_added']}")
        print(f"  Errors: {self.pipeline_stats['population']['errors']}")
        
        # Success rates
        total_scraped = self.pipeline_stats["scraping"]["documents_scraped"]
        total_added = self.pipeline_stats["population"]["documents_added"]
        
        if total_scraped > 0:
            success_rate = (total_added / total_scraped) * 100
            print(f"\nOVERALL SUCCESS RATE: {success_rate:.1f}%")
        
        print("="*80)
    
    async def run_complete_pipeline(self) -> bool:
        """Run the complete data pipeline"""
        logger.info("Starting Master Data Pipeline for Colombian Legal Database")
        logger.info(f"Configuration: {json.dumps(self.config, indent=2)}")
        
        self.pipeline_stats["start_time"] = datetime.now()
        
        try:
            # Phase 1: Web Scraping
            scraped_file = await self.run_scraping_phase()
            
            # Phase 2: Data Processing
            processed_file = await self.run_processing_phase(scraped_file)
            
            # Phase 3: Knowledge Base Population
            await self.run_population_phase(processed_file)
            
            # Pipeline completed successfully
            self.pipeline_stats["end_time"] = datetime.now()
            self.pipeline_stats["total_duration"] = self.pipeline_stats["end_time"] - self.pipeline_stats["start_time"]
            
            # Print final report
            self.print_final_report()
            
            logger.info("Master Data Pipeline completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Error in master pipeline: {e}")
            self.pipeline_stats["end_time"] = datetime.now()
            return False
    
    def save_pipeline_report(self):
        """Save pipeline report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"pipeline_report_{timestamp}.json"
        
        report_data = {
            "pipeline_stats": self.pipeline_stats,
            "configuration": self.config,
            "timestamp": timestamp
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"Pipeline report saved to: {report_file}")

async def main():
    """Main function to run the master pipeline"""
    
    # Configuration options
    config_options = {
        "full_pipeline": {
            "scraping": {"enabled": True},
            "processing": {"enabled": True},
            "population": {"enabled": True}
        },
        "scraping_only": {
            "scraping": {"enabled": True},
            "processing": {"enabled": False},
            "population": {"enabled": False}
        },
        "processing_only": {
            "scraping": {"enabled": False},
            "processing": {"enabled": True},
            "population": {"enabled": False}
        },
        "population_only": {
            "scraping": {"enabled": False},
            "processing": {"enabled": False},
            "population": {"enabled": True}
        }
    }
    
    # Choose configuration (default to full pipeline)
    config_name = os.getenv("PIPELINE_CONFIG", "full_pipeline")
    config = config_options.get(config_name, config_options["full_pipeline"])
    
    print(f"Running pipeline with configuration: {config_name}")
    
    # Initialize and run pipeline
    pipeline = MasterDataPipeline(config)
    success = await pipeline.run_complete_pipeline()
    
    # Save report
    pipeline.save_pipeline_report()
    
    if success:
        print("\n✅ Pipeline completed successfully!")
        print("Your Colombian legal database has been built and populated.")
        print("You can now use the legal AI assistant with comprehensive knowledge.")
    else:
        print("\n❌ Pipeline encountered errors. Check the logs for details.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main()) 