from agno.agent import Agent
from config.database import get_agent_storage
from config.ai_models import get_model
from config.knowledge_base import get_knowledge_base
from config.colombian_compliance import (
    ColombianLegalFramework,
    get_legal_term,
    get_data_category,
    validate_consent,
    get_administrative_deadline
)
from typing import Dict, List, Optional
from datetime import datetime, timedelta

def create_demand_letter_agent() -> Agent:
    """Create a specialized agent for demand letter drafting"""
    return Agent(
        name="Especialista en Requerimientos Legales",
        role="Especialista en redacción de requerimientos jurídicos",
        model=get_model("demand"),
        knowledge=get_knowledge_base(),
        search_knowledge=True,
        storage=get_agent_storage("demand_sessions"),
        instructions=[
            "Redactar requerimientos según normatividad colombiana",
            "Incluir fundamentos constitucionales y legales específicos",
            "Especificar términos perentorios y de caducidad",
            "Incorporar requisitos del CPACA cuando aplique",
            "Citar jurisprudencia vinculante y doctrina autorizada",
            "Mantener lenguaje formal según estándares jurídicos",
            "Proteger derechos fundamentales y habeas data",
            "Establecer pretensiones claras y jurídicamente viables",
            "Incluir recursos procedentes y términos legales",
            "Seguir lineamientos de autoridades administrativas",
            "Especificar consecuencias jurídicas del incumplimiento",
            "Incluir anexos y pruebas requeridas",
            "Verificar requisitos de notificación aplicables",
            "Considerar jurisdicción y competencia",
            "Establecer plazos según normativa vigente"
        ],
        markdown=True
    )

async def generate_demand_letter(
    situation_description: str,
    jurisdiction: str,
    legal_basis: List[str],
    requested_actions: List[str],
    deadline: str,
    parties: List[str],
    administrative_procedure: Optional[str] = None,
    legal_terms: Optional[List[str]] = None,
    data_processing: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    """Generate a demand letter with Colombian compliance"""
    agent = create_demand_letter_agent()
    
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
    
    # Get administrative deadlines if applicable
    deadlines = {}
    if administrative_procedure:
        response_time = get_administrative_deadline("response_time")
        appeal_time = get_administrative_deadline("appeal_time")
        recourse_time = get_administrative_deadline("recourse_time")
        deadlines = {
            "response": response_time,
            "appeal": appeal_time,
            "recourse": recourse_time
        }
    
    # Format parties for the prompt
    parties_text = "\n".join([f"- {party}" for party in parties])
    
    # Format legal basis for the prompt
    basis_text = "\n".join([f"- {basis}" for basis in legal_basis])
    
    # Format requested actions for the prompt
    actions_text = "\n".join([f"- {action}" for action in requested_actions])
    
    # Update prompt in Spanish
    prompt = f"""Generar un requerimiento legal con los siguientes parámetros:

DESCRIPCIÓN DE LA SITUACIÓN:
{situation_description}

JURISDICCIÓN: {jurisdiction}

FUNDAMENTO JURÍDICO:
{basis_text}

PRETENSIONES:
{actions_text}

TÉRMINO: {deadline}

PARTES INVOLUCRADAS:
{parties_text}
"""
    
    # Add Colombian legal framework requirements in Spanish
    prompt += f"""
MARCO JURÍDICO COLOMBIANO:
- Principios Constitucionales: {', '.join(ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES)}
"""
    
    if legal_term_definitions:
        prompt += "\nTÉRMINOS JURÍDICOS RELEVANTES:\n"
        for term, definition in legal_term_definitions.items():
            prompt += f"- {term}: {definition}\n"
    
    if administrative_procedure:
        prompt += f"""
DETALLES DEL PROCEDIMIENTO ADMINISTRATIVO:
- Tipo: {administrative_procedure}
- Término de Respuesta: {deadlines['response']} días
- Término de Apelación: {deadlines['appeal']} días
- Término de Reposición: {deadlines['recourse']} días
"""
    
    if data_processing:
        prompt += f"""
REQUISITOS DE TRATAMIENTO DE DATOS:
- Categoría de Datos: {data_compliance['category']}
- Cumplimiento de Consentimiento: {'Válido' if data_compliance['consent_valid'] else 'Inválido'}
- Derechos Constitucionales: {', '.join(ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES)}
"""
    
    prompt += """
Por favor generar un requerimiento que:
1. Describa claramente la situación fáctica
2. Cite normas y jurisprudencia aplicable
3. Especifique pretensiones concretas
4. Establezca términos perentorios
5. Incluya referencias jurídicas precisas
6. Cumpla con la normatividad colombiana
7. Utilice lenguaje formal y técnico
8. Incluya firmas y autenticaciones requeridas
9. Establezca consecuencias jurídicas
10. Siga lineamientos de práctica legal
11. Incluya estructura de honorarios si aplica
12. Proteja derechos del titular de datos
13. Reference principios constitucionales
14. Utilice terminología jurídica apropiada
15. Cumpla procedimientos administrativos

Presentar el requerimiento en formato apto para uso legal.
"""
    
    # Run the generation
    response = agent.run(prompt)
    
    # Structure the response
    result = {
        "letter": response.content,
        "situation_description": situation_description,
        "jurisdiction": jurisdiction,
        "legal_basis": legal_basis,
        "requested_actions": requested_actions,
        "deadline": deadline,
        "parties": parties,
        "colombian_compliance": {
            "constitutional_principles": ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES,
            "generation_date": datetime.now().isoformat()
        }
    }
    
    if legal_term_definitions:
        result["legal_terms"] = legal_term_definitions
    
    if administrative_procedure:
        result["administrative_procedure"] = {
            "type": administrative_procedure,
            "deadlines": deadlines,
            "response_due": (datetime.now() + timedelta(days=deadlines["response"])).isoformat()
        }
    
    if data_processing:
        result["data_processing"] = {
            "category": data_compliance["category"],
            "consent_valid": data_compliance["consent_valid"]
        }
    
    return result

async def draft_demand_letter(
    situation_description: str,
    jurisdiction: str,
    legal_basis: List[str],
    requested_actions: List[str],
    deadline: str,
    parties: List[str],
    administrative_procedure: Optional[str] = None,
    legal_terms: Optional[List[str]] = None,
    data_processing: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    """Redactar requerimiento legal con cumplimiento normativo colombiano"""
    return await generate_demand_letter(
        situation_description=situation_description,
        jurisdiction=jurisdiction,
        legal_basis=legal_basis,
        requested_actions=requested_actions,
        deadline=deadline,
        parties=parties,
        administrative_procedure=administrative_procedure,
        legal_terms=legal_terms,
        data_processing=data_processing
    ) 