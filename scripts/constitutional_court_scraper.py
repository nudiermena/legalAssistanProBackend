#!/usr/bin/env python3
"""
Colombian Constitutional Court Jurisprudence Scraper
Scrapes jurisprudence data from the Constitutional Court's search page
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

class ConstitutionalCourtScraper:
    """Scraper for Colombian Constitutional Court jurisprudence"""
    
    def __init__(self):
        self.base_url = "https://www.corteconstitucional.gov.co"
        self.search_url = "https://www.corteconstitucional.gov.co/relatoria/buscador-jurisprudencia"
        self.session = None
        self.scraped_cases = []
        
        # Headers to mimic a real browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def get_search_page(self) -> Optional[str]:
        """Get the main search page to understand the structure"""
        try:
            async with self.session.get(self.search_url) as response:
                if response.status == 200:
                    content = await response.text()
                    logger.info(f"Successfully retrieved search page: {len(content)} characters")
                    return content
                else:
                    logger.error(f"Failed to retrieve search page: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error retrieving search page: {e}")
            return None
    
    def extract_case_links(self, html_content: str) -> List[str]:
        """Extract case links from the search page"""
        soup = BeautifulSoup(html_content, 'html.parser')
        case_links = []
        
        # Look for various patterns that might contain case links
        # This will need to be adjusted based on the actual page structure
        
        # Pattern 1: Direct links to cases
        for link in soup.find_all('a', href=True):
            href = link['href']
            if any(keyword in href.lower() for keyword in ['sentencia', 'auto', 'concepto', 'caso']):
                if href.startswith('/'):
                    full_url = self.base_url + href
                elif href.startswith('http'):
                    full_url = href
                else:
                    full_url = self.base_url + '/' + href
                case_links.append(full_url)
        
        # Pattern 2: Look for case numbers in text
        case_patterns = [
            r'Sentencia\s+[CT]-\d+/\d{4}',
            r'Auto\s+\d+/\d{4}',
            r'Concepto\s+\d+/\d{4}',
            r'Caso\s+\d+/\d{4}'
        ]
        
        for pattern in case_patterns:
            matches = re.findall(pattern, html_content)
            for match in matches:
                # Create a search URL for this case
                search_url = f"{self.search_url}?q={match}"
                case_links.append(search_url)
        
        # Remove duplicates and limit to reasonable number
        unique_links = list(set(case_links))[:50]  # Limit to 50 cases for initial testing
        logger.info(f"Found {len(unique_links)} potential case links")
        
        return unique_links
    
    async def scrape_case_page(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape individual case page"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    return await self.parse_case_content(content, url)
                else:
                    logger.warning(f"Failed to retrieve case page {url}: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error scraping case page {url}: {e}")
            return None
    
    async def parse_case_content(self, html_content: str, url: str) -> Optional[Dict[str, Any]]:
        """Parse case content from HTML"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract case information
            case_data = {
                'source_url': url,
                'scraped_date': datetime.now().isoformat(),
                'court': 'Corte Constitucional',
                'case_number': None,
                'decision_type': None,
                'decision_date': None,
                'topic': None,
                'summary': None,
                'full_text': None,
                'key_holdings': [],
                'legal_principles': [],
                'cited_laws': [],
                'cited_precedents': [],
                'tags': []
            }
            
            # Extract case number and type
            title_elem = soup.find('title')
            if title_elem:
                title_text = title_elem.get_text().strip()
                case_data['topic'] = title_text
                
                # Extract case number from title
                case_patterns = [
                    r'[CT]-\d+/\d{4}',
                    r'Sentencia\s+([CT]-\d+/\d{4})',
                    r'Auto\s+(\d+/\d{4})',
                    r'Concepto\s+(\d+/\d{4})'
                ]
                
                for pattern in case_patterns:
                    match = re.search(pattern, title_text)
                    if match:
                        case_data['case_number'] = match.group(1) if len(match.groups()) > 0 else match.group(0)
                        break
                
                # Determine decision type
                if 'sentencia' in title_text.lower():
                    case_data['decision_type'] = 'sentencia'
                elif 'auto' in title_text.lower():
                    case_data['decision_type'] = 'auto'
                elif 'concepto' in title_text.lower():
                    case_data['decision_type'] = 'concepto'
            
            # Extract main content
            main_content = soup.find('main') or soup.find('div', class_='content') or soup.find('body')
            if main_content:
                # Get full text
                case_data['full_text'] = main_content.get_text(separator=' ', strip=True)
                
                # Create summary (first 500 characters)
                if case_data['full_text']:
                    case_data['summary'] = case_data['full_text'][:500] + "..." if len(case_data['full_text']) > 500 else case_data['full_text']
                
                # Extract key holdings and legal principles
                text_lower = case_data['full_text'].lower()
                
                # Look for key legal concepts
                legal_concepts = [
                    'derechos fundamentales', 'control constitucional', 'principio de igualdad',
                    'debido proceso', 'libertad de expresión', 'derecho a la vida',
                    'derecho a la salud', 'derecho a la educación', 'derecho al trabajo'
                ]
                
                for concept in legal_concepts:
                    if concept in text_lower:
                        case_data['legal_principles'].append(concept)
                
                # Extract cited laws (look for law references)
                law_patterns = [
                    r'Ley\s+\d+\s+de\s+\d{4}',
                    r'Decreto\s+\d+\s+de\s+\d{4}',
                    r'Resolución\s+\d+\s+de\s+\d{4}'
                ]
                
                for pattern in law_patterns:
                    matches = re.findall(pattern, case_data['full_text'])
                    case_data['cited_laws'].extend(matches)
                
                # Generate tags based on content
                if case_data['legal_principles']:
                    case_data['tags'].extend(case_data['legal_principles'])
                if case_data['decision_type']:
                    case_data['tags'].append(case_data['decision_type'])
                if case_data['case_number']:
                    case_data['tags'].append(case_data['case_number'])
            
            # Generate document hash
            content_for_hash = f"{case_data.get('case_number', '')}:{case_data.get('topic', '')}:{case_data.get('full_text', '')}"
            case_data['document_hash'] = hashlib.md5(content_for_hash.encode('utf-8')).hexdigest()
            
            # Validate case data
            if case_data['full_text'] and len(case_data['full_text']) > 100:
                logger.info(f"Successfully parsed case: {case_data.get('case_number', 'Unknown')}")
                return case_data
            else:
                logger.warning(f"Case content too short or empty: {case_data.get('case_number', 'Unknown')}")
                return None
                
        except Exception as e:
            logger.error(f"Error parsing case content: {e}")
            return None
    
    async def scrape_jurisprudence(self, max_cases: int = 100) -> List[Dict[str, Any]]:
        """Main method to scrape jurisprudence"""
        logger.info("Starting Constitutional Court jurisprudence scraping...")
        
        # Get the search page
        search_content = await self.get_search_page()
        if not search_content:
            logger.error("Failed to retrieve search page")
            return []
        
        # Extract case links
        case_links = self.extract_case_links(search_content)
        if not case_links:
            logger.warning("No case links found")
            return []
        
        # Scrape individual cases
        logger.info(f"Scraping {len(case_links)} case pages...")
        
        # Process cases concurrently with rate limiting
        semaphore = asyncio.Semaphore(5)  # Limit concurrent requests
        
        async def scrape_case_with_semaphore(url):
            async with semaphore:
                await asyncio.sleep(0.5)  # Rate limiting
                return await self.scrape_case_page(url)
        
        tasks = [scrape_case_with_semaphore(url) for url in case_links[:max_cases]]
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
            filename = f"data_pipeline_output/constitutional_court_cases_{timestamp}.json"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(cases, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(cases)} cases to {filename}")
        return filename

async def main():
    """Main scraping function"""
    async with ConstitutionalCourtScraper() as scraper:
        # Scrape jurisprudence
        cases = await scraper.scrape_jurisprudence(max_cases=50)
        
        if cases:
            # Save scraped data
            filename = scraper.save_scraped_data(cases)
            
            print(f"\n{'='*60}")
            print("CONSTITUTIONAL COURT SCRAPING COMPLETED")
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
        else:
            print("No cases were scraped successfully")

if __name__ == "__main__":
    asyncio.run(main())
