#!/usr/bin/env python3
"""
Improved Constitutional Court Scraper
Extracts full case information including topics, summaries, and details
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import os
import sys
from pathlib import Path
import re
import hashlib

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ImprovedConstitutionalScraper:
    """Improved scraper for Colombian Constitutional Court jurisprudence"""
    
    def __init__(self):
        self.base_url = "https://www.corteconstitucional.gov.co"
        self.search_url = "https://www.corteconstitucional.gov.co/relatoria/buscador-jurisprudencia"
        self.browser = None
        self.page = None
        self.scraped_cases = []
        
    async def __aenter__(self):
        """Async context manager entry"""
        try:
            from playwright.async_api import async_playwright
            
            self.playwright = await async_playwright().start()
            
            # Launch browser in headless mode
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]
            )
            
            # Create new page
            self.page = await self.browser.new_page()
            
            # Set viewport
            await self.page.set_viewport_size({"width": 1920, "height": 1080})
            
            # Set user agent
            await self.page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            logger.info("Headless browser initialized successfully")
            return self
            
        except ImportError:
            logger.error("Playwright not installed. Please install it with: pip install playwright")
            raise
        except Exception as e:
            logger.error(f"Error initializing browser: {e}")
            raise
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
            logger.info("Browser resources cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up browser: {e}")
    
    async def search_for_cases(self, search_query: str = "derechos fundamentales", max_pages: int = 3) -> List[Dict[str, Any]]:
        """Search for cases and extract case information"""
        try:
            logger.info(f"Searching for cases with query: '{search_query}'")
            
            # Navigate to search page
            await self.page.goto(self.search_url, wait_until='networkidle')
            await self.page.wait_for_load_state('domcontentloaded')
            await asyncio.sleep(3)
            
            # Find and fill search input
            search_input = await self.page.query_selector('input[placeholder*="buscar"]')
            if not search_input:
                logger.error("Search input not found")
                return []
            
            await search_input.fill(search_query)
            await asyncio.sleep(1)
            
            # Find and click search button
            search_button = await self.page.query_selector('button[type="submit"]')
            if not search_button:
                logger.error("Search button not found")
                return []
            
            await search_button.click()
            logger.info("Search button clicked, waiting for results...")
            await asyncio.sleep(5)
            
            all_cases = []
            
            # Extract cases from multiple pages
            for page_num in range(1, max_pages + 1):
                logger.info(f"Extracting cases from page {page_num}")
                
                # Extract cases from current page
                page_cases = await self.extract_cases_from_current_page()
                if page_cases:
                    all_cases.extend(page_cases)
                    logger.info(f"Found {len(page_cases)} cases on page {page_num}")
                else:
                    logger.warning(f"No cases found on page {page_num}")
                
                # Try to go to next page if not on last page
                if page_num < max_pages:
                    next_page_button = await self.page.query_selector('a[aria-label="Next page"], a:has-text(">>>")')
                    if next_page_button:
                        await next_page_button.click()
                        await asyncio.sleep(3)
                    else:
                        logger.info("No next page button found, stopping pagination")
                        break
            
            logger.info(f"Total cases extracted: {len(all_cases)}")
            return all_cases
            
        except Exception as e:
            logger.error(f"Error searching for cases: {e}")
            return []
    
    async def extract_cases_from_current_page(self) -> List[Dict[str, Any]]:
        """Extract case information from the current page"""
        try:
            # Get the full page text content
            page_text = await self.page.text_content('body')
            
            # Extract case information using regex patterns
            cases = self.extract_cases_from_text(page_text)
            
            if cases:
                logger.info(f"Extracted {len(cases)} cases from page text")
                return cases
            else:
                logger.warning("No cases found on current page")
                return []
            
        except Exception as e:
            logger.error(f"Error extracting cases from current page: {e}")
            return []
    
    def extract_cases_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract case information from text content using regex patterns"""
        cases = []
        
        # Pattern to find case blocks - look for case numbers followed by content
        # This pattern looks for case numbers and captures the following text until the next case number
        case_blocks = re.split(r'(?=([CTSU]-\d+/\d{2,4}))', text)
        
        for i in range(1, len(case_blocks), 2):  # Skip even indices (empty strings)
            if i + 1 < len(case_blocks):
                case_number = case_blocks[i]
                case_content = case_blocks[i + 1] if i + 1 < len(case_blocks) else ""
                
                if case_number and self.is_valid_case_number(case_number):
                    case_info = self.parse_case_block(case_number, case_content)
                    if case_info:
                        cases.append(case_info)
        
        # If the above method didn't work, try a simpler approach
        if not cases:
            logger.info("Trying alternative case extraction method...")
            cases = self.extract_cases_simple(text)
        
        return cases
    
    def extract_cases_simple(self, text: str) -> List[Dict[str, Any]]:
        """Simple case extraction method"""
        cases = []
        
        # Find all case numbers in the text
        case_numbers = re.findall(r'([CTSU]-\d+/\d{2,4})', text)
        
        for case_number in case_numbers:
            # Find the context around this case number
            case_match = re.search(rf'{re.escape(case_number)}[^CTSU]*?(?=[CTSU]-\d+/\d{{2,4}}|$)', text, re.DOTALL)
            
            if case_match:
                case_content = case_match.group(0)
                case_info = self.parse_case_block(case_number, case_content)
                if case_info:
                    cases.append(case_info)
        
        return cases
    
    def is_valid_case_number(self, case_number: str) -> bool:
        """Check if a case number is valid"""
        if not case_number:
            return False
        
        # Clean the case number
        clean_number = case_number.strip()
        
        # Check if it matches the expected pattern
        pattern = r'^[CTSU]-\d+/\d{2,4}$'
        return bool(re.match(pattern, clean_number))
    
    def parse_case_block(self, case_number: str, case_content: str) -> Optional[Dict[str, Any]]:
        """Parse a case block and extract information"""
        try:
            # Clean the case number
            case_number = case_number.strip()
            
            # Determine decision type
            decision_type = 'unknown'
            if 'T-' in case_number:
                decision_type = 'tutela'
            elif 'C-' in case_number:
                decision_type = 'constitucionalidad'
            elif 'SU-' in case_number:
                decision_type = 'sentencia_unificacion'
            
            # Extract year
            year_match = re.search(r'/(\d{2,4})', case_number)
            year = year_match.group(1) if year_match else None
            
            # Normalize year to 4 digits
            if year and len(year) == 2:
                year = '20' + year if int(year) < 50 else '19' + year
            
            # Extract additional information from case content
            case_info = {
                'case_number': case_number,
                'decision_type': decision_type,
                'year': year,
                'full_text': case_content,
                'source_url': self.search_url,
                'scraped_date': datetime.now().isoformat(),
                'court': 'Corte Constitucional',
                'document_hash': hashlib.md5(f"{case_number}:{case_content}".encode('utf-8')).hexdigest()
            }
            
            # Extract topic/theme
            topic_match = re.search(r'Tema:\s*([^\.]+)', case_content)
            if topic_match:
                case_info['topic'] = topic_match.group(1).strip()
            
            # Extract date
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', case_content)
            if date_match:
                case_info['decision_date'] = date_match.group(1)
            
            # Extract summary
            summary_match = re.search(r'Resumen:\s*([^\.]+)', case_content)
            if summary_match:
                case_info['summary'] = summary_match.group(1).strip()
            
            # Extract magistrate
            magistrate_match = re.search(r'Magistrado/a\s+([^\.]+)', case_content)
            if magistrate_match:
                case_info['magistrate'] = magistrate_match.group(1).strip()
            
            # Extract relevance score if available
            relevance_match = re.search(r'(\d+\.\d+)', case_content)
            if relevance_match:
                case_info['relevance_score'] = float(relevance_match.group(1))
            
            return case_info
            
        except Exception as e:
            logger.warning(f"Error parsing case block for {case_number}: {e}")
            return None
    
    async def scrape_jurisprudence(self, search_queries: List[str] = None, max_pages_per_query: int = 3) -> List[Dict[str, Any]]:
        """Main method to scrape jurisprudence"""
        if search_queries is None:
            search_queries = [
                'derechos fundamentales',
                'control constitucional',
                'debido proceso',
                'libertad de expresión',
                'principio de igualdad'
            ]
        
        logger.info("Starting Improved Constitutional Court jurisprudence scraping...")
        
        all_cases = []
        
        for query in search_queries:
            try:
                logger.info(f"Searching with query: '{query}'")
                cases = await self.search_for_cases(query, max_pages_per_query)
                
                if cases:
                    # Add query information to cases
                    for case in cases:
                        case['search_query'] = query
                    
                    all_cases.extend(cases)
                    logger.info(f"Found {len(cases)} cases for query '{query}'")
                else:
                    logger.warning(f"No cases found for query '{query}'")
                
                # Small delay between queries
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error with query '{query}': {e}")
                continue
        
        # Remove duplicates based on case number
        unique_cases = []
        seen_numbers = set()
        for case in all_cases:
            case_number = case.get('case_number')
            if case_number and case_number not in seen_numbers:
                unique_cases.append(case)
                seen_numbers.add(case_number)
        
        logger.info(f"Total unique cases found: {len(unique_cases)}")
        return unique_cases
    
    def save_scraped_data(self, cases: List[Dict[str, Any]], filename: str = None) -> str:
        """Save scraped cases to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data_pipeline_output/constitutional_court_cases_improved_{timestamp}.json"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(cases, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(cases)} cases to {filename}")
        return filename

async def main():
    """Main scraping function"""
    try:
        async with ImprovedConstitutionalScraper() as scraper:
            # Scrape jurisprudence
            cases = await scraper.scrape_jurisprudence(max_pages_per_query=2)
            
            if cases:
                # Save scraped data
                filename = scraper.save_scraped_data(cases)
                
                print(f"\n{'='*60}")
                print("IMPROVED CONSTITUTIONAL COURT SCRAPING COMPLETED")
                print(f"{'='*60}")
                print(f"Total cases scraped: {len(cases)}")
                print(f"Data saved to: {filename}")
                
                # Show sample of scraped data
                if cases:
                    print(f"\nSample cases:")
                    for i, case in enumerate(cases[:5]):
                        print(f"  {i+1}. {case.get('case_number', 'N/A')} - {case.get('decision_type', 'N/A')}")
                        if case.get('topic'):
                            print(f"     Topic: {case.get('topic', 'N/A')[:80]}...")
                        if case.get('year'):
                            print(f"     Year: {case.get('year', 'N/A')}")
                        if case.get('summary'):
                            print(f"     Summary: {case.get('summary', 'N/A')[:100]}...")
            else:
                print("No cases were scraped successfully")
                
    except ImportError:
        print("\n" + "="*60)
        print("PLAYWRIGHT NOT INSTALLED")
        print("="*60)
        print("To use this scraper, you need to install Playwright:")
        print("1. pip install playwright")
        print("2. playwright install chromium")
        print("\nThen run this script again.")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    asyncio.run(main())
