from agno.agent import Agent
from agno.tools.googlesearch import GoogleSearchTools
from config.database import get_agent_storage
from config.ai_models import get_model
from config.knowledge_base import get_knowledge_base
from config.colombian_compliance import (
    ColombianIPFramework,
    get_ip_requirements,
    get_ip_protection_period,
    ColombianLegalFramework,
    get_legal_term,
    get_data_category,
    validate_consent
)
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class QueryGenerator:
    def generate_patent_queries(self, invention_description: str, technical_features: list, relevant_fields: list = None) -> list:
        """Generate search queries for patent search based on invention description and features"""
        queries = []
        
        # Basic query from description
        queries.append(invention_description[:100])
        
        # Queries from technical features
        for feature in technical_features:
            queries.append(feature)
            
        # Combine features with fields if provided
        if relevant_fields:
            for field in relevant_fields:
                for feature in technical_features[:2]:  # Limit combinations
                    queries.append(f"{field} {feature}")
        
        return queries[:5]  # Limit to 5 queries

def create_patent_agent() -> Agent:
    """Create a specialized agent for patent analysis"""
    return Agent(
        name="Especialista en Propiedad Industrial",
        role="Especialista en derecho de patentes colombiano",
        model=get_model("patent"),
        knowledge=get_knowledge_base(),
        search_knowledge=True,
        storage=get_agent_storage("patent_sessions"),
        instructions=[
            "Analizar patentabilidad según Decisión 486 CAN",
            "Aplicar normativa de la SIC y propiedad industrial",
            "Evaluar requisitos de novedad, nivel inventivo y aplicación industrial",
            "Considerar excepciones y exclusiones de patentabilidad",
            "Verificar requisitos formales ante la SIC",
            "Proteger secretos empresariales según Ley 256 de 1996",
            "Aplicar tratados internacionales ratificados",
            "Garantizar derechos de propiedad intelectual",
            "Seguir circulares y conceptos de la SIC",
            "Mantener estándares técnico-jurídicos",
            "Evaluar reivindicaciones y suficiencia descriptiva",
            "Considerar derechos de prioridad aplicables",
            "Verificar requisitos de representación legal",
            "Analizar posibles infracciones",
            "Recomendar estrategias de protección"
        ],
        markdown=True
    )

async def analyze_patent(
    patent_text: str,
    patent_type: str,
    jurisdiction: str,
    specific_concerns: Optional[List[str]] = None,
    technical_field: Optional[str] = None
) -> Dict[str, str]:
    """Analizar una patente y proporcionar análisis detallado según normativa colombiana"""
    agent = create_patent_agent()
    
    # Get Colombian IP requirements
    ip_requirements = get_ip_requirements(patent_type)
    protection_period = get_ip_protection_period(patent_type)
    
    # Prepare the prompt
    prompt = f"""Analizar la siguiente patente de {patent_type}:

{patent_text}

JURISDICCIÓN: {jurisdiction}

Por favor proporcionar:
1. Resumen ejecutivo conciso (máximo 150 palabras)
2. Características técnicas y reivindicaciones principales
3. Evaluación de novedad
4. Análisis de nivel inventivo
5. Aplicabilidad industrial
6. Evaluación de cumplimiento con normativa PI colombiana
7. Análisis del período de protección
8. Riesgos potenciales de infracción
9. Suficiencia descriptiva
10. Unidad de invención
11. Claridad y sustento
12. Excepciones de patentabilidad
13. Requisitos formales SIC
14. Clasificación IPC/CIP
15. Recomendaciones de protección
"""
    
    if specific_concerns:
        prompt += f"\nENFOQUE ESPECIAL EN: {', '.join(specific_concerns)}"
    
    if technical_field:
        prompt += f"\nCAMPO TÉCNICO: {technical_field}"
    
    prompt += f"""
REQUISITOS DE PI COLOMBIANA:
- Elementos Requeridos: {', '.join(ip_requirements)}
- Período de Protección: {protection_period} años
- Requisitos de Registro: Cumplimiento total con Decisión 486 CAN
- Normativa Aplicable:
  * Decisión 486 de la CAN
  * Circular Única SIC
  * Resoluciones SIC aplicables
  * TLC vigentes
"""
    
    # Run the analysis
    response = agent.run(prompt)
    
    # Structure the response
    result = {
        "summary": response.content,
        "patent_type": patent_type,
        "jurisdiction": jurisdiction,
        "specific_concerns_addressed": specific_concerns if specific_concerns else [],
        "technical_field": technical_field,
        "colombian_compliance": {
            "ip_requirements": ip_requirements,
            "protection_period": protection_period,
            "analysis_date": datetime.now().isoformat(),
            "expiry_date": (datetime.now() + timedelta(days=protection_period*365)).isoformat()
        }
    }
    
    return result

async def draft_patent_application(
    invention_description: str,
    claims: List[str],
    technical_field: str,
    jurisdiction: str,
    inventors: List[str],
    priority_date: Optional[str] = None
) -> Dict[str, str]:
    """Redactar solicitud de patente según normativa colombiana"""
    agent = create_patent_agent()
    
    # Get Colombian IP requirements
    ip_requirements = get_ip_requirements("patent")
    protection_period = get_ip_protection_period("patent")
    
    # Format inventors for the prompt
    inventors_text = "\n".join([f"- {inventor}" for inventor in inventors])
    
    # Format claims for the prompt
    claims_text = "\n".join([f"{i+1}. {claim}" for i, claim in enumerate(claims)])
    
    # Prepare the prompt
    prompt = f"""Redactar solicitud de patente con los siguientes parámetros:

DESCRIPCIÓN DE LA INVENCIÓN:
{invention_description}

CAMPO TÉCNICO:
{technical_field}

REIVINDICACIONES:
{claims_text}

INVENTORES:
{inventors_text}

JURISDICCIÓN:
{jurisdiction}

La solicitud debe:
1. Seguir formato estándar SIC
2. Incluir secciones requeridas:
   - Descripción
   - Reivindicaciones
   - Resumen
   - Dibujos (si aplica)
3. Describir claramente la invención
4. Presentar reivindicaciones técnicamente sustentadas
5. Cumplir requisitos formales SIC
6. Incluir antecedentes relevantes
7. Detallar mejor modo de realización
8. Evidenciar aplicación industrial
9. Mantener unidad de invención
10. Incluir ejemplos ilustrativos
11. Cumplir requisitos de representación
12. Especificar prioridades (si aplica)
"""
    
    if priority_date:
        prompt += f"\nFECHA DE PRIORIDAD: {priority_date}"
    
    # Add Colombian IP requirements
    prompt += f"""
REQUISITOS DE PI COLOMBIANA:
- Elementos Requeridos: {', '.join(ip_requirements)}
- Período de Protección: {protection_period} años
- Requisitos de Registro: Cumplimiento total con Decisión 486 CAN
- Normativa Aplicable:
  * Decisión 486 de la CAN
  * Circular Única SIC
  * Resoluciones SIC aplicables
  * TLC vigentes
"""
    
    # Run the drafting
    response = agent.run(prompt)
    
    # Structure the response
    result = {
        "application": response.content,
        "patent_type": "patent",
        "jurisdiction": jurisdiction,
        "inventors": inventors,
        "technical_field": technical_field,
        "colombian_compliance": {
            "ip_requirements": ip_requirements,
            "protection_period": protection_period,
            "draft_date": datetime.now().isoformat(),
            "expiry_date": (datetime.now() + timedelta(days=protection_period*365)).isoformat()
        }
    }
    
    if priority_date:
        result["priority_date"] = priority_date
    
    return result

async def search_prior_art(
    invention_description: str,
    technical_features: list,
    proposed_claims: list = None,
    relevant_fields: list = None,
    filing_timeline: str = None
) -> dict:
    """Search for prior art related to patent applications"""
    agent = create_patent_agent()
    query_generator = QueryGenerator()
    
    # Generate search queries based on invention description and features
    search_queries = query_generator.generate_patent_queries(
        invention_description=invention_description,
        technical_features=technical_features,
        relevant_fields=relevant_fields if relevant_fields else []
    )
    
    # Prepare the prompt
    prompt = f"""Conduct a comprehensive prior art analysis for the following invention:

INVENTION DESCRIPTION:
{invention_description}

KEY TECHNICAL FEATURES:
{', '.join(technical_features)}
"""
    
    if proposed_claims:
        prompt += f"\nPROPOSED CLAIMS:\n{', '.join(proposed_claims)}\n"
    
    if relevant_fields:
        prompt += f"\nRELEVANT FIELDS:\n{', '.join(relevant_fields)}\n"
    
    if filing_timeline:
        prompt += f"\nFILING TIMELINE:\n{filing_timeline}\n"
    
    prompt += f"\nSEARCH QUERIES USED:\n{', '.join(search_queries)}\n"
    
    prompt += """
For your analysis:
1. Identify the most relevant potential prior art references
2. For each reference, analyze:
   - Specific overlap with our invention's claims
   - Critical differences that might maintain patentability
   - Filing/priority dates relative to our timeline
   - Assignee/inventor information
3. Map each reference to specific claims/features of our invention
4. Suggest claim modifications to overcome identified prior art
5. Assess patentability likelihood for key features
6. Identify white space opportunities for focusing claims
7. Flag any potential obviousness combinations of references

Organize findings by potential impact on patentability, from most concerning to least concerning references.
"""
    
    # Run the search
    response = agent.run(prompt)
    
    return {
        "report": response.content,
        "search_queries_used": search_queries,
        "invention_summary": invention_description[:200] + "..."
    }

async def search_patents(
    invention_description: str,
    jurisdiction: str,
    data_processing: Optional[Dict[str, str]] = None,
    legal_terms: Optional[List[str]] = None
) -> Dict[str, str]:
    """Búsqueda de patentes con cumplimiento normativo colombiano"""
    agent = create_patent_agent()
    
    # Get Colombian legal terms if provided
    legal_term_definitions = {}
    if legal_terms:
        legal_term_definitions = {term: get_legal_term(term) for term in legal_terms if get_legal_term(term)}
    
    # Get data processing details if provided
    data_compliance = {}
    if data_processing:
        data_category = get_data_category(data_processing.get("type", "personal"))
        consent_valid = validate_consent(data_processing.get("consent", {}))
        data_compliance = {
            "category": data_category.value,
            "consent_valid": consent_valid
        }
    
    # Prepare the prompt
    prompt = f"""Realizar búsqueda de patentes relacionadas con:

DESCRIPCIÓN DE LA INVENCIÓN: {invention_description}
JURISDICCIÓN: {jurisdiction}

MARCO NORMATIVO COLOMBIANO:
- Principios Constitucionales: {', '.join(ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES)}
- Normativa PI:
  * Decisión 486 CAN
  * Circular Única SIC
  * Tratados internacionales vigentes
"""
    
    if legal_term_definitions:
        prompt += "\nRELEVANT LEGAL TERMS:\n"
        for term, definition in legal_term_definitions.items():
            prompt += f"- {term}: {definition}\n"
    
    if data_processing:
        prompt += f"""
REQUISITOS DE PROCESAMIENTO DE DATOS:
- Categoría de Datos: {data_compliance['category']}
- Cumplimiento de Consentimiento: {'Válido' if data_compliance['consent_valid'] else 'Inválido'}
- Derechos Constitucionales: {', '.join(ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES)}
"""
    
    prompt += """
Please provide:
1. Relevant patent search results
2. Analysis of similar inventions
3. Potential prior art identification
4. Patent classification analysis
5. Jurisdictional considerations
6. Colombian constitutional principles analysis
7. Intellectual property rights implications
8. Data protection compliance
9. Legal term compliance

Present this analysis in a format suitable for patent search results.
"""
    
    # Run the search
    response = agent.run(prompt)
    
    # Structure the response
    result = {
        "search_results": response.content,
        "invention_description": invention_description,
        "jurisdiction": jurisdiction,
        "colombian_compliance": {
            "constitutional_principles": ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES,
            "search_date": datetime.now().isoformat()
        }
    }
    
    if legal_term_definitions:
        result["legal_terms"] = legal_term_definitions
    
    if data_processing:
        result["data_processing"] = {
            "category": data_compliance["category"],
            "consent_valid": data_compliance["consent_valid"]
        }
    
    return result

async def analyze_patentability(
    invention_description: str,
    prior_art: List[str],
    jurisdiction: str,
    data_processing: Optional[Dict[str, str]] = None,
    legal_terms: Optional[List[str]] = None
) -> Dict[str, str]:
    """Analizar patentabilidad según normativa colombiana"""
    agent = create_patent_agent()
    
    # Get Colombian legal terms if provided
    legal_term_definitions = {}
    if legal_terms:
        legal_term_definitions = {term: get_legal_term(term) for term in legal_terms if get_legal_term(term)}
    
    # Get data processing details if provided
    data_compliance = {}
    if data_processing:
        data_category = get_data_category(data_processing.get("type", "personal"))
        consent_valid = validate_consent(data_processing.get("consent", {}))
        data_compliance = {
            "category": data_category.value,
            "consent_valid": consent_valid
        }
    
    # Prepare the prompt
    prompt = f"""Analizar patentabilidad de la siguiente invención:

DESCRIPCIÓN: {invention_description}
JURISDICCIÓN: {jurisdiction}
ARTE PREVIO: {', '.join(prior_art)}

Por favor proporcionar:
1. Análisis de novedad
2. Evaluación de nivel inventivo
3. Aplicabilidad industrial
4. Comparación con arte previo
5. Conclusión de patentabilidad
6. Análisis de principios constitucionales
7. Implicaciones de derechos PI
8. Cumplimiento protección de datos
9. Conformidad términos legales
10. Recomendaciones para solicitud
11. Excepciones de patentabilidad
12. Requisitos de forma SIC
13. Estrategia de protección
14. Riesgos identificados
15. Recomendaciones técnicas
"""
    
    if legal_term_definitions:
        prompt += "\nRELEVANT LEGAL TERMS:\n"
        for term, definition in legal_term_definitions.items():
            prompt += f"- {term}: {definition}\n"
    
    if data_processing:
        prompt += f"""
REQUISITOS DE PROCESAMIENTO DE DATOS:
- Categoría de Datos: {data_compliance['category']}
- Cumplimiento de Consentimiento: {'Válido' if data_compliance['consent_valid'] else 'Inválido'}
- Derechos Constitucionales: {', '.join(ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES)}
"""
    
    prompt += """
Please provide:
1. Novelty analysis
2. Inventive step assessment
3. Industrial applicability evaluation
4. Prior art comparison
5. Patentability conclusion
6. Colombian constitutional principles analysis
7. Intellectual property rights implications
8. Data protection compliance
9. Legal term compliance
10. Recommendations for patent application
11. Exceptions to patentability
12. Requirements for SIC format
13. Protection strategy
14. Identified risks
15. Technical recommendations

Present this analysis in a format suitable for patentability assessment.
"""
    
    # Run the analysis
    response = agent.run(prompt)
    
    # Structure the response
    result = {
        "analysis": response.content,
        "invention_description": invention_description,
        "prior_art": prior_art,
        "jurisdiction": jurisdiction,
        "colombian_compliance": {
            "constitutional_principles": ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES,
            "analysis_date": datetime.now().isoformat()
        }
    }
    
    if legal_term_definitions:
        result["legal_terms"] = legal_term_definitions
    
    if data_processing:
        result["data_processing"] = {
            "category": data_compliance["category"],
            "consent_valid": data_compliance["consent_valid"]
        }
    
    return result

async def search_prior_art(
    invention_description: str,
    jurisdiction: str,
    data_processing: Optional[Dict[str, str]] = None,
    legal_terms: Optional[List[str]] = None
) -> Dict[str, str]:
    """Search for prior art with Colombian compliance"""
    agent = create_patent_agent()
    
    # Get Colombian legal terms if provided
    legal_term_definitions = {}
    if legal_terms:
        legal_term_definitions = {term: get_legal_term(term) for term in legal_terms if get_legal_term(term)}
    
    # Get data processing details if provided
    data_compliance = {}
    if data_processing:
        data_category = get_data_category(data_processing.get("type", "personal"))
        consent_valid = validate_consent(data_processing.get("consent", {}))
        data_compliance = {
            "category": data_category.value,
            "consent_valid": consent_valid
        }
    
    # Prepare the prompt
    prompt = f"""Search for prior art related to the following invention:

INVENTION DESCRIPTION: {invention_description}
JURISDICCIÓN: {jurisdiction}
"""
    
    # Add Colombian legal framework requirements
    prompt += f"""
REQUISITOS DE PI COLOMBIANA:
- Principios Constitucionales: {', '.join(ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES)}
"""
    
    if legal_term_definitions:
        prompt += "\nRELEVANT LEGAL TERMS:\n"
        for term, definition in legal_term_definitions.items():
            prompt += f"- {term}: {definition}\n"
    
    if data_processing:
        prompt += f"""
REQUISITOS DE PROCESAMIENTO DE DATOS:
- Categoría de Datos: {data_compliance['category']}
- Cumplimiento de Consentimiento: {'Válido' if data_compliance['consent_valid'] else 'Inválido'}
- Derechos Constitucionales: {', '.join(ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES)}
"""
    
    prompt += """
Please provide:
1. Prior art search results
2. Analysis of similar inventions
3. Potential novelty issues
4. Jurisdictional considerations
5. Colombian constitutional principles analysis
6. Intellectual property rights implications
7. Data protection compliance
8. Legal term compliance

Present this analysis in a format suitable for prior art search results.
"""
    
    # Run the search
    response = agent.run(prompt)
    
    # Structure the response
    result = {
        "search_results": response.content,
        "invention_description": invention_description,
        "jurisdiction": jurisdiction,
        "colombian_compliance": {
            "constitutional_principles": ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES,
            "search_date": datetime.now().isoformat()
        }
    }
    
    if legal_term_definitions:
        result["legal_terms"] = legal_term_definitions
    
    if data_processing:
        result["data_processing"] = {
            "category": data_compliance["category"],
            "consent_valid": data_compliance["consent_valid"]
        }
    
    return result 