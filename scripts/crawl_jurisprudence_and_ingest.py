import os
import re
import sys
import csv
import time
import json
import httpx
import logging
import argparse
from io import StringIO, BytesIO
from typing import List, Tuple, Dict, Optional, Any
import unicodedata

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import POSTGRES_URL, MISTRAL_API_KEY
from agno.vectordb.pgvector import PgVector, SearchType
from agno.embedder.mistral import MistralEmbedder
from agno.document import Document
from utils.pdf_processor import extract_text_from_pdf_content, sanitize_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALLOWED_DOMAINS = [
    "corteconstitucional.gov.co",
    "cortesuprema.gov.co",
    "consejodeestado.gov.co",
    "ramajudicial.gov.co",
    "funcionpublica.gov.co",
    "secretariasenado.gov.co",
    "www.suin-juriscol.gov.co",
]

JURIS_REGEX = re.compile(r"\b(SU|T|C|SL|SP|SC|CE|Auto|A|Rad|Sentencia)\s*[-–]?\s*\d+\s*(de)?\s*\d{4}\b", re.IGNORECASE)


def to_sqlalchemy_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def ddg_search(query: str, num_results: int = 5) -> List[str]:
    """Search using DuckDuckGo and return result URLs (filtered)."""
    urls: List[str] = []
    q = query + " site:" + " OR site:".join(ALLOWED_DOMAINS)
    search_url = f"https://duckduckgo.com/html/?q={httpx.QueryParams({'q': q})['q']}"
    try:
        with httpx.Client(timeout=30.0, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"}) as client:
            r = client.get(search_url)
            r.raise_for_status()
            # Naive link extraction
            for m in re.finditer(r'href=\"(https?://[^\"]+)\"', r.text):
                url = m.group(1)
                if any(domain in url for domain in ALLOWED_DOMAINS):
                    urls.append(url)
                if len(urls) >= num_results:
                    break
    except Exception as e:
        logger.warning(f"DuckDuckGo search failed for '{query}': {e}")
    # Deduplicate while preserving order
    seen = set()
    filtered = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            filtered.append(u)
    return filtered


def fetch_url(url: str) -> Tuple[Optional[str], Optional[bytes]]:
    """Fetch a URL, return content-type and bytes. None on failure."""
    try:
        with httpx.Client(timeout=60.0, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"}) as client:
            r = client.get(url)
            r.raise_for_status()
            ctype = r.headers.get("content-type", "").lower()
            return ctype, r.content
    except Exception as e:
        logger.warning(f"Fetch failed {url}: {e}")
        return None, None


def html_to_text(html_bytes: bytes) -> str:
    html = html_bytes.decode("utf-8", errors="ignore")
    # Remove scripts/styles
    html = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
    html = re.sub(r"<style[\s\S]*?</style>", " ", html, flags=re.IGNORECASE)
    # Replace <br> and <p> with newlines
    html = re.sub(r"<\s*br\s*/?>", "\n", html, flags=re.IGNORECASE)
    html = re.sub(r"<\s*/?p\s*>", "\n", html, flags=re.IGNORECASE)
    # Strip tags
    text = re.sub(r"<[^>]+>", " ", html)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _norm(s: str) -> str:
    s = s or ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.strip().lower()


def extract_queries_from_sheet(sheet_url: str, max_rows: int = 500, column: Optional[str] = None) -> List[str]:
    base = sheet_url.split("/edit")[0]
    gid = None
    if "gid=" in sheet_url:
        try:
            gid = sheet_url.split("gid=")[1].split("#")[0]
        except Exception:
            gid = None
    csv_url = base + "/export?format=csv"
    if gid:
        csv_url += f"&gid={gid}"
    logger.info("Downloading Google Sheet as CSV...")
    with httpx.Client(timeout=60.0, follow_redirects=True) as client:
        resp = client.get(csv_url)
        resp.raise_for_status()
        csv_text = resp.text
    f = StringIO(csv_text)
    reader = list(csv.reader(f))
    rows = reader[:max_rows]
    queries: List[str] = []

    # Resolve column selection if provided
    col_index: Optional[int] = None
    if column and rows:
        header = rows[0]
        # Try integer index
        if column.isdigit():
            try:
                col_index = int(column)
            except Exception:
                col_index = None
        else:
            # Match by header name (case-insensitive, trimmed)
            norm_header = [h.strip().lower() for h in header]
            if column.strip().lower() in norm_header:
                col_index = norm_header.index(column.strip().lower())

    def push(cell: str):
        cell = (cell or "").strip()
        if not cell:
            return
        if JURIS_REGEX.search(cell):
            queries.append(cell)

    # Pass 1: collect regex-matching cells (prefer selected column if provided)
    for ri, row in enumerate(rows):
        if col_index is not None and col_index < len(row):
            push(row[col_index])
        else:
            for cell in row:
                push(cell)

    # Fallback A: if no regex matches, try composing queries from common headers
    if not queries and rows:
        header = rows[0]
        header_norm = [_norm(h) for h in header]
        # Map likely column indices
        idx_num = next((i for i,h in enumerate(header_norm) if h in {"numero","número","nro","num"}), None)
        idx_year = next((i for i,h in enumerate(header_norm) if h in {"ano","año","year"}), None)
        idx_type = next((i for i,h in enumerate(header_norm) if any(k in h for k in ["tipo","sentencia","clase"]) ), None)
        idx_court = next((i for i,h in enumerate(header_norm) if any(k in h for k in ["corte","tribunal","sala"]) ), None)
        # Build queries like: "{tipo} {numero} de {año} {corte}"
        for ri, row in enumerate(rows[1:], start=1):
            num = (row[idx_num] if idx_num is not None and idx_num < len(row) else "").strip()
            year = (row[idx_year] if idx_year is not None and idx_year < len(row) else "").strip()
            tipo = (row[idx_type] if idx_type is not None and idx_type < len(row) else "").strip()
            corte = (row[idx_court] if idx_court is not None and idx_court < len(row) else "").strip()
            if num or year or tipo or corte:
                parts = []
                if tipo:
                    parts.append(tipo)
                if num:
                    parts.append(str(num))
                if year:
                    parts.append(f"de {year}")
                if corte:
                    parts.append(corte)
                q = " ".join(p for p in parts if p)
                if q:
                    queries.append(q)

    # Fallback B: if still no queries, take non-empty cells from selected column or first column
    if not queries:
        for ri, row in enumerate(rows):
            if ri == 0 and col_index is None and rows and any(isinstance(x, str) for x in rows[0]):
                # skip header by default only if matching by header
                pass
            target_idx = col_index if col_index is not None else 0
            if target_idx < len(row):
                val = (row[target_idx] or "").strip()
                if val:
                    queries.append(val)

    # Deduplicate
    seen = set()
    uniq = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            uniq.append(q)
    logger.info(f"Extracted {len(uniq)} jurisprudence queries from sheet")
    return uniq


def fetch_sheet_xlsx(sheet_url: str) -> bytes:
    base = sheet_url.split("/edit")[0]
    xlsx_url = base + "/export?format=xlsx"
    with httpx.Client(timeout=60.0, follow_redirects=True) as client:
        r = client.get(xlsx_url)
        r.raise_for_status()
        return r.content


def extract_rows_with_links(sheet_url: str, max_rows: int = 1000) -> List[Dict[str, Any]]:
    """Return rows with header mapping and include hyperlink targets, especially from Numero column."""
    try:
        from openpyxl import load_workbook
    except Exception as e:
        logger.warning(f"openpyxl not available: {e}")
        return []
    content = fetch_sheet_xlsx(sheet_url)
    wb = load_workbook(BytesIO(content), data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=False))
    if not rows:
        return []
    # Header
    header_cells = rows[0]
    headers = [(_norm(c.value) if c.value else f"col_{i}") for i, c in enumerate(header_cells)]
    out: List[Dict[str, Any]] = []
    for r in rows[1:max_rows+1]:
        row_map: Dict[str, Any] = {}
        for i, cell in enumerate(r):
            key = headers[i]
            row_map[key] = {
                "value": (cell.value if cell.value is not None else ""),
                "link": (cell.hyperlink.target if getattr(cell, "hyperlink", None) else None)
            }
        out.append(row_map)
    return out


def extract_queries_and_urls(sheet_url: str) -> Tuple[List[str], List[Tuple[str, str]]]:
    """Return queries and (query, direct_url) pairs using XLSX hyperlinks when present."""
    rows = extract_rows_with_links(sheet_url)
    if not rows:
        return [], []
    # Identify useful columns
    sample = rows[0]
    keys = list(sample.keys())
    key_num = next((k for k in keys if any(x in k for x in ["numero","número","nro","num"])), None)
    key_year = next((k for k in keys if any(x in k for x in ["ano","año","year"])), None)
    key_type = next((k for k in keys if any(x in k for x in ["tipo","sentencia","clase"]) ), None)
    key_court = next((k for k in keys if any(x in k for x in ["corte","tribunal","sala"]) ), None)

    queries: List[str] = []
    direct: List[Tuple[str, str]] = []
    for rm in rows:
        num_val = (rm.get(key_num, {}).get("value") if key_num else None)
        num_link = (rm.get(key_num, {}).get("link") if key_num else None)
        year_val = (rm.get(key_year, {}).get("value") if key_year else None)
        type_val = (rm.get(key_type, {}).get("value") if key_type else None)
        court_val = (rm.get(key_court, {}).get("value") if key_court else None)
        parts = []
        if type_val:
            parts.append(str(type_val))
        if num_val:
            parts.append(str(num_val))
        if year_val:
            parts.append(f"de {year_val}")
        if court_val:
            parts.append(str(court_val))
        q = " ".join(p for p in parts if p)
        if q:
            queries.append(q)
            if num_link and isinstance(num_link, str) and num_link.startswith("http"):
                direct.append((q, num_link))
    return queries, direct


def extract_links_from_corte_buscador(page_url: str, max_items: int = 50) -> List[Tuple[str, str]]:
    """Extract (numero_text, href) pairs from Corte Constitucional buscador page.
    Reference: https://www.corteconstitucional.gov.co/relatoria/buscador-jurisprudencia
    """
    try:
        from bs4 import BeautifulSoup
    except Exception as e:
        logger.warning(f"beautifulsoup4 not available: {e}")
        return []
    with httpx.Client(timeout=60.0, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"}) as client:
        r = client.get(page_url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
    pairs: List[Tuple[str, str]] = []
    # Heuristic: take anchors whose text looks like Numero (e.g., T-123 de 2020, SU-123/2018, C-123/20)
    numero_pattern = re.compile(r"\b(SU|T|C|A|Auto|SL|SP|SC)\s*[-–]?\s*\d+\s*(de|/)?\s*\d{2,4}\b", re.IGNORECASE)
    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True)
        href = a["href"].strip()
        if not href:
            continue
        if numero_pattern.search(text):
            # Normalize absolute URL
            if href.startswith("/"):
                from urllib.parse import urljoin
                abs_url = urljoin(page_url, href)
            elif href.startswith("http"):
                abs_url = href
            else:
                from urllib.parse import urljoin
                abs_url = urljoin(page_url, href)
            pairs.append((text, abs_url))
            if len(pairs) >= max_items:
                break
    logger.info(f"Extracted {len(pairs)} links from Corte buscador page")
    return pairs


def extract_links_from_corte_buscador_playwright(page_url: str, max_items: int = 50) -> List[Tuple[str, str]]:
    """Use Playwright to render the buscador and extract (numero, href) links."""
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        logger.warning(f"Playwright is not installed or unavailable: {e}")
        return []
    
    # Accept forms like: C-269/25, T-329/25, T-312/25, T-321/25, SU.204/25
    numero_pattern = re.compile(r"\b(SU|T|C|A|Auto|SL|SP|SC)[\.-]?\s*\d+\s*(?:de|/)?\s*\d{2,4}\b", re.IGNORECASE)
    pairs: List[Tuple[str, str]] = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                context = browser.new_context()
                page = context.new_page()
                
                logger.info(f"Loading page: {page_url}")
                page.goto(page_url, wait_until="domcontentloaded")
                
                # Wait for initial content to load
                page.wait_for_timeout(3000)
                
                # Debug: Take a screenshot to see what's loaded
                try:
                    page.screenshot(path="debug_page.png")
                    logger.info("Screenshot saved as debug_page.png")
                except Exception as e:
                    logger.warning(f"Could not save screenshot: {e}")
                
                # Debug: Log page title and content
                try:
                    title = page.title()
                    logger.info(f"Page title: {title}")
                except Exception:
                    pass
                
                # Wait for dynamic content to load - the jurisprudence table might be loaded via AJAX
                logger.info("Waiting for dynamic content to load...")
                
                # Try to wait for the jurisprudence table to appear
                try:
                    # Wait for any element containing jurisprudence-related text
                    page.wait_for_selector("text=Últimas", timeout=15000)
                    logger.info("Found 'Últimas' text, waiting for table...")
                    
                    # Additional wait for the table structure
                    page.wait_for_timeout(2000)
                except Exception:
                    logger.warning("'Últimas' text not found, continuing anyway...")
                
                # Wait for network to be idle (AJAX calls to complete)
                try:
                    page.wait_for_load_state("networkidle", timeout=15000)
                    logger.info("Network is idle")
                except Exception:
                    logger.warning("Network idle timeout, continuing...")
                
                # Additional wait for any remaining dynamic content
                page.wait_for_timeout(3000)
                
                # Try to interact with the page to trigger jurisprudence loading
                logger.info("Attempting to interact with page to load jurisprudence...")
                
                # Look for and click any search or load buttons
                try:
                    search_selectors = [
                        "button:has-text('Buscar')",
                        "button:has-text('Search')",
                        "button:has-text('Cargar')",
                        "button:has-text('Load')",
                        "input[type='submit']",
                        "[class*='search']",
                        "[class*='btn']"
                    ]
                    
                    for selector in search_selectors:
                        try:
                            if page.locator(selector).count() > 0:
                                logger.info(f"Found button with selector: {selector}")
                                page.locator(selector).first.click()
                                logger.info("Clicked button, waiting for content...")
                                page.wait_for_timeout(3000)
                                break
                        except Exception:
                            continue
                except Exception as e:
                    logger.debug(f"Button interaction failed: {e}")
                
                # Try to change the "Mostrar" dropdown if it exists
                try:
                    mostrar_selectors = [
                        "select:has-text('Mostrar')",
                        "select:has-text('Show')",
                        "[name*='mostrar']",
                        "[name*='show']"
                    ]
                    
                    for selector in mostrar_selectors:
                        try:
                            if page.locator(selector).count() > 0:
                                logger.info(f"Found dropdown with selector: {selector}")
                                # Select 50 items
                                page.locator(selector).select_option("50")
                                logger.info("Changed dropdown to 50, waiting for content...")
                                page.wait_for_timeout(3000)
                                break
                        except Exception:
                            continue
                except Exception as e:
                    logger.debug(f"Dropdown interaction failed: {e}")
                
                # Debug: Check what elements are actually on the page
                try:
                    all_elements = page.locator("*")
                    element_count = all_elements.count()
                    logger.info(f"Total elements on page: {element_count}")
                    
                    # Check for specific text patterns
                    if page.locator("text=Últimas").count() > 0:
                        logger.info("Found 'Últimas' text on page")
                    if page.locator("text=Sentencias").count() > 0:
                        logger.info("Found 'Sentencias' text on page")
                    if page.locator("text=Número").count() > 0:
                        logger.info("Found 'Número' text on page")
                    
                    # Check for table elements
                    table_count = page.locator("table").count()
                    logger.info(f"Found {table_count} table elements")
                    
                    # Check for div elements that might contain the jurisprudence data
                    div_count = page.locator("div").count()
                    logger.info(f"Found {div_count} div elements")
                    
                    # Check if we now have more content
                    if page.locator("text=C-269/25").count() > 0:
                        logger.info("Found jurisprudence case C-269/25!")
                    if page.locator("text=T-329/25").count() > 0:
                        logger.info("Found jurisprudence case T-329/25!")
                except Exception as e:
                    logger.warning(f"Debug element check failed: {e}")
                
                # Look for the jurisprudence data - it might not be in a standard table
                logger.info("Looking for jurisprudence data...")
                
                # Check if we can find the jurisprudence content directly
                jurisprudence_found = False
                
                # Look for various containers that might hold the jurisprudence data
                content_selectors = [
                    "table:has-text('Últimas')",
                    "table:has-text('Sentencias')", 
                    "table:has-text('Número')",
                    "table",
                    ".table",
                    "[class*='table']",
                    "[class*='grid']",
                    "[class*='list']",
                    "[class*='content']",
                    "div:has-text('Últimas')",
                    "div:has-text('Sentencias')",
                    "div:has-text('Número')"
                ]
                
                for selector in content_selectors:
                    try:
                        if page.locator(selector).count() > 0:
                            logger.info(f"Found content with selector: {selector}")
                            jurisprudence_found = True
                            break
                    except Exception:
                        continue
                
                if not jurisprudence_found:
                    logger.warning("No jurisprudence content found on page")
                    return []
                
                def collect_from_frame(frame) -> List[Tuple[str, str]]:
                    results: List[Tuple[str, str]] = []
                    try:
                        # Try multiple strategies to find the jurisprudence links
                        selectors = [
                            "table a",           # Standard table links
                            ".table a",          # Bootstrap table links
                            "[class*='table'] a", # Generic table class links
                            "[class*='grid'] a",  # Grid container links
                            "[class*='list'] a",  # List container links
                            "[class*='content'] a", # Content container links
                            "a[href*='relatoria']", # Links containing 'relatoria'
                            "a[href*='sentencia']", # Links containing 'sentencia'
                            "a[href*='expediente']", # Links containing 'expediente'
                            "a[href*='buscador']",  # Links containing 'buscador'
                            "a[href*='numero']",    # Links containing 'numero'
                            "a[href*='caso']",      # Links containing 'caso'
                            "a[href*='sentencia']", # Links containing 'sentencia'
                            "a[href*='decision']"   # Links containing 'decision'
                        ]
                        
                        all_anchors = []
                        for selector in selectors:
                            try:
                                anchors = frame.locator(selector)
                                count = anchors.count()
                                if count > 0:
                                    logger.info(f"Selector '{selector}' found {count} anchors")
                                    for i in range(count):
                                        try:
                                            all_anchors.append(anchors.nth(i))
                                        except Exception:
                                            continue
                            except Exception:
                                continue
                        
                        # If no anchors found with specific selectors, try all anchors
                        if not all_anchors:
                            logger.info("No anchors found with specific selectors, trying all anchors...")
                            try:
                                all_anchors = frame.locator("a").all()
                                logger.info(f"Found {len(all_anchors)} total anchors")
                            except Exception as e:
                                logger.warning(f"Could not get all anchors: {e}")
                                all_anchors = []
                        
                        # Also try to find anchors that might be in the jurisprudence table
                        # Look for anchors near the "Número" column header
                        try:
                            numero_header = frame.locator("text=Número")
                            if numero_header.count() > 0:
                                logger.info("Found 'Número' header, looking for nearby anchors...")
                                # Look for anchors in the same container or nearby
                                container = numero_header.locator("xpath=ancestor::*[contains(@class, 'table') or contains(@class, 'grid') or contains(@class, 'content')]")
                                if container.count() > 0:
                                    container_anchors = container.locator("a")
                                    container_count = container_anchors.count()
                                    logger.info(f"Found {container_count} anchors in 'Número' container")
                                    for i in range(container_count):
                                        try:
                                            all_anchors.append(container_anchors.nth(i))
                                        except Exception:
                                            continue
                        except Exception as e:
                            logger.debug(f"Could not find 'Número' container: {e}")
                        
                        # Remove duplicates while preserving order
                        seen_anchors = set()
                        unique_anchors = []
                        for anchor in all_anchors:
                            try:
                                text = (anchor.inner_text() or "").strip()
                                href = anchor.get_attribute("href") or ""
                                key = f"{text}:{href}"
                                if key not in seen_anchors:
                                    seen_anchors.add(key)
                                    unique_anchors.append((anchor, text, href))
                            except Exception:
                                continue
                        
                        logger.info(f"Processing {len(unique_anchors)} unique anchors")
                        
                        # Debug: Log some anchor details
                        for i, (anchor, text, href) in enumerate(unique_anchors[:5]):  # Log first 5
                            logger.info(f"Anchor {i}: text='{text}', href='{href}'")
                        
                        for anchor, text, href in unique_anchors:
                            try:
                                if not text or not href:
                                    continue
                                
                                # Check if this looks like a jurisprudence number
                                if numero_pattern.search(text):
                                    # Normalize URL
                                    if href.startswith("/"):
                                        from urllib.parse import urljoin
                                        href = urljoin(page_url, href)
                                    elif href.startswith("javascript:"):
                                        continue
                                    
                                    results.append((text, href))
                                    logger.info(f"Found jurisprudence link: {text} -> {href}")
                                    
                                    if len(results) >= max_items:
                                        break
                                else:
                                    logger.debug(f"Text '{text}' doesn't match jurisprudence pattern")
                            except Exception as e:
                                logger.debug(f"Error processing anchor: {e}")
                                continue
                    except Exception as e:
                        logger.warning(f"Error collecting from frame: {e}")
                    return results
                
                # Collect from main page
                pairs.extend(collect_from_frame(page))
                
                # Also check child frames
                for fr in page.frames:
                    if fr is page.main_frame:
                        continue
                    try:
                        pairs.extend(collect_from_frame(fr))
                    except Exception as e:
                        logger.debug(f"Error processing child frame: {e}")
                        continue
                
                # Deduplicate
                seen = set()
                uniq = []
                for t, u in pairs:
                    if (t, u) not in seen:
                        seen.add((t, u))
                        uniq.append((t, u))
                pairs = uniq[:max_items]
                
            finally:
                try:
                    context.close()
                except:
                    pass
                try:
                    browser.close()
                except:
                    pass
                
    except Exception as e:
        logger.error(f"Playwright error: {e}")
        return []
    
    logger.info(f"Playwright extracted {len(pairs)} links from Corte buscador page")
    return pairs


def infer_metadata_from(q: str, url: str, text: str) -> Dict[str, Any]:
    case_match = JURIS_REGEX.search(q) or JURIS_REGEX.search(text[:2000])
    case_number = case_match.group(0) if case_match else None
    court = None
    domain_to_court = {
        "corteconstitucional.gov.co": "Corte Constitucional",
        "cortesuprema.gov.co": "Corte Suprema de Justicia",
        "consejodeestado.gov.co": "Consejo de Estado",
    }
    for domain, name in domain_to_court.items():
        if domain in url:
            court = name
            break
    decision_type = "sentencia"
    if re.search(r"\bauto\b", q, re.IGNORECASE) or re.search(r"\bauto\b", text[:1000], re.IGNORECASE):
        decision_type = "auto"
    summary = text[:800]
    topic = q[:200]
    return {
        "case_number": case_number,
        "court": court,
        "decision_type": decision_type,
        "decision_date": None,
        "topic": topic,
        "summary": summary,
        "source_url": url,
    }


def build_documents_from_queries(queries: List[str], delay: float = 2.0, max_per_query: int = 2) -> List[Document]:
    documents: List[Document] = []
    for i, q in enumerate(queries, 1):
        logger.info(f"[{i}/{len(queries)}] Searching web for: {q}")
        urls = ddg_search(q, num_results=max_per_query)
        if not urls:
            logger.info(f"No URLs found for {q}")
            continue
        for url in urls[:max_per_query]:
            logger.info(f"Fetching: {url}")
            ctype, content = fetch_url(url)
            if not content:
                continue
            text = ""
            if ctype and "pdf" in ctype:
                text_raw = extract_text_from_pdf_content(content) or ""
                text = sanitize_text(text_raw)
            else:
                text = sanitize_text(html_to_text(content))
            if len(text) < 300:
                logger.info(f"Content too short from {url} ({len(text)} chars), skipping")
                continue
            doc = Document(
                name=f"Jurisprudencia: {q}",
                content=text,
                meta_data={
                    "source": "web",
                    "query": q,
                    "url": url
                }
            )
            # Attach provisional metadata for jurisprudence
            doc.meta_data.update(infer_metadata_from(q, url, text))
            documents.append(doc)
            time.sleep(delay)
    logger.info(f"Built {len(documents)} documents from web content")
    return documents


def upsert_documents_pgvector(documents: List[Document], table_name: str):
    if not documents:
        logger.info("No documents to upsert")
        return

    db_url = to_sqlalchemy_url(POSTGRES_URL)
    embedder = MistralEmbedder(
        id="mistral-embed",
        dimensions=1024,
        api_key=MISTRAL_API_KEY
    )
    vector_db = PgVector(
        table_name=table_name,
        db_url=db_url,
        search_type=SearchType.hybrid,
        embedder=embedder
    )
    batch_size = 5
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        logger.info(f"Upserting batch {i//batch_size + 1}/{(len(documents)+batch_size-1)//batch_size} ({len(batch)} docs)")
        vector_db.upsert(batch)
        time.sleep(1.0)


def format_vector(vec: List[float]) -> str:
    return "[" + ",".join(str(x) for x in vec) + "]"


def upsert_documents_jurisprudence_psycopg(documents: List[Document]):
    if not documents:
        logger.info("No documents to upsert")
        return

    import psycopg

    # Use plain psycopg connection string (no +psycopg)
    dsn = POSTGRES_URL
    embedder = MistralEmbedder(id="mistral-embed", dimensions=1024, api_key=MISTRAL_API_KEY)

    inserted_jurisprudence = 0
    inserted_legal_docs = 0
    
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            for doc in documents:
                meta = doc.meta_data or {}
                emb = embedder.get_embedding(doc.content)
                vector_str = format_vector(emb) if emb else None
                
                # Convert empty arrays to PostgreSQL format {} instead of []
                key_holdings = meta.get("key_holdings") or []
                legal_principles = meta.get("legal_principles") or []
                cited_laws = meta.get("cited_laws") or []
                cited_precedents = meta.get("cited_precedents") or []
                tags = ["jurisprudencia"]
                
                # 1. Insert into jurisprudence table
                jurisprudence_fields = (
                    meta.get("case_number"),
                    meta.get("court"),
                    meta.get("decision_type"),
                    meta.get("decision_date"),
                    meta.get("topic") or (doc.name or "")[:200],
                    meta.get("summary") or doc.content[:800],
                    doc.content,
                    key_holdings,
                    legal_principles,
                    cited_laws,
                    cited_precedents,
                    None,  # relevance_score
                    tags,
                    meta.get("source_url") or meta.get("url"),
                    vector_str,
                )
                
                sql_jurisprudence = (
                    "INSERT INTO jurisprudence (case_number, court, decision_type, decision_date, topic, summary, full_text, "
                    "key_holdings, legal_principles, cited_laws, cited_precedents, relevance_score, tags, source_url, vector_embedding) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, "
                    "%s, %s, %s, %s, %s, %s, %s, %s::vector)"
                )
                
                try:
                    cur.execute(sql_jurisprudence, jurisprudence_fields)
                    inserted_jurisprudence += 1
                    logger.info(f"Inserted jurisprudence: {doc.name}")
                except Exception as e:
                    logger.warning(f"Jurisprudence insert failed: {e}")
                    try:
                        # Fallback without vector
                        sql2 = (
                            "INSERT INTO jurisprudence (case_number, court, decision_type, decision_date, topic, summary, full_text, "
                            "key_holdings, legal_principles, cited_laws, cited_precedents, relevance_score, tags, source_url) "
                            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                        )
                        cur.execute(sql2, jurisprudence_fields[:-1])
                        inserted_jurisprudence += 1
                        logger.info(f"Inserted jurisprudence (no vector): {doc.name}")
                    except Exception as e2:
                        logger.error(f"Jurisprudence insert failed completely: {e2}")
                        continue
                
                # 2. Also insert into legal_documents_ai for general AI agent access
                # Map jurisprudence to legal document format
                document_type = meta.get("decision_type") or "sentencia"
                if not document_type or document_type.lower() in ["auto", "concepto"]:
                    document_type = "sentencia"
                
                title = f"{meta.get('case_number', 'Jurisprudencia')} - {meta.get('topic', 'Corte Constitucional')}"
                if len(title) > 500:
                    title = title[:497] + "..."
                
                legal_docs_fields = (
                    title,
                    document_type,
                    meta.get("case_number"),
                    meta.get("decision_date", "2024").split("-")[0] if meta.get("decision_date") else "2024",
                    "Colombia",  # jurisdiction
                    doc.content,
                    meta.get("summary") or doc.content[:800],
                    ["jurisprudencia", "corte constitucional"] + (meta.get("tags") or []),
                    tags,
                    meta.get("source_url") or meta.get("url"),
                    None,  # official_gazette_reference
                    meta.get("decision_date"),
                    None,  # amendment_date
                    "active",  # status
                    vector_str,
                )
                
                sql_legal_docs = (
                    "INSERT INTO legal_documents_ai (title, document_type, document_number, year, jurisdiction, content, summary, "
                    "keywords, tags, source_url, official_gazette_reference, effective_date, amendment_date, status, vector_embedding) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector)"
                )
                
                try:
                    cur.execute(sql_legal_docs, legal_docs_fields)
                    inserted_legal_docs += 1
                    logger.info(f"Inserted legal_documents_ai: {title}")
                except Exception as e:
                    logger.warning(f"Legal documents insert failed: {e}")
                    try:
                        # Fallback without vector
                        sql2 = (
                            "INSERT INTO legal_documents_ai (title, document_type, document_number, year, jurisdiction, content, summary, "
                            "keywords, tags, source_url, official_gazette_reference, effective_date, amendment_date, status) "
                            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                        )
                        cur.execute(sql2, legal_docs_fields[:-1])
                        inserted_legal_docs += 1
                        logger.info(f"Inserted legal_documents_ai (no vector): {title}")
                    except Exception as e2:
                        logger.error(f"Legal documents insert failed completely: {e2}")
                
                # Commit after each document to avoid large transactions
                conn.commit()
                time.sleep(0.3)

    logger.info(f"Inserted {inserted_jurisprudence}/{len(documents)} into jurisprudence")
    logger.info(f"Inserted {inserted_legal_docs}/{len(documents)} into legal_documents_ai")


def main():
    parser = argparse.ArgumentParser(description="Crawl jurisprudence by name and ingest into Supabase")
    parser.add_argument("--sheet", help="Google Sheets URL containing jurisprudence names")
    parser.add_argument("--queries", help="Semicolon-separated list of jurisprudence queries")
    parser.add_argument("--table", default="legal_documents_ai", help="Target table name for pgvector mode (default: legal_documents_ai)")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between fetches")
    parser.add_argument("--max-per-query", type=int, default=2, help="Max URLs per query to ingest")
    parser.add_argument("--sheet-col", help="Optional column index (0-based) or header name to read queries from")
    parser.add_argument("--corte-url", help="Corte Constitucional buscador URL to extract Numero links")
    parser.add_argument("--corte-limit", type=int, default=20, help="Max items to pull from Corte buscador")
    parser.add_argument("--corte-rendered", action="store_true", help="Use Playwright to render Corte buscador and extract Numero links")
    parser.add_argument("--mode", choices=["pgvector", "jurisprudence"], default="jurisprudence", help="Ingest mode: pgvector table or jurisprudence table")
    args = parser.parse_args()

    if not POSTGRES_URL and args.mode == "pgvector":
        logger.error("POSTGRES_URL not configured")
        sys.exit(1)
    if not MISTRAL_API_KEY:
        logger.error("MISTRAL_API_KEY not configured")
        sys.exit(1)

    queries: List[str] = []
    direct_urls: List[Tuple[str, str]] = []
    if args.sheet:
        try:
            # Prefer XLSX hyperlinks when available
            q2, direct_urls = extract_queries_and_urls(args.sheet)
            queries.extend(q2)
            # Fallback to CSV-based extraction for additional candidates
            queries.extend(extract_queries_from_sheet(args.sheet, column=args.sheet_col))
        except Exception as e:
            logger.error(f"Failed to extract queries from sheet: {e}")

    if args.corte_url:
        try:
            if args.corte_rendered:
                corte_pairs = extract_links_from_corte_buscador_playwright(args.corte_url, max_items=args.corte_limit)
                if not corte_pairs:
                    # fallback to static parse
                    corte_pairs = extract_links_from_corte_buscador(args.corte_url, max_items=args.corte_limit)
            else:
                corte_pairs = extract_links_from_corte_buscador(args.corte_url, max_items=args.corte_limit)
            direct_urls.extend(corte_pairs)
            # Also add the Numero texts as queries for better metadata inference
            queries.extend([q for q,_ in corte_pairs])
        except Exception as e:
            logger.error(f"Failed to extract links from Corte buscador: {e}")

    if args.queries:
        queries.extend([q.strip() for q in args.queries.split(";") if q.strip()])

    # Deduplicate
    seen = set()
    queries = [q for q in queries if not (q in seen or seen.add(q))]

    if not queries and not direct_urls:
        logger.error("No queries or direct URLs provided or found. Use --sheet, --queries, or --corte-url.")
        sys.exit(1)

    # If we have direct URLs from Numero column, fetch them first
    direct_docs: List[Document] = []
    for (q, url) in direct_urls:
        ctype, content = fetch_url(url)
        if not content:
            continue
        if ctype and "pdf" in ctype:
            text_raw = extract_text_from_pdf_content(content) or ""
            text = sanitize_text(text_raw)
        else:
            text = sanitize_text(html_to_text(content))
        if len(text) < 300:
            continue
        
        # Truncate text to avoid Mistral token limit (8192 tokens ≈ 24,000 characters)
        # Keep a safety margin - be more aggressive with truncation
        max_chars = 20000
        if len(text) > max_chars:
            logger.info(f"Truncating text from {len(text)} to {max_chars} characters for {q}")
            text = text[:max_chars] + "\n\n[Texto truncado por límite de tokens]"
        doc = Document(
            name=f"Jurisprudencia: {q}",
            content=text,
            meta_data={
                "source": "web",
                "query": q,
                "url": url
            }
        )
        doc.meta_data.update(infer_metadata_from(q, url, text))
        direct_docs.append(doc)

    # Then do search-based collection for remaining
    docs = build_documents_from_queries(queries, delay=args.delay, max_per_query=args.max_per_query)
    docs = direct_docs + docs

    if args.mode == "pgvector":
        upsert_documents_pgvector(docs, table_name=args.table)
    else:
        upsert_documents_jurisprudence_psycopg(docs)

if __name__ == "__main__":
    main()