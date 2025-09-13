#!/usr/bin/env python3
"""
Debug API Response
Examines the raw response from the Constitutional Court search API
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def debug_api_response():
    """Debug the API response to understand its format"""
    
    base_url = "https://www.corteconstitucional.gov.co"
    search_api = "/api/search"
    
    headers = {
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
    
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            # Test different search queries
            test_queries = [
                'derechos fundamentales',
                'jurisprudencia',
                'sentencia',
                'tutela'
            ]
            
            for query in test_queries:
                print(f"\n{'='*60}")
                print(f"Testing query: '{query}'")
                print(f"{'='*60}")
                
                search_url = base_url + search_api
                search_params = {
                    'q': query,
                    'limit': '10',
                    'page': '1'
                }
                
                print(f"URL: {search_url}")
                print(f"Params: {search_params}")
                
                async with session.get(search_url, params=search_params) as response:
                    print(f"Status: {response.status}")
                    print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
                    print(f"Content-Length: {response.headers.get('content-length', 'unknown')}")
                    
                    content = await response.text()
                    print(f"Response length: {len(content)} characters")
                    
                    # Show first 500 characters of response
                    print(f"\nResponse preview (first 500 chars):")
                    print("-" * 40)
                    print(content[:500])
                    print("-" * 40)
                    
                    # Try to parse as JSON
                    try:
                        data = json.loads(content)
                        print(f"\n✓ Successfully parsed as JSON")
                        print(f"JSON type: {type(data)}")
                        if isinstance(data, list):
                            print(f"JSON length: {len(data)}")
                            if data:
                                print(f"First item keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'not a dict'}")
                        elif isinstance(data, dict):
                            print(f"JSON keys: {list(data.keys())}")
                    except json.JSONDecodeError as e:
                        print(f"\n✗ Not valid JSON: {e}")
                        
                        # Look for HTML indicators
                        if '<html' in content.lower() or '<body' in content.lower():
                            print("Response appears to be HTML")
                        elif '<' in content and '>' in content:
                            print("Response appears to contain XML/HTML tags")
                        else:
                            print("Response appears to be plain text")
                    
                    # Look for case numbers in the response
                    import re
                    case_patterns = [
                        r'[CT]-\d+/\d{4}',
                        r'Sentencia\s+[CT]-\d+/\d{4}',
                        r'Auto\s+\d+/\d{4}',
                        r'Concepto\s+\d+/\d{4}'
                    ]
                    
                    print(f"\nSearching for case numbers in response...")
                    for pattern in case_patterns:
                        matches = re.findall(pattern, content)
                        if matches:
                            print(f"  Pattern {pattern}: Found {len(matches)} matches")
                            for match in matches[:3]:  # Show first 3
                                print(f"    - {match}")
                        else:
                            print(f"  Pattern {pattern}: No matches")
                    
                    # Save response to file for manual inspection
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    response_filename = f"data_pipeline_output/api_response_{query.replace(' ', '_')}_{timestamp}.txt"
                    
                    os.makedirs(os.path.dirname(response_filename), exist_ok=True)
                    with open(response_filename, 'w', encoding='utf-8') as f:
                        f.write(f"Query: {query}\n")
                        f.write(f"URL: {search_url}\n")
                        f.write(f"Params: {search_params}\n")
                        f.write(f"Status: {response.status}\n")
                        f.write(f"Content-Type: {response.headers.get('content-type', 'unknown')}\n")
                        f.write(f"Response:\n")
                        f.write(content)
                    
                    print(f"Full response saved to: {response_filename}")
                    
                    # Small delay between queries
                    await asyncio.sleep(1)
                    
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_api_response())
