#import os
# from agno.knowledge.pdf_url import PDFUrlKnowledgeBase
# from agno.knowledge.website import WebsiteKnowledgeBase
# from agno.knowledge.combined import CombinedKnowledgeBase
# from agno.vectordb.memory import MemoryVectorDB

# # Initialize in-memory vector database
# gt = MemoryVectorDB()

# # Initialize knowledge bases
# pdf_knowledge_base = PDFUrlKnowledgeBase(
#     urls=["https://biblioteca.gafilat.org/wp-content/uploads/2024/07/Recomendaciones-metodologia-actDIC2023.pdf"],
#     vector_db=vector_db
# )

# website_knowledge_base = WebsiteKnowledgeBase(
#     urls=["https://www.supersociedades.gov.co/web/nuestra-entidad/cap-10-autocontrol-y-gesti%C3%B3n-del-riesgo-integral",
#           "https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=175606",
#           "https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=43292"
#           ],
#     vector_db=vector_db
# )

# # Combined knowledge base
# knowledge_base = CombinedKnowledgeBase(
#     sources=[pdf_knowledge_base, website_knowledge_base],
#     vector_db=vector_db
# )

def get_knowledge_base():
    """Get the combined knowledge base instance"""
    return None 