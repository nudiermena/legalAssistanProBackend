#!/usr/bin/env python3
"""
Legal Web Scraper for Colombian Legal Database
Comprehensive framework to collect legal documents from official sources
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import os
import sys
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re
from dataclasses import dataclass
from enum import Enum
import time
from tenacity import retry, stop_after_attempt, wait_exponential
import random
import pathlib

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.supabase_knowledge_base import KnowledgeType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DocumentType(Enum):
    """Types of legal documents"""
    CONSTITUTIONAL = "constitutional"
    LEGISLATION = "legislation"
    JURISPRUDENCE = "jurisprudence"
    REGULATORY = "regulatory"
    DOCTRINE = "doctrine"

@dataclass
class LegalDocument:
    """Legal document data structure"""
    title: str
    content: str
    document_type: DocumentType
    source_url: str
    document_number: Optional[str] = None
    date: Optional[str] = None
    authority: Optional[str] = None
    metadata: Dict[str, Any] = None

HEADERS_LIST = [
    {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept-Language': 'es-CO,es;q=0.9,en;q=0.8',
    },
    {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
        'Accept-Language': 'es-CO,es;q=0.9,en;q=0.8',
    },
    {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Accept-Language': 'es-CO,es;q=0.9,en;q=0.8',
    },
    {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
        'Accept-Language': 'es-CO,es;q=0.9,en;q=0.8',
    },
]

# Proxy support (disabled by default)
PROXIES_LIST = []  # Add proxies here if needed
USE_PROXIES = False

TMP_HTML_DIR = pathlib.Path('tmp_html')
TMP_HTML_DIR.mkdir(exist_ok=True)

FAILED_URLS_LOG = 'failed_urls.log'

class ColombianLegalScraper:
    """Comprehensive scraper for Colombian legal sources"""
    
    def __init__(self):
        self.session = None
        self.scraped_documents = []
        
        # Colombian legal sources
        self.legal_sources = {
            DocumentType.CONSTITUTIONAL: {
                "corte_constitucional": {
                    "base_url": "https://www.corteconstitucional.gov.co",
                    "endpoints": [
                        "/relatoria/",
                        "/jurisprudencia/",
                        "/comunicados/"
                    ],
                    "selectors": {
                        "title": "h1, h2, .titulo",
                        "content": ".contenido, .texto, .sentencia",
                        "date": ".fecha, .date",
                        "number": ".numero, .expediente"
                    }
                },
                "consejo_estado": {
                    "base_url": "https://www.consejodeestado.gov.co",
                    "endpoints": [
                        "/jurisprudencia/",
                        "/sentencias/"
                    ],
                    "selectors": {
                        "title": "h1, h2, .titulo",
                        "content": ".contenido, .texto",
                        "date": ".fecha",
                        "number": ".numero"
                    }
                }
            },
            DocumentType.LEGISLATION: {
                "funcion_publica": {
                    "base_url": "https://www.funcionpublica.gov.co",
                    "endpoints": [
                        "/eva/gestornormativo/norma.php"
                    ],
                    "selectors": {
                        "title": "h1, .titulo-norma",
                        "content": ".contenido-norma, .texto",
                        "date": ".fecha-publicacion",
                        "number": ".numero-norma"
                    }
                },
                "secretaria_senado": {
                    "base_url": "https://www.secretariasenado.gov.co",
                    "endpoints": [
                        "/leyes/",
                        "/proyectos/"
                    ],
                    "selectors": {
                        "title": "h1, .titulo",
                        "content": ".contenido, .texto",
                        "date": ".fecha",
                        "number": ".numero"
                    }
                }
            },
            DocumentType.JURISPRUDENCE: {
                "ramajudicial": {
                    "base_url": "https://www.ramajudicial.gov.co",
                    "endpoints": [
                        "/web/jurisprudencia/",
                        "/web/sentencias/"
                    ],
                    "selectors": {
                        "title": "h1, .titulo-sentencia",
                        "content": ".contenido-sentencia, .texto",
                        "date": ".fecha-sentencia",
                        "number": ".numero-expediente"
                    }
                },
                "cortesuprema": {
                    "base_url": "https://www.cortesuprema.gov.co",
                    "endpoints": [
                        "/jurisprudencia/",
                        "/sentencias/"
                    ],
                    "selectors": {
                        "title": "h1, .titulo",
                        "content": ".contenido, .texto",
                        "date": ".fecha",
                        "number": ".numero"
                    }
                }
            },
            DocumentType.REGULATORY: {
                "sic": {
                    "base_url": "https://www.sic.gov.co",
                    "endpoints": [
                        "/normatividad/",
                        "/circulares/"
                    ],
                    "selectors": {
                        "title": "h1, .titulo",
                        "content": ".contenido, .texto",
                        "date": ".fecha",
                        "number": ".numero"
                    }
                },
                "superfinanciera": {
                    "base_url": "https://www.superfinanciera.gov.co",
                    "endpoints": [
                        "/normatividad/",
                        "/circulares/"
                    ],
                    "selectors": {
                        "title": "h1, .titulo",
                        "content": ".contenido, .texto",
                        "date": ".fecha",
                        "number": ".numero"
                    }
                }
            },
            DocumentType.DOCTRINE: {
                "vlex_colombia": {
                    "base_url": "https://vlex.com.co/jurisdictions/CO?_gl=1*1pbae35*_up*MQ..*_ga*MTIzMzE3NDMyLjE3NTM1MTY3NzA.*_ga_85GW7N2JQZ*czE3NTM1MTY3NjkkbzEkZzEkdDE3NTM1MTY3ODckajQyJGwwJGgw",
                    "endpoints": [""],
                    "selectors": {
                        "title": "title",
                        "content": "body"
                    },
                    "follow_links": True  # New flag to indicate link following
                }
            }
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def fetch_page(self, url: str) -> Optional[str]:
        """Fetch a web page with retry logic, rotating headers and optional proxies"""
        headers = random.choice(HEADERS_LIST)
        proxy = random.choice(PROXIES_LIST) if (USE_PROXIES and PROXIES_LIST) else None
        timeout = aiohttp.ClientTimeout(total=30)
        try:
            async with self.session.get(url, headers=headers, proxy=proxy, timeout=timeout) as response:
                html = await response.text()
                if response.status == 200:
                    return html
                else:
                    logger.warning(f"Failed to fetch {url}: {response.status}")
                    self.log_failed_url(url, f"HTTP {response.status}")
                    self.save_html_temp(url, html)
                    return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            self.log_failed_url(url, str(e))
            self.save_html_temp(url, None)
            return None

    def log_failed_url(self, url: str, reason: str):
        """Log failed URL with reason to file and console"""
        msg = f"FAILED: {url} | Reason: {reason}"
        logger.warning(msg)
        with open(FAILED_URLS_LOG, 'a', encoding='utf-8') as f:
            f.write(msg + '\n')

    def save_html_temp(self, url: str, html: Optional[str]):
        """Save HTML to tmp_html/ for debugging"""
        safe_url = url.replace('://', '_').replace('/', '_').replace('?', '_').replace('&', '_')
        filename = TMP_HTML_DIR / f"{safe_url}_{int(datetime.now().timestamp())}.html"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                if html:
                    f.write(html)
                else:
                    f.write(f"No HTML content for {url}")
        except Exception as e:
            logger.error(f"Error saving HTML for {url}: {e}")
    
    def extract_text_with_selectors(self, soup: BeautifulSoup, selectors: Dict[str, str]) -> Dict[str, str]:
        """Extract text using CSS selectors"""
        extracted = {}
        
        for field, selector in selectors.items():
            elements = soup.select(selector)
            if elements:
                # Join multiple elements with newlines
                text = '\n'.join([elem.get_text(strip=True) for elem in elements])
                extracted[field] = text
            else:
                extracted[field] = ""
        
        return extracted
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep Spanish accents
        text = re.sub(r'[^\w\sáéíóúñÁÉÍÓÚÑ.,;:!?()\-–—""''%$#@&+=<>[\]{}|\\/]', '', text)
        
        return text.strip()
    
    def extract_document_metadata(self, url: str, content: str) -> Dict[str, Any]:
        """Extract metadata from document content and URL"""
        metadata = {
            "source_url": url,
            "scraped_date": datetime.now().isoformat(),
            "word_count": len(content.split()),
            "domain": urlparse(url).netloc
        }
        
        # Try to extract document number from URL or content
        doc_number_match = re.search(r'(\d{4})', url)
        if doc_number_match:
            metadata["document_number"] = doc_number_match.group(1)
        
        # Try to extract date
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', content)
        if date_match:
            metadata["date"] = date_match.group(1)
        
        return metadata
    
    def extract_vlex_links(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract category links from vLex index page"""
        links = []
        
        # Look for category links in the index
        # Based on the vLex structure shown in the image
        category_selectors = [
            "a[href*='legislacion']",
            "a[href*='jurisprudencia']", 
            "a[href*='doctrina']",
            "a[href*='libros']",
            "a[href*='minutas']",
            "a[href*='iniciativas']",
            "a[href*='noticias']",
            "a[href*='normativa']",
            "a[href*='boletines']",
            "a[href*='practicos']"
        ]
        
        for selector in category_selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                text = element.get_text(strip=True)
                if href and text:
                    # Convert relative URLs to absolute
                    if href.startswith('/'):
                        href = f"https://vlex.com.co{href}"
                    elif not href.startswith('http'):
                        href = f"https://vlex.com.co/{href}"
                    
                    links.append({
                        'url': href,
                        'category': text,
                        'text': text
                    })
        
        # Also look for general content links
        content_links = soup.find_all('a', href=True)
        for link in content_links:
            href = link.get('href')
            text = link.get_text(strip=True)
            
            # Filter for likely legal content URLs
            if (href and text and 
                any(keyword in href.lower() for keyword in ['ley', 'decreto', 'sentencia', 'resolucion', 'circular']) and
                len(text) > 10):  # Avoid navigation text
                
                if href.startswith('/'):
                    href = f"https://vlex.com.co{href}"
                elif not href.startswith('http'):
                    href = f"https://vlex.com.co/{href}"
                
                links.append({
                    'url': href,
                    'category': 'legal_document',
                    'text': text
                })
        
        return links

    def extract_vlex_source_links(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract source links from vLex category pages (like court sources)"""
        links = []
        
        # Look for source links in category pages
        # These are typically in lists with class names like 'ul_flechas-t2' or 'src_children'
        source_selectors = [
            ".ul_flechas-t2 a",
            ".src_children a", 
            ".sources a",
            "ul li a[href*='source']",
            ".item a[href*='source']"
        ]
        
        for selector in source_selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                text = element.get_text(strip=True)
                title = element.get('title', text)
                
                if href and text and len(text) > 3:  # Avoid empty or very short texts
                    # Convert relative URLs to absolute
                    if href.startswith('/'):
                        href = f"https://vlex.com.co{href}"
                    elif not href.startswith('http'):
                        href = f"https://vlex.com.co/{href}"
                    
                    links.append({
                        'url': href,
                        'category': 'source',
                        'text': text,
                        'title': title
                    })
        
        # Also look for any links that contain 'source' in the URL
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href')
            text = link.get_text(strip=True)
            
            if (href and 'source' in href and text and len(text) > 3):
                if href.startswith('/'):
                    href = f"https://vlex.com.co{href}"
                elif not href.startswith('http'):
                    href = f"https://vlex.com.co/{href}"
                
                links.append({
                    'url': href,
                    'category': 'source',
                    'text': text,
                    'title': text
                })
        
        return links

    async def scrape_vlex_source(self, source_url: str, source_name: str) -> List[LegalDocument]:
        """Scrape a specific vLex source page (like a court)"""
        documents = []
        
        try:
            html_content = await self.fetch_page(source_url)
            if not html_content:
                return documents
            
            # Save the source HTML for debugging
            self.save_html_temp(source_url, html_content)
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for document links on the source page
            doc_links = self.extract_vlex_document_links(soup)
            
            logger.info(f"Found {len(doc_links)} potential documents in source: {source_name}")
            
            # Follow each document link (limit to first 5 for testing)
            for i, link_info in enumerate(doc_links[:20]):  # Increased from 5 to 20 documents
                try:
                    doc_url = link_info['url']
                    logger.info(f"Scraping document {i+1}/{min(len(doc_links), 20)}: {link_info['text'][:50]}...")
                    
                    doc_html = await self.fetch_page(doc_url)
                    if not doc_html:
                        continue
                    
                    doc_soup = BeautifulSoup(doc_html, 'html.parser')
                    
                    # Extract document content with vLex-specific selectors
                    title = self.extract_text_with_selectors(doc_soup, {
                        "title": "h1, h2, .titulo, .title, .document-title, .case-title"
                    })
                    content = self.extract_text_with_selectors(doc_soup, {
                        "content": ".contenido, .texto, .documento, .content, article, .main-content, .document-content, .case-content, .sentencia-content"
                    })
                    
                    title_text = self.clean_text(title.get("title", link_info['text']))
                    content_text = self.clean_text(content.get("content", ""))
                    
                    if title_text and content_text and len(content_text) > 100:  # Minimum content threshold
                        doc = LegalDocument(
                            title=title_text,
                            content=content_text,
                            document_type=DocumentType.DOCTRINE,
                            source_url=doc_url,
                            document_number="",
                            date="",
                            authority=f"vlex_{source_name}",
                            metadata={
                                "source_url": doc_url,
                                "scraped_date": datetime.now().isoformat(),
                                "word_count": len(content_text.split()),
                                "domain": "vlex.com.co",
                                "source": source_name,
                                "original_link_text": link_info['text']
                            }
                        )
                        documents.append(doc)
                        logger.info(f"✅ Scraped: {title_text[:50]}...")
                    
                    # Rate limiting
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error scraping document {doc_url}: {e}")
                    self.log_failed_url(doc_url, str(e))
                    continue
            
        except Exception as e:
            logger.error(f"Error scraping vLex source {source_name}: {e}")
            self.log_failed_url(source_url, str(e))
        
        return documents

    def extract_vlex_document_links(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract document links from vLex source pages"""
        links = []
        
        # Look for document links on source pages
        # These might be in search results, document lists, etc.
        doc_selectors = [
            ".search-results a",
            ".document-list a",
            ".case-list a",
            ".sentencia-list a",
            "a[href*='document']",
            "a[href*='case']",
            "a[href*='sentencia']",
            "a[href*='resolucion']",
            "a[href*='decreto']",
            "a[href*='ley']"
        ]
        
        for selector in doc_selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                text = element.get_text(strip=True)
                
                if href and text and len(text) > 10:  # Avoid navigation text
                    # Convert relative URLs to absolute
                    if href.startswith('/'):
                        href = f"https://vlex.com.co{href}"
                    elif not href.startswith('http'):
                        href = f"https://vlex.com.co/{href}"
                    
                    links.append({
                        'url': href,
                        'category': 'document',
                        'text': text
                    })
        
        return links

    async def scrape_vlex_category(self, category_url: str, category_name: str) -> List[LegalDocument]:
        """Scrape a specific vLex category page"""
        documents = []
        
        try:
            html_content = await self.fetch_page(category_url)
            if not html_content:
                return documents
            
            # Always save vLex HTML for debugging
            self.save_html_temp(category_url, html_content)
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract source links from category page (like court sources)
            source_links = self.extract_vlex_source_links(soup)
            
            logger.info(f"Found {len(source_links)} source links in {category_name}")
            
            # Scrape each source (limit to first 5 for testing)
            for i, link_info in enumerate(source_links[:10]):  # Increased from 3 to 10 sources
                source_url = link_info['url']
                source_name = link_info['text']
                
                logger.info(f"Scraping source {i+1}/{min(len(source_links), 10)}: {source_name}")
                
                source_docs = await self.scrape_vlex_source(source_url, source_name)
                documents.extend(source_docs)
                
                # Rate limiting between sources
                await asyncio.sleep(3)
            
        except Exception as e:
            logger.error(f"Error scraping vLex category {category_name}: {e}")
            self.log_failed_url(category_url, str(e))
        
        return documents

    async def scrape_source(self, source_name: str, source_config: Dict[str, Any], doc_type: DocumentType) -> List[LegalDocument]:
        """Scrape a legal source"""
        documents = []
        base_url = source_config["base_url"]
        selectors = source_config["selectors"]
        follow_links = source_config.get("follow_links", False)
        
        logger.info(f"Scraping {source_name} ({base_url})")
        
        # Special handling for vLex with link following
        if follow_links and "vlex" in source_name.lower():
            return await self.scrape_vlex_with_links(source_config, doc_type)
        
        # Standard scraping for other sources
        for endpoint in source_config.get("endpoints", [""]):
            url = urljoin(base_url, endpoint)
            try:
                html_content = await self.fetch_page(url)
                if not html_content:
                    continue
                
                # Always save vLex HTML for manual analysis
                if 'vlex.com.co' in url:
                    self.save_html_temp(url, html_content)
                
                soup = BeautifulSoup(html_content, 'html.parser')
                extracted = self.extract_text_with_selectors(soup, selectors)
                title = self.clean_text(extracted.get("title", ""))
                content = self.clean_text(extracted.get("content", ""))
                
                if title and content:
                    doc = LegalDocument(
                        title=title,
                        content=content,
                        document_type=doc_type,
                        source_url=url,
                        document_number=extracted.get("number", ""),
                        date=extracted.get("date", ""),
                        authority=source_name,
                        metadata=self.extract_document_metadata(url, content)
                    )
                    documents.append(doc)
                    logger.info(f"Scraped: {title[:50]}...")
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
                self.log_failed_url(url, str(e))
                self.save_html_temp(url, None)
                continue
        
        return documents

    async def scrape_vlex_with_links(self, source_config: Dict[str, Any], doc_type: DocumentType) -> List[LegalDocument]:
        """Specialized scraper for vLex that follows category links"""
        documents = []
        base_url = source_config["base_url"]
        
        try:
            # First, get the main index page
            logger.info("Scraping vLex Colombia index page...")
            html_content = await self.fetch_page(base_url)
            if not html_content:
                return documents
            
            # Save the index HTML
            self.save_html_temp(base_url, html_content)
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract category links
            category_links = self.extract_vlex_links(soup)
            logger.info(f"Found {len(category_links)} category links on vLex index")
            
            # Scrape each category
            for i, link_info in enumerate(category_links[:10]):  # Increased from 5 to 10 categories
                category_url = link_info['url']
                category_name = link_info['category']
                
                logger.info(f"Scraping category {i+1}/{min(len(category_links), 10)}: {category_name}")
                
                category_docs = await self.scrape_vlex_category(category_url, category_name)
                documents.extend(category_docs)
                
                # Rate limiting between categories
                await asyncio.sleep(3)
            
        except Exception as e:
            logger.error(f"Error in vLex link following: {e}")
            self.log_failed_url(base_url, str(e))
        
        return documents
    
    async def scrape_all_sources(self) -> List[LegalDocument]:
        """Scrape all legal sources"""
        all_documents = []
        
        for doc_type, sources in self.legal_sources.items():
            logger.info(f"Scraping {doc_type.value} documents...")
            
            for source_name, source_config in sources.items():
                try:
                    documents = await self.scrape_source(source_name, source_config, doc_type)
                    all_documents.extend(documents)
                    
                    logger.info(f"Scraped {len(documents)} documents from {source_name}")
                    
                except Exception as e:
                    logger.error(f"Error scraping {source_name}: {e}")
                    continue
        
        self.scraped_documents = all_documents
        return all_documents
    
    def save_documents(self, filename: str = None):
        """Save scraped documents to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scraped_legal_documents_{timestamp}.json"
        
        documents_data = []
        for doc in self.scraped_documents:
            doc_dict = {
                "title": doc.title,
                "content": doc.content,
                "document_type": doc.document_type.value,
                "source_url": doc.source_url,
                "document_number": doc.document_number,
                "date": doc.date,
                "authority": doc.authority,
                "metadata": doc.metadata
            }
            documents_data.append(doc_dict)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(documents_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(documents_data)} documents to {filename}")
        return filename

async def main():
    """Main scraping function"""
    logger.info("Starting Colombian Legal Document Scraping...")
    
    async with ColombianLegalScraper() as scraper:
        documents = await scraper.scrape_all_sources()
        
        logger.info(f"Scraping completed. Total documents: {len(documents)}")
        
        # Save documents
        filename = scraper.save_documents()
        
        # Print summary
        doc_types = {}
        for doc in documents:
            doc_type = doc.document_type.value
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
        
        logger.info("Document Summary:")
        for doc_type, count in doc_types.items():
            logger.info(f"  {doc_type}: {count} documents")

if __name__ == "__main__":
    asyncio.run(main()) 