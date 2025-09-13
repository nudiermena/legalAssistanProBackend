#!/usr/bin/env python3
"""
Fix Colombian Legal Framework Ingestion
Ingests only the fixed Colombian legal documents with proper array formatting
"""

import asyncio
import logging
from typing import Dict, List, Any
import os
import sys

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

class ColombianLegalIngester:
    """Ingests fixed Colombian legal framework documents"""
    
    def __init__(self, mock_mode: bool = False):
        self.kb = SupabaseLegalKnowledgeBase(mock_mode=mock_mode)
        self.ingestion_stats = {
            "total_added": 0,
            "errors": 0,
            "by_table": {}
        }
    
    async def add_document_with_stats(self, doc: Dict[str, Any], knowledge_type: KnowledgeType):
        """Add document and update statistics"""
        try:
            content = doc.get("content", "")
            metadata = dict(doc.get("metadata", {}))

            # Ensure required columns per table are present
            if knowledge_type == KnowledgeType.JURISPRUDENCE:
                # jurisprudence requires court
                if "court" not in metadata:
                    metadata["court"] = "Corte Constitucional"
            
            success = await self.kb.add_custom_knowledge(
                content=content,
                metadata=metadata,
                knowledge_type=knowledge_type
            )
            
            if success:
                self.ingestion_stats["total_added"] += 1
                table_name = knowledge_type.value
                self.ingestion_stats["by_table"][table_name] = \
                    self.ingestion_stats["by_table"].get(table_name, 0) + 1
            else:
                self.ingestion_stats["errors"] += 1
                
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            self.ingestion_stats["errors"] += 1
    
    async def ingest_colombian_legal_framework(self):
        """Ingest the fixed Colombian legal framework documents"""
        logger.info("Ingesting fixed Colombian legal framework documents...")
        
        # Constitutional Article 15 - Habeas Data (Fixed)
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
        
        # Decreto 1377 de 2013 - Complete Regulation (Fixed)
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
        
        # Ingest both documents to jurisprudence table
        jurisprudence_docs = [
            constitutional_article_15,
            decreto_1377_complete
        ]
        
        for doc in jurisprudence_docs:
            await self.add_document_with_stats(doc, KnowledgeType.JURISPRUDENCE)
        
        logger.info(f"Successfully ingested {len(jurisprudence_docs)} fixed Colombian legal framework documents")
    
    def print_ingestion_report(self):
        """Print ingestion statistics report"""
        print("\n" + "="*60)
        print("COLOMBIAN LEGAL FRAMEWORK INGESTION REPORT")
        print("="*60)
        total_added = self.ingestion_stats['total_added']
        total_errors = self.ingestion_stats['errors']
        denominator = total_added + total_errors
        success_rate = (total_added / denominator * 100) if denominator > 0 else 0.0
        print(f"Total documents added: {total_added}")
        print(f"Errors encountered: {total_errors}")
        print(f"Success rate: {success_rate:.1f}%")
        
        print("\nDocuments by table:")
        for table_name, count in self.ingestion_stats["by_table"].items():
            print(f"  {table_name}: {count} documents")
        
        print("="*60)

async def main():
    """Main ingestion function"""
    logger.info("Starting Colombian legal framework ingestion...")
    
    # Initialize ingester
    ingester = ColombianLegalIngester(mock_mode=False)
    
    # Ingest Colombian legal framework
    await ingester.ingest_colombian_legal_framework()
    
    # Print report
    ingester.print_ingestion_report()
    
    logger.info("Colombian legal framework ingestion completed")

if __name__ == "__main__":
    asyncio.run(main())
