#!/usr/bin/env python3
"""
Debug Headless Browser Scraper
Captures screenshots and examines rendered content to debug case number detection
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

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DebugHeadlessBrowserScraper:
    """Debug headless browser scraper for Constitutional Court"""
    
    def __init__(self):
        self.base_url = "https://www.corteconstitucional.gov.co"
        self.search_url = "https://www.corteconstitucional.gov.co/relatoria/buscador-jurisprudencia"
        self.browser = None
        self.page = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        try:
            from playwright.async_api import async_playwright
            
            self.playwright = await async_playwright().start()
            
            # Launch browser in headless mode (set to False for debugging)
            self.browser = await self.playwright.chromium.launch(
                headless=False,  # Set to False to see what's happening
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
            
            logger.info("Debug headless browser initialized successfully")
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
    
    async def debug_page_content(self):
        """Debug the page content to understand its structure"""
        try:
            logger.info(f"Navigating to: {self.search_url}")
            
            # Navigate to the page
            await self.page.goto(self.search_url, wait_until='networkidle')
            await self.page.wait_for_load_state('domcontentloaded')
            
            # Wait for Angular to initialize
            await asyncio.sleep(5)
            
            # Get page title
            title = await self.page.title()
            logger.info(f"Page title: {title}")
            
            # Capture screenshot
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"data_pipeline_output/page_screenshot_{timestamp}.png"
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
            await self.page.screenshot(path=screenshot_path, full_page=True)
            logger.info(f"Screenshot saved to: {screenshot_path}")
            
            # Get page content
            page_content = await self.page.content()
            
            # Save HTML content
            html_path = f"data_pipeline_output/page_content_{timestamp}.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(page_content)
            logger.info(f"HTML content saved to: {html_path}")
            
            # Analyze page structure
            await self.analyze_page_structure()
            
            # Look for specific elements
            await self.look_for_specific_elements()
            
            # Try to find any text that might be case numbers
            await self.search_for_case_patterns()
            
            # Wait for user to examine the page
            logger.info("Browser window is open for manual inspection. Press Enter to continue...")
            input()
            
        except Exception as e:
            logger.error(f"Error debugging page content: {e}")
    
    async def analyze_page_structure(self):
        """Analyze the structure of the page"""
        try:
            logger.info("Analyzing page structure...")
            
            # Count different types of elements
            element_counts = {}
            
            element_types = [
                'div', 'span', 'p', 'a', 'table', 'tr', 'td', 'th',
                'input', 'button', 'form', 'section', 'article', 'main'
            ]
            
            for element_type in element_types:
                try:
                    count = await self.page.locator(element_type).count()
                    element_counts[element_type] = count
                except:
                    element_counts[element_type] = 0
            
            logger.info("Element counts:")
            for element_type, count in element_counts.items():
                if count > 0:
                    logger.info(f"  {element_type}: {count}")
            
            # Look for forms
            forms = await self.page.locator('form').count()
            logger.info(f"Forms found: {forms}")
            
            if forms > 0:
                for i in range(forms):
                    form = self.page.locator('form').nth(i)
                    try:
                        form_action = await form.get_attribute('action')
                        form_method = await form.get_attribute('method')
                        logger.info(f"  Form {i+1}: action={form_action}, method={form_method}")
                    except:
                        pass
            
        except Exception as e:
            logger.error(f"Error analyzing page structure: {e}")
    
    async def look_for_specific_elements(self):
        """Look for specific elements that might contain case data"""
        try:
            logger.info("Looking for specific elements...")
            
            # Look for search-related elements
            search_selectors = [
                'input[type="text"]',
                'input[placeholder*="buscar"]',
                'input[placeholder*="search"]',
                'input[name*="search"]',
                'input[name*="buscar"]',
                'input[class*="search"]',
                'input[class*="buscar"]',
                'button[type="submit"]',
                'button:has-text("Buscar")',
                'button:has-text("Search")'
            ]
            
            for selector in search_selectors:
                try:
                    count = await self.page.locator(selector).count()
                    if count > 0:
                        logger.info(f"  Found {selector}: {count} elements")
                        
                        # Get details of first element
                        element = self.page.locator(selector).first()
                        try:
                            placeholder = await element.get_attribute('placeholder')
                            name = await element.get_attribute('name')
                            class_attr = await element.get_attribute('class')
                            value = await element.get_attribute('value')
                            logger.info(f"    placeholder: {placeholder}, name: {name}, class: {class_attr}, value: {value}")
                        except:
                            pass
                except:
                    continue
            
            # Look for table-like structures
            table_selectors = [
                'table',
                '[class*="table"]',
                '[class*="grid"]',
                '[class*="list"]',
                '[class*="results"]'
            ]
            
            for selector in table_selectors:
                try:
                    count = await self.page.locator(selector).count()
                    if count > 0:
                        logger.info(f"  Found {selector}: {count} elements")
                except:
                    continue
            
        except Exception as e:
            logger.error(f"Error looking for specific elements: {e}")
    
    async def search_for_case_patterns(self):
        """Search for case number patterns in the page content"""
        try:
            logger.info("Searching for case number patterns...")
            
            # Get all text content from the page
            page_text = await self.page.text_content('body')
            
            # Look for case number patterns
            case_patterns = [
                r'[CT]-\d+/\d{4}',  # T-123/2024 or C-456/2023
                r'Sentencia\s+[CT]-\d+/\d{4}',  # Sentencia T-123/2024
                r'Auto\s+\d+/\d{4}',  # Auto 123/2024
                r'Concepto\s+\d+/\d{4}',  # Concepto 123/2024
                r'\d{4}-\d+',  # Alternative format: 2024-123
                r'[A-Z]+\s+\d+/\d{4}',  # Any uppercase letters followed by numbers
            ]
            
            found_patterns = []
            for pattern in case_patterns:
                matches = re.findall(pattern, page_text)
                if matches:
                    logger.info(f"  Pattern {pattern}: Found {len(matches)} matches")
                    for match in matches[:5]:  # Show first 5
                        logger.info(f"    - {match}")
                        found_patterns.append(match)
                else:
                    logger.info(f"  Pattern {pattern}: No matches")
            
            if not found_patterns:
                logger.info("No case number patterns found. Looking for any text that might be case numbers...")
                
                # Look for any text that might be case numbers
                words = re.findall(r'\b[A-Z]+-\d+/\d{4}\b', page_text)
                if words:
                    logger.info(f"Found potential case numbers: {words[:10]}")
                else:
                    logger.info("No potential case numbers found")
            
            # Save text content for manual inspection
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            text_path = f"data_pipeline_output/page_text_{timestamp}.txt"
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(page_text)
            logger.info(f"Page text content saved to: {text_path}")
            
        except Exception as e:
            logger.error(f"Error searching for case patterns: {e}")
    
    async def try_interactive_search(self):
        """Try to interact with the search interface"""
        try:
            logger.info("Trying interactive search...")
            
            # Look for search input
            search_input = None
            search_selectors = [
                'input[type="text"]',
                'input[placeholder*="buscar"]',
                'input[placeholder*="search"]'
            ]
            
            for selector in search_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        search_input = element
                        logger.info(f"Found search input: {selector}")
                        break
                except:
                    continue
            
            if search_input:
                # Try to type in the search input
                await search_input.fill('derechos fundamentales')
                await asyncio.sleep(2)
                
                # Look for search button
                search_button = None
                button_selectors = [
                    'button[type="submit"]',
                    'button:has-text("Buscar")',
                    'button:has-text("Search")'
                ]
                
                for selector in button_selectors:
                    try:
                        element = await self.page.query_selector(selector)
                        if element:
                            search_button = element
                            logger.info(f"Found search button: {selector}")
                            break
                    except:
                        continue
                
                if search_button:
                    # Click search button
                    await search_button.click()
                    logger.info("Clicked search button, waiting for results...")
                    await asyncio.sleep(5)
                    
                    # Take another screenshot
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot_path = f"data_pipeline_output/search_results_{timestamp}.png"
                    await self.page.screenshot(path=screenshot_path, full_page=True)
                    logger.info(f"Search results screenshot saved to: {screenshot_path}")
                    
                    # Check if content appeared
                    await self.search_for_case_patterns()
                else:
                    logger.info("No search button found")
            else:
                logger.info("No search input found")
                
        except Exception as e:
            logger.error(f"Error trying interactive search: {e}")

async def main():
    """Main debug function"""
    try:
        async with DebugHeadlessBrowserScraper() as scraper:
            # Debug the page content
            await scraper.debug_page_content()
            
            # Try interactive search
            await scraper.try_interactive_search()
            
            print("\nDebug session completed. Check the generated files for analysis.")
            
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
