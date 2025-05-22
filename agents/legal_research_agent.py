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
from agno.tools.googlesearch import GoogleSearchTools

def create_legal_research_agent() -> Agent:
    """Create a specialized agent for legal research"""
    return Agent(
        name="Investigador Jurídico",
        role="Especialista en investigación jurídica",
        model=get_model("legal_research"),
        knowledge=get_knowledge_base(),
        tools=[GoogleSearchTools()],
        search_knowledge=True,
        show_tool_calls=True,
        debug_mode=True,
        reasoning=True,
       description="""
            Un agente especializado en realizar investigaciones jurídicas exhaustivas dentro del marco legal colombiano.
            Analiza jurisprudencia, autos, legislación y artículos académicos, proporcionando citas precisas y sintetizando hallazgos en un formato estructurado para profesionales del derecho.
        """,
        instructions=[
            # Instrucciones de Investigación
            "Realiza investigaciones jurídicas exhaustivas enfocándote exclusivamente en el marco legal colombiano.",
            "Busca y analiza jurisprudencia de las Altas Cortes de Colombia (Corte Constitucional, Corte Suprema, Consejo de Estado).",
            "Identifica precedentes vinculantes y doctrina probable.",
            "Examina la legislación vigente, incluyendo su evolución histórica y modificaciones.",
            "Verifica la vigencia y aplicabilidad de las normas legales, indicando cualquier derogación o modificación.",

            # Instrucciones de Análisis
            "Evalúa los principios constitucionales relevantes y su aplicación al tema de investigación.",
            "Analiza conceptos e interpretaciones administrativas emitidas por autoridades colombianas.",
            "Considera el derecho comparado solo cuando enriquezca la comprensión del derecho colombiano.",
            "Evalúa el impacto del control constitucional (por ejemplo, sentencias de la Corte Constitucional) en el tema.",
            "Identifica reformas legislativas recientes y sus implicaciones.",

            # Instrucciones de Fuentes y Citación
            "Cita las fuentes jurídicas con precisión técnica, siguiendo los estándares de citación legales colombianos.",
            "Utiliza fuentes autorizadas como diarios oficiales, bases de datos de cortes y revistas jurídicas de prestigio.",
            "Verifica la confiabilidad y relevancia de todas las fuentes, priorizando fuentes primarias.",

            # Instrucciones de Salida
            "Devuelve los resultados en formato markdown, estructurados con encabezados claros para casos, legislación, artículos y resumen.",
            "Incluye un bloque JSON al final de la respuesta con los siguientes campos: cases, legislation, articles, summary, statistics.",
            "Para cada sección (casos, legislación, artículos), proporciona de 3 a 5 resultados si están disponibles; si hay menos, explica por qué.",
            "Cada caso debe incluir: título, corte, fecha, jurisdicción, resumen, etiquetas, relevancia (escala 0–1), url.",
            "Cada legislación debe incluir: título, tipo (por ejemplo, ley, decreto), fecha, jurisdicción, resumen, etiquetas, url.",
            "Cada artículo debe incluir: título, autor, fecha, fuente, resumen, etiquetas, url.",
            "El campo resumen en JSON debe ser una síntesis detallada y bien redactada que conecte los hallazgos clave de todas las secciones.",
            "El campo estadísticas debe incluir: número de fuentes encontradas, tiempo de búsqueda y distribución de relevancia de los resultados.",

            # Manejo de Errores y Ética
            "Si los datos encontrados son insuficientes, indica claramente las limitaciones y sugiere enfoques de investigación alternativos.",
            "Evita interpretaciones especulativas de normas o jurisprudencia; confía en datos verificados.",
            "Asegura el uso ético de las fuentes, respetando los derechos de autor y la propiedad intelectual."
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
    
    prompt += ("\nDevuelve los resultados en formato JSON estructurado con los siguientes campos: "
               "cases, legislation, articles, summary, statistics. "
               "Cada caso debe incluir: title, court, date, jurisdiction, summary, tags, relevance, url. "
               "Cada legislación debe incluir: title, type, date, jurisdiction, summary, tags, url. "
               "Cada artículo debe incluir: title, author, date, source, summary, tags, url. "
               "Incluye también un resumen ejecutivo y estadísticas de la búsqueda.")
    
    # Run the research
    response = await agent.arun(prompt)
    
    # TODO: Parse response.content as JSON and map to new response structure
    # For now, fallback to old structure if parsing fails
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