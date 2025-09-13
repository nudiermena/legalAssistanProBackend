#!/usr/bin/env python3
"""
Advanced Colombian Constitutional Court Jurisprudence Scraper
Handles JavaScript-rendered Angular application to extract case numbers and links
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
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AdvancedConstitutionalCourtScraper:
    """Advanced scraper for Colombian Constitutional Court jurisprudence with JS support"""
    
    def __init__(self):
        self.base_url = "https://www.corteconstitucional.gov.co"
        self.search_url = "https://www.corteconstitucional.gov.co/relatoria/buscador-jurisprudencia"
        self.session = None
        self.scraped_cases = []
        
        # Headers to mimic a real browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def get_initial_page(self) -> Optional[str]:
        """Get the initial page to understand the structure"""
        try:
            async with self.session.get(self.search_url) as response:
                if response.status == 200:
                    content = await response.text()
                    logger.info(f"Successfully retrieved initial page: {len(content)} characters")
                    return content
                else:
                    logger.error(f"Failed to retrieve initial page: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error retrieving initial page: {e}")
            return None
    
    async def wait_for_content_load(self, max_wait: int = 30) -> Optional[str]:
        """Wait for JavaScript content to load and return the rendered page"""
        logger.info("Waiting for JavaScript content to load...")
        
        # Try multiple approaches to get the rendered content
        
        # Approach 1: Wait and retry with delays
        for attempt in range(max_wait):
            try:
                async with self.session.get(self.search_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Check if content has loaded (look for case numbers or table structure)
                        if self.has_case_content(content):
                            logger.info(f"Content loaded after {attempt + 1} seconds")
                            return content
                        
                        # Wait before next attempt
                        await asyncio.sleep(1)
                        
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(1)
        
        logger.warning("Content did not load within expected time")
        return None
    
    def has_case_content(self, html_content: str) -> bool:
        """Check if the HTML contains case-related content"""
        # Look for indicators that the content has loaded
        indicators = [
            'sentencia',
            'auto',
            'concepto',
            'caso',
            'jurisprudencia',
            'número',
            'número de expediente',
            'tabla',
            'table',
            'tbody',
            'tr',
            'td'
        ]
        
        content_lower = html_content.lower()
        return any(indicator in content_lower for indicator in indicators)
    
    async def extract_case_links_from_table(self, html_content: str) -> List[Dict[str, Any]]:
        """Extract case links from the rendered table structure"""
        soup = BeautifulSoup(html_content, 'html.parser')
        case_links = []
        
        logger.info("Analyzing page structure for case links...")
        
        # Look for table structures that might contain case information
        tables = soup.find_all('table')
        logger.info(f"Found {len(tables)} tables")
        
        for table_idx, table in enumerate(tables):
            logger.info(f"Analyzing table {table_idx + 1}")
            
            # Look for rows that might contain case information
            rows = table.find_all('tr')
            logger.info(f"  Table {table_idx + 1} has {len(rows)} rows")
            
            for row_idx, row in enumerate(rows):
                cells = row.find_all(['td', 'th'])
                
                # Look for cells that might contain case numbers
                for cell_idx, cell in enumerate(cells):
                    cell_text = cell.get_text(strip=True)
                    
                    # Check if this cell contains a case number
                    if self.is_case_number(cell_text):
                        logger.info(f"    Found case number: {cell_text} in row {row_idx + 1}, cell {cell_idx + 1}")
                        
                        # Look for links in this cell or nearby cells
                        links = cell.find_all('a', href=True)
                        
                        if links:
                            for link in links:
                                href = link['href']
                                link_text = link.get_text(strip=True)
                                
                                case_info = {
                                    'case_number': cell_text,
                                    'link_text': link_text,
                                    'href': href,
                                    'full_url': self.resolve_url(href),
                                    'row': row_idx + 1,
                                    'cell': cell_idx + 1,
                                    'table': table_idx + 1
                                }
                                
                                case_links.append(case_info)
                                logger.info(f"      Found link: {link_text} -> {case_info['full_url']}")
                        
                        # If no links in this cell, check the entire row
                        else:
                            row_links = row.find_all('a', href=True)
                            if row_links:
                                for link in row_links:
                                    href = link['href']
                                    link_text = link.get_text(strip=True)
                                    
                                    case_info = {
                                        'case_number': cell_text,
                                        'link_text': link_text,
                                        'href': href,
                                        'full_url': self.resolve_url(href),
                                        'row': row_idx + 1,
                                        'cell': cell_idx + 1,
                                        'table': table_idx + 1,
                                        'note': 'Link found in row'
                                    }
                                    
                                    case_links.append(case_info)
                                    logger.info(f"      Found link in row: {link_text} -> {case_info['full_url']}")
        
        # Also look for any links that might contain case numbers
        all_links = soup.find_all('a', href=True)
        logger.info(f"Found {len(all_links)} total links on page")
        
        for link in all_links:
            href = link['href']
            link_text = link.get_text(strip=True)
            
            # Check if link text contains a case number
            if self.is_case_number(link_text):
                case_info = {
                    'case_number': link_text,
                    'link_text': link_text,
                    'href': href,
                    'full_url': self.resolve_url(href),
                    'row': 'unknown',
                    'cell': 'unknown',
                    'table': 'unknown',
                    'note': 'Direct link with case number'
                }
                
                # Avoid duplicates
                if not any(c['case_number'] == link_text for c in case_links):
                    case_links.append(case_info)
                    logger.info(f"Found direct case link: {link_text} -> {case_info['full_url']}")
        
        logger.info(f"Total case links found: {len(case_links)}")
        return case_links
    
    def is_case_number(self, text: str) -> bool:
        """Check if text contains a case number pattern"""
        if not text:
            return False
        
        # Colombian Constitutional Court case number patterns
        case_patterns = [
            r'^[CT]-\d+/\d{4}$',  # T-123/2024 or C-456/2023
            r'^Sentencia\s+[CT]-\d+/\d{4}$',  # Sentencia T-123/2024
            r'^Auto\s+\d+/\d{4}$',  # Auto 123/2024
            r'^Concepto\s+\d+/\d{4}$',  # Concepto 123/2024
            r'^[CT]-\d+/\d{4}\s*$',  # With trailing spaces
            r'^[CT]-\d+/\d{4}\s*[-–—]\s*',  # With dash and description
        ]
        
        for pattern in case_patterns:
            if re.match(pattern, text.strip()):
                return True
        
        return False
    
    def resolve_url(self, href: str) -> str:
        """Resolve relative URLs to absolute URLs"""
        if href.startswith('http'):
            return href
        elif href.startswith('/'):
            return self.base_url + href
        else:
            return self.base_url + '/' + href
    
    async def scrape_case_details(self, case_link: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Scrape detailed information from a case page"""
        try:
            url = case_link['full_url']
            logger.info(f"Scraping case details from: {url}")
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    return await self.parse_case_page(content, case_link)
                else:
                    logger.warning(f"Failed to retrieve case page {url}: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error scraping case page {case_link.get('case_number', 'Unknown')}: {e}")
            return None
    
    async def parse_case_page(self, html_content: str, case_link: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse case page content"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            case_data = {
                'source_url': case_link['full_url'],
                'scraped_date': datetime.now().isoformat(),
                'court': 'Corte Constitucional',
                'case_number': case_link['case_number'],
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
            
            # Extract title/topic
            title_elem = soup.find('title')
            if title_elem:
                case_data['topic'] = title_elem.get_text().strip()
                
                # Determine decision type from title
                title_lower = case_data['topic'].lower()
                if 'sentencia' in title_lower:
                    case_data['decision_type'] = 'sentencia'
                elif 'auto' in title_lower:
                    case_data['decision_type'] = 'auto'
                elif 'concepto' in title_lower:
                    case_data['decision_type'] = 'concepto'
            
            # Extract main content
            main_content = soup.find('main') or soup.find('div', class_='content') or soup.find('body')
            if main_content:
                case_data['full_text'] = main_content.get_text(separator=' ', strip=True)
                
                # Create summary
                if case_data['full_text']:
                    case_data['summary'] = case_data['full_text'][:500] + "..." if len(case_data['full_text']) > 500 else case_data['full_text']
                
                # Extract legal concepts
                text_lower = case_data['full_text'].lower()
                legal_concepts = [
                    'derechos fundamentales', 'control constitucional', 'principio de igualdad',
                    'debido proceso', 'libertad de expresión', 'derecho a la vida',
                    'derecho a la salud', 'derecho a la educación', 'derecho al trabajo'
                ]
                
                for concept in legal_concepts:
                    if concept in text_lower:
                        case_data['legal_principles'].append(concept)
                
                # Extract cited laws
                law_patterns = [
                    r'Ley\s+\d+\s+de\s+\d{4}',
                    r'Decreto\s+\d+\s+de\s+\d{4}',
                    r'Resolución\s+\d+\s+de\s+\d{4}'
                ]
                
                for pattern in law_patterns:
                    matches = re.findall(pattern, case_data['full_text'])
                    case_data['cited_laws'].extend(matches)
                
                # Generate tags
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
                logger.warning(f"Case content too short: {case_data.get('case_number', 'Unknown')}")
                return None
                
        except Exception as e:
            logger.error(f"Error parsing case page: {e}")
            return None
    
    async def scrape_jurisprudence(self, max_cases: int = 50) -> List[Dict[str, Any]]:
        """Main method to scrape jurisprudence"""
        logger.info("Starting advanced Constitutional Court jurisprudence scraping...")
        
        # Get the initial page
        initial_content = await self.get_initial_page()
        if not initial_content:
            logger.error("Failed to retrieve initial page")
            return []
        
        # Wait for JavaScript content to load
        rendered_content = await self.wait_for_content_load()
        if not rendered_content:
            logger.warning("Could not get rendered content, trying with initial content")
            rendered_content = initial_content
        
        # Extract case links from the table
        case_links = await self.extract_case_links_from_table(rendered_content)
        if not case_links:
            logger.warning("No case links found")
            return []
        
        # Limit to requested number of cases
        case_links = case_links[:max_cases]
        logger.info(f"Scraping {len(case_links)} case pages...")
        
        # Scrape individual cases with rate limiting
        semaphore = asyncio.Semaphore(3)  # Limit concurrent requests
        
        async def scrape_case_with_semaphore(case_link):
            async with semaphore:
                await asyncio.sleep(1)  # Rate limiting
                return await self.scrape_case_details(case_link)
        
        tasks = [scrape_case_with_semaphore(case_link) for case_link in case_links]
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
            filename = f"data_pipeline_output/constitutional_court_cases_advanced_{timestamp}.json"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(cases, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(cases)} cases to {filename}")
        return filename

async def main():
    """Main scraping function"""
    async with AdvancedConstitutionalCourtScraper() as scraper:
        # Scrape jurisprudence
        cases = await scraper.scrape_jurisprudence(max_cases=30)
        
        if cases:
            # Save scraped data
            filename = scraper.save_scraped_data(cases)
            
            print(f"\n{'='*60}")
            print("ADVANCED CONSTITUTIONAL COURT SCRAPING COMPLETED")
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
