#!/usr/bin/env python3
"""
Headless Browser Scraper for Constitutional Court
Uses Playwright to handle JavaScript-rendered Angular application
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

class HeadlessBrowserScraper:
    """Headless browser scraper for Colombian Constitutional Court jurisprudence"""
    
    def __init__(self):
        self.base_url = "https://www.corteconstitucional.gov.co"
        self.search_url = "https://www.corteconstitucional.gov.co/relatoria/buscador-jurisprudencia"
        self.browser = None
        self.page = None
        self.scraped_cases = []
        
    async def __aenter__(self):
        """Async context manager entry"""
        try:
            # Import playwright
            from playwright.async_api import async_playwright
            
            self.playwright = await async_playwright().start()
            
            # Launch browser in headless mode
            self.browser = await self.playwright.chromium.launch(
                headless=True,  # Set to False for debugging
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
            logger.info("Then run: playwright install chromium")
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
    
    async def navigate_to_search_page(self) -> bool:
        """Navigate to the search page and wait for it to load"""
        try:
            logger.info(f"Navigating to: {self.search_url}")
            
            # Navigate to the page
            await self.page.goto(self.search_url, wait_until='networkidle')
            
            # Wait for the page to be fully loaded
            await self.page.wait_for_load_state('domcontentloaded')
            
            # Additional wait for Angular to initialize
            await asyncio.sleep(3)
            
            # Check if page loaded successfully
            title = await self.page.title()
            logger.info(f"Page title: {title}")
            
            # Wait for any loading indicators to disappear
            try:
                await self.page.wait_for_selector('[class*="loading"], [class*="spinner"]', timeout=5000)
                logger.info("Loading indicator found, waiting for it to disappear...")
                await self.page.wait_for_selector('[class*="loading"], [class*="spinner"]', state='hidden', timeout=10000)
            except:
                logger.info("No loading indicators found or they disappeared quickly")
            
            return True
            
        except Exception as e:
            logger.error(f"Error navigating to search page: {e}")
            return False
    
    async def wait_for_content_to_load(self, max_wait: int = 30) -> bool:
        """Wait for the actual content to load after JavaScript execution"""
        logger.info("Waiting for content to load...")
        
        for attempt in range(max_wait):
            try:
                # Check if we can find any case-related content
                content_indicators = [
                    'table',
                    'tbody',
                    'tr',
                    'td',
                    '[class*="case"]',
                    '[class*="sentencia"]',
                    '[class*="jurisprudencia"]',
                    '[class*="buscador"]'
                ]
                
                for selector in content_indicators:
                    try:
                        element = await self.page.query_selector(selector)
                        if element:
                            logger.info(f"Found content indicator: {selector}")
                            return True
                    except:
                        continue
                
                # Check page content for case numbers
                page_content = await self.page.content()
                if self.has_case_content(page_content):
                    logger.info(f"Case content detected after {attempt + 1} seconds")
                    return True
                
                # Wait before next attempt
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(1)
        
        logger.warning("Content did not load within expected time")
        return False
    
    def has_case_content(self, html_content: str) -> bool:
        """Check if the HTML contains case-related content"""
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
    
    async def interact_with_search_interface(self) -> bool:
        """Try to interact with the search interface to trigger content loading"""
        try:
            logger.info("Attempting to interact with search interface...")
            
            # Look for search input fields
            search_selectors = [
                'input[type="text"]',
                'input[placeholder*="buscar"]',
                'input[placeholder*="search"]',
                'input[name*="search"]',
                'input[name*="buscar"]',
                'input[class*="search"]',
                'input[class*="buscar"]'
            ]
            
            search_input = None
            for selector in search_selectors:
                try:
                    search_input = await self.page.query_selector(selector)
                    if search_input:
                        logger.info(f"Found search input: {selector}")
                        break
                except:
                    continue
            
            if search_input:
                # Try to type a search query
                await search_input.fill('derechos fundamentales')
                await asyncio.sleep(1)
                
                # Look for search button
                search_button_selectors = [
                    'button[type="submit"]',
                    'button:has-text("Buscar")',
                    'button:has-text("Search")',
                    'button[class*="search"]',
                    'button[class*="buscar"]',
                    'input[type="submit"]'
                ]
                
                for selector in search_button_selectors:
                    try:
                        search_button = await self.page.query_selector(selector)
                        if search_button:
                            logger.info(f"Found search button: {selector}")
                            await search_button.click()
                            await asyncio.sleep(3)  # Wait for search results
                            return True
                    except:
                        continue
            
            # If no search interface found, try to scroll to trigger lazy loading
            logger.info("No search interface found, trying to scroll to trigger content...")
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)
            
            return True
            
        except Exception as e:
            logger.error(f"Error interacting with search interface: {e}")
            return False
    
    async def extract_case_links_from_rendered_page(self) -> List[Dict[str, Any]]:
        """Extract case links from the fully rendered page"""
        try:
            logger.info("Extracting case links from rendered page...")
            
            # Get the fully rendered page content
            page_content = await self.page.content()
            
            # Look for table structures
            tables = await self.page.query_selector_all('table')
            logger.info(f"Found {len(tables)} tables")
            
            case_links = []
            
            for table_idx, table in enumerate(tables):
                logger.info(f"Analyzing table {table_idx + 1}")
                
                # Get all rows in the table
                rows = await table.query_selector_all('tr')
                logger.info(f"  Table {table_idx + 1} has {len(rows)} rows")
                
                for row_idx, row in enumerate(rows):
                    # Get all cells in the row
                    cells = await row.query_selector_all('td, th')
                    
                    # Look for cells that might contain case numbers
                    for cell_idx, cell in enumerate(cells):
                        cell_text = await cell.text_content()
                        if cell_text:
                            cell_text = cell_text.strip()
                            
                            # Check if this cell contains a case number
                            if self.is_case_number(cell_text):
                                logger.info(f"    Found case number: {cell_text} in row {row_idx + 1}, cell {cell_idx + 1}")
                                
                                # Look for links in this cell or nearby cells
                                links = await cell.query_selector_all('a[href]')
                                
                                if links:
                                    for link in links:
                                        href = await link.get_attribute('href')
                                        link_text = await link.text_content()
                                        
                                        if href and link_text:
                                            case_info = {
                                                'case_number': cell_text,
                                                'link_text': link_text.strip(),
                                                'href': href,
                                                'full_url': self.resolve_url(href),
                                                'row': row_idx + 1,
                                                'cell': cell_idx + 1,
                                                'table': table_idx + 1
                                            }
                                            
                                            case_links.append(case_info)
                                            logger.info(f"      Found link: {link_text.strip()} -> {case_info['full_url']}")
                                
                                # If no links in this cell, check the entire row
                                else:
                                    row_links = await row.query_selector_all('a[href]')
                                    if row_links:
                                        for link in row_links:
                                            href = await link.get_attribute('href')
                                            link_text = await link.text_content()
                                            
                                            if href and link_text:
                                                case_info = {
                                                    'case_number': cell_text,
                                                    'link_text': link_text.strip(),
                                                    'href': href,
                                                    'full_url': self.resolve_url(href),
                                                    'row': row_idx + 1,
                                                    'cell': cell_idx + 1,
                                                    'table': table_idx + 1,
                                                    'note': 'Link found in row'
                                                }
                                            
                                                case_links.append(case_info)
                                                logger.info(f"      Found link in row: {link_text.strip()} -> {case_info['full_url']}")
            
            # Also look for any links that might contain case numbers
            all_links = await self.page.query_selector_all('a[href]')
            logger.info(f"Found {len(all_links)} total links on page")
            
            for link in all_links:
                try:
                    href = await link.get_attribute('href')
                    link_text = await link.text_content()
                    
                    if href and link_text:
                        link_text = link_text.strip()
                        
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
                except Exception as e:
                    logger.warning(f"Error processing link: {e}")
                    continue
            
            logger.info(f"Total case links found: {len(case_links)}")
            return case_links
            
        except Exception as e:
            logger.error(f"Error extracting case links: {e}")
            return []
    
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
            
            # Navigate to case page
            await self.page.goto(url, wait_until='networkidle')
            await self.page.wait_for_load_state('domcontentloaded')
            await asyncio.sleep(2)
            
            # Get page content
            page_content = await self.page.content()
            return await self.parse_case_page(page_content, case_link)
                    
        except Exception as e:
            logger.error(f"Error scraping case page {case_link.get('case_number', 'Unknown')}: {e}")
            return None
    
    async def parse_case_page(self, html_content: str, case_link: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse case page content"""
        try:
            from bs4 import BeautifulSoup
            
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
    
    async def scrape_jurisprudence(self, max_cases: int = 30) -> List[Dict[str, Any]]:
        """Main method to scrape jurisprudence using headless browser"""
        logger.info("Starting headless browser Constitutional Court jurisprudence scraping...")
        
        # Navigate to search page
        if not await self.navigate_to_search_page():
            logger.error("Failed to navigate to search page")
            return []
        
        # Wait for content to load
        if not await self.wait_for_content_to_load():
            logger.warning("Content did not load automatically")
            
            # Try to interact with search interface
            if not await self.interact_with_search_interface():
                logger.warning("Could not interact with search interface")
        
        # Extract case links from the rendered page
        case_links = await self.extract_case_links_from_rendered_page()
        if not case_links:
            logger.warning("No case links found")
            return []
        
        # Limit to requested number of cases
        case_links = case_links[:max_cases]
        logger.info(f"Scraping {len(case_links)} case pages...")
        
        # Scrape individual cases
        successful_cases = []
        for i, case_link in enumerate(case_links):
            try:
                logger.info(f"Scraping case {i+1}/{len(case_links)}: {case_link['case_number']}")
                
                case_data = await self.scrape_case_details(case_link)
                if case_data:
                    successful_cases.append(case_data)
                
                # Small delay between cases
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error scraping case {case_link.get('case_number', 'Unknown')}: {e}")
                continue
        
        logger.info(f"Successfully scraped {len(successful_cases)} cases")
        return successful_cases
    
    def save_scraped_data(self, cases: List[Dict[str, Any]], filename: str = None) -> str:
        """Save scraped cases to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data_pipeline_output/constitutional_court_cases_headless_{timestamp}.json"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(cases, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(cases)} cases to {filename}")
        return filename

async def main():
    """Main scraping function"""
    try:
        async with HeadlessBrowserScraper() as scraper:
            # Scrape jurisprudence
            cases = await scraper.scrape_jurisprudence(max_cases=20)
            
            if cases:
                # Save scraped data
                filename = scraper.save_scraped_data(cases)
                
                print(f"\n{'='*60}")
                print("HEADLESS BROWSER SCRAPING COMPLETED")
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
