#!/usr/bin/env python3
"""
Debug Constitutional Court Page Structure
Examines the actual structure of the constitutional court page to understand how to extract cases
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

async def debug_constitutional_court_page():
    """Debug the constitutional court page structure"""
    
    url = "https://www.corteconstitucional.gov.co/relatoria/buscador-jurisprudencia"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    print(f"Page retrieved successfully: {len(content)} characters")
                    print("="*60)
                    
                    # Parse with BeautifulSoup
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Look for title
                    title = soup.find('title')
                    if title:
                        print(f"Page title: {title.get_text().strip()}")
                    
                    # Look for main content areas
                    main_content = soup.find('main') or soup.find('div', class_='content') or soup.find('body')
                    if main_content:
                        print(f"\nMain content found: {len(main_content.get_text())} characters")
                        
                        # Look for forms (search forms)
                        forms = main_content.find_all('form')
                        print(f"\nFound {len(forms)} forms")
                        
                        for i, form in enumerate(forms):
                            print(f"\nForm {i+1}:")
                            print(f"  Action: {form.get('action', 'N/A')}")
                            print(f"  Method: {form.get('method', 'N/A')}")
                            
                            # Look for input fields
                            inputs = form.find_all('input')
                            for inp in inputs:
                                print(f"    Input: {inp.get('type', 'text')} - {inp.get('name', 'N/A')} - {inp.get('placeholder', 'N/A')}")
                            
                            # Look for select fields
                            selects = form.find_all('select')
                            for sel in selects:
                                print(f"    Select: {sel.get('name', 'N/A')}")
                                options = sel.find_all('option')
                                for opt in options[:5]:  # Show first 5 options
                                    print(f"      Option: {opt.get('value', 'N/A')} - {opt.get_text().strip()}")
                    
                    # Look for any links that might contain case information
                    all_links = soup.find_all('a', href=True)
                    print(f"\nFound {len(all_links)} total links")
                    
                    # Look for links that might be related to cases
                    case_related_links = []
                    for link in all_links:
                        href = link['href']
                        text = link.get_text().strip()
                        
                        if any(keyword in href.lower() or keyword in text.lower() 
                               for keyword in ['sentencia', 'auto', 'concepto', 'caso', 'jurisprudencia']):
                            case_related_links.append({
                                'href': href,
                                'text': text,
                                'full_url': href if href.startswith('http') else f"https://www.corteconstitucional.gov.co{href}"
                            })
                    
                    print(f"\nFound {len(case_related_links)} case-related links:")
                    for link in case_related_links[:10]:  # Show first 10
                        print(f"  {link['text'][:50]}... -> {link['href']}")
                    
                    # Look for any text that might contain case numbers
                    text_content = soup.get_text()
                    case_patterns = [
                        r'[CT]-\d+/\d{4}',
                        r'Sentencia\s+([CT]-\d+/\d{4})',
                        r'Auto\s+(\d+/\d{4})',
                        r'Concepto\s+(\d+/\d{4})'
                    ]
                    
                    print(f"\nSearching for case patterns in text...")
                    for pattern in case_patterns:
                        matches = re.findall(pattern, text_content)
                        if matches:
                            print(f"  Pattern {pattern}: Found {len(matches)} matches")
                            for match in matches[:5]:  # Show first 5
                                print(f"    {match}")
                    
                    # Save the HTML content for manual inspection
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    html_filename = f"data_pipeline_output/constitutional_court_debug_{timestamp}.html"
                    
                    os.makedirs(os.path.dirname(html_filename), exist_ok=True)
                    with open(html_filename, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    print(f"\nHTML content saved to: {html_filename}")
                    
                    # Save structured debug info
                    debug_info = {
                        'timestamp': timestamp,
                        'url': url,
                        'content_length': len(content),
                        'title': title.get_text().strip() if title else None,
                        'forms_count': len(forms),
                        'total_links': len(all_links),
                        'case_related_links': case_related_links,
                        'case_patterns_found': {
                            pattern: len(re.findall(pattern, text_content)) 
                            for pattern in case_patterns
                        }
                    }
                    
                    debug_filename = f"data_pipeline_output/constitutional_court_debug_{timestamp}.json"
                    with open(debug_filename, 'w', encoding='utf-8') as f:
                        json.dump(debug_info, f, ensure_ascii=False, indent=2)
                    
                    print(f"Debug info saved to: {debug_filename}")
                    
                else:
                    print(f"Failed to retrieve page: {response.status}")
                    
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_constitutional_court_page())
