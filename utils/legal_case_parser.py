"""
Legal Case Document Parser
Parses "Ficha de Análisis Jurisprudencial" documents into structured data
"""

import re
import uuid
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class LegalCaseData:
    """Structured data extracted from legal case analysis document"""
    # Basic case information
    process_number: str
    process_type: str
    provision_type: str
    sentence_number: Optional[str]
    provision_date: Optional[str]
    
    # Court information
    court: str
    section: str
    reporting_judge: str
    
    # Parties
    plaintiff: str
    defendant: str
    
    # Ruling
    ruling_direction: str
    
    # Legal analysis
    relevant_facts: str
    legal_problem: str
    challenged_act: Optional[str]
    legal_foundation_demand: Optional[str]
    legal_foundation_defense: Optional[str]
    
    # Legal support
    supporting_normativity: List[str]
    supporting_jurisprudence: List[str]
    
    # Legal reasoning
    legal_thesis: str
    extract: str
    
    # Dissenting and clarifying votes
    dissenting_vote: Optional[str]
    dissenting_thesis: Optional[str]
    dissenting_extract: Optional[str]
    clarifying_vote: Optional[str]
    clarifying_thesis: Optional[str]
    clarifying_extract: Optional[str]

class LegalCaseParser:
    """Parser for Ficha de Análisis Jurisprudencial documents"""
    
    def __init__(self):
        # Define patterns for extracting structured data
        self.patterns = {
            'process_number': r'NÚMERO DEL PROCESO.*?:\s*([^\n]+)',
            'process_type': r'TIPO DE PROCESO.*?:\s*([^\n]+)',
            'provision_type': r'TIPO DE PROVIDENCIA.*?:\s*([^\n]+)',
            'sentence_number': r'NÚMERO DE LA SENTENCIA.*?:\s*([^\n]+)',
            'provision_date': r'FECHA DE LA PROVIDENCIA.*?:\s*([^\n]+)',
            'court_section': r'DESPACHO.*?:\s*([^\n]+)',
            'reporting_judge': r'MAGISTRADO PONENTE.*?:\s*([^\n]+)',
            'plaintiff': r'ACTOR.*?:\s*([^\n]+)',
            'defendant': r'DEMANDADO.*?:\s*([^\n]+)',
            'ruling_direction': r'SENTIDO DEL FALLO.*?:\s*([^\n]+)',
            'relevant_facts': r'HECHOS RELEVANTES.*?:\s*([\s\S]*?)(?=PROBLEMA JURÍDICO)',
            'legal_problem': r'PROBLEMA JURÍDICO.*?:\s*([\s\S]*?)(?=ACTO DEMANDADO)',
            'challenged_act': r'ACTO DEMANDADO.*?:\s*([\s\S]*?)(?=FUNDAMENTO LEGAL DE LA DEMANDA)',
            'legal_foundation_demand': r'FUNDAMENTO LEGAL DE LA DEMANDA.*?:\s*([\s\S]*?)(?=FUNDAMENTO LEGAL DE LA DEFENSA)',
            'legal_foundation_defense': r'FUNDAMENTO LEGAL DE LA DEFENSA.*?:\s*([\s\S]*?)(?=NORMATIVIDAD QUE APOYA)',
            'supporting_normativity': r'NORMATIVIDAD QUE APOYA.*?:\s*([\s\S]*?)(?=JURISPRUDENCIA QUE APOYA)',
            'supporting_jurisprudence': r'JURISPRUDENCIA QUE APOYA.*?:\s*([\s\S]*?)(?=TESIS JURÍDICA)',
            'legal_thesis': r'TESIS JURÍDICA.*?:\s*([\s\S]*?)(?=EXTRACTO)',
            'extract': r'EXTRACTO.*?:\s*([\s\S]*?)(?=SALVAMENTO DE VOTO)',
            'dissenting_vote': r'SALVAMENTO DE VOTO.*?:\s*([\s\S]*?)(?=TESIS JURÍDICA DEL SALVAMENTO)',
            'dissenting_thesis': r'TESIS JURÍDICA DEL SALVAMENTO.*?:\s*([\s\S]*?)(?=EXTRACTO DEL SALVAMENTO)',
            'dissenting_extract': r'EXTRACTO DEL SALVAMENTO.*?:\s*([\s\S]*?)(?=ACLARACIÓN DE VOTO)',
            'clarifying_vote': r'ACLARACIÓN DE VOTO.*?:\s*([\s\S]*?)(?=TESIS JURÍDICA DE LA ACLARACIÓN)',
            'clarifying_thesis': r'TESIS JURÍDICA DE LA ACLARACIÓN.*?:\s*([\s\S]*?)(?=EXTRACTO DE LA ACLARACIÓN)',
            'clarifying_extract': r'EXTRACTO DE LA ACLARACIÓN.*?:\s*([\s\S]*?)(?=\n\n|\Z)'
        }
    
    def parse_document(self, document_text: str) -> LegalCaseData:
        """
        Parse a legal case analysis document into structured data
        
        Args:
            document_text: Raw text of the Ficha de Análisis Jurisprudencial
            
        Returns:
            LegalCaseData object with extracted information
        """
        try:
            # Clean the document text
            cleaned_text = self._clean_text(document_text)
            
            # Extract all fields using regex patterns
            extracted_data = {}
            for field, pattern in self.patterns.items():
                match = re.search(pattern, cleaned_text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                if match:
                    extracted_data[field] = match.group(1).strip()
                else:
                    extracted_data[field] = None
            
            # Parse court and section
            court, section = self._parse_court_section(extracted_data.get('court_section', ''))
            
            # Parse supporting normativity and jurisprudence
            supporting_normativity = self._parse_list(extracted_data.get('supporting_normativity', ''))
            supporting_jurisprudence = self._parse_list(extracted_data.get('supporting_jurisprudence', ''))
            
            # Parse date
            provision_date = self._parse_date(extracted_data.get('provision_date', ''))
            
            # Create LegalCaseData object
            case_data = LegalCaseData(
                process_number=extracted_data.get('process_number', ''),
                process_type=extracted_data.get('process_type', ''),
                provision_type=extracted_data.get('provision_type', ''),
                sentence_number=extracted_data.get('sentence_number'),
                provision_date=provision_date,
                court=court,
                section=section,
                reporting_judge=extracted_data.get('reporting_judge', ''),
                plaintiff=extracted_data.get('plaintiff', ''),
                defendant=extracted_data.get('defendant', ''),
                ruling_direction=extracted_data.get('ruling_direction', ''),
                relevant_facts=extracted_data.get('relevant_facts', ''),
                legal_problem=extracted_data.get('legal_problem', ''),
                challenged_act=extracted_data.get('challenged_act'),
                legal_foundation_demand=extracted_data.get('legal_foundation_demand'),
                legal_foundation_defense=extracted_data.get('legal_foundation_defense'),
                supporting_normativity=supporting_normativity,
                supporting_jurisprudence=supporting_jurisprudence,
                legal_thesis=extracted_data.get('legal_thesis', ''),
                extract=extracted_data.get('extract', ''),
                dissenting_vote=extracted_data.get('dissenting_vote'),
                dissenting_thesis=extracted_data.get('dissenting_thesis'),
                dissenting_extract=extracted_data.get('dissenting_extract'),
                clarifying_vote=extracted_data.get('clarifying_vote'),
                clarifying_thesis=extracted_data.get('clarifying_thesis'),
                clarifying_extract=extracted_data.get('clarifying_extract')
            )
            
            logger.info(f"Successfully parsed legal case: {case_data.process_number}")
            return case_data
            
        except Exception as e:
            logger.error(f"Error parsing legal case document: {e}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize the document text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove page headers/footers
        text = re.sub(r'Código:.*?Página \d+ de \d+', '', text)
        text = re.sub(r'FICHA DE ANÁLISIS JURISPRUDENCIAL', '', text)
        return text.strip()
    
    def _parse_court_section(self, court_section: str) -> Tuple[str, str]:
        """Parse court and section from the DESPACHO field"""
        if not court_section or court_section == 'N/A':
            return '', ''
        
        # Split by '/' and clean
        parts = [part.strip() for part in court_section.split('/')]
        court = parts[0] if len(parts) > 0 else ''
        section = parts[1] if len(parts) > 1 else ''
        
        return court, section
    
    def _parse_list(self, text: str) -> List[str]:
        """Parse a list from text (comma-separated or line-separated)"""
        if not text or text == 'N/A':
            return []
        
        # Split by commas or newlines
        items = re.split(r'[,\n]', text)
        # Clean and filter empty items
        items = [item.strip() for item in items if item.strip()]
        return items
    
    def _parse_date(self, date_text: str) -> Optional[str]:
        """Parse date from various formats"""
        if not date_text or date_text == 'N/A':
            return None
        
        # Try different date formats
        date_formats = [
            r'(\d{4})/(\d{1,2})/(\d{1,2})',  # YYYY/MM/DD
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # MM/DD/YYYY
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
        ]
        
        for pattern in date_formats:
            match = re.search(pattern, date_text)
            if match:
                groups = match.groups()
                if len(groups) == 3:
                    # Standardize to YYYY-MM-DD format
                    if len(groups[0]) == 4:  # YYYY/MM/DD
                        return f"{groups[0]}-{groups[1].zfill(2)}-{groups[2].zfill(2)}"
                    else:  # MM/DD/YYYY
                        return f"{groups[2]}-{groups[0].zfill(2)}-{groups[1].zfill(2)}"
        
        return None
    
    def extract_legal_concepts(self, case_data: LegalCaseData) -> List[str]:
        """Extract legal concepts from the case data"""
        concepts = set()
        
        # Extract from process type
        if case_data.process_type:
            concepts.add(case_data.process_type)
        
        # Extract from legal problem and thesis
        text_fields = [
            case_data.legal_problem,
            case_data.legal_thesis,
            case_data.extract
        ]
        
        for text in text_fields:
            if text:
                # Look for common legal terms
                legal_terms = re.findall(r'\b(?:derecho|garantía|principio|acción|recurso|proceso|debido proceso|tutela|amparo|constitucional|fundamental)\b', text, re.IGNORECASE)
                concepts.update(legal_terms)
        
        return list(concepts)
    
    def extract_legal_areas(self, case_data: LegalCaseData) -> List[str]:
        """Extract legal areas from the case data"""
        areas = set()
        
        # Map process types to legal areas
        process_type_mapping = {
            'ACCIÓN DE TUTELA': 'Constitutional Law',
            'ACCIÓN DE CUMPLIMIENTO': 'Constitutional Law',
            'ACCIÓN POPULAR': 'Constitutional Law',
            'ACCIÓN DE GRUPO': 'Constitutional Law',
            'ACCIÓN DE NULIDAD': 'Administrative Law',
            'ACCIÓN DE REPARACIÓN DIRECTA': 'Administrative Law',
            'ACCIÓN DE REPARACIÓN DIRECTA': 'Administrative Law',
            'ACCIÓN DE REPARACIÓN DIRECTA': 'Administrative Law',
        }
        
        if case_data.process_type in process_type_mapping:
            areas.add(process_type_mapping[case_data.process_type])
        
        # Extract from court type
        if 'CONSTITUCIONAL' in case_data.court.upper():
            areas.add('Constitutional Law')
        elif 'ADMINISTRATIVO' in case_data.court.upper():
            areas.add('Administrative Law')
        elif 'CIVIL' in case_data.court.upper():
            areas.add('Civil Law')
        elif 'PENAL' in case_data.court.upper():
            areas.add('Criminal Law')
        
        return list(areas)
    
    def calculate_complexity_score(self, case_data: LegalCaseData) -> float:
        """Calculate complexity score based on case characteristics"""
        score = 0.0
        
        # Base score
        score += 0.2
        
        # Length of legal thesis (longer = more complex)
        if case_data.legal_thesis:
            score += min(len(case_data.legal_thesis) / 1000, 0.3)
        
        # Number of supporting jurisprudence (more = more complex)
        score += min(len(case_data.supporting_jurisprudence) * 0.05, 0.2)
        
        # Number of supporting normativity (more = more complex)
        score += min(len(case_data.supporting_normativity) * 0.05, 0.1)
        
        # Presence of dissenting or clarifying votes (more complex)
        if case_data.dissenting_vote and case_data.dissenting_vote != 'N/A':
            score += 0.1
        if case_data.clarifying_vote and case_data.clarifying_vote != 'N/A':
            score += 0.1
        
        # Constitutional cases are generally more complex
        if 'CONSTITUCIONAL' in case_data.court.upper():
            score += 0.1
        
        return min(score, 1.0)  # Cap at 1.0

def create_neo4j_case_properties(case_data: LegalCaseData) -> Dict[str, Any]:
    """Convert LegalCaseData to Neo4j properties format"""
    return {
        'case_id': case_data.process_number,
        'process_number': case_data.process_number,
        'process_type': case_data.process_type,
        'provision_type': case_data.provision_type,
        'sentence_number': case_data.sentence_number,
        'provision_date': case_data.provision_date,
        'court': case_data.court,
        'section': case_data.section,
        'reporting_judge': case_data.reporting_judge,
        'plaintiff': case_data.plaintiff,
        'defendant': case_data.defendant,
        'ruling_direction': case_data.ruling_direction,
        'relevant_facts': case_data.relevant_facts,
        'legal_problem': case_data.legal_problem,
        'challenged_act': case_data.challenged_act,
        'legal_foundation_demand': case_data.legal_foundation_demand,
        'legal_foundation_defense': case_data.legal_foundation_defense,
        'supporting_normativity': case_data.supporting_normativity,
        'supporting_jurisprudence': case_data.supporting_jurisprudence,
        'legal_thesis': case_data.legal_thesis,
        'extract': case_data.extract,
        'dissenting_vote': case_data.dissenting_vote,
        'dissenting_thesis': case_data.dissenting_thesis,
        'dissenting_extract': case_data.dissenting_extract,
        'clarifying_vote': case_data.clarifying_vote,
        'clarifying_thesis': case_data.clarifying_thesis,
        'clarifying_extract': case_data.clarifying_extract,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }

# Example usage
if __name__ == "__main__":
    # Test with the provided document
    sample_document = """
    FICHA DE ANÁLISIS JURISPRUDENCIAL 
    
    Código: GP-F-01 V-0  Página 1 de 3 
    
    NÚMERO DEL PROCESO (radicación 23 dígitos + n.° expediente): 
    T- 2266809 
    TIPO DE PROCESO (tipo de acción): 
    ACCIÓN DE TUTELA. 
    TIPO DE PROVIDENCIA (sentencia de unificación, sentencia, auto de unificación, auto):  
    SENTENCIA. 
    NÚMERO DE LA SENTENCIA (si aplica): 
    T-629-2009 
    FECHA DE LA PROVIDENCIA (año/mes/día):  
    2009/09/04. 
    DESPACHO (corporación/sección/subsección/sala plena/sala de decisión):  
    CORTE CONSTITUCIONAL/SALA CUARTA DE REVISIÓN. 
    MAGISTRADO PONENTE:  
    GABRIEL EDUARDO MENDOZA MARTELO. 
    ACTOR:  
    ADOLDO RAAD HERNÁNDEZ. 
    DEMANDADO:  
    PROCURADURÍA GENERAL DE LA NACIÓN. 
    SENTIDO DEL FALLO : 
    FAVORABLE. 
    HECHOS RELEVANTES (los hechos que resultaron probados, no los narrados en la demanda, 
    limitados al problema jurídico concreto que orienta la ficha):  
    La Procuraduría General de la Nación, declaró disciplinariamente responsable al 
    Presidente del Concejo Distrital de Cartagena Adolfo Raad Hernández, imponiendo 
    como sanción la destitución del cargo e inhabilidad para el ejercicio de función pública 
    por veinte (20) años. 
    
    El actor considera que le fue violado el derecho al debido proceso, al acceso a la 
    administración de justicia y al acceso a cargos y funciones públicas. 
    PROBLEMA JURÍDICO DEL CASO CONCRETO (en concordancia con los hechos relevantes): 
     ¿Es procedente la acción de tutela para declarar la suspensión de los efectos de una 
    sanción de destitución e inhabilidad general interpuesta por parte de la Procuraduría 
    General de la Nación al Presidente del Concejo de Cartagena? 
    ACTO DEMANDADO (si aplica, por ejemplo si se pide la nulidad de un acto administrativo): 
    N/A 
    FUNDAMENTO LEGAL DE LA DEMANDA (si aplica y en relación con el problema jurídico 
    concreto que orienta la ficha): 
    N/A 
    FUNDAMENTO LEGAL DE LA DEFENSA (si aplica y en relación con el problema jurídico 
    concreto que orienta la ficha): 
    N/A 
    NORMATIVIDAD QUE APOYA LA DECISIÓN (si aplica y en relación con el problema 
    jurídico concreto que orienta la ficha): 
    Artículo 86 de la Constitución Política, Artículo 6º numeral 1° del Decreto 2591 
    de 1991 
    
    JURISPRUDENCIA QUE APOYA LA DECISIÓN (si aplica y en relación con el problema 
    jurídico concreto que orienta la ficha): 
    T-161 de 2009, T 640 de 1996, T-106 de 1993, T-983 de 2001, T-1222 de 2001, T-514 de 
    2003, T-132 de 2006, T--634 de 2006, T-262 de 1998,  T-215 de 2000, T -743 de 2002, T-193 
    de 2007. 
    TESIS JURÍDICA (es el resumen del extracto y debe dar respuesta al problema jurídico concreto 
    que orienta la ficha): 
    
    Según la jurisprudencia de la Corte Constitucional, la acción de tutela no es procedente 
    para declarar la suspensión de los efectos de las decisiones adoptadas en materia 
    sancionatoria por la Procuraduría General de la Nación, ya que este mecanismo 
    procedente excepcionalmente cuando: (i) los medios ordinarios de defensa judicial  no 
    son lo suficientemente idóneos y eficaces, (ii) los medios de defensa sean idóneos, se 
    produzca un perjuicio irremediable de los derechos fundamentales, (iii) el accionante es 
    un sujeto de especial protección constitucional.   
    
    En el caso concreto de análisis, se determinó que el mecanismo de nulidad y 
    restablecimiento del derecho era el medio idóneo para solicitar la suspensión de los 
    efectos de un acto administrativo sancionatorio, así mismo, se demostró que: (i) no 
    existió perjuicio irremediable, (ii) no existió una violación al debido proceso, (iii) el 
    perjuicio que se alegó no es cierto e inminente, grave y de urgente atención, y, (iv) los 
    medios que dejó de utilizar eran los idóneos para el amparo de sus pretensiones. Así 
    pues, se encontró improcedente la acción de tutela. 
    
    EXTRACTO (se cita textualmente el aparte de la providencia analizada que da respuesta al 
    problema jurídico concreto que orienta la ficha, sin comentarios o anotaciones personales, sin 
    pies de página): 
    "Como ya se expuso, en desarrollo del principio de subsidiariedad, la jurisprudencia 
    constitucional ha señalado que en los casos en que el accionante tenga a su alcance otros 
    medios o recursos de defensa judicial, la acción de tutela procederá excepcionalmente en 
    los siguientes eventos: (i) los medios ordinarios de defensa judicial no son lo 
    suficientemente idóneos y eficaces para proteger los derechos presuntamente 
    conculcados; (ii) aún cuando tales medios de defensa judicial sean idóneos, de no 
    concederse la tutela como mecanismo transitorio de protección, se produciría un 
    perjuicio irremediable a los derechos fundamentales; (iii) el  accionante es un sujeto de 
    especial protección constitucional (personas de la tercera edad, personas discapacitadas, 
    mujeres cabeza de familia, población desplazada, niños y niñas, etc.), y por tanto su 
    situación requiere de particular consideración por parte del juez de tutela." 
    
    "Si la parte afectada no ejerce las acciones ni utiliza los recursos establecidos en el 
    ordenamiento jurídico para salvaguardar los derechos amenazados o vulnerados, éste 
    mecanismo de amparo no tiene la virtualidad de revivir los términos vencidos ni se 
    convierte en un recurso adicional o supletorio de las instancias previstas en cada 
    jurisdicción." 
    
    "En este orden de ideas, resulta indispensable analizar frente a cada caso, si el 
    ordenamiento jurídico tiene previstos otros medios de defensa judicial para la protección 
    de los derechos fundamentales presuntamente vulnerados o amenazados, si los mismos 
    son lo suficientemente idóneos y eficaces para otorgar una protección integral y además 
    establecer si fueron utilizados en término para hacer prevalecer los derechos 
    supuestamente vulnerados." 
    SALVAMENTO DE VOTO (si aplica*, se identifica al magistrado que salvó y la votación): 
    N/A
    TESIS JURÍDICA DEL SALVAMENTO (es el resumen del extracto del salvamento y debe 
    guardar coherencia con el problema jurídico concreto que orienta la ficha): 
    N/A
    EXTRACTO DEL SALVAMENTO (se cita textualmente el aparte del salvamento que 
    cuestiona o se aparta de la solución jurídica dada por la providencia problema jurídico concreto 
    que orienta la ficha, sin comentarios o anotaciones personales): 
    N/A
    ACLARACIÓN DE VOTO (si aplica** se identifica al magistrado que aclaró y la votación): 
    N/A  
    TESIS JURÍDICA DE LA ACLARACIÓN (es el resumen del extracto de la aclaración y debe 
    guardar coherencia con el problema jurídico concreto que orienta la ficha): 
    N/A
    EXTRACTO DE LA ACLARACIÓN (se cita textualmente el aparte del salvamento que 
    cuestiona o se aparta de la solución jurídica dada por la providencia problema jurídico concreto 
    que orienta la ficha, sin comentarios o anotaciones personales): 
    N/A
    """
    
    parser = LegalCaseParser()
    case_data = parser.parse_document(sample_document)
    
    print("Parsed Case Data:")
    print(f"Process Number: {case_data.process_number}")
    print(f"Process Type: {case_data.process_type}")
    print(f"Court: {case_data.court}")
    print(f"Section: {case_data.section}")
    print(f"Ruling Direction: {case_data.ruling_direction}")
    print(f"Supporting Jurisprudence: {case_data.supporting_jurisprudence}")
    print(f"Legal Concepts: {parser.extract_legal_concepts(case_data)}")
    print(f"Legal Areas: {parser.extract_legal_areas(case_data)}")
    print(f"Complexity Score: {parser.calculate_complexity_score(case_data)}")
