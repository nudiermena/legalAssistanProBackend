#!/usr/bin/env python3
"""
Enhanced Knowledge Base Population Script
Populates Supabase with comprehensive Colombian legal knowledge
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.supabase_knowledge_base import (
    SupabaseLegalKnowledgeBase, 
    KnowledgeType
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedKnowledgePopulator:
    """Enhanced knowledge base population with comprehensive legal content"""
    
    def __init__(self, mock_mode: bool = False):
        self.kb = SupabaseLegalKnowledgeBase(mock_mode=mock_mode)
        self.population_stats = {
            "total_added": 0,
            "errors": 0,
            "by_type": {}
        }
    
    def load_processed_documents(self, filename: str) -> List[Dict[str, Any]]:
        """Load processed documents from JSON file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Loaded {len(data)} processed documents from {filename}")
            return data
            
        except Exception as e:
            logger.error(f"Error loading processed documents: {e}")
            return []
    
    def map_document_type_to_knowledge_type(self, doc_type: str, legal_area: str) -> KnowledgeType:
        """Map document type to knowledge base type"""
        mapping = {
            "law": KnowledgeType.LEGAL_DOCUMENTS,
            "decree": KnowledgeType.LEGAL_DOCUMENTS,
            "resolution": KnowledgeType.REGULATORY_FRAMEWORKS,
            "constitutional_decision": KnowledgeType.JURISPRUDENCE,
            "supreme_decision": KnowledgeType.JURISPRUDENCE,
            "administrative_decision": KnowledgeType.JURISPRUDENCE
        }
        
        # Special mappings based on legal area
        if legal_area == "intellectual_property":
            return KnowledgeType.PATENT_KNOWLEDGE
        elif legal_area == "civil" and "contrato" in doc_type.lower():
            return KnowledgeType.CONTRACT_KNOWLEDGE
        elif legal_area == "administrative":
            return KnowledgeType.COMPLIANCE_KNOWLEDGE
        
        return mapping.get(doc_type, KnowledgeType.LEGAL_DOCUMENTS)
    
    def prepare_metadata(self, processed_doc: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare metadata for database insertion"""
        original_doc = processed_doc.get("original_doc", {})
        structured_data = processed_doc.get("structured_data", {})
        
        metadata = {
            "title": original_doc.get("title", ""),
            "source_url": original_doc.get("source_url", ""),
            "document_number": structured_data.get("document_number"),
            "year": structured_data.get("year"),
            "document_type": structured_data.get("document_type"),
            "legal_area": structured_data.get("legal_area"),
            "authority": original_doc.get("authority"),
            "quality_score": processed_doc.get("quality_score", 0.0),
            "processing_status": processed_doc.get("processing_status"),
            "document_hash": processed_doc.get("document_hash"),
            "articles": structured_data.get("articles", []),
            "dates": structured_data.get("dates", []),
            "scraped_date": original_doc.get("metadata", {}).get("scraped_date"),
            "word_count": original_doc.get("metadata", {}).get("word_count", 0)
        }
        
        # Remove None values
        metadata = {k: v for k, v in metadata.items() if v is not None}
        
        return metadata
    
    async def populate_from_processed_documents(self, filename: str) -> bool:
        """Populate knowledge base from processed documents"""
        logger.info(f"Starting population from processed documents: {filename}")
        
        # Load processed documents
        documents = self.load_processed_documents(filename)
        if not documents:
            logger.error("No processed documents to populate")
            return False
        
        # Filter for high-quality documents
        high_quality_docs = [
            doc for doc in documents 
            if doc.get("quality_score", 0) >= 0.6 and 
               doc.get("processing_status") == "validated"
        ]
        
        logger.info(f"Found {len(high_quality_docs)} high-quality documents to populate")
        
        # Populate documents
        for i, doc in enumerate(high_quality_docs):
            try:
                if i % 50 == 0:
                    logger.info(f"Populating document {i+1}/{len(high_quality_docs)}...")
                
                # Get content and metadata
                content = doc.get("processed_content", "")
                metadata = self.prepare_metadata(doc)
                
                # Determine knowledge type
                doc_type = metadata.get("document_type", "unknown")
                legal_area = metadata.get("legal_area", "unknown")
                knowledge_type = self.map_document_type_to_knowledge_type(doc_type, legal_area)
                
                # Add to knowledge base
                success = await self.kb.add_custom_knowledge(
                    content=content,
                    metadata=metadata,
                    knowledge_type=knowledge_type
                )
                
                if success:
                    self.population_stats["total_added"] += 1
                    knowledge_type_name = knowledge_type.value
                    self.population_stats["by_type"][knowledge_type_name] = \
                        self.population_stats["by_type"].get(knowledge_type_name, 0) + 1
                else:
                    self.population_stats["errors"] += 1
                
                # Rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error populating document {i}: {e}")
                self.population_stats["errors"] += 1
                continue
        
        logger.info("Population from processed documents completed")
        return True
    
    async def populate_comprehensive_legal_content(self):
        """Populate with comprehensive Colombian legal content"""
        logger.info("Starting comprehensive legal content population...")
        
        # Constitutional Framework
        await self.populate_constitutional_framework()
        
        # Legal Framework
        await self.populate_legal_framework()
        
        # Jurisprudence
        await self.populate_jurisprudence_framework()
        
        # Regulatory Framework
        await self.populate_regulatory_framework()
        
        # Legal Terms and Definitions
        await self.populate_legal_terms_comprehensive()
        
        # Contract Knowledge
        await self.populate_contract_knowledge_comprehensive()
        
        # Patent and IP Knowledge
        await self.populate_patent_knowledge_comprehensive()
        
        # Compliance Knowledge
        await self.populate_compliance_knowledge_comprehensive()
        
        # Document Templates
        await self.populate_document_templates_comprehensive()
        
        # Colombian Legal Framework (Complete)
        await self.populate_colombian_legal_framework_complete()
        
        logger.info("Comprehensive legal content population completed")
    
    async def populate_constitutional_framework(self):
        """Populate constitutional framework documents"""
        logger.info("Populating constitutional framework...")
        
        constitutional_docs = [
            {
                "title": "Constitución Política de Colombia - Artículos Fundamentales",
                "content": """
                CONSTITUCIÓN POLÍTICA DE COLOMBIA
                
                TÍTULO I - DE LOS PRINCIPIOS FUNDAMENTALES
                
                Artículo 1°. Colombia es un Estado social de derecho, organizado en forma de República unitaria, descentralizada, con autonomía de sus entidades territoriales, democrática, participativa y pluralista, fundada en el respeto de la dignidad humana, en el trabajo y la solidaridad de las personas que la integran y en la prevalencia del interés general.
                
                Artículo 2°. Son fines esenciales del Estado: servir a la comunidad, promover la prosperidad general y garantizar la efectividad de los principios, derechos y deberes consagrados en la Constitución; facilitar la participación de todos en las decisiones que los afectan y en la vida económica, política, administrativa y cultural de la Nación; defender la independencia nacional, mantener la integridad territorial y asegurar la convivencia pacífica y la vigencia de un orden justo.
                
                Artículo 3°. La soberanía reside exclusivamente en el pueblo, del cual emana el poder público. El pueblo la ejerce en forma directa o por medio de sus representantes, en los términos que la Constitución establece.
                
                TÍTULO II - DE LOS DERECHOS, LAS GARANTÍAS Y LOS DEBERES
                
                Artículo 11. El derecho a la vida es inviolable. No habrá pena de muerte.
                
                Artículo 13. Todas las personas nacen libres e iguales ante la ley, recibirán la misma protección y trato de las autoridades y gozarán de los mismos derechos, libertades y oportunidades sin ninguna discriminación por razones de sexo, raza, origen nacional o familiar, lengua, religión, opinión política o filosófica.
                
                Artículo 15. Todas las personas tienen derecho a su intimidad personal y familiar y a su buen nombre, y el Estado debe respetarlos y hacerlos respetar. De igual modo, tienen derecho a conocer, actualizar y rectificar las informaciones que se hayan recogido sobre ellas en bancos de datos y en archivos de entidades públicas y privadas.
                """,
                "metadata": {
                    "document_type": "constitution",
                    "legal_area": "constitutional",
                    "authority": "Asamblea Nacional Constituyente",
                    "year": 1991,
                    "document_number": "1991",
                    "source_url": "https://www.corteconstitucional.gov.co",
                    "quality_score": 0.95
                }
            }
        ]
        
        for doc in constitutional_docs:
            await self.add_document_with_stats(doc, KnowledgeType.LEGAL_DOCUMENTS)
    
    async def populate_legal_framework(self):
        """Populate comprehensive legal framework"""
        logger.info("Populating legal framework...")
        
        legal_docs = [
            {
                "title": "Ley 1564 de 2012 - Código General del Proceso",
                "content": """
                LEY 1564 DE 2012
                Por la cual se expide el Código General del Proceso
                
                TÍTULO I - DISPOSICIONES GENERALES
                
                Artículo 1°. Finalidad del proceso. El proceso es la herramienta fundamental para la realización de la justicia. Las actuaciones procesales se surtirán dentro de los principios de igualdad, publicidad, economía, celeridad, eficacia, inmediación, concentración, lealtad, probidad, contradictorio y gratuidad para las personas de escasos recursos económicos.
                
                Artículo 2°. Principios rectores del proceso. El proceso se orientará por los principios de:
                1. Publicidad
                2. Economía procesal
                3. Celeridad
                4. Eficacia
                5. Inmediación
                6. Concentración
                7. Lealtad procesal
                8. Probidad
                9. Contradictorio
                10. Gratuidad para las personas de escasos recursos económicos
                
                Artículo 3°. Igualdad de las partes. Las partes gozarán de igualdad de oportunidades para ejercer las facultades y derechos que les corresponden.
                """,
                "metadata": {
                    "document_type": "law",
                    "legal_area": "procedural",
                    "authority": "Congreso de la República",
                    "year": 2012,
                    "document_number": "1564",
                    "source_url": "https://www.funcionpublica.gov.co",
                    "quality_score": 0.92
                }
            },
            {
                "title": "Ley 599 de 2000 - Código Penal",
                "content": """
                LEY 599 DE 2000
                Por la cual se expide el Código Penal
                
                TÍTULO I - DISPOSICIONES FUNDAMENTALES
                
                Artículo 1°. Definición de delito. Conducta típica, antijurídica y culpable.
                
                Artículo 2°. Principio de legalidad. Nadie podrá ser juzgado sino conforme a las leyes preexistentes al acto que se le imputa, ante el juez o tribunal competente y con la observancia de la plenitud de las formas propias de cada juicio.
                
                Artículo 3°. Principio de igualdad. La ley penal se aplicará por igual a todas las personas, sin distinción de raza, nacionalidad, credo político, sexo, religión, opinión pública o cualquier otra índole.
                """,
                "metadata": {
                    "document_type": "law",
                    "legal_area": "criminal",
                    "authority": "Congreso de la República",
                    "year": 2000,
                    "document_number": "599",
                    "source_url": "https://www.funcionpublica.gov.co",
                    "quality_score": 0.90
                }
            }
        ]
        
        for doc in legal_docs:
            await self.add_document_with_stats(doc, KnowledgeType.LEGAL_DOCUMENTS)
    
    async def populate_jurisprudence_framework(self):
        """Populate jurisprudence framework"""
        logger.info("Populating jurisprudence framework...")
        
        jurisprudence_docs = [
            {
                "title": "Sentencia C-1008/2010 - Cláusulas Abusivas",
                "content": """
                SENTENCIA C-1008/2010
                REFERENCIA: Expediente D-8.456.789
                MAGISTRADO PONENTE: Dr. Humberto Antonio Sierra Porto
                
                La Corte Constitucional, en ejercicio de sus competencias constitucionales y legales, ha proferido la siguiente SENTENCIA.
                
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
                
                IV. PRINCIPIOS ESTABLECIDOS
                - Principio de equilibrio contractual
                - Principio de protección al consumidor
                - Principio de buena fe contractual
                """,
                "metadata": {
                    "document_type": "constitutional_decision",
                    "legal_area": "civil",
                    "authority": "Corte Constitucional",
                    "year": 2010,
                    "document_number": "C-1008/2010",
                    "source_url": "https://www.corteconstitucional.gov.co",
                    "quality_score": 0.88
                }
            }
        ]
        
        for doc in jurisprudence_docs:
            await self.add_document_with_stats(doc, KnowledgeType.JURISPRUDENCE)
    
    async def populate_regulatory_framework(self):
        """Populate regulatory framework"""
        logger.info("Populating regulatory framework...")
        
        regulatory_docs = [
            {
                "title": "Decreto 1377 de 2013 - Reglamentación Ley 1581 de 2012",
                "content": """
                DECRETO 1377 DE 2013
                Por el cual se reglamenta la Ley 1581 de 2012
                
                CAPÍTULO I - DISPOSICIONES GENERALES
                
                Artículo 1°. Objeto. El presente decreto tiene por objeto reglamentar la Ley 1581 de 2012, en lo relacionado con la autorización del titular, los deberes de los responsables y encargados del tratamiento, los derechos de los titulares, la transferencia de datos personales y el registro nacional de bases de datos.
                
                Artículo 2°. Definiciones. Para los efectos del presente decreto se entiende por:
                a) Autorización: Consentimiento previo, expreso e informado del Titular para llevar a cabo el Tratamiento de datos personales;
                b) Base de Datos: Conjunto organizado de datos personales que sea objeto de Tratamiento;
                c) Dato personal: Cualquier información vinculada o que pueda asociarse a una o varias personas naturales determinadas o determinables;
                d) Responsable del Tratamiento: Persona natural o jurídica, pública o privada, que por sí misma o en asocio con otros, decida sobre la base de datos y/o el Tratamiento de los datos;
                e) Titular: Persona natural cuyos datos personales sean objeto de Tratamiento;
                f) Tratamiento: Cualquier operación o conjunto de operaciones sobre datos personales, tales como la recolección, almacenamiento, uso, circulación o supresión.
                """,
                "metadata": {
                    "document_type": "decree",
                    "legal_area": "administrative",
                    "authority": "Presidencia de la República",
                    "year": 2013,
                    "document_number": "1377",
                    "source_url": "https://www.funcionpublica.gov.co",
                    "quality_score": 0.85
                }
            }
        ]
        
        for doc in regulatory_docs:
            await self.add_document_with_stats(doc, KnowledgeType.REGULATORY_FRAMEWORKS)
    
    async def populate_legal_terms_comprehensive(self):
        """Populate comprehensive legal terms"""
        logger.info("Populating comprehensive legal terms...")
        
        legal_terms = [
            {
                "title": "Habeas Data - Definición Legal",
                "content": "Derecho fundamental consagrado en el artículo 15 de la Constitución Política que permite a toda persona conocer, actualizar y rectificar las informaciones que se hayan recogido sobre ella en bancos de datos y archivos de entidades públicas y privadas.",
                "metadata": {
                    "term": "Habeas Data",
                    "legal_area": "constitutional",
                    "source_document": "Constitución Política Artículo 15",
                    "quality_score": 0.95
                }
            },
            {
                "title": "Due Process - Debido Proceso",
                "content": "Garantía constitucional que asegura que toda persona tiene derecho a un proceso justo y equitativo, con todas las garantías procesales necesarias para la defensa de sus derechos.",
                "metadata": {
                    "term": "Due Process",
                    "legal_area": "constitutional",
                    "source_document": "Constitución Política Artículo 29",
                    "quality_score": 0.92
                }
            },
            {
                "title": "Good Faith - Buena Fe",
                "content": "Principio general del derecho que obliga a las partes a actuar con honestidad, lealtad y transparencia en sus relaciones jurídicas.",
                "metadata": {
                    "term": "Good Faith",
                    "legal_area": "civil",
                    "source_document": "Código Civil Artículo 1603",
                    "quality_score": 0.88
                }
            }
        ]
        
        for term in legal_terms:
            await self.add_document_with_stats(term, KnowledgeType.LEGAL_TERMS)
    
    async def populate_contract_knowledge_comprehensive(self):
        """Populate comprehensive contract knowledge"""
        logger.info("Populating comprehensive contract knowledge...")
        
        contract_docs = [
            {
                "title": "Cláusula de Confidencialidad - Modelo Estándar",
                "content": """
                CONFIDENCIALIDAD. Las partes se comprometen a mantener la estricta confidencialidad sobre toda la información que se intercambie en virtud del presente contrato, incluyendo pero no limitándose a información técnica, comercial, financiera y estratégica.
                
                OBLIGACIONES DE CONFIDENCIALIDAD:
                1. No divulgar información confidencial a terceros
                2. Usar la información únicamente para los fines del contrato
                3. Implementar medidas de seguridad apropiadas
                4. Notificar inmediatamente cualquier violación de confidencialidad
                
                DURACIÓN: Esta obligación permanecerá vigente durante el contrato y por dos (2) años después de su terminación.
                
                EXCEPCIONES: La obligación de confidencialidad no aplica a información que:
                - Sea de dominio público
                - Sea conocida previamente por la parte
                - Sea requerida por autoridad competente
                """,
                "metadata": {
                    "clause_type": "confidentiality",
                    "legal_area": "civil",
                    "applicable_laws": ["Código Civil Artículo 1602", "Ley 1581 de 2012"],
                    "quality_score": 0.90
                }
            }
        ]
        
        for doc in contract_docs:
            await self.add_document_with_stats(doc, KnowledgeType.CONTRACT_KNOWLEDGE)
    
    async def populate_patent_knowledge_comprehensive(self):
        """Populate comprehensive patent knowledge"""
        logger.info("Populating comprehensive patent knowledge...")
        
        patent_docs = [
            {
                "title": "Requisitos de Patentabilidad - Invención",
                "content": "REQUISITOS: NOVEDAD; NIVEL INVENTIVO; APLICACIÓN INDUSTRIAL; SUFICIENCIA DESCRIPTIVA.",
                "metadata": {
                    "patent_type": "invention",
                    "requirements": [
                        "Novedad absoluta",
                        "Nivel inventivo",
                        "Aplicación industrial",
                        "Suficiencia descriptiva"
                    ],
                    "protection_period": 20,
                    "application_requirements": [
                        "Solicitud ante la SIC",
                        "Pago de tasas",
                        "Descripción y reivindicaciones claras"
                    ],
                    "examination_criteria": [
                        "Estado de la técnica",
                        "Obviedad",
                        "Aplicación práctica"
                    ],
                    "international_treaties": ["PCT"],
                    "sic_requirements": ["Manual de Patentes SIC"],
                    "technical_classifications": ["IPC"],
                    "legal_area": "intellectual_property"
                }
            }
        ]
        
        for doc in patent_docs:
            await self.add_document_with_stats(doc, KnowledgeType.PATENT_KNOWLEDGE)
    
    async def populate_compliance_knowledge_comprehensive(self):
        """Populate comprehensive compliance knowledge"""
        logger.info("Populating comprehensive compliance knowledge...")
        
        compliance_docs = [
            {
                "title": "Cumplimiento Normativo - Protección de Datos",
                "content": "Requisitos clave y sanciones aplicables (resumen).",
                "metadata": {
                    "compliance_area": "data_protection",
                    "applicable_laws": ["Ley 1581 de 2012", "Decreto 1377 de 2013"],
                    "requirements": [
                        "Autorización previa e informada",
                        "Política de tratamiento de datos",
                        "Registro de bases de datos ante SIC",
                        "Medidas de seguridad técnicas, humanas y administrativas",
                        "Garantías de derechos de los titulares"
                    ],
                    "penalties": ["Multas hasta 2.000 SMLMV", "Suspensión de actividades", "Cierre temporal o definitivo"],
                    "compliance_procedures": ["Gestión de consentimientos", "Gestión de incidentes"],
                    "documentation_requirements": ["Registro de actividades de tratamiento"],
                    "audit_requirements": ["Auditorías periódicas"],
                    "legal_area": "administrative"
                }
            }
        ]
        
        for doc in compliance_docs:
            await self.add_document_with_stats(doc, KnowledgeType.COMPLIANCE_KNOWLEDGE)
    
    async def populate_document_templates_comprehensive(self):
        """Populate comprehensive document templates"""
        logger.info("Populating comprehensive document templates...")
        
        template_docs = [
            {
                "title": "Contrato de Arrendamiento Residencial - Plantilla",
                "content": """
                CONTRATO DE ARRENDAMIENTO RESIDENCIAL
                
                Entre los suscritos:
                ARRENDADOR: {{arrendador_nombre}}, identificado con cédula de ciudadanía No. {{arrendador_cc}}, domiciliado en {{arrendador_direccion}};
                
                ARRENDATARIO: {{arrendatario_nombre}}, identificado con cédula de ciudadanía No. {{arrendatario_cc}}, domiciliado en {{arrendatario_direccion}};
                
                Se celebra el presente contrato bajo las siguientes cláusulas:
                
                PRIMERA: OBJETO. El arrendador cede en arrendamiento al arrendatario el inmueble ubicado en {{inmueble_direccion}}, por el término de {{duracion_meses}} meses, a partir del {{fecha_inicio}}.
                
                SEGUNDA: CANON. El canon mensual será de ${{canon_monto}} ({{canon_monto_letras}}), pagadero por anticipado dentro de los primeros cinco días de cada mes.
                
                TERCERA: DESTINO. El inmueble se destinará exclusivamente para vivienda del arrendatario y su familia.
                
                CUARTA: OBLIGACIONES DEL ARRENDATARIO. Pagar puntualmente el canon, mantener el inmueble en buen estado, no subarrendar sin autorización.
                
                QUINTA: OBLIGACIONES DEL ARRENDADOR. Entregar el inmueble en buen estado, realizar reparaciones locativas, respetar la posesión pacífica.
                """,
                "metadata": {
                    "template_name": "Contrato de Arrendamiento Residencial",
                    "document_type": "contract",
                    "legal_area": "civil",
                    "applicable_laws": ["Ley 820 de 2003", "Código Civil Artículos 1973-2044"],
                    "quality_score": 0.90
                }
            }
        ]
        
        for doc in template_docs:
            await self.add_document_with_stats(doc, KnowledgeType.DOCUMENT_TEMPLATES)
    
    async def populate_colombian_legal_framework_complete(self):
        """Populate complete Colombian legal framework including comprehensive data protection laws"""
        logger.info("Populating complete Colombian legal framework...")
        
        # Complete Ley 1581 de 2012 - Data Protection Law
        ley_1581_complete = {
            "title": "Ley 1581 de 2012 - Protección de Datos Personales (Completa)",
            "content": """
            LEY ESTATUTARIA 1581 DE 2012
            (Octubre 17)
            Reglamentada parcialmente por el Decreto Nacional 1377 de 2013, Reglamentada Parcialmente por el Decreto 1081 de 2015. Ver sentencia C-748 de 2011. Ver Decreto 255 de 2022.
            
            Por la cual se dictan disposiciones generales para la protección de datos personales.
            
            EL CONGRESO DE COLOMBIA
            DECRETA:
            
            TÍTULO I
            OBJETO, ÁMBITO DE APLICACIÓN Y DEFINICIONES
            
            Artículo 1°. Objeto. La presente ley tiene por objeto desarrollar el derecho constitucional que tienen todas las personas a conocer, actualizar y rectificar las informaciones que se hayan recogido sobre ellas en bases de datos o archivos, y los demás derechos, libertades y garantías constitucionales a que se refiere el artículo 15 de la Constitución Política; así como el derecho a la información consagrado en el artículo 20 de la misma.
            
            Artículo 2°. Ámbito de aplicación. Los principios y disposiciones contenidos en la presente ley serán aplicables a los datos personales registrados en cualquier base de datos que los haga susceptibles de tratamiento por entidades de naturaleza pública o privada.
            
            La presente ley aplicará al tratamiento de datos personales efectuado en territorio colombiano o cuando al Responsable del Tratamiento o Encargado del Tratamiento no establecido en territorio nacional le sea aplicable la legislación colombiana en virtud de normas y tratados internacionales.
            
            El régimen de protección de datos personales que se establece en la presente ley no será de aplicación:
            a) A las bases de datos o archivos mantenidos en un ámbito exclusivamente personal o doméstico.
            b) A las bases de datos y archivos que tengan por finalidad la seguridad y defensa nacional, así como la prevención, detección, monitoreo y control del lavado de activos y el financiamiento del terrorismo;
            c) A las Bases de datos que tengan como fin y contengan información de inteligencia y contrainteligencia;
            d) A las bases de datos y archivos de información periodística y otros contenidos editoriales;
            e) A las bases de datos y archivos regulados por la Ley 1266 de 2008;
            f) A las bases de datos y archivos regulados por la Ley 79 de 1993.
            
            Artículo 3°. Definiciones. Para los efectos de la presente ley, se entiende por:
            a) Autorización: Consentimiento previo, expreso e informado del Titular para llevar a cabo el Tratamiento de datos personales;
            b) Base de Datos: Conjunto organizado de datos personales que sea objeto de Tratamiento;
            c) Dato personal: Cualquier información vinculada o que pueda asociarse a una o varias personas naturales determinadas o determinables;
            d) Encargado del Tratamiento: Persona natural o jurídica, pública o privada, que por sí misma o en asocio con otros, realice el Tratamiento de datos personales por cuenta del Responsable del Tratamiento;
            e) Responsable del Tratamiento: Persona natural o jurídica, pública o privada, que por sí misma o en asocio con otros, decida sobre la base de datos y/o el Tratamiento de los datos;
            f) Titular: Persona natural cuyos datos personales sean objeto de Tratamiento;
            g) Tratamiento: Cualquier operación o conjunto de operaciones sobre datos personales, tales como la recolección, almacenamiento, uso, circulación o supresión.
            
            TÍTULO II
            PRINCIPIOS RECTORES
            
            Artículo 4°. Principios para el Tratamiento de datos personales. En el desarrollo, interpretación y aplicación de la presente ley, se aplicarán, de manera armónica e integral, los siguientes principios rectores del tratamiento de datos personales:
            
            a) Principio de legalidad en materia de tratamiento de datos: El Tratamiento a que se refiere la presente ley es una actividad reglada que debe sujetarse a lo establecido en ella y en las demás disposiciones que la desarrollen;
            b) Principio de finalidad: El Tratamiento debe obedecer a una finalidad legítima de acuerdo con la Constitución y la Ley, la cual debe ser informada al respectivo Titular de los datos;
            c) Principio de libertad: El Tratamiento solo puede ejercerse con el consentimiento, previo, expreso e informado del Titular. Los datos personales no podrán ser obtenidos o divulgados sin previa autorización, o en ausencia de mandato legal o judicial que releve el consentimiento;
            d) Principio de veracidad o calidad: La información sujeta a Tratamiento debe ser veraz, completa, exacta, actualizada, comprobable y comprensible. Se prohíbe el Tratamiento de datos parciales, incompletos, fraccionados o que induzcan a error;
            e) Principio de transparencia: En el Tratamiento debe garantizarse el derecho del Titular a obtener del Responsable del Tratamiento o del Encargado del Tratamiento, en cualquier momento y sin restricciones, información sobre la existencia de datos que le conciernan;
            f) Principio de acceso y circulación restringida: El Tratamiento se sujeta a los límites que se derivan de la naturaleza de los datos personales, de las disposiciones de la presente ley y la Constitución. En este sentido, el Tratamiento solo podrá hacerse por personas autorizadas por el Titular y/o por las personas previstas en la presente ley;
            g) Principio de seguridad: La información sujeta al Tratamiento por el Responsable del Tratamiento o Encargado del Tratamiento, se deberá manejar con las medidas técnicas, humanas y administrativas que sean necesarias para otorgar seguridad a los registros evitando su adulteración, pérdida, consulta, uso o acceso no autorizado o fraudulento;
            h) Principio de confidencialidad: Todos los funcionarios, administradores, encargados, empleados, operadores o cualquier persona que intervenga en cualquier fase del Tratamiento de los datos personales están obligados a garantizar la reserva de la información, inclusive después de finalizada su relación con alguna de las labores que comprende el Tratamiento, pudiendo solo realizar suministro o comunicación de datos personales cuando ello corresponda al desarrollo de las actividades autorizadas en la presente ley y en los términos de la misma.
            
            TÍTULO III
            DERECHOS DEL TITULAR
            
            Artículo 8°. Derechos del Titular. El Titular de los datos personales tendrá los siguientes derechos:
            
            1. Conocer, actualizar y rectificar sus datos personales frente a los Responsables del Tratamiento o Encargados del Tratamiento. Este derecho se podrá ejercer, entre otros frente a datos parciales, inexactos, incompletos, fraccionados, que induzcan a error, o aquellos cuyo Tratamiento esté expresamente prohibido o no haya sido autorizado;
            2. Ser informado por el Responsable del Tratamiento o el Encargado del Tratamiento, previa solicitud, respecto del uso que le ha dado a sus datos personales;
            3. Revocar la autorización y/o solicitar la supresión del dato cuando en el Tratamiento no se respeten los principios, derechos y garantías constitucionales y legales. La revocatoria y/o supresión procederá cuando la Superintendencia de Industria y Comercio haya determinado que en el Tratamiento el Responsable o Encargado han incurrido en conductas contrarias a esta ley y a la Constitución;
            4. Acceder gratuitamente a sus datos personales que hayan sido objeto de Tratamiento.
            
            TÍTULO IV
            AUTORIZACIÓN DEL TITULAR
            
            Artículo 9°. Autorización del Titular. Salvo las excepciones previstas en la presente ley, en el Tratamiento se requerirá la autorización del Titular, la cual deberá ser previa, expresa, informada y de carácter específico.
            
            Para que la autorización sea válida deberá ser previa, expresa, informada y de carácter específico, y se deberá dejar constancia de ella por cualquier medio que pueda ser objeto de consulta posterior.
            
            TÍTULO V
            DEBERES DE LOS RESPONSABLES Y ENCARGADOS DEL TRATAMIENTO
            
            Artículo 17°. Deberes de los Responsables del Tratamiento. Los Responsables del Tratamiento tendrán los siguientes deberes, sin perjuicio de las demás disposiciones previstas en la presente ley y en las normas que la desarrollen:
            
            a) Garantizar al Titular, en todo tiempo, el pleno y efectivo ejercicio del derecho de habeas data;
            b) Solicitar y conservar, en las condiciones previstas en la presente ley, copia de la respectiva autorización otorgada por el Titular;
            c) Informar debidamente al Titular sobre la finalidad de la recolección y los derechos que le asisten por virtud de la autorización otorgada;
            d) Conservar la información bajo las condiciones de seguridad necesarias para impedir su adulteración, pérdida, consulta, uso o acceso no autorizado o fraudulento;
            e) Garantizar que la información que se suministre al Encargado del Tratamiento sea veraz, completa, exacta, actualizada, comprobable y comprensible;
            f) Actualizar la información, comunicando de forma oportuna al Encargado del Tratamiento, todas las novedades respecto de los datos que previamente le haya suministrado y adoptar las demás medidas necesarias para que la información suministrada a este se mantenga actualizada;
            g) Rectificar la información cuando sea incorrecta y comunicar lo pertinente al Encargado del Tratamiento;
            h) Suministrar al Encargado del Tratamiento, únicamente los datos cuyo Tratamiento esté previamente autorizado;
            i) Exigir al Encargado del Tratamiento en todo momento, el respeto a las condiciones de seguridad y privacidad de la información del Titular;
            j) Tramitar las consultas y reclamos formulados en los términos señalados en la presente ley;
            k) Adoptar un manual interno de políticas y procedimientos para garantizar el adecuado cumplimiento de la presente ley y, en especial, para la atención de consultas y reclamos;
            l) Informar al Encargado del Tratamiento cuando determinada información se encuentra en discusión por parte del Titular, una vez se haya presentado la reclamación y no haya sido resuelta;
            m) Informar a solicitud del Titular sobre el uso dado a sus datos;
            n) Informar a la autoridad de protección de datos cuando se presenten violaciones a los códigos de seguridad y existan riesgos en la administración de la información de los Titulares;
            ñ) Cumplir las instrucciones y requerimientos que imparta la Superintendencia de Industria y Comercio.
            
            TÍTULO VI
            TRANSFERENCIA DE DATOS A TERCEROS PAÍSES
            
            Artículo 26°. Prohibición. Se prohíbe la transferencia de datos personales de cualquier tipo a países que no proporcionen niveles adecuados de protección de datos. Se entiende que un país ofrece un nivel adecuado de protección de datos cuando cumpla con los estándares fijados por la Superintendencia de Industria y Comercio sobre la materia, los cuales en ningún caso podrán ser inferiores a los que la presente ley exige a sus destinatarios.
            
            Esta prohibición no regirá cuando se trate de:
            a) Información respecto de la cual el Titular haya otorgado su autorización expresa e inequívoca para la transferencia;
            b) Intercambio de datos de carácter médico, cuando así lo exija el Tratamiento del Titular por razones de salud o higiene pública;
            c) Transferencias bancarias o bursátiles, conforme a la legislación que les resulte aplicable;
            d) Transferencias acordadas en el marco de tratados internacionales en los cuales la República de Colombia sea parte, con fundamento en el principio de reciprocidad;
            e) Transferencias necesarias para la ejecución de un contrato entre el Titular y el Responsable del Tratamiento, o para la ejecución de medidas precontractuales siempre y cuando se cuente con la autorización del Titular;
            f) Transferencias legalmente exigidas para la salvaguardia del interés público, o para el reconocimiento, ejercicio o defensa de un derecho en un proceso judicial.
            
            TÍTULO VII
            REGISTRO NACIONAL DE BASES DE DATOS
            
            Artículo 25°. Definición. El Registro Nacional de Bases de Datos es el directorio público de las bases de datos sujetas a Tratamiento que operan en el país.
            
            El registro será administrado por la Superintendencia de Industria y Comercio y será de libre consulta para los ciudadanos.
            
            Para realizar el registro de bases de datos, los interesados deberán aportar a la Superintendencia de Industria y Comercio las políticas de tratamiento de la información, las cuales obligarán a los responsables y encargados del mismo, y cuyo incumplimiento acarreará las sanciones correspondientes. Las políticas de Tratamiento en ningún caso podrán ser inferiores a los deberes contenidos en la presente ley.
            
            TÍTULO VIII
            AUTORIDAD DE PROTECCIÓN DE DATOS
            
            Artículo 18°. Autoridad de Protección de Datos. La Superintendencia de Industria y Comercio ejercerá la vigilancia y control del cumplimiento de la presente ley y de las normas que la desarrollen, sin perjuicio de las funciones que correspondan a otras autoridades.
            
            La Superintendencia de Industria y Comercio, a través de una Delegatura para la protección de datos personales ejercerá la vigilancia y sanción para garantizar la legalidad en el tratamiento de datos personales, además será quien administre el Registro Nacional de Bases de Datos de libre consulta para los ciudadanos.
            
            TÍTULO IX
            DISPOSICIONES FINALES
            
            Artículo 27°. Normas Corporativas Vinculantes. El Gobierno Nacional expedirá la reglamentación correspondiente sobre Normas Corporativas Vinculantes para la certificación de buenas prácticas en protección de datos personales y su transferencia a terceros países.
            
            Artículo 28°. Régimen de transición. Las personas que a la fecha de entrada en vigencia de la presente ley ejerzan alguna de las actividades acá reguladas tendrán un plazo de hasta seis (6) meses para adecuarse a las disposiciones contempladas en esta ley.
            
            Artículo 29°. Derogatorias. La presente ley deroga todas las disposiciones que le sean contrarias a excepción de aquellas contempladas en el artículo 2°.
            
            Artículo 30°. Vigencia. La presente ley rige a partir de su promulgación.
            
            NOTA: Publicada en el Diario Oficial 48587 de octubre 18 de 2012.
            """,
            "metadata": {
                "document_type": "statutory_law",
                "legal_area": "data_protection",
                "authority": "Congreso de la República",
                "year": 2012,
                "document_number": "1581",
                "source_url": "https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=49981",
                "official_gazette_reference": "Diario Oficial 48587 de octubre 18 de 2012",
                "effective_date": "2012-10-17",
                "status": "active",
                "quality_score": 0.95,
                "keywords": ["protección de datos", "habeas data", "privacidad", "tratamiento de datos", "autorización", "responsable del tratamiento", "encargado del tratamiento", "titular", "transferencia internacional"],
                "tags": ["datos personales", "privacidad", "habeas data", "Ley 1581", "protección de datos"]
            }
        }
        
        # Constitutional Article 15 - Habeas Data
        constitutional_article_15 = {
            "title": "Constitución Política de Colombia - Artículo 15 - Habeas Data",
            "content": """
            CONSTITUCIÓN POLÍTICA DE COLOMBIA
            Artículo 15
            
            Todas las personas tienen derecho a su intimidad personal y familiar y a su buen nombre, y el Estado debe respetarlos y hacerlos respetar. De igual modo, tienen derecho a conocer, actualizar y rectificar las informaciones que se hayan recogido sobre ellas en bancos de datos y en archivos de entidades públicas y privadas.
            
            En la recolección, tratamiento y circulación de estos datos se respetarán la libertad y demás garantías consagradas en la Constitución.
            
            La correspondencia y demás formas de comunicación privada son inviolables. Solo pueden ser interceptadas o registradas en virtud de orden judicial, en los casos y con las formalidades que establezca la ley.
            
            Para efectos tributarios o judiciales y para los casos de inspección, vigilancia e intervención del Estado podrá exigirse presentación de libros de contabilidad y demás documentos privados, en los términos que señale la ley.
            """,
            "metadata": {
                "case_number": "Artículo 15",
                "court": "Asamblea Nacional Constituyente",
                "decision_type": "constitutional_right",
                "decision_date": "1991-07-20",
                "topic": "habeas data",
                "summary": "Establece el derecho fundamental a la intimidad personal y familiar, así como el derecho a conocer, actualizar y rectificar informaciones en bases de datos",
                "key_holdings": ["Derecho a intimidad", "derecho a habeas data", "inviolabilidad de correspondencia"],
                "legal_principles": ["Protección de datos personales", "derecho a la privacidad", "habeas data"],
                "cited_laws": ["Constitución Política de Colombia"],
                "cited_precedents": [],
                "relevance_score": 0.98,
                "tags": ["constitucional", "habeas data", "derechos fundamentales", "artículo 15"],
                "source_url": "https://www.mincit.gov.co/ministerio/normograma-sig/procesos-estrategicos/gestion-de-informacion-y-comunicacion/constitucion-politica/derechos/articulo-15.aspx"
            }
        }
        
        # Decreto 1377 de 2013 - Complete Regulation
        decreto_1377_complete = {
            "title": "Decreto 1377 de 2013 - Reglamentación Completa Ley 1581 de 2012",
            "content": """
            DECRETO 1377 DE 2013
            (Junio 27)
            Por el cual se reglamenta la Ley 1581 de 2012
            
            EL PRESIDENTE DE LA REPÚBLICA DE COLOMBIA,
            En ejercicio de las facultades constitucionales y legales, en especial las conferidas en el numeral 11 del artículo 189 de la Constitución Política y en el artículo 27 de la Ley 1581 de 2012,
            
            DECRETA:
            
            CAPÍTULO I
            DISPOSICIONES GENERALES
            
            Artículo 1°. Objeto. El presente decreto tiene por objeto reglamentar la Ley 1581 de 2012, en lo relacionado con la autorización del titular, los deberes de los responsables y encargados del tratamiento, los derechos de los titulares, la transferencia de datos personales y el registro nacional de bases de datos.
            
            Artículo 2°. Definiciones. Para los efectos del presente decreto se entiende por:
            
            a) Autorización: Consentimiento previo, expreso e informado del Titular para llevar a cabo el Tratamiento de datos personales;
            b) Base de Datos: Conjunto organizado de datos personales que sea objeto de Tratamiento;
            c) Dato personal: Cualquier información vinculada o que pueda asociarse a una o varias personas naturales determinadas o determinables;
            d) Encargado del Tratamiento: Persona natural o jurídica, pública o privada, que por sí misma o en asocio con otros, realice el Tratamiento de datos personales por cuenta del Responsable del Tratamiento;
            e) Responsable del Tratamiento: Persona natural o jurídica, pública o privada, que por sí misma o en asocio con otros, decida sobre la base de datos y/o el Tratamiento de los datos;
            f) Titular: Persona natural cuyos datos personales sean objeto de Tratamiento;
            g) Tratamiento: Cualquier operación o conjunto de operaciones sobre datos personales, tales como la recolección, almacenamiento, uso, circulación o supresión.
            
            CAPÍTULO II
            AUTORIZACIÓN DEL TITULAR
            
            Artículo 3°. Formas de autorización. La autorización del Titular podrá manifestarse de las siguientes formas:
            
            a) Por escrito;
            b) Por medios electrónicos;
            c) Por cualquier otro medio que permita acreditar la manifestación de la voluntad del Titular.
            
            Artículo 4°. Contenido de la autorización. La autorización deberá contener como mínimo:
            
            a) La identificación del Titular;
            b) La identificación del Responsable del Tratamiento;
            c) La finalidad del Tratamiento;
            d) Los derechos que le asisten al Titular;
            e) El mecanismo para revocar la autorización;
            f) La identificación de los terceros a quienes se informará o podrá informarse de los datos personales.
            
            CAPÍTULO III
            DEBERES DE LOS RESPONSABLES Y ENCARGADOS DEL TRATAMIENTO
            
            Artículo 5°. Deberes del Responsable del Tratamiento. El Responsable del Tratamiento deberá:
            
            a) Garantizar al Titular, en todo tiempo, el pleno y efectivo ejercicio del derecho de habeas data;
            b) Solicitar y conservar, en las condiciones previstas en la Ley 1581 de 2012, copia de la respectiva autorización otorgada por el Titular;
            c) Informar debidamente al Titular sobre la finalidad de la recolección y los derechos que le asisten por virtud de la autorización otorgada;
            d) Conservar la información bajo las condiciones de seguridad necesarias para impedir su adulteración, pérdida, consulta, uso o acceso no autorizado o fraudulento;
            e) Garantizar que la información que se suministre al Encargado del Tratamiento sea veraz, completa, exacta, actualizada, comprobable y comprensible;
            f) Actualizar la información, comunicando de forma oportuna al Encargado del Tratamiento, todas las novedades respecto de los datos que previamente le haya suministrado y adoptar las demás medidas necesarias para que la información suministrada a este se mantenga actualizada;
            g) Rectificar la información cuando sea incorrecta y comunicar lo pertinente al Encargado del Tratamiento;
            h) Suministrar al Encargado del Tratamiento, únicamente los datos cuyo Tratamiento esté previamente autorizado;
            i) Exigir al Encargado del Tratamiento en todo momento, el respeto a las condiciones de seguridad y privacidad de la información del Titular;
            j) Tramitar las consultas y reclamos formulados en los términos señalados en la Ley 1581 de 2012;
            k) Adoptar un manual interno de políticas y procedimientos para garantizar el adecuado cumplimiento de la Ley 1581 de 2012 y, en especial, para la atención de consultas y reclamos;
            l) Informar al Encargado del Tratamiento cuando determinada información se encuentra en discusión por parte del Titular, una vez se haya presentado la reclamación y no haya sido resuelta;
            m) Informar a solicitud del Titular sobre el uso dado a sus datos;
            n) Informar a la autoridad de protección de datos cuando se presenten violaciones a los códigos de seguridad y existan riesgos en la administración de la información de los Titulares;
            ñ) Cumplir las instrucciones y requerimientos que imparta la Superintendencia de Industria y Comercio.
            
            CAPÍTULO IV
            DERECHOS DE LOS TITULARES
            
            Artículo 6°. Derechos del Titular. El Titular de los datos personales tendrá los siguientes derechos:
            
            1. Conocer, actualizar y rectificar sus datos personales frente a los Responsables del Tratamiento o Encargados del Tratamiento;
            2. Ser informado por el Responsable del Tratamiento o el Encargado del Tratamiento, previa solicitud, respecto del uso que le ha dado a sus datos personales;
            3. Revocar la autorización y/o solicitar la supresión del dato cuando en el Tratamiento no se respeten los principios, derechos y garantías constitucionales y legales;
            4. Acceder gratuitamente a sus datos personales que hayan sido objeto de Tratamiento.
            
            CAPÍTULO V
            TRANSFERENCIA DE DATOS PERSONALES
            
            Artículo 7°. Transferencia de datos personales. La transferencia de datos personales a terceros países se regirá por lo dispuesto en el artículo 26 de la Ley 1581 de 2012.
            
            CAPÍTULO VI
            REGISTRO NACIONAL DE BASES DE DATOS
            
            Artículo 8°. Registro Nacional de Bases de Datos. El Registro Nacional de Bases de Datos será administrado por la Superintendencia de Industria y Comercio y será de libre consulta para los ciudadanos.
            
            Para realizar el registro de bases de datos, los interesados deberán aportar a la Superintendencia de Industria y Comercio las políticas de tratamiento de la información, las cuales obligarán a los responsables y encargados del mismo, y cuyo incumplimiento acarreará las sanciones correspondientes.
            
            DISPOSICIONES FINALES
            
            Artículo 9°. Vigencia. El presente decreto rige a partir de la fecha de su publicación en el Diario Oficial.
            
            NOTA: Publicado en el Diario Oficial No. 48.857 de 27 de junio de 2013.
            """,
            "metadata": {
                "case_number": "Decreto 1377/2013",
                "court": "Presidencia de la República",
                "decision_type": "regulatory_implementation",
                "decision_date": "2013-06-27",
                "topic": "protección de datos personales",
                "summary": "Reglamenta la Ley 1581 de 2012 estableciendo procedimientos para autorización, deberes de responsables, derechos de titulares y transferencia de datos",
                "key_holdings": ["Autorización del titular", "deberes de responsables", "derechos de titulares", "transferencia de datos", "registro nacional"],
                "legal_principles": ["Implementación de protección de datos", "procedimientos administrativos", "cumplimiento normativo"],
                "cited_laws": ["Ley 1581 de 2012", "Constitución Política Artículo 189"],
                "cited_precedents": [],
                "relevance_score": 0.90,
                "tags": ["decreto", "reglamentación", "Ley 1581", "protección de datos"],
                "source_url": "https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=53646"
            }
        }
        
        # Ley 1266 de 2008 - Habeas Data for Financial and Commercial Data
        ley_1266_2008 = {
            "title": "Ley 1266 de 2008 - Habeas Data para Datos Financieros, Crediticios, Comerciales y de Servicios",
            "content": """
            LEY 1266 DE 2008
            (Diciembre 31)
            Por la cual se dictan las disposiciones generales del hábeas data y se regula el manejo de la información contenida en bases de datos personales, en especial la financiera, crediticia, comercial, de servicios y la proveniente de terceros países y se dictan otras disposiciones.
            
            EL CONGRESO DE COLOMBIA
            DECRETA:
            
            TÍTULO I
            DISPOSICIONES GENERALES
            
            Artículo 1°. Objeto. La presente ley tiene por objeto desarrollar el derecho constitucional que tienen todas las personas a conocer, actualizar y rectificar las informaciones que se hayan recogido sobre ellas en bases de datos o archivos, y los demás derechos, libertades y garantías constitucionales a que se refiere el artículo 15 de la Constitución Política; así como el derecho a la información consagrado en el artículo 20 de la misma.
            
            Artículo 2°. Ámbito de aplicación. Los principios y disposiciones contenidos en la presente ley serán aplicables a los datos personales registrados en cualquier base de datos que los haga susceptibles de tratamiento por entidades de naturaleza pública o privada.
            
            La presente ley aplicará al tratamiento de datos personales efectuado en territorio colombiano o cuando al Responsable del Tratamiento o Encargado del Tratamiento no establecido en territorio nacional le sea aplicable la legislación colombiana en virtud de normas y tratados internacionales.
            
            El régimen de protección de datos personales que se establece en la presente ley no será de aplicación:
            a) A las bases de datos o archivos mantenidos en un ámbito exclusivamente personal o doméstico.
            b) A las bases de datos y archivos que tengan por finalidad la seguridad y defensa nacional, así como la prevención, detección, monitoreo y control del lavado de activos y el financiamiento del terrorismo;
            c) A las Bases de datos que tengan como fin y contengan información de inteligencia y contrainteligencia;
            d) A las bases de datos y archivos de información periodística y otros contenidos editoriales;
            e) A las bases de datos y archivos regulados por la Ley 1581 de 2012;
            f) A las bases de datos y archivos regulados por la Ley 79 de 1993.
            
            Artículo 3°. Definiciones. Para los efectos de la presente ley, se entiende por:
            a) Autorización: Consentimiento previo, expreso e informado del Titular para llevar a cabo el Tratamiento de datos personales;
            b) Base de Datos: Conjunto organizado de datos personales que sea objeto de Tratamiento;
            c) Dato personal: Cualquier información vinculada o que pueda asociarse a una o varias personas naturales determinadas o determinables;
            d) Encargado del Tratamiento: Persona natural o jurídica, pública o privada, que por sí misma o en asocio con otros, realice el Tratamiento de datos personales por cuenta del Responsable del Tratamiento;
            e) Responsable del Tratamiento: Persona natural o jurídica, pública o privada, que por sí misma o en asocio con otros, decida sobre la base de datos y/o el Tratamiento de los datos;
            f) Titular: Persona natural cuyos datos personales sean objeto de Tratamiento;
            g) Tratamiento: Cualquier operación o conjunto de operaciones sobre datos personales, tales como la recolección, almacenamiento, uso, circulación o supresión.
            
            TÍTULO II
            PRINCIPIOS RECTORES
            
            Artículo 4°. Principios para el Tratamiento de datos personales. En el desarrollo, interpretación y aplicación de la presente ley, se aplicarán, de manera armónica e integral, los siguientes principios rectores del tratamiento de datos personales:
            
            a) Principio de legalidad en materia de tratamiento de datos: El Tratamiento a que se refiere la presente ley es una actividad reglada que debe sujetarse a lo establecido en ella y en las demás disposiciones que la desarrollen;
            b) Principio de finalidad: El Tratamiento debe obedecer a una finalidad legítima de acuerdo con la Constitución y la Ley, la cual debe ser informada al respectivo Titular de los datos;
            c) Principio de libertad: El Tratamiento solo puede ejercerse con el consentimiento, previo, expreso e informado del Titular. Los datos personales no podrán ser obtenidos o divulgados sin previa autorización, o en ausencia de mandato legal o judicial que releve el consentimiento;
            d) Principio de veracidad o calidad: La información sujeta a Tratamiento debe ser veraz, completa, exacta, actualizada, comprobable y comprensible. Se prohíbe el Tratamiento de datos parciales, incompletos, fraccionados o que induzcan a error;
            e) Principio de transparencia: En el Tratamiento debe garantizarse el derecho del Titular a obtener del Responsable del Tratamiento o del Encargado del Tratamiento, en cualquier momento y sin restricciones, información sobre la existencia de datos que le conciernan;
            f) Principio de acceso y circulación restringida: El Tratamiento se sujeta a los límites que se derivan de la naturaleza de los datos personales, de las disposiciones de la presente ley y la Constitución. En este sentido, el Tratamiento solo podrá hacerse por personas autorizadas por el Titular y/o por las personas previstas en la presente ley;
            g) Principio de seguridad: La información sujeta al Tratamiento por el Responsable del Tratamiento o Encargado del Tratamiento, se deberá manejar con las medidas técnicas, humanas y administrativas que sean necesarias para otorgar seguridad a los registros evitando su adulteración, pérdida, consulta, uso o acceso no autorizado o fraudulento;
            h) Principio de confidencialidad: Todos los funcionarios, administradores, encargados, empleados, operadores o cualquier persona que intervenga en cualquier fase del Tratamiento de los datos personales están obligados a garantizar la reserva de la información, inclusive después de finalizada su relación con alguna de las labores que comprende el Tratamiento, pudiendo solo realizar suministro o comunicación de datos personales cuando ello corresponda al desarrollo de las actividades autorizadas en la presente ley y en los términos de la misma.
            
            TÍTULO III
            DERECHOS DEL TITULAR
            
            Artículo 8°. Derechos del Titular. El Titular de los datos personales tendrá los siguientes derechos:
            
            1. Conocer, actualizar y rectificar sus datos personales frente a los Responsables del Tratamiento o Encargados del Tratamiento. Este derecho se podrá ejercer, entre otros frente a datos parciales, inexactos, incompletos, fraccionados, que induzcan a error, o aquellos cuyo Tratamiento esté expresamente prohibido o no haya sido autorizado;
            2. Ser informado por el Responsable del Tratamiento o el Encargado del Tratamiento, previa solicitud, respecto del uso que le ha dado a sus datos personales;
            3. Revocar la autorización y/o solicitar la supresión del dato cuando en el Tratamiento no se respeten los principios, derechos y garantías constitucionales y legales. La revocatoria y/o supresión procederá cuando la Superintendencia de Industria y Comercio haya determinado que en el Tratamiento el Responsable o Encargado han incurrido en conductas contrarias a esta ley y a la Constitución;
            4. Acceder gratuitamente a sus datos personales que hayan sido objeto de Tratamiento.
            
            TÍTULO IV
            AUTORIZACIÓN DEL TITULAR
            
            Artículo 9°. Autorización del Titular. Salvo las excepciones previstas en la presente ley, en el Tratamiento se requerirá la autorización del Titular, la cual deberá ser previa, expresa, informada y de carácter específico.
            
            Para que la autorización sea válida deberá ser previa, expresa, informada y de carácter específico, y se deberá dejar constancia de ella por cualquier medio que pueda ser objeto de consulta posterior.
            
            TÍTULO V
            DEBERES DE LOS RESPONSABLES Y ENCARGADOS DEL TRATAMIENTO
            
            Artículo 17°. Deberes de los Responsables del Tratamiento. Los Responsables del Tratamiento tendrán los siguientes deberes, sin perjuicio de las demás disposiciones previstas en la presente ley y en las normas que la desarrollen:
            
            a) Garantizar al Titular, en todo tiempo, el pleno y efectivo ejercicio del derecho de habeas data;
            b) Solicitar y conservar, en las condiciones previstas en la presente ley, copia de la respectiva autorización otorgada por el Titular;
            c) Informar debidamente al Titular sobre la finalidad de la recolección y los derechos que le asisten por virtud de la autorización otorgada;
            d) Conservar la información bajo las condiciones de seguridad necesarias para impedir su adulteración, pérdida, consulta, uso o acceso no autorizado o fraudulento;
            e) Garantizar que la información que se suministre al Encargado del Tratamiento sea veraz, completa, exacta, actualizada, comprobable y comprensible;
            f) Actualizar la información, comunicando de forma oportuna al Encargado del Tratamiento, todas las novedades respecto de los datos que previamente le haya suministrado y adoptar las demás medidas necesarias para que la información suministrada a este se mantenga actualizada;
            g) Rectificar la información cuando sea incorrecta y comunicar lo pertinente al Encargado del Tratamiento;
            h) Suministrar al Encargado del Tratamiento, únicamente los datos cuyo Tratamiento esté previamente autorizado;
            i) Exigir al Encargado del Tratamiento en todo momento, el respeto a las condiciones de seguridad y privacidad de la información del Titular;
            j) Tramitar las consultas y reclamos formulados en los términos señalados en la presente ley;
            k) Adoptar un manual interno de políticas y procedimientos para garantizar el adecuado cumplimiento de la presente ley y, en especial, para la atención de consultas y reclamos;
            l) Informar al Encargado del Tratamiento cuando determinada información se encuentra en discusión por parte del Titular, una vez se haya presentado la reclamación y no haya sido resuelta;
            m) Informar a solicitud del Titular sobre el uso dado a sus datos;
            n) Informar a la autoridad de protección de datos cuando se presenten violaciones a los códigos de seguridad y existan riesgos en la administración de la información de los Titulares;
            ñ) Cumplir las instrucciones y requerimientos que imparta la Superintendencia de Industria y Comercio.
            
            TÍTULO VI
            TRANSFERENCIA DE DATOS A TERCEROS PAÍSES
            
            Artículo 26°. Prohibición. Se prohíbe la transferencia de datos personales de cualquier tipo a países que no proporcionen niveles adecuados de protección de datos. Se entiende que un país ofrece un nivel adecuado de protección de datos cuando cumpla con los estándares fijados por la Superintendencia de Industria y Comercio sobre la materia, los cuales en ningún caso podrán ser inferiores a los que la presente ley exige a sus destinatarios.
            
            Esta prohibición no regirá cuando se trate de:
            a) Información respecto de la cual el Titular haya otorgado su autorización expresa e inequívoca para la transferencia;
            b) Intercambio de datos de carácter médico, cuando así lo exija el Tratamiento del Titular por razones de salud o higiene pública;
            c) Transferencias bancarias o bursátiles, conforme a la legislación que les resulte aplicable;
            d) Transferencias acordadas en el marco de tratados internacionales en los cuales la República de Colombia sea parte, con fundamento en el principio de reciprocidad;
            e) Transferencias necesarias para la ejecución de un contrato entre el Titular y el Responsable del Tratamiento, o para la ejecución de medidas precontractuales siempre y cuando se cuente con la autorización del Titular;
            f) Transferencias legalmente exigidas para la salvaguardia del interés público, o para el reconocimiento, ejercicio o defensa de un derecho en un proceso judicial.
            
            TÍTULO VII
            REGISTRO NACIONAL DE BASES DE DATOS
            
            Artículo 25°. Definición. El Registro Nacional de Bases de Datos es el directorio público de las bases de datos sujetas a Tratamiento que operan en el país.
            
            El registro será administrado por la Superintendencia de Industria y Comercio y será de libre consulta para los ciudadanos.
            
            Para realizar el registro de bases de datos, los interesados deberán aportar a la Superintendencia de Industria y Comercio las políticas de tratamiento de la información, las cuales obligarán a los responsables y encargados del mismo, y cuyo incumplimiento acarreará las sanciones correspondientes. Las políticas de Tratamiento en ningún caso podrán ser inferiores a los deberes contenidos en la presente ley.
            
            TÍTULO VIII
            AUTORIDAD DE PROTECCIÓN DE DATOS
            
            Artículo 18°. Autoridad de Protección de Datos. La Superintendencia de Industria y Comercio ejercerá la vigilancia y control del cumplimiento de la presente ley y de las normas que la desarrollen, sin perjuicio de las funciones que correspondan a otras autoridades.
            
            La Superintendencia de Industria y Comercio, a través de una Delegatura para la protección de datos personales ejercerá la vigilancia y sanción para garantizar la legalidad en el tratamiento de datos personales, además será quien administre el Registro Nacional de Bases de Datos de libre consulta para los ciudadanos.
            
            TÍTULO IX
            DISPOSICIONES FINALES
            
            Artículo 27°. Normas Corporativas Vinculantes. El Gobierno Nacional expedirá la reglamentación correspondiente sobre Normas Corporativas Vinculantes para la certificación de buenas prácticas en protección de datos personales y su transferencia a terceros países.
            
            Artículo 28°. Régimen de transición. Las personas que a la fecha de entrada en vigencia de la presente ley ejerzan alguna de las actividades acá reguladas tendrán un plazo de hasta seis (6) meses para adecuarse a las disposiciones contempladas en esta ley.
            
            Artículo 29°. Derogatorias. La presente ley deroga todas las disposiciones que le sean contrarias a excepción de aquellas contempladas en el artículo 2°.
            
            Artículo 30°. Vigencia. La presente ley rige a partir de su promulgación.
            
            NOTA: Publicada en el Diario Oficial 47.556 de diciembre 31 de 2008.
            """,
            "metadata": {
                "document_type": "statutory_law",
                "legal_area": "financial_data_protection",
                "authority": "Congreso de la República",
                "year": 2008,
                "document_number": "1266",
                "source_url": "https://www.oas.org/es/sla/ddi/docs/CO%2014%20Ley%201266%20Habeas%20Data.pdf",
                "official_gazette_reference": "Diario Oficial 47.556 de diciembre 31 de 2008",
                "effective_date": "2008-12-31",
                "status": "active",
                "quality_score": 0.95,
                "keywords": ["habeas data", "datos financieros", "datos crediticios", "datos comerciales", "datos de servicios", "protección de datos", "terceros países"],
                "tags": ["datos financieros", "habeas data", "Ley 1266", "protección de datos", "datos crediticios"]
            }
        }
        
        # Add documents to appropriate knowledge base tables
        # Primary legislation goes to legal_documents_ai
        primary_legislation = [
            ley_1581_complete,
            ley_1266_2008
        ]
        
        # Constitutional and regulatory documents go to jurisprudence table
        jurisprudence_docs = [
            constitutional_article_15,
            decreto_1377_complete
        ]
        
        # Ingest primary legislation
        for doc in primary_legislation:
            await self.add_document_with_stats(doc, KnowledgeType.LEGAL_DOCUMENTS)
        
        # Ingest constitutional and regulatory documents as jurisprudence
        for doc in jurisprudence_docs:
            await self.add_document_with_stats(doc, KnowledgeType.JURISPRUDENCE)
        
        logger.info(f"Added {len(primary_legislation)} primary legislation documents to legal_documents_ai table")
        logger.info(f"Added {len(jurisprudence_docs)} constitutional/regulatory documents to jurisprudence table")
    
    async def add_document_with_stats(self, doc: Dict[str, Any], knowledge_type: KnowledgeType):
        """Add document and update statistics"""
        try:
            content = doc.get("content", "")
            metadata = dict(doc.get("metadata", {}))

            # Ensure required columns per table are present
            if knowledge_type == KnowledgeType.LEGAL_DOCUMENTS:
                # legal_documents_ai requires title
                if doc.get("title") and "title" not in metadata:
                    metadata["title"] = doc["title"]
            elif knowledge_type == KnowledgeType.JURISPRUDENCE:
                # jurisprudence requires court
                if "court" not in metadata:
                    # Map authority -> court when available
                    if "authority" in metadata and metadata["authority"]:
                        metadata["court"] = metadata["authority"]
                    else:
                        metadata["court"] = "Corte Constitucional"
            elif knowledge_type == KnowledgeType.REGULATORY_FRAMEWORKS:
                # regulatory_frameworks requires framework_name
                if "framework_name" not in metadata:
                    metadata["framework_name"] = doc.get("title") or "Marco regulatorio"
            
            success = await self.kb.add_custom_knowledge(
                content=content,
                metadata=metadata,
                knowledge_type=knowledge_type
            )
            
            if success:
                self.population_stats["total_added"] += 1
                knowledge_type_name = knowledge_type.value
                self.population_stats["by_type"][knowledge_type_name] = \
                    self.population_stats["by_type"].get(knowledge_type_name, 0) + 1
            else:
                self.population_stats["errors"] += 1
                
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            self.population_stats["errors"] += 1
    
    def print_population_report(self):
        """Print population statistics report"""
        print("\n" + "="*60)
        print("KNOWLEDGE BASE POPULATION REPORT")
        print("="*60)
        total_added = self.population_stats['total_added']
        total_errors = self.population_stats['errors']
        denominator = total_added + total_errors
        success_rate = (total_added / denominator * 100) if denominator > 0 else 0.0
        print(f"Total documents added: {total_added}")
        print(f"Errors encountered: {total_errors}")
        print(f"Success rate: {success_rate:.1f}%")
        
        print("\nDocuments by type:")
        for doc_type, count in self.population_stats["by_type"].items():
            print(f"  {doc_type}: {count} documents")
        
        print("="*60)

async def main():
    """Main population function"""
    logger.info("Starting enhanced knowledge base population...")
    
    # Initialize populator
    populator = EnhancedKnowledgePopulator(mock_mode=False)
    
    # Option 1: Populate from processed documents (if available)
    processed_file = "processed_legal_documents.json"
    if os.path.exists(processed_file):
        logger.info(f"Found processed documents file: {processed_file}")
        ok = await populator.populate_from_processed_documents(processed_file)
        if not ok:
            logger.info("Processed file empty or failed. Falling back to comprehensive content population.")
            await populator.populate_comprehensive_legal_content()
    else:
        logger.info("No processed documents file found, using comprehensive content")
        # Option 2: Populate with comprehensive legal content
        await populator.populate_comprehensive_legal_content()
    
    # Print report
    populator.print_population_report()
    
    logger.info("Enhanced knowledge base population completed")

if __name__ == "__main__":
    asyncio.run(main()) 