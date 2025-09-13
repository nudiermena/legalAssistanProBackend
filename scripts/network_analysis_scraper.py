#!/usr/bin/env python3
"""
Network Analysis Scraper for Constitutional Court
Analyzes network requests to find API endpoints that provide case data
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NetworkAnalysisScraper:
    """Analyzes network requests to find case data endpoints"""
    
    def __init__(self):
        self.base_url = "https://www.corteconstitucional.gov.co"
        self.search_url = "https://www.corteconstitucional.gov.co/relatoria/buscador-jurisprudencia"
        self.session = None
        
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
    
    async def analyze_page_network(self) -> Dict[str, Any]:
        """Analyze the page to understand its network structure"""
        logger.info("Analyzing page network structure...")
        
        try:
            # Get the main page
            async with self.session.get(self.search_url) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Look for JavaScript files that might contain API endpoints
                    js_files = self.extract_js_files(content)
                    logger.info(f"Found {len(js_files)} JavaScript files")
                    
                    # Look for potential API endpoints in the HTML
                    potential_apis = self.find_potential_apis(content)
                    logger.info(f"Found {len(potential_apis)} potential API endpoints")
                    
                    # Look for configuration or data in the HTML
                    config_data = self.extract_config_data(content)
                    
                    return {
                        'js_files': js_files,
                        'potential_apis': potential_apis,
                        'config_data': config_data,
                        'content_length': len(content)
                    }
                else:
                    logger.error(f"Failed to retrieve page: {response.status}")
                    return {}
                    
        except Exception as e:
            logger.error(f"Error analyzing page: {e}")
            return {}
    
    def extract_js_files(self, html_content: str) -> List[str]:
        """Extract JavaScript file references from HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        js_files = []
        
        # Look for script tags
        scripts = soup.find_all('script', src=True)
        for script in scripts:
            src = script['src']
            if src.endswith('.js') or 'chunk' in src:
                js_files.append(src)
        
        # Look for modulepreload links
        module_links = soup.find_all('link', rel='modulepreload')
        for link in module_links:
            href = link.get('href', '')
            if href.endswith('.js'):
                js_files.append(href)
        
        return js_files
    
    def find_potential_apis(self, html_content: str) -> List[str]:
        """Find potential API endpoints in the HTML content"""
        potential_apis = []
        
        # Look for common API patterns
        api_patterns = [
            r'["\']/api/[^"\']+["\']',
            r'["\']/relatoria/[^"\']+["\']',
            r'["\']/jurisprudencia/[^"\']+["\']',
            r'["\']/buscador/[^"\']+["\']',
            r'["\']/search[^"\']*["\']',
            r'["\']/cases[^"\']*["\']',
            r'["\']/sentencias[^"\']*["\']'
        ]
        
        for pattern in api_patterns:
            matches = re.findall(pattern, html_content)
            potential_apis.extend(matches)
        
        return list(set(potential_apis))
    
    def extract_config_data(self, html_content: str) -> Dict[str, Any]:
        """Extract configuration data from HTML"""
        config_data = {}
        
        # Look for JSON data in script tags
        soup = BeautifulSoup(html_content, 'html.parser')
        scripts = soup.find_all('script')
        
        for script in scripts:
            if script.string:
                # Look for JSON configuration
                json_patterns = [
                    r'window\.config\s*=\s*({[^}]+})',
                    r'window\.data\s*=\s*({[^}]+})',
                    r'window\.app\s*=\s*({[^}]+})',
                    r'const\s+config\s*=\s*({[^}]+})',
                    r'var\s+config\s*=\s*({[^}]+})'
                ]
                
                for pattern in json_patterns:
                    matches = re.findall(pattern, script.string)
                    if matches:
                        try:
                            config_data['script_config'] = matches[0]
                        except:
                            pass
        
        return config_data
    
    async def test_potential_endpoints(self, endpoints: List[str]) -> List[Dict[str, Any]]:
        """Test potential API endpoints to see which ones return case data"""
        logger.info(f"Testing {len(endpoints)} potential API endpoints...")
        
        working_endpoints = []
        
        for endpoint in endpoints:
            try:
                # Clean the endpoint
                clean_endpoint = endpoint.strip('"\'')
                if clean_endpoint.startswith('/'):
                    full_url = self.base_url + clean_endpoint
                else:
                    full_url = self.base_url + '/' + clean_endpoint
                
                logger.info(f"Testing endpoint: {full_url}")
                
                # Try to get data from the endpoint
                async with self.session.get(full_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Check if this looks like case data
                        if self.looks_like_case_data(content):
                            working_endpoints.append({
                                'endpoint': clean_endpoint,
                                'full_url': full_url,
                                'status': response.status,
                                'content_length': len(content),
                                'content_preview': content[:200] + "..." if len(content) > 200 else content
                            })
                            logger.info(f"  ✓ Working endpoint: {clean_endpoint}")
                        else:
                            logger.info(f"  ✗ Not case data: {clean_endpoint}")
                    else:
                        logger.info(f"  ✗ Failed: {clean_endpoint} (Status: {response.status})")
                
                # Small delay between requests
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.warning(f"Error testing endpoint {endpoint}: {e}")
        
        return working_endpoints
    
    def looks_like_case_data(self, content: str) -> bool:
        """Check if content looks like case data"""
        # Look for indicators of case data
        case_indicators = [
            'sentencia',
            'auto',
            'concepto',
            'caso',
            'jurisprudencia',
            'número',
            'expediente',
            'corte constitucional',
            'derechos fundamentales',
            'control constitucional'
        ]
        
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in case_indicators)
    
    async def try_search_api(self) -> Optional[Dict[str, Any]]:
        """Try to find and use a search API endpoint"""
        logger.info("Attempting to find search API...")
        
        # Common search API patterns for Angular apps
        search_endpoints = [
            '/api/search',
            '/api/jurisprudencia/search',
            '/api/sentencias/search',
            '/api/cases/search',
            '/relatoria/api/search',
            '/jurisprudencia/api/search',
            '/api/buscador',
            '/api/relatoria/search'
        ]
        
        for endpoint in search_endpoints:
            try:
                full_url = self.base_url + endpoint
                logger.info(f"Trying search endpoint: {full_url}")
                
                # Try a simple search query
                search_params = {
                    'q': 'derechos fundamentales',
                    'limit': '10',
                    'page': '1'
                }
                
                async with self.session.get(full_url, params=search_params) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        if self.looks_like_case_data(content):
                            logger.info(f"Found working search API: {endpoint}")
                            return {
                                'endpoint': endpoint,
                                'full_url': full_url,
                                'method': 'GET',
                                'params': search_params,
                                'sample_response': content[:500] + "..." if len(content) > 500 else content
                            }
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.warning(f"Error testing search endpoint {endpoint}: {e}")
        
        return None
    
    async def try_post_search(self) -> Optional[Dict[str, Any]]:
        """Try POST-based search endpoints"""
        logger.info("Attempting POST-based search endpoints...")
        
        post_endpoints = [
            '/api/search',
            '/api/jurisprudencia/search',
            '/api/sentencias/search',
            '/relatoria/api/search'
        ]
        
        for endpoint in post_endpoints:
            try:
                full_url = self.base_url + endpoint
                logger.info(f"Trying POST endpoint: {full_url}")
                
                # Try a POST request with search data
                search_data = {
                    'query': 'derechos fundamentales',
                    'limit': 10,
                    'page': 1,
                    'type': 'all'
                }
                
                async with self.session.post(full_url, json=search_data) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        if self.looks_like_case_data(content):
                            logger.info(f"Found working POST search API: {endpoint}")
                            return {
                                'endpoint': endpoint,
                                'full_url': full_url,
                                'method': 'POST',
                                'data': search_data,
                                'sample_response': content[:500] + "..." if len(content) > 500 else content
                            }
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.warning(f"Error testing POST endpoint {endpoint}: {e}")
        
        return None

async def main():
    """Main analysis function"""
    async with NetworkAnalysisScraper() as scraper:
        # Analyze the page network structure
        analysis = await scraper.analyze_page_network()
        
        print(f"\n{'='*60}")
        print("NETWORK ANALYSIS RESULTS")
        print(f"{'='*60}")
        print(f"Content length: {analysis.get('content_length', 0)} characters")
        
        # Show JavaScript files
        js_files = analysis.get('js_files', [])
        print(f"\nJavaScript files found: {len(js_files)}")
        for js_file in js_files[:5]:  # Show first 5
            print(f"  - {js_file}")
        
        # Show potential APIs
        potential_apis = analysis.get('potential_apis', [])
        print(f"\nPotential API endpoints: {len(potential_apis)}")
        for api in potential_apis[:5]:  # Show first 5
            print(f"  - {api}")
        
        # Test potential endpoints
        if potential_apis:
            working_endpoints = await scraper.test_potential_endpoints(potential_apis)
            print(f"\nWorking endpoints: {len(working_endpoints)}")
            for endpoint in working_endpoints:
                print(f"  ✓ {endpoint['endpoint']} - {endpoint['content_length']} chars")
        
        # Try search APIs
        print(f"\nTrying search APIs...")
        search_api = await scraper.try_search_api()
        if search_api:
            print(f"  ✓ Found GET search API: {search_api['endpoint']}")
        else:
            print("  ✗ No GET search API found")
        
        post_search_api = await scraper.try_post_search()
        if post_search_api:
            print(f"  ✓ Found POST search API: {post_search_api['endpoint']}")
        else:
            print("  ✗ No POST search API found")
        
        # Save analysis results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        analysis_filename = f"data_pipeline_output/network_analysis_{timestamp}.json"
        
        os.makedirs(os.path.dirname(analysis_filename), exist_ok=True)
        with open(analysis_filename, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        print(f"\nAnalysis results saved to: {analysis_filename}")

if __name__ == "__main__":
    asyncio.run(main())
