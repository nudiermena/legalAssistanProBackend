"""
Legal Web Searcher Utility
Enhanced web search for legal sources with validation and classification
"""

import asyncio
import logging
import re
import time
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import hashlib
from dataclasses import dataclass
from enum import Enum

from agno.tools.googlesearch import GoogleSearchTools

logger = logging.getLogger(__name__)

class SourceType(Enum):
    """Types of legal sources"""
    LAW = "law"
    JURISPRUDENCE = "jurisprudence"
    DOCTRINE = "doctrine"
    REGULATION = "regulation"
    GENERAL = "general"

@dataclass
class LegalSource:
    """Represents a legal source with metadata"""
    title: str
    url: str
    snippet: str
    source_type: SourceType
    verified: bool
    relevance_score: float
    content: Optional[str] = None
    page_number: Optional[str] = None
    date: Optional[str] = None
    court: Optional[str] = None
    citation: Optional[str] = None

class LegalWebSearcher:
    """Enhanced web search for legal sources"""
    
    def __init__(self):
        self.google_tools = GoogleSearchTools()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Legal domain patterns
        self.legal_domains = [
            'corteconstitucional.gov.co',
            'consejodeestado.gov.co',
            'cortesuprema.gov.co',
            'dian.gov.co',
            'minjusticia.gov.co',
            'superintendencias.gov.co',
            'vlex.com',
            'legis.com',
            'actualicese.com',
            'legislacion-asuntos-legales.com',
            'web.archive.org',
            'congresovisible.org',
            'presidencia.gov.co',
            'minhacienda.gov.co',
            'minsalud.gov.co',
            'mintrabajo.gov.co',
            'minambiente.gov.co',
            'mincomercio.gov.co',
            'mineducacion.gov.co',
            'mininterior.gov.co',
            'mindefensa.gov.co',
            'minagricultura.gov.co',
            'minminas.gov.co',
            'mintransporte.gov.co',
            'minvivienda.gov.co',
            'mincultura.gov.co',
            'mindeporte.gov.co',
            'mintecnologia.gov.co',
            'minenergia.gov.co',
            'minasuntospublicos.gov.co'
        ]
        
        # Source type classification patterns
        self.source_patterns = {
            SourceType.LAW: [
                r'ley\s+\d+',
                r'decreto\s+\d+',
                r'código\s+\w+',
                r'constitución',
                r'normativa',
                r'legislación'
            ],
            SourceType.JURISPRUDENCE: [
                r'sentencia\s+[a-z]-\d+',
                r'auto\s+\d+',
                r'laudo\s+\d+',
                r'corte\s+constitucional',
                r'consejo\s+de\s+estado',
                r'corte\s+suprema',
                r'fallo',
                r'decisión'
            ],
            SourceType.DOCTRINE: [
                r'doctrina',
                r'comentario',
                r'interpretación',
                r'análisis',
                r'estudio',
                r'investigación'
            ],
            SourceType.REGULATION: [
                r'reglamento',
                r'circular',
                r'resolución',
                r'directiva',
                r'instrucción',
                r'concepto'
            ]
        }
    
    async def search_legal_sources(self, 
                                 query: str, 
                                 max_results: int = 16,
                                 source_types: Optional[List[SourceType]] = None) -> List[LegalSource]:
        """Search for legal sources using Google and validate URLs"""
        
        try:
            logger.info(f"Starting legal web search for: {query}")
            
            # Perform Google search
            search_results = await self.google_tools.search(query, num_results=max_results * 2)  # Get more to filter
            
            legal_sources = []
            for result in search_results:
                url = result.get('url', '')
                title = result.get('title', '')
                snippet = result.get('snippet', '')
                
                # Check if it's a legal source
                if self._is_legal_source(url, title, snippet):
                    # Classify source type
                    source_type = self._classify_source_type(url, title, snippet)
                    
                    # Filter by requested source types
                    if source_types and source_type not in source_types:
                        continue
                    
                    # Verify URL
                    verified = await self._verify_url(url)
                    
                    # Calculate relevance score
                    relevance_score = self._calculate_relevance_score(query, title, snippet)
                    
                    # Extract additional metadata
                    metadata = await self._extract_metadata(url, title, snippet)
                    
                    legal_source = LegalSource(
                        title=title,
                        url=url,
                        snippet=snippet,
                        source_type=source_type,
                        verified=verified,
                        relevance_score=relevance_score,
                        page_number=metadata.get('page_number'),
                        date=metadata.get('date'),
                        court=metadata.get('court'),
                        citation=metadata.get('citation')
                    )
                    
                    legal_sources.append(legal_source)
                    
                    # Limit results
                    if len(legal_sources) >= max_results:
                        break
            
            # Sort by relevance score
            legal_sources.sort(key=lambda x: x.relevance_score, reverse=True)
            
            logger.info(f"Found {len(legal_sources)} legal sources")
            return legal_sources
            
        except Exception as e:
            logger.error(f"Error in legal web search: {str(e)}")
            return []
    
    def _is_legal_source(self, url: str, title: str, snippet: str) -> bool:
        """Check if URL/title/snippet indicates a legal source"""
        
        # Check domain
        parsed_url = urlparse(url.lower())
        domain = parsed_url.netloc.replace('www.', '')
        
        # Check if domain is in legal domains
        if any(legal_domain in domain for legal_domain in self.legal_domains):
            return True
        
        # Check title and snippet for legal keywords
        legal_keywords = [
            'derecho', 'ley', 'código', 'norma', 'jurídico', 'legal',
            'constitución', 'corte', 'tribunal', 'juez', 'sentencia',
            'fallo', 'resolución', 'decreto', 'reglamento', 'estatuto',
            'contrato', 'obligación', 'responsabilidad', 'jurisprudencia',
            'doctrina', 'legislación', 'normativa', 'regulación'
        ]
        
        text_to_check = f"{title} {snippet}".lower()
        legal_keyword_count = sum(1 for keyword in legal_keywords if keyword in text_to_check)
        
        return legal_keyword_count >= 2  # At least 2 legal keywords
    
    def _classify_source_type(self, url: str, title: str, snippet: str) -> SourceType:
        """Classify the type of legal source"""
        
        text_to_check = f"{url} {title} {snippet}".lower()
        
        # Check patterns for each source type
        for source_type, patterns in self.source_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_to_check, re.IGNORECASE):
                    return source_type
        
        # Default classification based on domain
        parsed_url = urlparse(url.lower())
        domain = parsed_url.netloc.replace('www.', '')
        
        if 'corteconstitucional' in domain or 'consejodeestado' in domain or 'cortesuprema' in domain:
            return SourceType.JURISPRUDENCE
        elif 'dian.gov.co' in domain or 'superintendencias' in domain:
            return SourceType.REGULATION
        elif 'minjusticia' in domain or 'congresovisible' in domain:
            return SourceType.LAW
        else:
            return SourceType.GENERAL
    
    async def _verify_url(self, url: str) -> bool:
        """Verify that URL is accessible"""
        try:
            response = self.session.head(url, timeout=10, allow_redirects=True)
            return response.status_code == 200
        except:
            try:
                response = self.session.get(url, timeout=10, allow_redirects=True)
                return response.status_code == 200
            except:
                return False
    
    def _calculate_relevance_score(self, query: str, title: str, snippet: str) -> float:
        """Calculate relevance score for a source"""
        
        query_words = set(query.lower().split())
        title_words = set(title.lower().split())
        snippet_words = set(snippet.lower().split())
        
        # Calculate word overlap
        title_overlap = len(query_words.intersection(title_words))
        snippet_overlap = len(query_words.intersection(snippet_words))
        
        # Base score from word overlap
        base_score = (title_overlap * 0.7 + snippet_overlap * 0.3) / len(query_words)
        
        # Boost for legal keywords
        legal_keywords = [
            'derecho', 'ley', 'código', 'norma', 'jurídico', 'legal',
            'constitución', 'corte', 'tribunal', 'sentencia', 'fallo',
            'contrato', 'obligación', 'responsabilidad', 'jurisprudencia'
        ]
        
        text_to_check = f"{title} {snippet}".lower()
        legal_keyword_count = sum(1 for keyword in legal_keywords if keyword in text_to_check)
        legal_boost = min(legal_keyword_count * 0.1, 0.3)
        
        # Boost for official sources
        official_boost = 0.2 if any(domain in title.lower() for domain in ['corte', 'consejo', 'ministerio', 'superintendencia']) else 0.0
        
        final_score = min(base_score + legal_boost + official_boost, 1.0)
        return final_score
    
    async def _extract_metadata(self, url: str, title: str, snippet: str) -> Dict[str, Optional[str]]:
        """Extract additional metadata from source"""
        
        metadata = {
            'page_number': None,
            'date': None,
            'court': None,
            'citation': None
        }
        
        text_to_check = f"{url} {title} {snippet}"
        
        # Extract page number
        page_match = re.search(r'página\s+(\d+)', text_to_check, re.IGNORECASE)
        if page_match:
            metadata['page_number'] = page_match.group(1)
        
        # Extract date
        date_match = re.search(r'(\d{4})', text_to_check)
        if date_match:
            metadata['date'] = date_match.group(1)
        
        # Extract court
        court_patterns = [
            r'corte\s+constitucional',
            r'consejo\s+de\s+estado',
            r'corte\s+suprema',
            r'tribunal\s+administrativo',
            r'corte\s+de\s+apelaciones'
        ]
        
        for pattern in court_patterns:
            court_match = re.search(pattern, text_to_check, re.IGNORECASE)
            if court_match:
                metadata['court'] = court_match.group(0)
                break
        
        # Extract citation
        citation_patterns = [
            r'sentencia\s+[a-z]-\d+\s+de\s+\d{4}',
            r'auto\s+\d+\s+de\s+\d{4}',
            r'laudo\s+\d+\s+de\s+\d{4}',
            r'ley\s+\d+\s+de\s+\d{4}',
            r'decreto\s+\d+\s+de\s+\d{4}'
        ]
        
        for pattern in citation_patterns:
            citation_match = re.search(pattern, text_to_check, re.IGNORECASE)
            if citation_match:
                metadata['citation'] = citation_match.group(0)
                break
        
        return metadata
    
    async def get_source_content(self, source: LegalSource) -> Optional[str]:
        """Get full content from a legal source"""
        
        if not source.verified:
            return None
        
        try:
            response = self.session.get(source.url, timeout=15)
            if response.status_code != 200:
                return None
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract text content
            text_content = soup.get_text()
            
            # Clean up text
            cleaned_content = re.sub(r'\s+', ' ', text_content).strip()
            
            return cleaned_content
            
        except Exception as e:
            logger.error(f"Error getting content from {source.url}: {str(e)}")
            return None
    
    async def search_and_ingest(self, 
                               query: str,
                               max_results: int = 16,
                               source_types: Optional[List[SourceType]] = None) -> Tuple[List[LegalSource], Dict[str, int]]:
        """Search for legal sources and prepare for ingestion"""
        
        # Search for sources
        sources = await self.search_legal_sources(query, max_results, source_types)
        
        # Get content for verified sources
        for source in sources:
            if source.verified:
                content = await self.get_source_content(source)
                if content:
                    source.content = content
        
        # Prepare ingestion data
        ingestion_data = []
        for source in sources:
            if source.content:
                ingestion_data.append({
                    'title': source.title,
                    'content': source.content,
                    'source_type': source.source_type.value,
                    'citation': source.citation or source.title,
                    'url': source.url,
                    'metadata': {
                        'page_number': source.page_number,
                        'date': source.date,
                        'court': source.court,
                        'relevance_score': source.relevance_score,
                        'verified': source.verified,
                        'search_query': query
                    }
                })
        
        # Statistics
        stats = {
            'total_sources': len(sources),
            'verified_sources': len([s for s in sources if s.verified]),
            'sources_with_content': len([s for s in sources if s.content]),
            'ready_for_ingestion': len(ingestion_data)
        }
        
        return sources, stats

# === DEMONSTRATION FUNCTION ===

async def demonstrate_legal_web_search():
    """Demonstrate legal web search capabilities"""
    
    print("🚀 DEMOSTRACIÓN DE BÚSQUEDA WEB LEGAL")
    print("=" * 50)
    
    searcher = LegalWebSearcher()
    
    # Test 1: General legal search
    print("\n📚 TEST 1: Búsqueda general de fuentes legales")
    print("-" * 40)
    
    try:
        sources, stats = await searcher.search_and_ingest(
            query="principios fundamentales contratos Colombia",
            max_results=8
        )
        
        print(f"✅ Búsqueda completada")
        print(f"📊 Total de fuentes: {stats['total_sources']}")
        print(f"🔍 Fuentes verificadas: {stats['verified_sources']}")
        print(f"📄 Fuentes con contenido: {stats['sources_with_content']}")
        print(f"🚀 Listas para ingestión: {stats['ready_for_ingestion']}")
        
        # Show top sources
        print("\n📖 Top 3 fuentes encontradas:")
        for i, source in enumerate(sources[:3], 1):
            print(f"   {i}. {source.title}")
            print(f"      Tipo: {source.source_type.value}")
            print(f"      URL: {source.url}")
            print(f"      Relevancia: {source.relevance_score:.2f}")
            print(f"      Verificado: {'✅' if source.verified else '❌'}")
            print()
        
    except Exception as e:
        print(f"❌ Error en test 1: {str(e)}")
    
    # Test 2: Specific source type search
    print("\n📚 TEST 2: Búsqueda por tipo de fuente")
    print("-" * 40)
    
    try:
        sources, stats = await searcher.search_and_ingest(
            query="jurisprudencia Corte Constitucional contratos",
            max_results=5,
            source_types=[SourceType.JURISPRUDENCE]
        )
        
        print(f"✅ Búsqueda de jurisprudencia completada")
        print(f"📊 Fuentes encontradas: {stats['total_sources']}")
        print(f"🔍 Fuentes verificadas: {stats['verified_sources']}")
        
        # Show jurisprudence sources
        print("\n📖 Fuentes de jurisprudencia:")
        for i, source in enumerate(sources, 1):
            print(f"   {i}. {source.title}")
            print(f"      Corte: {source.court or 'N/A'}")
            print(f"      Cita: {source.citation or 'N/A'}")
            print(f"      Relevancia: {source.relevance_score:.2f}")
            print()
        
    except Exception as e:
        print(f"❌ Error en test 2: {str(e)}")
    
    print("\n🎯 CAPACIDADES DEL BUSCADOR WEB LEGAL:")
    print("=" * 50)
    print("✅ Búsqueda avanzada en Google")
    print("✅ Clasificación automática de fuentes")
    print("✅ Verificación de URLs")
    print("✅ Extracción de contenido")
    print("✅ Cálculo de relevancia")
    print("✅ Extracción de metadatos")
    print("✅ Filtrado por tipo de fuente")
    print("✅ Preparación para ingestión")
    
    print("\n🚀 Buscador web legal listo para usar!")
    print("💡 Integra búsqueda, verificación y extracción de contenido")

# Main execution for demonstration
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run demonstration
    asyncio.run(demonstrate_legal_web_search())
