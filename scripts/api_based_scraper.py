#!/usr/bin/env python3
"""
API-Based Constitutional Court Scraper
Uses the discovered search API to extract case numbers and links
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import os
import sys
from pathlib import Path
import re
from bs4 import BeautifulSoup
import hashlib

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class APIBasedConstitutionalCourtScraper:
    """API-based scraper for Colombian Constitutional Court jurisprudence"""
    
    def __init__(self):
        self.base_url = "https://www.corteconstitucional.gov.co"
        self.search_api = "/api/search"
        self.session = None
        self.scraped_cases = []
        
        # Headers to mimic a real browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.corteconstitucional.gov.co/relatoria/buscador-jurisprudencia',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def search_cases(self, query: str = "", limit: int = 50, page: int = 1) -> Optional[List[Dict[str, Any]]]:
        """Search for cases using the API"""
        try:
            search_url = self.base_url + self.search_api
            
            # Search parameters
            search_params = {
                'q': query if query else 'jurisprudencia',
                'limit': str(limit),
                'page': str(page)
            }
            
            logger.info(f"Searching cases with query: '{query}', limit: {limit}, page: {page}")
            
            async with self.session.get(search_url, params=search_params) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Try to parse as JSON
                    try:
                        data = json.loads(content)
                        logger.info(f"Successfully retrieved search results: {len(data) if isinstance(data, list) else 'single result'}")
                        return data if isinstance(data, list) else [data]
                    except json.JSONDecodeError:
                        logger.warning("Response is not valid JSON, treating as text")
                        # If not JSON, try to extract case information from HTML/text
                        return self.extract_cases_from_text(content)
                else:
                    logger.error(f"Search API failed: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error searching cases: {e}")
            return None
    
    def extract_cases_from_text(self, content: str) -> List[Dict[str, Any]]:
        """Extract case information from text/HTML content"""
        cases = []
        
        # Look for case numbers in the content
        case_patterns = [
            r'[CT]-\d+/\d{4}',  # T-123/2024 or C-456/2023
            r'Sentencia\s+[CT]-\d+/\d{4}',  # Sentencia T-123/2024
            r'Auto\s+\d+/\d{4}',  # Auto 123/2024
            r'Concepto\s+\d+/\d{4}'  # Concepto 123/2024
        ]
        
        for pattern in case_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                case_info = {
                    'case_number': match,
                    'decision_type': self.determine_decision_type(match),
                    'source': 'api_search',
                    'extracted_from': 'text_pattern'
                }
                cases.append(case_info)
        
        # Remove duplicates
        unique_cases = []
        seen_numbers = set()
        for case in cases:
            if case['case_number'] not in seen_numbers:
                unique_cases.append(case)
                seen_numbers.add(case['case_number'])
        
        logger.info(f"Extracted {len(unique_cases)} unique cases from text")
        return unique_cases
    
    def determine_decision_type(self, case_number: str) -> str:
        """Determine decision type from case number"""
        if 'sentencia' in case_number.lower():
            return 'sentencia'
        elif 'auto' in case_number.lower():
            return 'auto'
        elif 'concepto' in case_number.lower():
            return 'concepto'
        else:
            # Default based on case number format
            if case_number.startswith('T-'):
                return 'sentencia'  # T- cases are usually sentencias
            elif case_number.startswith('C-'):
                return 'concepto'    # C- cases are usually conceptos
            else:
                return 'auto'        # Default to auto
    
    async def get_case_details(self, case_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific case"""
        try:
            case_number = case_info['case_number']
            logger.info(f"Getting details for case: {case_number}")
            
            # Try to get case details from the API
            detail_url = f"{self.base_url}/api/case/{case_number}"
            
            async with self.session.get(detail_url) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    try:
                        case_data = json.loads(content)
                        logger.info(f"Successfully retrieved case details for {case_number}")
                        return self.enrich_case_data(case_data, case_info)
                    except json.JSONDecodeError:
                        logger.warning(f"Case details not in JSON format for {case_number}")
                        return self.create_basic_case_data(case_info)
                else:
                    logger.warning(f"Case details API failed for {case_number}: {response.status}")
                    return self.create_basic_case_data(case_info)
                    
        except Exception as e:
            logger.error(f"Error getting case details for {case_info.get('case_number', 'Unknown')}: {e}")
            return self.create_basic_case_data(case_info)
    
    def enrich_case_data(self, api_data: Dict[str, Any], case_info: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich case data with API information"""
        enriched_case = {
            'source_url': api_data.get('url') or f"{self.base_url}/relatoria/buscador-jurisprudencia",
            'scraped_date': datetime.now().isoformat(),
            'court': 'Corte Constitucional',
            'case_number': case_info['case_number'],
            'decision_type': case_info.get('decision_type') or api_data.get('type'),
            'decision_date': api_data.get('date'),
            'topic': api_data.get('title') or api_data.get('topic'),
            'summary': api_data.get('summary') or api_data.get('description'),
            'full_text': api_data.get('content') or api_data.get('text'),
            'key_holdings': api_data.get('holdings', []),
            'legal_principles': api_data.get('principles', []),
            'cited_laws': api_data.get('cited_laws', []),
            'cited_precedents': api_data.get('precedents', []),
            'tags': []
        }
        
        # Generate tags
        if enriched_case['legal_principles']:
            enriched_case['tags'].extend(enriched_case['legal_principles'])
        if enriched_case['decision_type']:
            enriched_case['tags'].append(enriched_case['decision_type'])
        if enriched_case['case_number']:
            enriched_case['tags'].append(enriched_case['case_number'])
        
        # Generate document hash
        content_for_hash = f"{enriched_case.get('case_number', '')}:{enriched_case.get('topic', '')}:{enriched_case.get('full_text', '')}"
        enriched_case['document_hash'] = hashlib.md5(content_for_hash.encode('utf-8')).hexdigest()
        
        return enriched_case
    
    def create_basic_case_data(self, case_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create basic case data when API details are not available"""
        basic_case = {
            'source_url': f"{self.base_url}/relatoria/buscador-jurisprudencia",
            'scraped_date': datetime.now().isoformat(),
            'court': 'Corte Constitucional',
            'case_number': case_info['case_number'],
            'decision_type': case_info.get('decision_type'),
            'decision_date': None,
            'topic': f"Case {case_info['case_number']}",
            'summary': f"Basic information for case {case_info['case_number']}",
            'full_text': f"Case {case_info['case_number']} from the Colombian Constitutional Court. This case was identified through the search API but detailed information was not available.",
            'key_holdings': [],
            'legal_principles': [],
            'cited_laws': [],
            'cited_precedents': [],
            'tags': [case_info['case_number'], case_info.get('decision_type', 'unknown')]
        }
        
        # Generate document hash
        content_for_hash = f"{basic_case.get('case_number', '')}:{basic_case.get('topic', '')}:{basic_case.get('full_text', '')}"
        basic_case['document_hash'] = hashlib.md5(content_for_hash.encode('utf-8')).hexdigest()
        
        return basic_case
    
    async def scrape_jurisprudence(self, max_cases: int = 50) -> List[Dict[str, Any]]:
        """Main method to scrape jurisprudence using the API"""
        logger.info("Starting API-based Constitutional Court jurisprudence scraping...")
        
        # Search for cases using different queries to get variety
        search_queries = [
            'derechos fundamentales',
            'control constitucional',
            'debido proceso',
            'libertad de expresión',
            'principio de igualdad',
            'sentencia tutela',
            'jurisprudencia'
        ]
        
        all_cases = []
        
        for query in search_queries:
            if len(all_cases) >= max_cases:
                break
                
            logger.info(f"Searching with query: '{query}'")
            cases = await self.search_cases(query=query, limit=20, page=1)
            
            if cases:
                # Add query information to cases
                for case in cases:
                    case['search_query'] = query
                
                all_cases.extend(cases)
                logger.info(f"Found {len(cases)} cases for query '{query}'")
            else:
                logger.warning(f"No cases found for query '{query}'")
            
            # Small delay between queries
            await asyncio.sleep(1)
        
        # Remove duplicates based on case number
        unique_cases = []
        seen_numbers = set()
        for case in all_cases:
            case_number = case.get('case_number')
            if case_number and case_number not in seen_numbers:
                unique_cases.append(case)
                seen_numbers.add(case_number)
        
        logger.info(f"Total unique cases found: {len(unique_cases)}")
        
        # Limit to requested number
        unique_cases = unique_cases[:max_cases]
        
        # Get detailed information for each case
        logger.info(f"Getting detailed information for {len(unique_cases)} cases...")
        
        # Process cases with rate limiting
        semaphore = asyncio.Semaphore(5)  # Limit concurrent requests
        
        async def get_case_with_semaphore(case_info):
            async with semaphore:
                await asyncio.sleep(0.5)  # Rate limiting
                return await self.get_case_details(case_info)
        
        tasks = [get_case_with_semaphore(case) for case in unique_cases]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        successful_cases = []
        for result in results:
            if isinstance(result, dict) and result:
                successful_cases.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Task failed with exception: {result}")
        
        logger.info(f"Successfully scraped {len(successful_cases)} cases")
        return successful_cases
    
    def save_scraped_data(self, cases: List[Dict[str, Any]], filename: str = None) -> str:
        """Save scraped cases to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data_pipeline_output/constitutional_court_cases_api_{timestamp}.json"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(cases, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(cases)} cases to {filename}")
        return filename

async def main():
    """Main scraping function"""
    async with APIBasedConstitutionalCourtScraper() as scraper:
        # Scrape jurisprudence
        cases = await scraper.scrape_jurisprudence(max_cases=30)
        
        if cases:
            # Save scraped data
            filename = scraper.save_scraped_data(cases)
            
            print(f"\n{'='*60}")
            print("API-BASED CONSTITUTIONAL COURT SCRAPING COMPLETED")
            print(f"{'='*60}")
            print(f"Total cases scraped: {len(cases)}")
            print(f"Data saved to: {filename}")
            
            # Show sample of scraped data
            if cases:
                sample_case = cases[0]
                print(f"\nSample case:")
                print(f"  Case number: {sample_case.get('case_number', 'N/A')}")
                print(f"  Decision type: {sample_case.get('decision_type', 'N/A')}")
                print(f"  Topic: {sample_case.get('topic', 'N/A')[:100]}...")
                print(f"  Content length: {len(sample_case.get('full_text', ''))} characters")
                print(f"  Search query: {sample_case.get('search_query', 'N/A')}")
        else:
            print("No cases were scraped successfully")

if __name__ == "__main__":
    asyncio.run(main())
