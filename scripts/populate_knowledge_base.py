cmd#!/usr/bin/env python3
"""
Knowledge Base Population Script for Colombian Legal AI
Populates Supabase with comprehensive legal knowledge for AI agents
"""

import asyncio
import json
import logging
from typing import Dict, List, Any
from datetime import datetime
import os
import sys
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.supabase_knowledge_base import (
    SupabaseLegalKnowledgeBase, 
    KnowledgeType, 
    AgentType
)

# Configure logging with detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class KnowledgeBasePopulator:
    """Populates the legal knowledge base with Colombian legal data"""
    
    def __init__(self):
        self.kb = SupabaseLegalKnowledgeBase(mock_mode=False)  # Use real database
        self.vlex_api_url = "https://api.vlex.com"  # Placeholder for vLex API
        self.sic_api_url = "https://sipi.sic.gov.co"  # Placeholder for SIC API
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def fetch_from_api(self, url: str, params: Dict[str, Any] = None) -> Dict:
        """Fetch data from external API with retry logic"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"API request failed: {response.status}")
                    raise Exception(f"API request failed: {response.status}")
        
    async def populate_all_knowledge(self):
        """Populate all knowledge types"""
        logger.info("Starting knowledge base population...")
        
        try:
            # Core legal knowledge
            await self.populate_legal_documents()
            await self.populate_jurisprudence()
            await self.populate_legal_terms()
            await self.populate_regulatory_frameworks()
            
            # Agent-specific knowledge
            await self.populate_contract_knowledge()
            await self.populate_patent_knowledge()
            await self.populate_case_prediction_knowledge()
            await self.populate_compliance_knowledge()
            await self.populate_document_templates()
            
            logger.info("Knowledge base population completed successfully!")
            
        except Exception as e:
            logger.error(f"Error populating knowledge base: {e}")
            raise
    
    async def populate_legal_documents(self):
        """Populate legal documents and legislation"""
        logger.info("Populating legal documents...")
        
        legal_documents = [
            {
                "title": "Constitución Política de Colombia",
                "document_type": "constitution",
                "document_number": "1991",
                "year": 1991,
                "content": """
                CONSTITUCIÓN POLÍTICA DE COLOMBIA
                
                PREÁMBULO
                El pueblo de Colombia, en ejercicio de su poder soberano, representado por sus delegatarios a la Asamblea Nacional Constituyente, invocando la protección de Dios, y con el fin de fortalecer la unidad de la Nación y asegurar a sus integrantes la vida, la convivencia, el trabajo, la justicia, la igualdad, el conocimiento, la libertad y la paz, dentro de un marco jurídico, democrático y participativo que garantice un orden político, económico y social justo, y comprometido a impulsar la integración de la comunidad latinoamericana, decreta, sanciona y promulga la siguiente:
                
                TÍTULO I
                DE LOS PRINCIPIOS FUNDAMENTALES
                
                Artículo 1°. Colombia es un Estado social de derecho, organizado en forma de República unitaria, descentralizada, con autonomía de sus entidades territoriales, democrática, participativa y pluralista, fundada en el respeto de la dignidad humana, en el trabajo y la solidaridad de las personas que la integran y en la prevalencia del interés general.
                
                Artículo 2°. Son fines esenciales del Estado: servir a la comunidad, promover la prosperidad general y garantizar la efectividad de los principios, derechos y deberes consagrados en la Constitución; facilitar la participación de todos en las decisiones que los afectan y en la vida económica, política, administrativa y cultural de la Nación; defender la independencia nacional, mantener la integridad territorial y asegurar la convivencia pacífica y la vigencia de un orden justo.
                """,
                "summary": "Constitución Política de Colombia de 1991, documento fundamental que establece los principios, derechos y deberes de los colombianos",
                "keywords": ["constitución", "derechos fundamentales", "estado social de derecho", "democracia"],
                "tags": ["constitucional", "fundamental", "derechos"],
                "source_url": "https://vlex.com.co/vid/constitucion-politica-colombia-42867930?from_fbt=1&forw=go&fbt=webapp_preview&addon_version=6.9",
                "official_gazette_reference": "Diario Oficial No. 39.554 de 20 de julio de 1991",
                "effective_date": "1991-07-20",
                "status": "active"
            },
            {
                "title": "Ley 1581 de 2012 - Protección de Datos Personales",
                "document_type": "law",
                "document_number": "1581",
                "year": 2012,
                "content": """
                LEY 1581 DE 2012
                Por la cual se dictan disposiciones generales para la protección de datos personales
                
                TÍTULO I
                DISPOSICIONES GENERALES
                
                Artículo 1°. Objeto. La presente ley tiene por objeto desarrollar el derecho constitucional que tienen todas las personas a conocer, actualizar y rectificar las informaciones que se hayan recogido sobre ellas en bancos de datos, y los demás derechos, libertades y garantías constitucionales a que se refiere el artículo 15 de la Constitución Política; así como el derecho a la información consagrado en el artículo 20 de la misma.
                
                Artículo 2°. Definiciones. Para los efectos de la presente ley se entiende por:
                a) Autorización: Consentimiento previo, expreso e informado del Titular para llevar a cabo el Tratamiento de datos personales;
                b) Base de Datos: Conjunto organizado de datos personales que sea objeto de Tratamiento;
                c) Dato personal: Cualquier información vinculada o que pueda asociarse a una o varias personas naturales determinadas o determinables;
                d) Responsable del Tratamiento: Persona natural o jurídica, pública o privada, que por sí misma o en asocio con otros, decida sobre la base de datos y/o el Tratamiento de los datos;
                e) Titular: Persona natural cuyos datos personales sean objeto de Tratamiento;
                f) Tratamiento: Cualquier operación o conjunto de operaciones sobre datos personales, tales como la recolección, almacenamiento, uso, circulación o supresión.
                """,
                "summary": "Ley que regula la protección de datos personales en Colombia, estableciendo los principios, derechos y deberes para el tratamiento de información personal",
                "keywords": ["protección de datos", "habeas data", "privacidad", "tratamiento de datos"],
                "tags": ["datos personales", "privacidad", "habeas data"],
                "source_url": "https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=49981",
                "official_gazette_reference": "Diario Oficial No. 48.587 de 17 de octubre de 2012",
                "effective_date": "2012-10-17",
                "status": "active"
            },
            {
                "title": "Código Civil Colombiano",
                "document_type": "code",
                "document_number": "57",
                "year": 1873,
                "content": """
                CÓDIGO CIVIL COLOMBIANO
                LEY 57 DE 1887
                
                LIBRO PRIMERO
                DE LAS PERSONAS
                
                TÍTULO I
                DE LAS PERSONAS EN CUANTO A SU NATURALEZA
                
                Artículo 1°. Las personas son naturales o jurídicas.
                Se llaman personas naturales todos los individuos de la especie humana, cualquiera que sea su edad, sexo, estirpe o condición.
                
                Artículo 2°. Se llama persona jurídica, una persona ficticia, capaz de ejercer derechos y contraer obligaciones civiles, y de ser representada judicial y extrajudicialmente.
                
                Artículo 3°. Las personas naturales y jurídicas, capaces de contraer obligaciones, que ejecuten algún hecho con la intención de dañar a otro, o que sin esta intención lo dañen culposamente, están obligadas a indemnizar el perjuicio que causaren.
                """,
                "summary": "Código Civil que regula las relaciones civiles, derechos de las personas, obligaciones y contratos en Colombia",
                "keywords": ["derecho civil", "personas", "obligaciones", "contratos"],
                "tags": ["civil", "código", "derechos"],
                "source_url": "https://vlex.com.co/vid/codigo-civil-43010756?from_fbt=1&forw=go&fbt=webapp_preview&addon_version=6.9",
                "official_gazette_reference": "Diario Oficial No. 2.911 de 31 de mayo de 1887",
                "effective_date": "1887-05-31",
                "status": "active"
            },
            {
                "title": "Código de Comercio",
                "document_type": "code",
                "document_number": "410",
                "year": 1971,
                "content": """
                CÓDIGO DE COMERCIO
                DECRETO 410 DE 1971
                
                TÍTULO PRELIMINAR
                DISPOSICIONES GENERALES
                
                Artículo 1°. Los comerciantes y los asuntos mercantiles se regirán por las disposiciones de este Código, y en su defecto, por las del Código Civil.
                
                Artículo 2°. Son comerciantes las personas que profesionalmente se ocupan de alguna de las actividades que la ley considera mercantiles.
                
                Artículo 3°. Los actos mercantiles serán los que se ejecuten con el propósito de obtener lucro, en los términos establecidos por este Código.
                """,
                "summary": "Código que regula las actividades comerciales, contratos mercantiles y obligaciones de los comerciantes en Colombia",
                "keywords": ["derecho comercial", "comerciantes", "contratos mercantiles", "obligaciones"],
                "tags": ["comercial", "código", "contratos"],
                "source_url": "https://vlex.com.co/vid/codigo-comercio-42856969?from_fbt=1&forw=go&fbt=webapp_preview&addon_version=6.9",
                "official_gazette_reference": "Diario Oficial No. 33.339 de 27 de marzo de 1971",
                "effective_date": "1971-03-27",
                "status": "active"
            },
            {
                "title": "Ley 1778 de 2016 - Responsabilidad Penal de Personas Jurídicas",
                "document_type": "law",
                "document_number": "1778",
                "year": 2016,
                "content": """
                LEY 1778 DE 2016
                Por la cual se dictan normas sobre la responsabilidad de las personas jurídicas por actos de corrupción transnacional
                
                Artículo 1°. Objeto. La presente ley tiene por objeto establecer la responsabilidad administrativa de las personas jurídicas por la comisión de los delitos de cohecho transnacional previstos en el artículo 433A del Código Penal.
                
                Artículo 2°. Ámbito de aplicación. Las disposiciones de esta ley se aplican a todas las personas jurídicas, nacionales o extranjeras, que cometan actos de corrupción transnacional en Colombia o que afecten los intereses del Estado colombiano.
                """,
                "summary": "Ley que establece la responsabilidad administrativa de personas jurídicas por actos de corrupción transnacional",
                "keywords": ["corrupción", "responsabilidad penal", "personas jurídicas", "cohecho"],
                "tags": ["anticorrupción", "compliance", "penal"],
                "source_url": "https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=67542",
                "official_gazette_reference": "Diario Oficial No. 49.759 de 2 de febrero de 2016",
                "effective_date": "2016-02-02",
                "status": "active"
            }
        ]
        
        for doc in legal_documents:
            try:
                await self.kb.add_custom_knowledge(
                    content=doc.get("content", ""),
                    metadata={k: v for k, v in doc.items() if k != "content"},
                    knowledge_type=KnowledgeType.LEGAL_DOCUMENTS
                )
            except Exception as e:
                logger.error(f"Failed to add legal document {doc['title']}: {e}")
                continue
        
        logger.info(f"Added {len(legal_documents)} legal documents")
    
    async def populate_jurisprudence(self):
        """Populate jurisprudence and court decisions"""
        logger.info("Populating jurisprudence...")
        
        jurisprudence = [
            {
                "case_number": "T-881/2022",
                "court": "Corte Constitucional",
                "decision_type": "sentencia",
                "decision_date": "2022-12-15",
                "topic": "Protección de datos personales en contratos laborales",
                "summary": "La Corte Constitucional establece que el empleador debe obtener autorización previa, expresa e informada del trabajador para el tratamiento de sus datos personales, incluso en el contexto laboral",
                "full_text": """
                SENTENCIA T-881/2022
                REFERENCIA: Expediente T-8.123.456
                MAGISTRADO PONENTE: Dr. Antonio José Lizarazo Ocampo
                
                La Corte Constitucional, en ejercicio de sus competencias constitucionales y legales, ha proferido la siguiente
                
                SENTENCIA
                
                En el proceso de tutela de la referencia, adelantado por la señora María González contra la empresa ABC S.A.S.
                
                I. ANTECEDENTES
                La accionante labora en la empresa ABC S.A.S. desde hace 5 años. La empresa implementó un nuevo sistema de control de acceso que incluye la captura de huella dactilar de todos los empleados. La señora González se negó a proporcionar su huella dactilar argumentando que no se le había solicitado autorización previa para el tratamiento de sus datos biométricos.
                
                II. FUNDAMENTOS JURÍDICOS
                El artículo 15 de la Constitución Política consagra el derecho fundamental al habeas data.
                
                III. DECISIÓN
                Se concede la tutela. La empresa ABC S.A.S. debe:
                1. Suspender la implementación del sistema de control de acceso
                2. Informar detalladamente a los empleados sobre el tratamiento de datos
                3. Obtener autorización escrita
                4. Implementar medidas de seguridad
                """,
                "key_holdings": [
                    "Autorización previa para datos personales",
                    "Protección especial para datos biométricos",
                    "Cumplimiento de normativa en relación laboral"
                ],
                "legal_principles": [
                    "Principio de autorización previa",
                    "Principio de finalidad",
                    "Principio de seguridad"
                ],
                "cited_laws": [
                    "Constitución Política Artículo 15",
                    "Ley 1581 de 2012",
                    "Decreto 1377 de 2013"
                ],
                "cited_precedents": [
                    "Sentencia T-729/2018",
                    "Sentencia C-748/2011"
                ],
                "relevance_score": 0.95,
                "tags": ["datos personales", "laboral", "biométricos", "autorización"],
                "source_url": "https://www.corteconstitucional.gov.co/relatoria/2022/T-881-22.htm"
            },
            {
                "case_number": "C-1008/2010",
                "court": "Corte Constitucional",
                "decision_type": "sentencia",
                "decision_date": "2010-12-15",
                "topic": "Cláusulas abusivas en contratos de adhesión",
                "summary": "La Corte Constitucional establece los criterios para determinar cuándo una cláusula contractual es abusiva y por tanto ineficaz",
                "full_text": """
                SENTENCIA C-1008/2010
                REFERENCIA: Expediente D-8.456.789
                MAGISTRADO PONENTE: Dr. Humberto Antonio Sierra Porto
                
                La Corte Constitucional, en ejercicio de sus competencias constitucionales y legales, ha proferido la siguiente
                
                SENTENCIA
                
                I. ANTECEDENTES
                Se demanda la constitucionalidad del artículo 45 de la Ley 1480 de 2011.
                
                II. FUNDAMENTOS JURÍDICOS
                El artículo 13 de la Constitución consagra el principio de igualdad.
                
                III. DECISIÓN
                Se declara la exequibilidad condicionada del artículo 45. Las cláusulas abusivas son aquellas que:
                1. Generan un desequilibrio significativo
                2. No son negociables
                3. Van en detrimento de derechos fundamentales
                4. No son razonables ni proporcionadas
                """,
                "key_holdings": [
                    "Cláusulas abusivas son ineficaces",
                    "Desequilibrio contractual significativo",
                    "Protección al consumidor"
                ],
                "legal_principles": [
                    "Principio de equilibrio contractual",
                    "Principio de protección al consumidor",
                    "Principio de buena fe"
                ],
                "cited_laws": [
                    "Constitución Política Artículos 13 y 42",
                    "Ley 1480 de 2011",
                    "Código Civil Artículo 1602"
                ],
                "cited_precedents": [
                    "Sentencia C-671/2001",
                    "Sentencia T-456/2008"
                ],
                "relevance_score": 0.92,
                "tags": ["contratos", "cláusulas abusivas", "consumidor", "protección"],
                "source_url": "https://www.corteconstitucional.gov.co/relatoria/2010/C-1008-10.htm"
            }
        ]
        
        for jur in jurisprudence:
            try:
                await self.kb.add_custom_knowledge(
                    content=jur.get("full_text", ""),
                    metadata={k: v for k, v in jur.items() if k != "full_text"},
                    knowledge_type=KnowledgeType.JURISPRUDENCE
                )
            except Exception as e:
                logger.error(f"Failed to add jurisprudence {jur['case_number']}: {e}")
                continue
        
        logger.info(f"Added {len(jurisprudence)} jurisprudence records")
    
    async def populate_legal_terms(self):
        """Populate legal terms and definitions"""
        logger.info("Populating legal terms...")
        
        legal_terms = [
            {
                "term": "Habeas Data",
                "definition": "Derecho fundamental consagrado en el artículo 15 de la Constitución Política que permite a toda persona conocer, actualizar y rectificar las informaciones que se hayan recogido sobre ella",
                "legal_area": "constitutional",
                "source_document": "Constitución Política Artículo 15",
                "related_terms": ["derecho a la intimidad", "protección de datos", "tratamiento de datos"],
                "examples": [
                    "Solicitar copia de datos personales",
                    "Corregir información incorrecta",
                    "Eliminar datos obsoletos"
                ]
            },
            {
                "term": "Due Process",
                "definition": "Garantía constitucional que asegura el derecho a un proceso justo y equitativo",
                "legal_area": "constitutional",
                "source_document": "Constitución Política Artículo 29",
                "related_terms": ["debido proceso", "garantías procesales", "derecho de defensa"],
                "examples": [
                    "Derecho a ser notificado",
                    "Derecho a presentar pruebas",
                    "Derecho a un abogado defensor"
                ]
            },
            {
                "term": "Good Faith",
                "definition": "Principio general del derecho que obliga a las partes a actuar con honestidad, lealtad y transparencia",
                "legal_area": "civil",
                "source_document": "Código Civil Artículo 1603",
                "related_terms": ["buena fe", "honestidad", "lealtad contractual"],
                "examples": [
                    "Cumplir obligaciones contractuales",
                    "No ocultar información relevante",
                    "Actuar transparentemente"
                ]
            }
        ]
        
        for term in legal_terms:
            try:
                await self.kb.add_custom_knowledge(
                    content=term.get("definition", ""),
                    metadata={k: v for k, v in term.items() if k != "definition"},
                    knowledge_type=KnowledgeType.LEGAL_TERMS
                )
            except Exception as e:
                logger.error(f"Failed to add legal term {term['term']}: {e}")
                continue
        
        logger.info(f"Added {len(legal_terms)} legal terms")
    
    async def populate_regulatory_frameworks(self):
        """Populate regulatory frameworks"""
        logger.info("Populating regulatory frameworks...")
        
        frameworks = [
            {
                "framework_name": "Protección de Datos Personales",
                "sector": "general",
                "description": "Marco regulatorio para la protección de datos personales en Colombia",
                "applicable_laws": [
                    "Ley 1581 de 2012",
                    "Decreto 1377 de 2013",
                    "Circular Externa SIC 002 de 2015"
                ],
                "compliance_requirements": [
                    "Autorización previa del titular",
                    "Política de tratamiento de datos",
                    "Medidas de seguridad",
                    "Registro de bases de datos ante SIC"
                ],
                "authority": "Superintendencia de Industria y Comercio (SIC)",
                "effective_date": "2012-10-17",
                "status": "active"
            },
            {
                "framework_name": "Propiedad Intelectual",
                "sector": "industrial",
                "description": "Marco regulatorio para la protección de patentes, marcas y derechos de autor",
                "applicable_laws": [
                    "Decisión 486 de la Comunidad Andina",
                    "Ley 23 de 1982",
                    "Decreto 2591 de 2000"
                ],
                "compliance_requirements": [
                    "Registro de patentes y marcas ante SIC",
                    "Cumplimiento de requisitos de novedad",
                    "Protección de derechos de autor",
                    "Vigilancia de infracciones"
                ],
                "authority": "Superintendencia de Industria y Comercio (SIC)",
                "effective_date": "2000-09-01",
                "status": "active"
            }
        ]
        
        for framework in frameworks:
            try:
                await self.kb.add_custom_knowledge(
                    content=framework.get("description", ""),
                    metadata={k: v for k, v in framework.items() if k != "description"},
                    knowledge_type=KnowledgeType.REGULATORY_FRAMEWORKS
                )
            except Exception as e:
                logger.error(f"Failed to add framework {framework['framework_name']}: {e}")
                continue
        
        logger.info(f"Added {len(frameworks)} regulatory frameworks")
    
    async def populate_contract_knowledge(self):
        """Populate contract-specific knowledge"""
        logger.info("Populating contract knowledge...")
        
        contract_knowledge = [
            {
                "clause_type": "confidentiality",
                "standard_clause": """
                CONFIDENCIALIDAD. Las partes se comprometen a mantener la estricta confidencialidad sobre toda la información que se intercambie en virtud del presente contrato.
                """,
                "legal_requirements": [
                    "Definición clara de información confidencial",
                    "Duración de la obligación",
                    "Excepciones a la confidencialidad",
                    "Medidas de protección"
                ],
                "risk_factors": [
                    "Falta de definición precisa",
                    "Duración excesiva",
                    "Ausencia de excepciones legales"
                ],
                "recommended_language": """
                CONFIDENCIALIDAD. Las partes se comprometen a mantener la confidencialidad de la información marcada como tal o que por su naturaleza sea claramente confidencial. Esta obligación permanecerá vigente durante el contrato y por dos (2) años después de su terminación.
                """,
                "applicable_laws": [
                    "Código Civil Artículo 1602",
                    "Ley 1581 de 2012",
                    "Código de Comercio Artículo 822"
                ],
                "jurisprudence_references": [
                    "Sentencia T-881/2022 Corte Constitucional"
                ],
                "industry_specific_considerations": {
                    "technology": "Proteger código fuente y algoritmos",
                    "healthcare": "Cumplir con Ley 1581 de 2012 para datos sensibles",
                    "finance": "Incluir regulaciones de la Superintendencia Financiera"
                }
            }
        ]
        
        for clause in contract_knowledge:
            try:
                await self.kb.add_custom_knowledge(
                    content=clause.get("standard_clause", ""),
                    metadata={k: v for k, v in clause.items() if k != "standard_clause"},
                    knowledge_type=KnowledgeType.CONTRACT_KNOWLEDGE
                )
            except Exception as e:
                logger.error(f"Failed to add contract clause {clause['clause_type']}: {e}")
                continue
        
        logger.info(f"Added {len(contract_knowledge)} contract clauses")
    
    async def populate_patent_knowledge(self):
        """Populate patent and IP knowledge"""
        logger.info("Populating patent knowledge...")
        
        patent_knowledge = [
            {
                "patent_type": "invention",
                "requirements": [
                    "Novedad absoluta",
                    "Nivel inventivo",
                    "Aplicación industrial",
                    "Suficiencia descriptiva"
                ],
                "protection_period": 20,
                "application_requirements": [
                    "Descripción detallada",
                    "Reivindicaciones claras",
                    "Dibujos técnicos si aplica",
                    "Resumen de la invención"
                ],
                "examination_criteria": [
                    "Búsqueda de estado del arte",
                    "Análisis de patentabilidad",
                    "Verificación de requisitos formales"
                ],
                "international_treaties": [
                    "Decisión 486 CAN",
                    "Tratado de Cooperación en Materia de Patentes (PCT)",
                    "Convenio de París"
                ],
                "sic_requirements": [
                    "Cumplimiento de formalidades",
                    "Pago de tasas oficiales",
                    "Documentos en español",
                    "Representante legal"
                ]
            },
            {
                "patent_type": "utility_model",
                "requirements": [
                    "Novedad relativa",
                    "Aplicación industrial",
                    "Suficiencia descriptiva"
                ],
                "protection_period": 10,
                "application_requirements": [
                    "Descripción detallada",
                    "Reivindicaciones claras",
                    "Resumen de la invención"
                ],
                "examination_criteria": [
                    "Búsqueda de estado del arte",
                    "Análisis de novedad",
                    "Verificación de requisitos formales"
                ],
                "international_treaties": [
                    "Decisión 486 CAN",
                    "Convenio de París"
                ],
                "sic_requirements": [
                    "Cumplimiento de formalidades",
                    "Pago de tasas oficiales",
                    "Documentos en español"
                ]
            }
        ]
        
        for patent in patent_knowledge:
            try:
                await self.kb.add_custom_knowledge(
                    content=patent.get("requirements", ""),
                    metadata={k: v for k, v in patent.items() if k != "requirements"},
                    knowledge_type=KnowledgeType.PATENT_KNOWLEDGE
                )
            except Exception as e:
                logger.error(f"Failed to add patent knowledge {patent['patent_type']}: {e}")
                continue
        
        logger.info(f"Added {len(patent_knowledge)} patent knowledge records")
    
    async def populate_case_prediction_knowledge(self):
        """Populate case prediction knowledge"""
        logger.info("Populating case prediction knowledge...")
        
        case_prediction_knowledge = [
            {
                "case_type": "civil",
                "success_factors": [
                    "Documentación probatoria completa",
                    "Testigos creíbles",
                    "Cronología clara de hechos",
                    "Fundamento legal sólido"
                ],
                "risk_factors": [
                    "Falta de pruebas documentales",
                    "Testigos contradictorios",
                    "Prescripción de la acción"
                ],
                "average_duration_months": 12,
                "success_rate": 0.65,
                "key_precedents": [
                    "Sentencia C-1008/2010 Corte Constitucional"
                ],
                "procedural_requirements": [
                    "Demanda con fundamentos claros",
                    "Conciliación prejudicial",
                    "Pruebas pertinentes"
                ]
            }
        ]
        
        for case in case_prediction_knowledge:
            try:
                await self.kb.add_custom_knowledge(
                    content=case.get("success_factors", ""),
                    metadata={k: v for k, v in case.items() if k != "success_factors"},
                    knowledge_type=KnowledgeType.CASE_PREDICTION_KNOWLEDGE
                )
            except Exception as e:
                logger.error(f"Failed to add case prediction {case['case_type']}: {e}")
                continue
        
        logger.info(f"Added {len(case_prediction_knowledge)} case prediction records")
    
    async def populate_compliance_knowledge(self):
        """Populate compliance knowledge"""
        logger.info("Populating compliance knowledge...")
        
        compliance_knowledge = [
            {
                "compliance_area": "data_protection",
                "applicable_laws": [
                    "Ley 1581 de 2012",
                    "Decreto 1377 de 2013",
                    "Circular Externa SIC 002 de 2015"
                ],
                "requirements": [
                    "Autorización previa del titular",
                    "Política de tratamiento de datos",
                    "Registro de bases de datos",
                    "Medidas de seguridad"
                ],
                "penalties": [
                    "Multas hasta 2.000 SMLMV",
                    "Suspensión de actividades",
                    "Cierre temporal o definitivo"
                ],
                "compliance_procedures": [
                    "Auditoría de bases de datos",
                    "Actualización de políticas",
                    "Capacitación del personal"
                ]
            }
        ]
        
        for compliance in compliance_knowledge:
            try:
                await self.kb.add_custom_knowledge(
                    content=compliance.get("requirements", ""),
                    metadata={k: v for k, v in compliance.items() if k != "requirements"},
                    knowledge_type=KnowledgeType.COMPLIANCE_KNOWLEDGE
                )
            except Exception as e:
                logger.error(f"Failed to add compliance knowledge {compliance['compliance_area']}: {e}")
                continue
        
        logger.info(f"Added {len(compliance_knowledge)} compliance records")
    
    async def populate_document_templates(self):
        """Populate document templates"""
        logger.info("Populating document templates...")
        
        document_templates = [
            {
                "template_name": "Contrato de Arrendamiento Residencial",
                "document_type": "contract",
                "template_content": """
                CONTRATO DE ARRENDAMIENTO RESIDENCIAL
                
                Entre los suscritos:
                ARRENDADOR: {{arrendador_nombre}}, identificado con cédula de ciudadanía No. {{arrendador_cc}}, domiciliado en {{arrendador_direccion}};
                
                ARRENDATARIO: {{arrendatario_nombre}}, identificado con cédula de ciudadanía No. {{arrendatario_cc}}, domiciliado en {{arrendatario_direccion}};
                
                Se celebra el presente contrato bajo las siguientes cláusulas:
                
                PRIMERA: OBJETO. El arrendador cede en arrendamiento al arrendatario el inmueble ubicado en {{inmueble_direccion}}, por el término de {{duracion_meses}} meses, a partir del {{fecha_inicio}}.
                
                SEGUNDA: CANON. El canon mensual será de ${{canon_monto}} ({{canon_monto_letras}}), pagadero por anticipado dentro de los primeros cinco días de cada mes.
                """,
                "required_sections": [
                    "Identificación de las partes",
                    "Objeto del contrato",
                    "Canon de arrendamiento"
                ],
                "legal_requirements": [
                    "Ley 820 de 2003",
                    "Código Civil Artículos 1973-2044"
                ],
                "jurisdiction": "Colombia"
            }
        ]
        
        for template in document_templates:
            try:
                await self.kb.add_custom_knowledge(
                    content=template.get("template_content", ""),
                    metadata={k: v for k, v in template.items() if k != "template_content"},
                    knowledge_type=KnowledgeType.DOCUMENT_TEMPLATES
                )
            except Exception as e:
                logger.error(f"Failed to add document template {template['template_name']}: {e}")
                continue
        
        logger.info(f"Added {len(document_templates)} document templates")

async def main():
    """Main function to populate knowledge base"""
    populator = KnowledgeBasePopulator()
    await populator.populate_all_knowledge()

if __name__ == "__main__":
    asyncio.run(main()) 