"""
Configuration for Colombian Supreme Court document scraping
"""

# Neo4j Configuration
NEO4J_CONFIG = {
    'uri': 'bolt://localhost:7687',
    'username': 'neo4j',
    'password': 'password',  # Default Neo4j password
    'database': 'neo4j'
}

# Scraping Configuration
SCRAPING_CONFIG = {
    'base_url': 'https://cortesuprema.gov.co',
    'target_url': 'https://cortesuprema.gov.co/sala-de-casacion-civil-y-agraria-relatoria-norma-sustancial/',
    'delay_between_requests': 3,  # seconds
    'timeout': 30,  # seconds
    'max_retries': 3,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Document Classification Patterns
DOCUMENT_PATTERNS = {
    'providencia': [
        'providencia',
        'ver providencia',
        'auto',
        'resolución'
    ],
    'sentencia': [
        'sentencia',
        'fallo',
        'decisión'
    ],
    'auto': [
        'auto',
        'providencia'
    ]
}

# Metadata Extraction Patterns
METADATA_PATTERNS = {
    'case_number': [
        r'Radicado[:\s]*(\d+)',
        r'Expediente[:\s]*(\d+)',
        r'Proceso[:\s]*(\d+)',
        r'Caso[:\s]*(\d+)',
        r'No\.?\s*(\d+)'
    ],
    'date': [
        r'(\d{1,2}/\d{1,2}/\d{4})',
        r'(\d{4}-\d{2}-\d{2})',
        r'(\d{1,2} de \w+ de \d{4})'
    ],
    'judge': [
        r'Magistrado[:\s]*([^,\n]+)',
        r'Juez[:\s]*([^,\n]+)',
        r'Ponente[:\s]*([^,\n]+)'
    ]
}

# Content Extraction Selectors
CONTENT_SELECTORS = [
    '.document-content',
    '.content',
    '.main-content',
    '.providencia-content',
    '.document-text',
    'article',
    '.entry-content',
    '.document-body',
    '.legal-document',
    '.court-document'
]

# Link Extraction Selectors
LINK_SELECTORS = [
    'a[href*="providencia"]',
    'a[href*="ver-prov"]',
    'a[href*="documento"]',
    '.document-link',
    '.providencia-link',
    'a[href*="sentencia"]',
    'a[href*="auto"]'
]
