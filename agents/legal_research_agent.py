from agno.agent import Agent
from agno.tools.googlesearch import GoogleSearchTools
from config.database import get_agent_storage
from config.ai_models import get_model
from config.knowledge_base import get_knowledge_base
from config.colombian_compliance import (
    ColombianLegalFramework,
    get_legal_term
)
from typing import Dict, List, Optional, Any
from datetime import datetime

def create_legal_research_agent() -> Agent:
    """Create a specialized agent for legal research"""
    return Agent(
        name="Investigador Jurídico",
        role="Especialista en investigación jurídica",
        model=get_model("legal_research"),
        knowledge=get_knowledge_base(),
        search_knowledge=True,
        storage=get_agent_storage("agent_sessions"),
        instructions=[
            "Realizar investigación jurídica profunda en derecho colombiano",
            "Analizar jurisprudencia y líneas jurisprudenciales de las Altas Cortes",
            "Identificar precedentes vinculantes y doctrina probable",
            "Examinar normatividad vigente y su evolución",
            "Citar fuentes jurídicas con precisión técnica",
            "Analizar conceptos de entidades administrativas",
            "Verificar vigencia y aplicabilidad de normas",
            "Considerar principios constitucionales relevantes",
            "Evaluar doctrina autorizada y conceptos jurídicos",
            "Identificar reformas legislativas recientes",
            "Analizar impacto de control constitucional",
            "Examinar precedentes administrativos aplicables",
            "Verificar interpretaciones vinculantes",
            "Considerar derecho comparado relevante",
            "Mantener enfoque en jurisdicción colombiana"
        ],
        markdown=True
    )

async def conduct_legal_research(
    research_topic: str,
    jurisdiction: str,
    specific_areas: Optional[List[str]] = None,
    data_processing: Optional[Dict[str, str]] = None,
    legal_terms: Optional[List[str]] = None,
    timeframe: str = None,
    case_law_only: bool = False
) -> Dict[str, Any]:
    """Realizar investigación jurídica exhaustiva sobre un tema específico"""
    agent = create_legal_research_agent()
    
    # Get Colombian legal terms if provided
    legal_terms_dict = {}
    if legal_terms:
        legal_terms_dict = {term: get_legal_term(term) for term in legal_terms if get_legal_term(term)}
    
    # Update prompt in Spanish
    prompt = f"""Realizar investigación jurídica exhaustiva sobre el siguiente tema:

TEMA: {research_topic}
JURISDICCIÓN: {jurisdiction}
"""

    if specific_areas:
        prompt += f"ÁREAS ESPECÍFICAS: {', '.join(specific_areas)}\n"
    
    if timeframe:
        prompt += f"PERÍODO DE ANÁLISIS: {timeframe}\n"
    
    if case_law_only:
        prompt += "Enfocarse únicamente en jurisprudencia, no en normatividad.\n"
    
    prompt += f"""
MARCO JURÍDICO COLOMBIANO:
- Principios Constitucionales: {', '.join(ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES)}
- Fuentes del Derecho:
  * Constitución Política
  * Leyes y Decretos
  * Jurisprudencia de Altas Cortes
  * Doctrina Autorizada
  * Conceptos Vinculantes
"""
    
    if legal_terms_dict:
        prompt += "\nTÉRMINOS JURÍDICOS RELEVANTES:\n"
        for term, definition in legal_terms_dict.items():
            prompt += f"- {term}: {definition}\n"
    
    # Run the research
    response = await agent.arun(prompt)
    
    # Structure the response in Spanish
    result = {
        "research_results": {
            "analisis_normativo": response.content,
            "jurisprudencia_relevante": [],
            "doctrina_aplicable": "",
            "recomendaciones": []
        },
        "legal_framework": {
            "leyes": [],
            "decretos": [],
            "resoluciones": []
        },
        "jurisprudence": [],
        "research_topic": research_topic,
        "jurisdiction": jurisdiction,
        "colombian_compliance": {
            "framework_version": ColombianLegalFramework.FRAMEWORK_VERSION,
            "constitutional_principles": ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES,
            "research_date": datetime.now().isoformat()
        }
    }
    
    if specific_areas:
        result["specific_areas"] = specific_areas
    
    if data_processing:
        result["data_processing"] = data_processing
    
    if legal_terms_dict:
        result["legal_terms"] = legal_terms_dict
    
    return result 