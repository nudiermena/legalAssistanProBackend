"""
Supabase Knowledge Base Integration for Legal AI Agents
Integrates with Agno framework for enhanced legal knowledge retrieval
"""

import os as os_module
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass
from enum import Enum

from supabase import create_client, Client

# Use the correct agno imports that are actually available
from agno.vectordb.pgvector import PgVector, SearchType
from agno.knowledge.pdf_url import PDFUrlKnowledgeBase
from agno.knowledge.website import WebsiteKnowledgeBase
from agno.knowledge.combined import CombinedKnowledgeBase
from agno.knowledge.text import TextKnowledgeBase
from agno.knowledge.docx import DocxKnowledgeBase

# Add Mistral import
from mistralai import Mistral

logger = logging.getLogger(__name__)

class KnowledgeType(Enum):
    """Types of legal knowledge"""
    LEGAL_DOCUMENTS = "legal_documents_ai"
    JURISPRUDENCE = "jurisprudence"
    LEGAL_TERMS = "legal_terms"
    REGULATORY_FRAMEWORKS = "regulatory_frameworks"
    CONTRACT_KNOWLEDGE = "contract_knowledge"
    PATENT_KNOWLEDGE = "patent_knowledge"
    CASE_PREDICTION_KNOWLEDGE = "case_prediction_knowledge"
    COMPLIANCE_KNOWLEDGE = "compliance_knowledge"
    DOCUMENT_TEMPLATES = "document_templates"

class AgentType(Enum):
    """Types of agents"""
    CONTRACT = "contract_agent"
    LEGAL_RESEARCH = "legal_research_agent"
    PATENT = "patent_agent"
    CASE_PREDICTION = "case_prediction_agent"
    DOCUMENT_DRAFTING = "document_drafting_agent"
    COMPLIANCE = "compliance_agent"
    CHATBOT = "chatbot_agent"
    DEMAND_LETTER = "demand_letter_agent"
    WHISTLEBLOWER = "whistleblower_agent"
    LEGAL_DIAGNOSIS = "legal_diagnosis_agent"
    REGULATORY = "regulatory_agent"

@dataclass
class KnowledgeSearchResult:
    """Result from knowledge base search"""
    content: str
    metadata: Dict[str, Any]
    score: float
    source: str
    knowledge_type: KnowledgeType

class MockKnowledgeBase:
    """Mock knowledge base for testing without Supabase connection"""
    
    def __init__(self):
        self.mock_data = {
            "legal_terms": {
                "habeas data": "Derecho constitucional que protege la intimidad y el buen nombre de las personas, así como el conocimiento y actualización de las informaciones que sobre ellas se registren en bancos de datos.",
                "due process": "Garantía constitucional que asegura que toda persona tiene derecho a un proceso justo y equitativo.",
                "contract": "Acuerdo de voluntades entre dos o más personas para crear, modificar o extinguir obligaciones.",
                "obligation": "Vínculo jurídico por virtud del cual una parte debe dar, hacer o no hacer algo en favor de otra.",
                "liability": "Responsabilidad legal por los daños causados a terceros."
            },
            "jurisprudence": [
                {
                    "content": "La Corte Constitucional ha establecido que el habeas data es un derecho fundamental que protege la intimidad personal y familiar.",
                    "metadata": {"court": "Corte Constitucional", "topic": "habeas data"},
                    "score": 0.95,
                    "source": "Sentencia C-1008/2010"
                },
                {
                    "content": "El debido proceso es una garantía fundamental que debe observarse en todo procedimiento judicial o administrativo.",
                    "metadata": {"court": "Corte Constitucional", "topic": "due process"},
                    "score": 0.92,
                    "source": "Sentencia C-254 de 2012"
                }
            ],
            "contract_clauses": [
                {
                    "content": "Cláusula de confidencialidad: Las partes se comprometen a mantener la confidencialidad de la información compartida.",
                    "metadata": {"clause_type": "confidencialidad"},
                    "score": 0.88,
                    "source": "Modelo de contrato"
                }
            ]
        }
    
    async def search_knowledge(self, query: str, limit: int = 10, knowledge_type: Optional[KnowledgeType] = None) -> Dict[str, Any]:
        """Mock search implementation"""
        results = []
        
        # Search in legal terms
        if "habeas data" in query.lower():
            results.append({
                "content": self.mock_data["legal_terms"]["habeas data"],
                "metadata": {"type": "legal_term", "term": "habeas data"},
                "score": 0.95,
                "source": "Constitución Política",
                "knowledge_type": "legal_terms"
            })
        
        if "due process" in query.lower():
            results.append({
                "content": self.mock_data["legal_terms"]["due process"],
                "metadata": {"type": "legal_term", "term": "due process"},
                "score": 0.92,
                "source": "Constitución Política",
                "knowledge_type": "legal_terms"
            })
        
        # Search in jurisprudence
        if "jurisprudencia" in query.lower():
            results.extend(self.mock_data["jurisprudence"])
        
        # Search in contract clauses
        if "contrato" in query.lower() or "cláusula" in query.lower():
            results.extend(self.mock_data["contract_clauses"])
        
        return {
            "results": results[:limit],
            "query": query,
            "total_results": len(results),
            "search_timestamp": datetime.now().isoformat()
        }
    
    async def get_legal_terms(self, terms: List[str]) -> Dict[str, str]:
        """Mock legal terms lookup"""
        definitions = {}
        for term in terms:
            if term in self.mock_data["legal_terms"]:
                definitions[term] = self.mock_data["legal_terms"][term]
            else:
                definitions[term] = f"Definición no encontrada para '{term}'"
        return definitions
    
    async def get_jurisprudence(self, topic: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Mock jurisprudence lookup"""
        return self.mock_data["jurisprudence"][:limit]
    
    async def get_contract_clauses(self) -> List[Dict[str, Any]]:
        """Mock contract clauses lookup"""
        return self.mock_data["contract_clauses"]
    
    async def get_document_templates(self, document_type: str = None, complexity: str = "standard") -> List[Dict[str, Any]]:
        """Mock document templates lookup"""
        return [{
            "content": f"Plantilla de {document_type or 'documento legal'} con complejidad {complexity}",
            "metadata": {"document_type": document_type, "complexity": complexity},
            "score": 0.85,
            "source": "Base de plantillas"
        }]
    
    async def get_agent_specific_knowledge(self, agent_type: str) -> List[Dict[str, Any]]:
        """Mock agent-specific knowledge lookup"""
        return [{
            "content": f"Conocimiento específico para {agent_type}",
            "metadata": {"agent_type": agent_type},
            "score": 0.90,
            "source": "Base de conocimiento"
        }]

class SupabaseLegalKnowledgeBase:
    """Supabase-based legal knowledge base for Colombian law"""
    
    def __init__(self, 
                 supabase_url: str = None,
                 supabase_key: str = None,
                 mistral_api_key: str = None,
                 embedding_model: str = "mistral-embed",
                 mock_mode: bool = False):
        """
        Initialize the legal knowledge base
        
        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase service role key
            mistral_api_key: Mistral API key for embeddings
            embedding_model: Mistral embedding model to use
            mock_mode: Whether to use mock mode for testing
        """
        self.mock_mode = mock_mode
        
        if mock_mode:
            # Use mock implementation
            self.kb = MockKnowledgeBase()
            logger.info("Supabase Legal Knowledge Base initialized in MOCK mode")
            return
        
        # Resolve credentials from args → env → settings.py
        self.supabase_url = supabase_url or os_module.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os_module.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.mistral_api_key = mistral_api_key or os_module.getenv("MISTRAL_API_KEY")

        # Fallback to config.settings if env not set
        if not self.supabase_url or not self.supabase_key or not self.mistral_api_key:
            try:
                from config.settings import SUPABASE_URL as _SET_SUPABASE_URL
                from config.settings import SUPABASE_SERVICE_ROLE_KEY as _SET_SERVICE_ROLE
                from config.settings import MISTRAL_API_KEY as _SET_MISTRAL_KEY
                self.supabase_url = self.supabase_url or _SET_SUPABASE_URL
                self.supabase_key = self.supabase_key or _SET_SERVICE_ROLE
                self.mistral_api_key = self.mistral_api_key or _SET_MISTRAL_KEY
            except Exception:
                pass
        self.embedding_model = embedding_model
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL and key are required")
        
        if not self.mistral_api_key:
            raise ValueError("Mistral API key is required for embeddings")
        
        # Initialize Supabase client
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        # Initialize Mistral client
        self.mistral_client = Mistral(api_key=self.mistral_api_key)
        
        # Initialize Mistral embedder first
        from agno.embedder.mistral import MistralEmbedder
        mistral_embedder = MistralEmbedder(
            api_key=self.mistral_api_key
        )
        
        # Initialize PgVector for vector search
        # Prefer configured POSTGRES_URL; fall back to constructing from Supabase URL
        try:
            from config.settings import POSTGRES_URL as _SET_POSTGRES_URL
        except Exception:
            _SET_POSTGRES_URL = None

        if _SET_POSTGRES_URL:
            if _SET_POSTGRES_URL.startswith("postgresql+psycopg://"):
                db_url = _SET_POSTGRES_URL
            elif _SET_POSTGRES_URL.startswith("postgresql://"):
                db_url = _SET_POSTGRES_URL.replace("postgresql://", "postgresql+psycopg://", 1)
            else:
                db_url = _SET_POSTGRES_URL
        else:
            db_url = f"postgresql+psycopg://postgres:{self.supabase_key.split('.')[0]}@{self.supabase_url.replace('https://', '').replace('.supabase.co', '.supabase.co:5432')}/postgres"
        
        self.vector_db = PgVector(
            table_name="legal_documents_ai_pgvector",  # Use the view that maps to PgVector expectations
            db_url=db_url,
            search_type=SearchType.hybrid,
            embedder=mistral_embedder  # Explicitly pass the embedder
        )
        
        # Define legal sources and text documents here
        legal_sources = {
            "pdfs": [
                # Datos, SARLAFT/SAGRILAFT/LAFT
                "https://biblioteca.gafilat.org/wp-content/uploads/2024/07/Recomendaciones-metodologia-actDIC2023.pdf",
                "https://expoganados.com/wp-content/uploads/2022/07/Manual-SAGRILAFT.pdf",
                # Compilaciones y guías públicas
                "https://www.mintic.gov.co/portal/715/articles-183824_guia_PDP.pdf",
                "https://www.mineducacion.gov.co/1759/articles-356126_PDF.pdf"
            ],
            "websites": [
                # Normativa y diario oficial (Función Pública)
                "https://www.funcionpublica.gov.co/eva/gestornormativo/",
                "https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=175606",
                "https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=43292",
                # Altas cortes
                "https://www.corteconstitucional.gov.co/",
                "https://www.consejodeestado.gov.co/",
                "https://www.cortesuprema.gov.co/",
                # Rama Judicial (jurisprudencia, acuerdos)
                "https://www.ramajudicial.gov.co/",
                # Entidades de control y regulación
                "https://www.superfinanciera.gov.co/",
                "https://www.sic.gov.co/",
                "https://www.supersociedades.gov.co/",
                "https://www.uiaf.gov.co/",
                "https://www.minjusticia.gov.co/",
                "https://www.mintrabajo.gov.co/",
                # Congreso Visible (seguimiento legislativo)
                "https://www.congresovisible.org/"
            ]
        }
        
        # Define text documents for TextKnowledgeBase
        text_documents = [
            "Constitución Política de Colombia - Artículo 15: Todas las personas tienen derecho a su intimidad personal y familiar y a su buen nombre.",
            "Código Civil Colombiano - Artículo 1502: Por el contrato de compraventa uno de los contratantes se obliga a entregar una cosa determinada y el otro a pagar por ella un precio cierto en dinero.",
            "Ley 1581 de 2012 - Protección de Datos Personales: Regula el derecho de habeas data y la protección de datos personales en Colombia."
        ]
        
        # Initialize knowledge bases with explicit Mistral embedder
        try:
            
            # Create knowledge bases with explicit embedder parameter
            self.pdf_knowledge = PDFUrlKnowledgeBase(
                urls=legal_sources["pdfs"],
                vector_db=self.vector_db,
                embedder=mistral_embedder  # Explicitly pass embedder
            )
            
            self.website_knowledge = WebsiteKnowledgeBase(
                urls=legal_sources["websites"],
                vector_db=self.vector_db,
                embedder=mistral_embedder  # Explicitly pass embedder
            )
            
            self.combined_knowledge = CombinedKnowledgeBase(
                sources=[self.pdf_knowledge, self.website_knowledge],
                vector_db=self.vector_db,
                embedder=mistral_embedder  # Explicitly pass embedder
            )
            
            # Initialize text knowledge base with explicit embedder
            # Create a temporary file with the text documents for TextKnowledgeBase
            import tempfile
            import os
            
            # Create a temporary directory for text documents
            temp_dir = tempfile.mkdtemp()
            text_file_path = os_module.path.join(temp_dir, "legal_documents.txt")
            
            # Write text documents to file
            with open(text_file_path, 'w', encoding='utf-8') as f:
                for doc in text_documents:
                    f.write(doc + "\n\n")
            
            self.text_knowledge = TextKnowledgeBase(
                path=text_file_path,  # Use path instead of texts
                vector_db=self.vector_db,
                embedder=mistral_embedder  # Explicitly pass embedder
            )
            
            # Initialize DOCX knowledge base with explicit embedder
            if hasattr(self, 'db_url') and self.db_url:
                try:
                    from agno.knowledge.docx import DocxKnowledgeBase
                    self.docx_knowledge = DocxKnowledgeBase(
                        folder_path="documents",
                        vector_db=self.vector_db,
                        embedder=mistral_embedder  # Explicitly pass embedder
                    )
                    logger.info("DOCX knowledge base initialized with Mistral embedder")
                except Exception as e:
                    logger.warning(f"Failed to initialize DOCX knowledge base: {e}")
                    self.docx_knowledge = None
            else:
                self.docx_knowledge = None
            
            logger.info("Supabase Legal Knowledge Base initialized with explicit Mistral embedder following Agno docs pattern")
            
        except Exception as e:
            logger.error(f"Failed to initialize knowledge bases with Mistral embedder: {e}")
            # Fallback to default embedder
            self.pdf_knowledge = None
            self.website_knowledge = None
            self.combined_knowledge = None
            self.text_knowledge = None
            self.docx_knowledge = None
    

    
    async def search_knowledge(self, query: str, limit: int = 10, knowledge_type: Optional[KnowledgeType] = None) -> Dict[str, Any]:
        """
        Search knowledge base for relevant information
        
        Args:
            query: Search query
            limit: Maximum number of results
            knowledge_type: Specific type of knowledge to search
            
        Returns:
            Dictionary with search results
        """
        if self.mock_mode:
            return await self.kb.search_knowledge(query, limit, knowledge_type)
        
        try:
            # Use the combined knowledge base for search (support sync/async)
            if hasattr(self.combined_knowledge, "asearch"):
                results = await self.combined_knowledge.asearch(query, limit=limit)
            else:
                results = await asyncio.to_thread(self.combined_knowledge.search, query, limit)
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "content": result.content,
                    "metadata": result.metadata,
                    "score": result.score,
                    "source": result.source,
                    "knowledge_type": knowledge_type.value if knowledge_type else "general"
                })
            
            return {
                "results": formatted_results,
                "query": query,
                "total_results": len(formatted_results),
                "search_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return {
                "results": [],
                "query": query,
                "total_results": 0,
                "error": str(e),
                "search_timestamp": datetime.now().isoformat()
            }
    
    async def get_legal_terms(self, terms: List[str]) -> Dict[str, str]:
        """
        Get definitions for legal terms
        
        Args:
            terms: List of legal terms to look up
            
        Returns:
            Dictionary mapping terms to definitions
        """
        if self.mock_mode:
            return await self.kb.get_legal_terms(terms)
        
        try:
            definitions = {}
            
            # Use direct table access for legal terms
            for term in terms:
                try:
                    response = self.supabase.table("legal_terms").select("definition").eq("term", term).execute()
                    if response.data:
                        definitions[term] = response.data[0]["definition"]
                    else:
                        definitions[term] = f"Definición no encontrada para '{term}'"
                except Exception as term_error:
                    logger.warning(f"Error looking up term '{term}': {term_error}")
                    definitions[term] = f"Error al buscar definición para '{term}'"
            
            return definitions
            
        except Exception as e:
            logger.error(f"Error getting legal terms: {e}")
            return {term: f"Error al buscar definición para '{term}'" for term in terms}
    
    async def get_jurisprudence(self, topic: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get relevant jurisprudence for a topic
        
        Args:
            topic: Legal topic
            limit: Maximum number of results
            
        Returns:
            List of jurisprudence results
        """
        if self.mock_mode:
            return await self.kb.get_jurisprudence(topic, limit)
        
        try:
            results = await self.search_knowledge(f"jurisprudencia {topic}", limit=limit)
            return results["results"]
            
        except Exception as e:
            logger.error(f"Error getting jurisprudence: {e}")
            return []
    
    async def get_contract_clauses(self) -> List[Dict[str, Any]]:
        """
        Get contract clauses and templates
        
        Returns:
            List of contract clauses
        """
        if self.mock_mode:
            return await self.kb.get_contract_clauses()
        
        try:
            # Use direct table access for contract clauses
            response = self.supabase.table("contract_knowledge").select("*").execute()
            return response.data
            
        except Exception as e:
            logger.error(f"Error getting contract clauses: {e}")
            # Fallback to search if direct access fails
            try:
                results = await self.search_knowledge("cláusulas contractuales", limit=10)
                return results["results"]
            except Exception as search_error:
                logger.error(f"Error in fallback search: {search_error}")
                return []
    
    async def get_document_templates(self, document_type: str = None, complexity: str = "standard") -> List[Dict[str, Any]]:
        """
        Get document templates
        
        Args:
            document_type: Type of document
            complexity: Complexity level
            
        Returns:
            List of document templates
        """
        if self.mock_mode:
            return await self.kb.get_document_templates(document_type, complexity)
        
        try:
            # Use direct table access instead of search
            query = self.supabase.table("document_templates").select("*")
            
            if document_type:
                query = query.eq("document_type", document_type)
            if complexity:
                query = query.eq("complexity_level", complexity)
            
            response = query.execute()
            return response.data
            
        except Exception as e:
            logger.error(f"Error getting document templates: {e}")
            # Fallback to search if direct access fails
            try:
                query = f"plantilla documento {document_type or 'legal'}"
                if complexity != "standard":
                    query += f" {complexity}"
                
                results = await self.search_knowledge(query, limit=10)
                return results["results"]
            except Exception as search_error:
                logger.error(f"Error in fallback search: {search_error}")
                return []
    
    async def get_agent_specific_knowledge(self, agent_type: str) -> List[Dict[str, Any]]:
        """
        Get knowledge specific to an agent type
        
        Args:
            agent_type: Type of agent
            
        Returns:
            List of agent-specific knowledge
        """
        if self.mock_mode:
            return await self.kb.get_agent_specific_knowledge(agent_type)
        
        try:
            # Map agent types to relevant search terms
            agent_queries = {
                "contract_agent": "contratos Colombia cláusulas CGP obligaciones buena fe Código Civil Ley 820 2003",
                "legal_research_agent": "jurisprudencia Colombia Corte Constitucional Consejo de Estado Corte Suprema doctrina",
                "patent_agent": "patentes Colombia SIC Decisión 486 CAN novedad nivel inventivo aplicación industrial",
                "case_prediction_agent": "jurisprudencia tendencias Colombia tasa éxito precedentes líneas jurisprudenciales",
                "compliance_agent": "cumplimiento normativo Colombia SIC SAGRILAFT LAFT protección de datos Ley 1581 Decreto 1377",
                "document_drafting_agent": "plantillas documentos legales Colombia tutela derecho de petición contratos",
                "chatbot_agent": "derecho colombiano definiciones conceptos básicos constitucional civil laboral administrativo",
                "demand_letter_agent": "cobros requerimientos jurídicos Colombia mora incumplimiento modelos carta",
                "whistleblower_agent": "denuncias internas Colombia protección informantes cumplimiento sanciones",
                "legal_diagnosis_agent": "diagnóstico legal Colombia competencia jurisdicción términos caducidad prescripción",
                "regulatory_agent": "marco regulatorio Colombia entes de control circulares resoluciones normas sectoriales"
            }
            
            query = agent_queries.get(agent_type, "derecho colombiano")
            results = await self.search_knowledge(query, limit=5)
            return results["results"]
            
        except Exception as e:
            logger.error(f"Error getting agent-specific knowledge: {e}")
            return []
    
    def _format_arrays_for_postgres(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format arrays for PostgreSQL insertion"""
        formatted_data = {}
        for key, value in data.items():
            if isinstance(value, list):
                # Convert Python list to PostgreSQL array format
                # PostgreSQL expects: {item1,item2,item3}
                formatted_items = []
                for item in value:
                    if isinstance(item, str):
                        # Escape single quotes and wrap in quotes
                        escaped_item = item.replace("'", "''")
                        formatted_items.append(f"'{escaped_item}'")
                    else:
                        formatted_items.append(str(item))
                formatted_data[key] = "{" + ",".join(formatted_items) + "}"
            else:
                formatted_data[key] = value
        return formatted_data

    async def add_custom_knowledge(self, content: str, metadata: Dict[str, Any], knowledge_type: KnowledgeType) -> bool:
        """
        Add custom knowledge to the base
        
        Args:
            content: Knowledge content
            metadata: Additional metadata
            knowledge_type: Type of knowledge
            
        Returns:
            Success status
        """
        if self.mock_mode:
            return True  # Mock always succeeds
        
        try:
            # Ensure content is a string
            if isinstance(content, list):
                content = str(content)
            elif not isinstance(content, str):
                content = str(content)
            
            # Map knowledge type to table name and content column
            table_mapping = {
                KnowledgeType.LEGAL_DOCUMENTS: ("legal_documents_ai", "content"),
                KnowledgeType.JURISPRUDENCE: ("jurisprudence", "full_text"),
                KnowledgeType.LEGAL_TERMS: ("legal_terms", "definition"),
                KnowledgeType.REGULATORY_FRAMEWORKS: ("regulatory_frameworks", "description"),
                KnowledgeType.CONTRACT_KNOWLEDGE: ("contract_knowledge", "standard_clause"),
                KnowledgeType.PATENT_KNOWLEDGE: ("patent_knowledge", "requirements"),
                KnowledgeType.CASE_PREDICTION_KNOWLEDGE: ("case_prediction_knowledge", "success_factors"),
                KnowledgeType.COMPLIANCE_KNOWLEDGE: ("compliance_knowledge", "requirements"),
                KnowledgeType.DOCUMENT_TEMPLATES: ("document_templates", "template_content")
            }
            
            table_name, content_column = table_mapping.get(knowledge_type, ("legal_documents_ai", "content"))

            # Whitelist allowed columns per table to avoid 400s from schema mismatch
            allowed_columns_by_table = {
                "legal_documents_ai": {
                    "title", "document_type", "document_number", "year", "jurisdiction",
                    "summary", "keywords", "tags", "source_url", "official_gazette_reference",
                    "effective_date", "amendment_date", "status"
                },
                "jurisprudence": {
                    "case_number", "court", "decision_type", "decision_date", "topic",
                    "summary", "key_holdings", "legal_principles", "cited_laws",
                    "cited_precedents", "relevance_score", "tags", "source_url"
                },
                "legal_terms": {
                    "term", "definition", "legal_area", "source_document", "related_terms", "examples"
                },
                "regulatory_frameworks": {
                    "framework_name", "sector", "description", "applicable_laws",
                    "compliance_requirements", "authority", "effective_date", "status"
                },
                "contract_knowledge": {
                    "clause_type", "standard_clause", "legal_requirements", "risk_factors",
                    "recommended_language", "applicable_laws", "jurisprudence_references",
                    "industry_specific_considerations"
                },
                "patent_knowledge": {
                    "patent_type", "requirements", "protection_period", "application_requirements",
                    "examination_criteria", "international_treaties", "sic_requirements",
                    "technical_classifications"
                },
                "case_prediction_knowledge": {
                    "case_type", "success_factors", "risk_factors", "average_duration_months",
                    "success_rate", "key_precedents", "procedural_requirements", "evidence_requirements"
                },
                "compliance_knowledge": {
                    "compliance_area", "applicable_laws", "requirements", "penalties",
                    "compliance_procedures", "documentation_requirements", "audit_requirements"
                },
                "document_templates": {
                    "template_name", "document_type", "template_content", "required_sections",
                    "optional_sections", "legal_requirements", "jurisdiction", "industry_specific",
                    "industry", "complexity_level"
                }
            }
            
            # Get embedding for the content
            embeddings = self._get_mistral_embedding([content])
            vector_str = None
            if embeddings and len(embeddings) > 0:
                # Format vector for PostgreSQL
                vector_str = self._format_vector_for_postgres(embeddings[0])
            
            # Prepare data for insertion; filter metadata to allowed columns
            allowed = allowed_columns_by_table.get(table_name, set())
            filtered_metadata = {k: v for k, v in metadata.items() if k in allowed}
            data = {content_column: content, **filtered_metadata}
            
            # Add vector embedding if available
            if vector_str:
                data["vector_embedding"] = vector_str
            
            # Format arrays properly for PostgreSQL
            data = self._format_arrays_for_postgres(data)
            
            # Insert into appropriate table
            response = self.supabase.table(table_name).insert(data).execute()
            
            if response.data:
                logger.info(f"Successfully added knowledge to {table_name}")
                return True
            else:
                logger.error(f"Failed to add knowledge to {table_name}")
                return False
            
        except Exception as e:
            logger.error(f"Error adding custom knowledge: {e}")
            return False
    
    async def load_knowledge(self, recreate: bool = False) -> bool:
        """
        Load knowledge into the vector database
        
        Args:
            recreate: Whether to recreate the knowledge base
            
        Returns:
            Success status
        """
        if self.mock_mode:
            return True  # Mock always succeeds
        
        try:
            # Load combined knowledge base
            await self.combined_knowledge.aload(recreate=recreate, upsert=True)
            logger.info("Knowledge base loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
            return False

    def _get_mistral_embedding(self, texts: list) -> list:
        """Get embeddings from Mistral API"""
        try:
            response = self.mistral_client.embeddings.create(
                model=self.embedding_model,
                inputs=texts  # Changed from 'input' to 'inputs'
            )
            # Return the embedding values as a list
            return [embedding.embedding for embedding in response.data]
        except Exception as e:
            logger.error(f"Error getting Mistral embedding: {e}")
            # Return zero vectors as fallback
            return [[0.0] * 1024 for _ in texts]

    def _format_vector_for_postgres(self, vector: list) -> str:
        """Format vector for PostgreSQL pgvector insertion"""
        # Convert list to PostgreSQL vector format: [0.1,0.2,0.3,...]
        return "[" + ",".join([str(x) for x in vector]) + "]"

def create_supabase_knowledge_base(mock_mode: bool = False) -> SupabaseLegalKnowledgeBase:
    """Create a Supabase knowledge base instance"""
    return SupabaseLegalKnowledgeBase(mock_mode=mock_mode) 