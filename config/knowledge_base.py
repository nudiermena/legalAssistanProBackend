import os
from agno.knowledge.pdf_url import PDFUrlKnowledgeBase
from agno.knowledge.website import WebsiteKnowledgeBase
from agno.knowledge.combined import CombinedKnowledgeBase
from agno.vectordb.qdrant import Qdrant

# Vector database configuration
qdrant_api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.si5dt8LrrOg1cIngEUoDg15xVcqWmoq6fm9mJIfmDJA"
qdrant_url = "https://1a0aea0b-e070-4e05-981e-4a23be0d7150.us-west-2-0.aws.cloud.qdrant.io"
collection_name = "legal_documents"

# Initialize vector database
vector_db = Qdrant(
    collection=collection_name,
    url=qdrant_url,
    api_key=qdrant_api_key,
)

# Initialize knowledge bases
pdf_knowledge_base = PDFUrlKnowledgeBase(
    urls=["https://biblioteca.gafilat.org/wp-content/uploads/2024/07/Recomendaciones-metodologia-actDIC2023.pdf"],
    vector_db=vector_db
)

website_knowledge_base = WebsiteKnowledgeBase(
    urls=["https://www.supersociedades.gov.co/web/nuestra-entidad/cap-10-autocontrol-y-gesti%C3%B3n-del-riesgo-integral",
          "https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=175606",
          "https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=43292"
          ],
    vector_db=vector_db
)

# Combined knowledge base
knowledge_base = CombinedKnowledgeBase(
    sources=[pdf_knowledge_base, website_knowledge_base],
    vector_db=vector_db
)

def get_knowledge_base():
    """Get the combined knowledge base instance"""
    return knowledge_base 