#!/usr/bin/env python3
"""
Constitutional Court Cases Ingester
Ingests scraped constitutional court cases into the jurisprudence table
"""

import asyncio
import logging
import json
import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime
import psycopg
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import configuration
from config.settings import POSTGRES_URL, MISTRAL_API_KEY

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConstitutionalCourtIngester:
    """Ingests constitutional court cases into the jurisprudence table"""
    
    def __init__(self):
        self.postgres_url = POSTGRES_URL
        self.mistral_api_key = MISTRAL_API_KEY
        self.ingestion_stats = {
            "total_cases": 0,
            "successfully_ingested": 0,
            "errors": 0,
            "by_decision_type": {},
            "by_year": {}
        }
    
    def load_scraped_cases(self, file_path: str) -> List[Dict[str, Any]]:
        """Load scraped cases from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                cases = json.load(f)
            
            logger.info(f"Loaded {len(cases)} cases from {file_path}")
            return cases
            
        except Exception as e:
            logger.error(f"Error loading scraped cases: {e}")
            return []
    
    def transform_case_data(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """Transform scraped case data to match jurisprudence table schema"""
        try:
            # Extract and clean case number
            case_number = case.get('case_number', '').strip()
            
            # Determine decision type
            decision_type = case.get('decision_type', 'unknown')
            if decision_type == 'tutela':
                decision_type = 'tutela'
            elif decision_type == 'constitucionalidad':
                decision_type = 'sentencia'
            elif decision_type == 'sentencia_unificacion':
                decision_type = 'sentencia'
            
            # Parse decision date
            decision_date = None
            if case.get('decision_date'):
                try:
                    decision_date = datetime.strptime(case['decision_date'], '%Y-%m-%d').date()
                except:
                    pass
            
            # Extract year from case number if no decision date
            year = case.get('year')
            if year and not decision_date:
                try:
                    decision_date = datetime.strptime(f"{year}-01-01", '%Y-%m-%d').date()
                except:
                    pass
            
            # Prepare topic
            topic = case.get('topic', '')
            if not topic and case.get('full_text'):
                # Extract topic from full text if available
                topic = case.get('full_text', '')[:200]
            
            # Prepare summary
            summary = case.get('summary', '')
            if not summary and case.get('full_text'):
                # Create summary from full text
                full_text = case.get('full_text', '')
                if len(full_text) > 500:
                    summary = full_text[:500] + "..."
                else:
                    summary = full_text
            
            # Prepare full text
            full_text = case.get('full_text', '')
            if not full_text:
                # Create basic content from available fields
                content_parts = []
                if case_number:
                    content_parts.append(f"Case Number: {case_number}")
                if topic:
                    content_parts.append(f"Topic: {topic}")
                if summary:
                    content_parts.append(f"Summary: {summary}")
                if case.get('magistrate'):
                    content_parts.append(f"Magistrate: {case['magistrate']}")
                
                full_text = "\n".join(content_parts)
            
            # Prepare tags
            tags = []
            if decision_type:
                tags.append(decision_type)
            if year:
                tags.append(f"year_{year}")
            if case.get('search_query'):
                tags.append(case['search_query'].replace(' ', '_'))
            tags.append('corte_constitucional')
            tags.append('colombia')
            
            # Prepare legal principles (extract from topic/summary)
            legal_principles = []
            if topic or summary:
                text_to_analyze = (topic + " " + summary).lower()
                principles = [
                    'derechos fundamentales', 'control constitucional', 'debido proceso',
                    'principio de igualdad', 'libertad de expresión', 'derecho a la vida',
                    'derecho a la salud', 'derecho a la educación', 'derecho al trabajo',
                    'derecho a la intimidad', 'habeas data', 'derecho de petición'
                ]
                for principle in principles:
                    if principle in text_to_analyze:
                        legal_principles.append(principle)
            
            # Prepare key holdings
            key_holdings = []
            if summary:
                # Extract key points from summary
                summary_lower = summary.lower()
                if 'concedida' in summary_lower:
                    key_holdings.append('Acción concedida')
                elif 'negada' in summary_lower:
                    key_holdings.append('Acción negada')
                elif 'exequible' in summary_lower:
                    key_holdings.append('Norma declarada exequible')
                elif 'inexequible' in summary_lower:
                    key_holdings.append('Norma declarada inexequible')
            
            # Prepare cited laws (extract from content)
            cited_laws = []
            if full_text:
                import re
                law_patterns = [
                    r'Ley\s+\d+\s+de\s+\d{4}',
                    r'Decreto\s+\d+\s+de\s+\d{4}',
                    r'Resolución\s+\d+\s+de\s+\d{4}'
                ]
                for pattern in law_patterns:
                    matches = re.findall(pattern, full_text)
                    cited_laws.extend(matches)
            
            # Prepare relevance score
            relevance_score = None
            if case.get('relevance_score'):
                try:
                    relevance_score = float(case['relevance_score'])
                except:
                    pass
            
            transformed_case = {
                'case_number': case_number,
                'court': case.get('court', 'Corte Constitucional'),
                'decision_type': decision_type,
                'decision_date': decision_date,
                'topic': topic,
                'summary': summary,
                'full_text': full_text,
                'key_holdings': key_holdings,
                'legal_principles': legal_principles,
                'cited_laws': cited_laws,
                'cited_precedents': [],  # Not available in scraped data
                'relevance_score': relevance_score,
                'tags': tags,
                'source_url': case.get('source_url', ''),
                'scraped_date': case.get('scraped_date', ''),
                'search_query': case.get('search_query', '')
            }
            
            return transformed_case
            
        except Exception as e:
            logger.error(f"Error transforming case data: {e}")
            return None
    
    def get_mistral_embedding(self, text: str) -> Optional[List[float]]:
        """Get vector embedding from Mistral API"""
        try:
            import requests
            
            headers = {
                'Authorization': f'Bearer {self.mistral_api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': 'mistral-embed',
                'input': text[:8000]  # Limit text length for API
            }
            
            response = requests.post(
                'https://api.mistral.ai/v1/embeddings',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['data'][0]['embedding']
            else:
                logger.warning(f"Mistral API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.warning(f"Error getting Mistral embedding: {e}")
            return None
    
    def format_vector_for_postgres(self, vector: List[float]) -> str:
        """Format vector for PostgreSQL insertion"""
        if not vector:
            return None
        return "[" + ",".join(str(x) for x in vector) + "]"
    
    async def ingest_case_to_database(self, case: Dict[str, Any]) -> bool:
        """Ingest a single case into the jurisprudence table"""
        try:
            # Get vector embedding
            text_for_embedding = f"{case.get('topic', '')} {case.get('summary', '')} {case.get('full_text', '')}"
            vector = self.get_mistral_embedding(text_for_embedding)
            
            # Connect to database
            with psycopg.connect(self.postgres_url) as conn:
                with conn.cursor() as cur:
                    # Prepare data for insertion
                    case_number = case.get('case_number')
                    court = case.get('court', 'Corte Constitucional')
                    decision_type = case.get('decision_type', 'unknown')
                    decision_date = case.get('decision_date')
                    topic = case.get('topic', '')[:500]  # Limit length
                    summary = case.get('summary', '')[:2000]  # Limit length
                    full_text = case.get('full_text', '')[:10000]  # Limit length
                    key_holdings = case.get('key_holdings', [])
                    legal_principles = case.get('legal_principles', [])
                    cited_laws = case.get('cited_laws', [])
                    cited_precedents = case.get('cited_precedents', [])
                    relevance_score = case.get('relevance_score')
                    tags = case.get('tags', [])
                    source_url = case.get('source_url', '')[:500]  # Limit length
                    vector_str = self.format_vector_for_postgres(vector)
                    
                    # Check if case already exists
                    cur.execute(
                        "SELECT id FROM jurisprudence WHERE case_number = %s AND court = %s",
                        (case_number, court)
                    )
                    
                    if cur.fetchone():
                        logger.info(f"Case {case_number} already exists, skipping...")
                        return True
                    
                    # Insert case
                    sql = """
                    INSERT INTO jurisprudence (
                        case_number, court, decision_type, decision_date, topic, summary, full_text,
                        key_holdings, legal_principles, cited_laws, cited_precedents, relevance_score,
                        tags, source_url, vector_embedding, created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector, NOW(), NOW()
                    )
                    """
                    
                    cur.execute(sql, (
                        case_number, court, decision_type, decision_date, topic, summary, full_text,
                        key_holdings, legal_principles, cited_laws, cited_precedents, relevance_score,
                        tags, source_url, vector_str
                    ))
                    
                    conn.commit()
                    
                    # Update statistics
                    self.ingestion_stats["successfully_ingested"] += 1
                    
                    # Track by decision type
                    decision_type = case.get('decision_type', 'unknown')
                    self.ingestion_stats["by_decision_type"][decision_type] = \
                        self.ingestion_stats["by_decision_type"].get(decision_type, 0) + 1
                    
                    # Track by year
                    if case.get('year'):
                        year = case['year']
                        self.ingestion_stats["by_year"][year] = \
                            self.ingestion_stats["by_year"].get(year, 0) + 1
                    
                    logger.info(f"Successfully ingested case: {case_number}")
                    return True
                    
        except Exception as e:
            logger.error(f"Error ingesting case {case.get('case_number', 'Unknown')}: {e}")
            self.ingestion_stats["errors"] += 1
            return False
    
    async def ingest_all_cases(self, cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Ingest all cases into the database"""
        logger.info(f"Starting ingestion of {len(cases)} cases...")
        
        self.ingestion_stats["total_cases"] = len(cases)
        
        for i, case in enumerate(cases):
            try:
                logger.info(f"Processing case {i+1}/{len(cases)}: {case.get('case_number', 'Unknown')}")
                
                # Transform case data
                transformed_case = self.transform_case_data(case)
                if not transformed_case:
                    logger.warning(f"Failed to transform case {case.get('case_number', 'Unknown')}")
                    continue
                
                # Ingest to database
                success = await self.ingest_case_to_database(transformed_case)
                if not success:
                    logger.error(f"Failed to ingest case {case.get('case_number', 'Unknown')}")
                
                # Small delay to avoid overwhelming the API
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error processing case {case.get('case_number', 'Unknown')}: {e}")
                self.ingestion_stats["errors"] += 1
                continue
        
        logger.info("Ingestion completed!")
        return self.ingestion_stats
    
    def print_ingestion_report(self, stats: Dict[str, Any]):
        """Print a summary of the ingestion process"""
        print("\n" + "="*60)
        print("CONSTITUTIONAL COURT CASES INGESTION REPORT")
        print("="*60)
        print(f"Total cases processed: {stats['total_cases']}")
        print(f"Successfully ingested: {stats['successfully_ingested']}")
        print(f"Errors: {stats['errors']}")
        
        if stats['by_decision_type']:
            print(f"\nBy decision type:")
            for decision_type, count in stats['by_decision_type'].items():
                print(f"  {decision_type}: {count}")
        
        if stats['by_year']:
            print(f"\nBy year:")
            for year, count in sorted(stats['by_year'].items()):
                print(f"  {year}: {count}")
        
        success_rate = (stats['successfully_ingested'] / stats['total_cases'] * 100) if stats['total_cases'] > 0 else 0
        print(f"\nSuccess rate: {success_rate:.1f}%")

async def main():
    """Main ingestion function"""
    try:
        # Find the most recent scraped cases file
        output_dir = Path("data_pipeline_output")
        case_files = list(output_dir.glob("constitutional_court_cases_improved_*.json"))
        
        if not case_files:
            print("No constitutional court cases files found!")
            return
        
        # Use the most recent file
        latest_file = max(case_files, key=lambda x: x.stat().st_mtime)
        print(f"Using file: {latest_file}")
        
        # Initialize ingester
        ingester = ConstitutionalCourtIngester()
        
        # Load cases
        cases = ingester.load_scraped_cases(str(latest_file))
        if not cases:
            print("No cases loaded!")
            return
        
        # Ingest cases
        stats = await ingester.ingest_all_cases(cases)
        
        # Print report
        ingester.print_ingestion_report(stats)
        
    except Exception as e:
        print(f"Error during ingestion: {e}")

if __name__ == "__main__":
    asyncio.run(main())
