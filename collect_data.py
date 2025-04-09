import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
from typing import List, Dict, Any, Optional
import json
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin
import urllib3
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import re
from datetime import datetime
from dataclasses import dataclass

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure retry strategy
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)

# Create a session with custom settings
session = requests.Session()
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)

# Update configurations with correct URLs
AGENT_CONFIGS = {
    "case_prediction": {
        "sources": {
            "rama_judicial": "https://ramajudicial.gov.co",
            "consejo_estado": "https://consejodeestado.gov.co",
            "corte_suprema": "https://cortesuprema.gov.co",
            "corte_constitucional": "https://www.corteconstitucional.gov.co/relatoria/",
            "procuraduria": "https://www.procuraduria.gov.co",
        }
    },
    "legal_chatbot": {
        "sources": {
            "gobierno_digital": "https://www.datos.gov.co",
            "minjusticia": "https://www.minjusticia.gov.co",
            "legal_clinics": {
                "unal": "https://consultoriojuridico.unal.edu.co",
                "uniandes": "https://consultoriojuridico.uniandes.edu.co",
                "uexternado": "https://consultoriojuridico.uexternado.edu.co",
                "urosario": "https://consultoriojuridico.urosario.edu.co"
            }
        }
    },
    "compliance": {
        "sources": {
            "diario_oficial": "http://svrpubindc.imprenta.gov.co/diario/",
            "sic": "https://www.sic.gov.co",
            "superfinanciera": "https://www.superfinanciera.gov.co",
            "secop": "https://colombiacompra.gov.co/secop-ii"
        }
    }
}

# Colombian Legal Document Patterns
@dataclass
class ColombianLegalPatterns:
    # Document Types
    SENTENCIA = r'Sentencia\s+(?:No\.)?\s*[\w-]+'
    AUTO = r'Auto\s+(?:No\.)?\s*[\w-]+'
    RESOLUCION = r'Resolución\s+(?:No\.)?\s*[\w-]+'
    DECRETO = r'Decreto\s+(?:No\.)?\s*[\w-]+'
    
    # Legal References
    ARTICULO = r'Art(?:ículo|iculo)\s+\d+'
    PARAGRAFO = r'Parágrafo\s+\d+'
    NUMERAL = r'Numeral\s+\d+'
    
    # Court References
    EXPEDIENTE = r'Expediente\s+(?:No\.)?\s*[\w-]+'
    RADICADO = r'Radicado\s+(?:No\.)?\s*[\w-]+'
    
    # Legal Entities
    CORPORACION = r'Corporación\s+[\w\s]+'
    JUZGADO = r'Juzgado\s+[\w\s]+'
    TRIBUNAL = r'Tribunal\s+[\w\s]+'

def scrape_website(url: str, selectors: Dict[str, str]) -> List[Dict[str, Any]]:
    """Generic scraping function with improved error handling and SSL verification options"""
    documents = []
    try:
        # Custom headers to mimic browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Make request with SSL verification disabled and custom headers
        response = session.get(
            url,
            headers=headers,
            verify=False,  # Disable SSL verification
            timeout=30
        )
        response.raise_for_status()
        
        # Parse content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try different selectors if the main ones don't work
        containers = soup.select(selectors.get('container', 'body'))
        if not containers:
            containers = soup.select('div.content, article, main, .main-content')
        
        for element in containers:
            title_element = element.select_one(selectors.get('title', 'h1,h2,h3'))
            title = title_element.get_text(strip=True) if title_element else "No title"
            
            documents.append({
                'title': title,
                'text': element.get_text(separator='\n', strip=True),
                'url': url,
                'source': url.split('/')[2]
            })
        
        # If no documents were found, try to get at least the page content
        if not documents:
            documents.append({
                'title': soup.title.string if soup.title else "No title",
                'text': soup.get_text(separator='\n', strip=True),
                'url': url,
                'source': url.split('/')[2]
            })
            
        time.sleep(2)  # Increased rate limiting
        
    except Exception as e:
        print(f"Error scraping {url}: {str(e)}")
        # Log the error for debugging
        with open("scraping_errors.log", "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {url}: {str(e)}\n")
    
    return documents

def scrape_case_prediction_data(url: str) -> List[Dict[str, Any]]:
    """Specialized scraper for case prediction data"""
    documents = []
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = session.get(url, headers=headers, verify=False, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for specific case-related content
        cases = soup.find_all(['div', 'article'], class_=re.compile(r'(sentencia|decision|case|fallo)'))
        
        for case in cases:
            # Extract structured case information
            case_data = {
                'case_number': extract_case_number(case),
                'date': extract_date(case),
                'court': extract_court_info(case),
                'type': extract_case_type(case),
                'summary': extract_case_summary(case),
                'decision': extract_decision(case),
                'keywords': extract_keywords(case),
                'url': url,
                'source': url.split('/')[2]
            }
            
            # Validate case data
            if is_valid_case_data(case_data):
                documents.append(case_data)
        
    except Exception as e:
        print(f"Error scraping case data from {url}: {str(e)}")
    
    return documents

def scrape_legal_chatbot_data(url: str) -> List[Dict[str, Any]]:
    """Specialized scraper for legal Q&A data"""
    documents = []
    try:
        response = session.get(url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for FAQ sections and legal questions
        qa_pairs = soup.find_all(['div', 'section'], class_=re.compile(r'(faq|pregunta|question)'))
        
        for qa in qa_pairs:
            qa_data = {
                'question': extract_question(qa),
                'answer': extract_answer(qa),
                'category': extract_legal_category(qa),
                'jurisdiction': extract_jurisdiction(qa),
                'source_type': 'FAQ' if is_faq(qa) else 'Legal Consultation',
                'date_added': extract_date(qa),
                'url': url,
                'source': url.split('/')[2]
            }
            
            if is_valid_qa_data(qa_data):
                documents.append(qa_data)
                
    except Exception as e:
        print(f"Error scraping legal Q&A from {url}: {str(e)}")
    
    return documents

def scrape_compliance_data(url: str) -> List[Dict[str, Any]]:
    """Specialized scraper for compliance and regulatory data"""
    documents = []
    try:
        response = session.get(url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for regulatory content
        regulations = soup.find_all(['div', 'article'], class_=re.compile(r'(regulation|norma|circular)'))
        
        for reg in regulations:
            reg_data = {
                'regulation_id': extract_regulation_id(reg),
                'title': extract_regulation_title(reg),
                'type': extract_regulation_type(reg),
                'issuing_body': extract_issuing_body(reg),
                'date_issued': extract_date(reg),
                'effective_date': extract_effective_date(reg),
                'summary': extract_regulation_summary(reg),
                'requirements': extract_requirements(reg),
                'affected_sectors': extract_affected_sectors(reg),
                'url': url,
                'source': url.split('/')[2]
            }
            
            if is_valid_regulation_data(reg_data):
                documents.append(reg_data)
                
    except Exception as e:
        print(f"Error scraping compliance data from {url}: {str(e)}")
    
    return documents

# Helper functions for data extraction and validation
def extract_case_number(element) -> str:
    """Extract standardized case number"""
    case_number = element.find(text=re.compile(r'[0-9]{2,}-[0-9]{3,}'))
    return case_number.strip() if case_number else None

def extract_date(element) -> str:
    """Extract and standardize dates"""
    date_text = element.find(text=re.compile(r'\d{1,2}\s+de\s+\w+\s+de\s+\d{4}'))
    if date_text:
        try:
            return datetime.strptime(date_text.strip(), '%d de %B de %Y').strftime('%Y-%m-%d')
        except:
            return None
    return None

def is_valid_case_data(case_data: Dict[str, Any]) -> bool:
    """Validate case data completeness and relevance"""
    required_fields = ['case_number', 'date', 'court', 'summary']
    return all(case_data.get(field) for field in required_fields)

def is_valid_qa_data(qa_data: Dict[str, Any]) -> bool:
    """Validate Q&A data completeness and relevance"""
    return (qa_data.get('question') and 
            qa_data.get('answer') and 
            len(qa_data['answer']) > 50)  # Ensure substantial answers

def is_valid_regulation_data(reg_data: Dict[str, Any]) -> bool:
    """Validate regulation data completeness and relevance"""
    required_fields = ['regulation_id', 'title', 'date_issued', 'summary']
    return all(reg_data.get(field) for field in required_fields)

# Specialized scrapers for additional agent types
def scrape_document_drafting_data(url: str) -> List[Dict[str, Any]]:
    """Specialized scraper for document drafting templates and examples"""
    documents = []
    try:
        response = session.get(url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for legal document templates
        templates = soup.find_all(['div', 'article'], class_=re.compile(r'(template|modelo|formato)'))
        
        for template in templates:
            template_data = {
                'document_type': extract_document_type(template),
                'title': extract_template_title(template),
                'content': extract_template_content(template),
                'sections': extract_document_sections(template),
                'usage_instructions': extract_usage_instructions(template),
                'jurisdiction': extract_jurisdiction(template),
                'keywords': extract_legal_keywords(template),
                'last_updated': extract_date(template),
                'url': url,
                'source': url.split('/')[2]
            }
            
            if is_valid_template_data(template_data):
                documents.append(template_data)
                
    except Exception as e:
        print(f"Error scraping document templates from {url}: {str(e)}")
    
    return documents

def scrape_patent_data(url: str) -> List[Dict[str, Any]]:
    """Specialized scraper for patent and intellectual property data"""
    documents = []
    try:
        response = session.get(url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for patent information
        patents = soup.find_all(['div', 'article'], class_=re.compile(r'(patent|patente|registro)'))
        
        for patent in patents:
            patent_data = {
                'patent_number': extract_patent_number(patent),
                'title': extract_patent_title(patent),
                'inventors': extract_inventors(patent),
                'filing_date': extract_filing_date(patent),
                'grant_date': extract_grant_date(patent),
                'abstract': extract_patent_abstract(patent),
                'claims': extract_patent_claims(patent),
                'classification': extract_patent_classification(patent),
                'legal_status': extract_legal_status(patent),
                'url': url,
                'source': url.split('/')[2]
            }
            
            if is_valid_patent_data(patent_data):
                documents.append(patent_data)
                
    except Exception as e:
        print(f"Error scraping patent data from {url}: {str(e)}")
    
    return documents

def scrape_regulatory_analysis_data(url: str) -> List[Dict[str, Any]]:
    """Specialized scraper for regulatory analysis content"""
    documents = []
    try:
        response = session.get(url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for regulatory analysis content
        regulations = soup.find_all(['div', 'article'], class_=re.compile(r'(regulation|analisis|normativa)'))
        
        for reg in regulations:
            reg_data = {
                'regulation_id': extract_regulation_id(reg),
                'title': extract_regulation_title(reg),
                'analysis_date': extract_date(reg),
                'sector': extract_sector(reg),
                'impact_analysis': extract_impact_analysis(reg),
                'key_requirements': extract_key_requirements(reg),
                'compliance_deadline': extract_compliance_deadline(reg),
                'affected_entities': extract_affected_entities(reg),
                'risk_assessment': extract_risk_assessment(reg),
                'implementation_guide': extract_implementation_guide(reg),
                'url': url,
                'source': url.split('/')[2]
            }
            
            if is_valid_regulatory_analysis_data(reg_data):
                documents.append(reg_data)
                
    except Exception as e:
        print(f"Error scraping regulatory analysis from {url}: {str(e)}")
    
    return documents

# Enhanced data validation functions
def is_valid_template_data(template_data: Dict[str, Any]) -> bool:
    """Validate document template data"""
    required_fields = ['document_type', 'title', 'content', 'sections']
    if not all(template_data.get(field) for field in required_fields):
        return False
    
    # Validate content length
    if len(template_data['content']) < 100:  # Minimum content length
        return False
    
    # Validate sections structure
    if not isinstance(template_data['sections'], list) or len(template_data['sections']) < 1:
        return False
    
    return True

def is_valid_patent_data(patent_data: Dict[str, Any]) -> bool:
    """Validate patent data"""
    required_fields = ['patent_number', 'title', 'filing_date', 'abstract']
    if not all(patent_data.get(field) for field in required_fields):
        return False
    
    # Validate dates
    try:
        datetime.strptime(patent_data['filing_date'], '%Y-%m-%d')
        if patent_data.get('grant_date'):
            datetime.strptime(patent_data['grant_date'], '%Y-%m-%d')
    except ValueError:
        return False
    
    return True

def is_valid_regulatory_analysis_data(reg_data: Dict[str, Any]) -> bool:
    """Validate regulatory analysis data"""
    required_fields = ['regulation_id', 'title', 'analysis_date', 'impact_analysis']
    if not all(reg_data.get(field) for field in required_fields):
        return False
    
    # Validate impact analysis content
    if len(reg_data['impact_analysis']) < 200:  # Minimum analysis length
        return False
    
    # Validate date
    try:
        datetime.strptime(reg_data['analysis_date'], '%Y-%m-%d')
    except ValueError:
        return False
    
    return True

# Helper functions for Colombian legal terminology extraction
def extract_legal_references(text: str) -> Dict[str, List[str]]:
    """Extract Colombian legal references from text"""
    references = {
        'sentencias': re.findall(ColombianLegalPatterns.SENTENCIA, text),
        'autos': re.findall(ColombianLegalPatterns.AUTO, text),
        'resoluciones': re.findall(ColombianLegalPatterns.RESOLUCION, text),
        'decretos': re.findall(ColombianLegalPatterns.DECRETO, text),
        'articulos': re.findall(ColombianLegalPatterns.ARTICULO, text),
        'paragrafos': re.findall(ColombianLegalPatterns.PARAGRAFO, text),
        'numerales': re.findall(ColombianLegalPatterns.NUMERAL, text),
        'expedientes': re.findall(ColombianLegalPatterns.EXPEDIENTE, text),
        'radicados': re.findall(ColombianLegalPatterns.RADICADO, text)
    }
    return {k: v for k, v in references.items() if v}  # Remove empty lists

def extract_legal_entities(text: str) -> Dict[str, List[str]]:
    """Extract Colombian legal entities from text"""
    entities = {
        'corporaciones': re.findall(ColombianLegalPatterns.CORPORACION, text),
        'juzgados': re.findall(ColombianLegalPatterns.JUZGADO, text),
        'tribunales': re.findall(ColombianLegalPatterns.TRIBUNAL, text)
    }
    return {k: v for k, v in entities.items() if v}  # Remove empty lists

# Update the main collection function to include new scrapers
def collect_agent_data(agent_name: str) -> List[Dict[str, Any]]:
    """Collect data using specialized scrapers for each agent type"""
    scrapers = {
        "case_prediction": scrape_case_prediction_data,
        "legal_chatbot": scrape_legal_chatbot_data,
        "compliance": scrape_compliance_data,
        "document_drafting": scrape_document_drafting_data,
        "patent_analysis": scrape_patent_data,
        "regulatory_analysis": scrape_regulatory_analysis_data
    }
    
    if agent_name not in scrapers:
        raise ValueError(f"Unknown agent: {agent_name}")
    
    documents = []
    scraper = scrapers[agent_name]
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for url in AGENT_CONFIGS[agent_name]['sources'].values():
            if isinstance(url, dict):
                for sub_url in url.values():
                    futures.append(executor.submit(scraper, sub_url))
            else:
                futures.append(executor.submit(scraper, url))
        
        for future in futures:
            try:
                result = future.result()
                documents.extend(result)
            except Exception as e:
                print(f"Error processing future: {str(e)}")
    
    return documents

def main():
    # Create directories
    os.makedirs("data", exist_ok=True)
    
    # Collect data for each agent
    for agent_name in AGENT_CONFIGS.keys():
        print(f"Collecting data for {agent_name}...")
        try:
            documents = collect_agent_data(agent_name)
            
            if documents:  # Only save if we have documents
                # Save to CSV and JSON
                df = pd.DataFrame(documents)
                df.to_csv(f"data/{agent_name}_data.csv", index=False)
                
                with open(f"data/{agent_name}_data.json", 'w', encoding='utf-8') as f:
                    json.dump(documents, f, ensure_ascii=False, indent=2)
                
                print(f"Collected {len(documents)} documents for {agent_name}")
            else:
                print(f"No documents collected for {agent_name}")
                
        except Exception as e:
            print(f"Error collecting data for {agent_name}: {str(e)}")

if __name__ == "__main__":
    main() 