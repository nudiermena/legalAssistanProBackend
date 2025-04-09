from agno.agent import Agent
from config.database import get_agent_storage
from config.ai_models import get_model
from config.knowledge_base import get_knowledge_base
from config.colombian_compliance import (
    ColombianLegalFramework,
    get_legal_term
)
from typing import Dict, List, Optional
from datetime import datetime

def create_legal_diagnosis_agent() -> Agent:
    """Create a specialized agent for legal diagnosis"""
    return Agent(
        name="Especialista en Diagnóstico Legal",
        role="Especialista en diagnóstico jurídico colombiano",
        model=get_model("legal"),
        knowledge=get_knowledge_base(),
        search_knowledge=True,
        storage=get_agent_storage("legal_sessions"),
        instructions=[
            "Analizar situaciones jurídicas bajo el marco legal colombiano",
            "Aplicar principios constitucionales y jurisprudencia de las Altas Cortes",
            "Identificar normativa aplicable y precedentes judiciales vinculantes",
            "Evaluar implicaciones constitucionales y derechos fundamentales",
            "Considerar doctrina legal y conceptos jurídicos de entidades competentes",
            "Proteger derechos del titular según Ley 1581 de 2012",
            "Garantizar cumplimiento del CPACA y procedimientos administrativos",
            "Proporcionar recomendaciones según jurisdicción y competencia",
            "Utilizar terminología jurídica del ordenamiento colombiano",
            "Citar fuentes normativas vigentes y aplicables",
            "Considerar términos y recursos procedentes",
            "Evaluar vías jurídicas disponibles (ordinaria, constitucional, administrativa)",
            "Analizar requisitos de procedibilidad aplicables",
            "Verificar legitimación en la causa y personería",
            "Recomendar medios de prueba pertinentes"
        ],
        markdown=True
    )

async def diagnose_legal_issue(
    situation_description: str,
    relevant_facts: List[str],
    jurisdiction: str,
    specific_concerns: Optional[List[str]] = None,
    legal_terms: Optional[List[str]] = None
) -> Dict[str, str]:
    """Analizar una situación jurídica y proporcionar un diagnóstico detallado"""
    agent = create_legal_diagnosis_agent()
    
    # Get Colombian legal terms if provided
    legal_term_definitions = {}
    if legal_terms:
        legal_term_definitions = {term: get_legal_term(term) for term in legal_terms if get_legal_term(term)}
    
    # Format facts for the prompt
    facts_text = "\n".join([f"- {fact}" for fact in relevant_facts])
    
    # Update prompt in Spanish
    prompt = f"""Analizar la siguiente situación jurídica:

SITUACIÓN:
{situation_description}

HECHOS RELEVANTES:
{facts_text}

JURISDICCIÓN: {jurisdiction}

Por favor proporcionar:
1. Identificación clara de los problemas jurídicos
2. Análisis de normatividad aplicable
3. Identificación de precedentes judiciales vinculantes
4. Evaluación de fortalezas y debilidades jurídicas
5. Riesgos y responsabilidades potenciales
6. Vías de acción recomendadas
7. Consideraciones de términos y plazos
8. Requisitos probatorios y procesales
9. Análisis de principios constitucionales aplicables
10. Requisitos de procedimientos administrativos
11. Consideraciones de protección de datos personales
12. Implicaciones de derechos fundamentales
13. Análisis de legitimación y personería
14. Evaluación de jurisdicción y competencia
15. Recomendaciones sobre medios de prueba
"""
    
    if specific_concerns:
        prompt += f"\nPREOCUPACIONES ESPECÍFICAS:\n{', '.join(specific_concerns)}\n"
    
    # Add Colombian legal framework requirements in Spanish
    prompt += f"""
MARCO JURÍDICO COLOMBIANO:
- Principios Constitucionales: {', '.join(ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES)}
- Vías Jurídicas Disponibles:
  * Ordinaria (civil, laboral, administrativa)
  * Constitucional (tutela, acción popular)
  * Administrativa (recursos, revocatoria)
- Requisitos de Procedibilidad:
  * Agotamiento de vía gubernativa
  * Conciliación prejudicial
  * Reclamación previa
"""
    
    if legal_term_definitions:
        prompt += "\nTÉRMINOS JURÍDICOS RELEVANTES:\n"
        for term, definition in legal_term_definitions.items():
            prompt += f"- {term}: {definition}\n"
    
    prompt += """
El diagnóstico debe incluir:
1. Fundamentos constitucionales aplicables
2. Normatividad específica vigente
3. Jurisprudencia vinculante relevante
4. Doctrina legal autorizada
5. Conceptos de entidades competentes
6. Términos y recursos procedentes
7. Requisitos probatorios aplicables
8. Consideraciones de caducidad y prescripción
9. Análisis de competencia territorial
10. Evaluación de procedimientos especiales
11. Recomendaciones de actuación inmediata
12. Riesgos procesales identificados

Presentar el análisis en formato jurídico profesional.
"""
    
    # Run the diagnosis
    response = agent.run(prompt)
    
    # Structure the response in Spanish
    result = {
        "diagnostico": response.content,
        "situacion": situation_description,
        "jurisdiccion": jurisdiction,
        "hechos_relevantes": relevant_facts,
        "cumplimiento_colombiano": {
            "principios_constitucionales": ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES,
            "fecha_diagnostico": datetime.now().isoformat()
        }
    }
    
    if specific_concerns:
        result["preocupaciones_especificas"] = specific_concerns
    
    if legal_term_definitions:
        result["terminos_juridicos"] = legal_term_definitions
    
    return result 