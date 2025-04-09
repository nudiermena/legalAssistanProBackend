from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime

class DataCategory(Enum):
    PERSONAL = "personal"
    SENSITIVE = "sensitive"
    PUBLIC = "public"

class ColombianDataProtection:
    # Data retention periods in days
    RETENTION_PERIODS = {
        DataCategory.PERSONAL: 365,
        DataCategory.SENSITIVE: 730,
        DataCategory.PUBLIC: 3650
    }
    
    # Required consent elements
    CONSENT_REQUIREMENTS = [
        "purpose",
        "processing_methods",
        "data_retention",
        "data_transfer",
        "data_subject_rights"
    ]
    
    # Special categories of data
    SENSITIVE_CATEGORIES = [
        "racial_or_ethnic_origin",
        "political_orientation",
        "religious_or_philosophical_beliefs",
        "union_membership",
        "social_organizations",
        "human_rights_organizations",
        "sexual_life",
        "biometric_data"
    ]

class ColombianLegalFramework:
    """Framework for Colombian legal compliance"""
    
    # Version information
    FRAMEWORK_VERSION = "2024.1"
    
    # Constitutional principles
    CONSTITUTIONAL_PRINCIPLES = [
        "Debido proceso",
        "Igualdad",
        "Buena fe",
        "Prevalencia del derecho sustancial",
        "Acceso a la justicia",
        "Legalidad"
    ]
    
    # Legal areas
    LEGAL_AREAS = {
        "derecho_publico": [
            "Constitucional",
            "Administrativo",
            "Tributario"
        ],
        "derecho_privado": [
            "Civil",
            "Comercial",
            "Laboral"
        ],
        "derecho_procesal": [
            "Teoría General",
            "Procedimiento Civil",
            "Procedimiento Penal"
        ],
        "nuevas_tecnologias": [
            "Derecho Digital",
            "Protección de Datos",
            "Comercio Electrónico"
        ]
    }
    
    # Legal terms dictionary
    LEGAL_TERMS = {
        "jurisprudencia": "Criterios establecidos en sentencias judiciales",
        "doctrina": "Opiniones y teorías de expertos en derecho",
        "ley": "Norma jurídica dictada por el legislador",
        "decreto": "Decisión del poder ejecutivo con contenido normativo",
        "sentencia": "Resolución judicial que decide definitivamente un proceso",
        "precedente": "Decisión anterior que sirve como referencia obligatoria"
    }
    
    # Document types
    DOCUMENT_TYPES = [
        "Sentencia",
        "Ley",
        "Decreto",
        "Resolución",
        "Concepto",
        "Doctrina"
    ]
    
    # Jurisdictions
    JURISDICTIONS = [
        "Constitucional",
        "Ordinaria",
        "Contencioso Administrativa",
        "Disciplinaria"
    ]

class ColombianIPFramework:
    # IP registration requirements
    IP_REQUIREMENTS = {
        "patent": ["novelty", "inventive_step", "industrial_application"],
        "trademark": ["distinctiveness", "non_deceptiveness"],
        "copyright": ["originality", "fixation"]
    }
    
    # IP protection periods
    PROTECTION_PERIODS = {
        "patent": 20,      # years
        "trademark": 10,   # years
        "copyright": 80    # years
    }

def get_data_category(data_type: str) -> DataCategory:
    """Determine the category of data based on Colombian law"""
    if data_type in ColombianDataProtection.SENSITIVE_CATEGORIES:
        return DataCategory.SENSITIVE
    elif data_type == "public_record":
        return DataCategory.PUBLIC
    else:
        return DataCategory.PERSONAL

def validate_consent(consent_data: Dict[str, str]) -> bool:
    """Validate if consent meets Colombian requirements"""
    return all(req in consent_data for req in ColombianDataProtection.CONSENT_REQUIREMENTS)

def get_retention_period(data_category: DataCategory) -> int:
    """Get the required retention period for a data category"""
    return ColombianDataProtection.RETENTION_PERIODS[data_category]

def get_legal_term(term: str) -> str:
    """Get the definition of a legal term"""
    return ColombianLegalFramework.LEGAL_TERMS.get(term.lower(), "")

def validate_jurisdiction(jurisdiction: str) -> bool:
    """Validate if a jurisdiction is valid in Colombian law"""
    return jurisdiction in ColombianLegalFramework.JURISDICTIONS

def get_document_metadata() -> Dict[str, str]:
    """Get metadata for legal documents"""
    return {
        "framework_version": ColombianLegalFramework.FRAMEWORK_VERSION,
        "timestamp": datetime.now().isoformat(),
        "jurisdiction": "Colombia",
        "language": "es"
    }

def get_legal_areas() -> Dict[str, List[str]]:
    """Get all available legal areas"""
    return ColombianLegalFramework.LEGAL_AREAS

def get_document_types() -> List[str]:
    """Get all available document types"""
    return ColombianLegalFramework.DOCUMENT_TYPES

def get_administrative_deadline(procedure_type: str) -> Optional[int]:
    """Get the deadline for an administrative procedure"""
    return ColombianLegalFramework.ADMINISTRATIVE_PROCEDURES["deadlines"].get(procedure_type)

def get_ip_requirements(ip_type: str) -> List[str]:
    """Get the requirements for IP registration"""
    return ColombianIPFramework.IP_REQUIREMENTS.get(ip_type, [])

def get_ip_protection_period(ip_type: str) -> Optional[int]:
    """Get the protection period for an IP right"""
    return ColombianIPFramework.PROTECTION_PERIODS.get(ip_type) 