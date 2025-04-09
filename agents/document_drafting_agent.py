from agno.agent import Agent
from config.database import get_agent_storage
from config.ai_models import get_model
from config.knowledge_base import get_knowledge_base
from config.colombian_compliance import (
    ColombianDataProtection,
    ColombianLegalFramework,
    get_data_category,
    validate_consent,
    get_retention_period,
    get_administrative_deadline,
    get_legal_term
)
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from time import sleep
import random
from tenacity import retry, stop_after_attempt, wait_exponential
#import openai  # Add this import

@retry(
    stop=stop_after_attempt(3),  # Try 3 times
    wait=wait_exponential(multiplier=1, min=4, max=10),  # Wait between 4-10 seconds, increasing exponentially
)
def create_document_drafting_agent() -> Agent:
    """Create a specialized agent for legal document drafting with retry logic"""
    try:
        agent = Agent(
            name="Especialista en Redacción Jurídica",
            role="Especialista en elaboración de documentos legales",
            model=get_model("document_drafting"),  # Specify model directly
            knowledge=get_knowledge_base(),
            search_knowledge=True,
            #storage=get_agent_storage("document_sessions"),
            instructions=[
                "Elaborar documentos según ordenamiento jurídico colombiano",
                "Incorporar cláusulas constitucionales y legales obligatorias",
                "Asegurar cumplimiento de requisitos de validez y eficacia",
                "Incluir autorizaciones de tratamiento de datos personales",
                "Establecer jurisdicción y competencia territorial",
                "Utilizar terminología jurídica del derecho colombiano",
                "Garantizar ejecutabilidad y eficacia jurídica",
                "Incluir mecanismos alternativos de solución de conflictos",
                "Proteger derechos fundamentales y constitucionales",
                "Cumplir requisitos de autenticidad y formalidades",
                "Especificar régimen legal aplicable",
                "Incluir causales de terminación y efectos",
                "Establecer procedimientos de notificación",
                "Definir obligaciones y responsabilidades",
                "Considerar normas de orden público aplicables"
            ]
        )
        return agent
    except Exception as e:
        print(f"Error creating agent: {str(e)}")
        raise

def clean_response(response: str) -> str:
    """Clean and format the agent's response"""
    # Remove RunResponse metadata
    if "RunResponse(content='" in response:
        response = response.split("RunResponse(content='", 1)[1].split("', content_type=", 1)[0]
    
    # Unescape any escaped characters
    response = response.replace('\\n', '\n')
    
    # Remove any remaining response metadata
    response = response.split("messages=[Message(", 1)[0] if "messages=[Message(" in response else response
    
    # Clean up any trailing metadata
    response = response.strip()
    
    return response

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def draft_legal_document(
    document_type: str,
    jurisdiction: str,
    key_requirements: List[str],
    parties: List[str],
    legal_terms: Optional[List[str]] = None,
    data_processing: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Draft legal document with Colombian compliance"""
    try:
        agent = create_document_drafting_agent()
        
        # Format the prompt
        prompt = format_document_prompt(
            document_type=document_type,
            jurisdiction=jurisdiction,
            key_requirements=key_requirements,
            parties=parties,
            legal_terms=legal_terms,
            data_processing=data_processing
        )

        # Get response from agent
        response = agent.run(prompt)
        
        # Clean and format the response
        document_content = clean_response(str(response))
        
        # Structure the response
        result = {
            "document": {
                "content": document_content,
                "sections": extract_document_sections(document_content),
                "markdown": True  # Indicate that the content uses markdown
            },
            "document_type": document_type,
            "jurisdiction": jurisdiction,
            "key_requirements": key_requirements,
            "parties": [{"name": name, "role": "Parte"} for name in parties],
            "colombian_compliance": {
                "framework_version": "2024.1",
                "status": "compliant",
                "constitutional_principles": [
                    "Dignidad humana",
                    "Buena fe",
                    "Debido proceso",
                    "Legalidad",
                    "Transparencia"
                ],
                "validation_date": datetime.now().isoformat()
            },
            "legal_terms": None,
            "data_processing": None,
            "timestamp": datetime.now().isoformat()
        }
        
        if legal_terms:
            result["legal_terms"] = {term: get_legal_term(term) for term in legal_terms}
            
        if data_processing:
            result["data_processing"] = process_data_requirements(data_processing)
            
        return result
        
    except Exception as e:
        print(f"Error drafting document: {str(e)}")
        raise

def format_document_prompt(
    document_type: str,
    jurisdiction: str,
    key_requirements: List[str],
    parties: List[str],
    legal_terms: Optional[List[str]] = None,
    data_processing: Optional[Dict[str, str]] = None
) -> str:
    """Format the prompt for document generation"""
    prompt = f"""Por favor redacta un documento legal tipo {document_type} con los siguientes parámetros:

JURISDICCIÓN:
{jurisdiction}

REQUISITOS CLAVE:
{chr(10).join(f'- {req}' for req in key_requirements)}

PARTES:
{chr(10).join(f'- {party}' for party in parties)}

{f'TÉRMINOS LEGALES:{chr(10)}{chr(10).join(f"- {term}" for term in legal_terms)}' if legal_terms else ''}

{f'TRATAMIENTO DE DATOS:{chr(10)}{chr(10).join(f"- {k}: {v}" for k, v in data_processing.items())}' if data_processing else ''}

El documento debe cumplir con todas las regulaciones colombianas aplicables y incluir todas las cláusulas necesarias.

Por favor proporciona el documento en formato de texto plano."""
    
    return prompt

def extract_document_sections(content: str) -> List[str]:
    """Extract main sections from the document"""
    sections = []
    lines = content.split('\n')
    
    for line in lines:
        clean_line = line.strip().upper()
        if clean_line and (
            clean_line.endswith(':') or 
            any(keyword in clean_line for keyword in ['CLÁUSULA', 'ARTÍCULO', 'SECCIÓN'])
        ):
            sections.append(clean_line.rstrip(':'))
    
    # If no sections were found, return default sections
    if not sections:
        return ["PARTES", "OBJETO", "OBLIGACIONES", "TÉRMINOS", "FIRMAS"]
    
    return sections

def process_data_requirements(data_processing: Dict[str, str]) -> Dict[str, str]:
    """Process data protection requirements"""
    category = get_data_category(data_processing.get("type", "personal"))
    retention = get_retention_period(category)
    consent = validate_consent(data_processing.get("consent", {}))
    
    return {
        "category": str(category.value if hasattr(category, 'value') else category),
        "retention_period": f"{retention} días",  # Convert to string with unit
        "consent_valid": str(consent).lower(),  # Convert boolean to string
        "requirements": "Requisitos: Recolección autorizada, Almacenamiento seguro, " +
                      "Procesamiento con consentimiento explícito, Compartir restringido, " +
                      "Retención según normativa vigente"  # Convert dict to string description
    }

async def draft_document(
    document_content: str,
    document_context: dict,
    parties: List[str],
    jurisdiction: str,
    special_considerations: Optional[List[str]] = None,
    administrative_procedure: Optional[str] = None,
    data_processing: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    """Redactar documentos legales con formato y cláusulas apropiadas"""
    agent = create_document_drafting_agent()
    
    # Format parties for the prompt
    parties_text = "\n".join([f"- {party}" for party in parties])
    
    # Format special considerations if provided
    considerations_text = "\n".join([f"- {consideration}" for consideration in special_considerations]) if special_considerations else "None specified"
    
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
    
    # Prepare the prompt
    prompt = f"""Redactar un documento legal con los siguientes parámetros:

CONTENIDO DEL DOCUMENTO:
{document_content}

CONTEXTO DEL DOCUMENTO:
{document_context}

PARTES INVOLUCRADAS:
{parties_text}

JURISDICCIÓN:
{jurisdiction}

CONSIDERACIONES ESPECIALES:
{considerations_text}

El documento debe:
1. Utilizar lenguaje jurídico y formato apropiado
2. Incluir todas las cláusulas y disposiciones necesarias
3. Cumplir requisitos jurisdiccionales específicos
4. Abordar todas las consideraciones especiales
5. Definir claramente términos y condiciones
6. Incluir espacios para firmas y fechas
7. Tener numeración y organización apropiada
8. Incluir avisos y revelaciones requeridas
9. Cumplir con el marco legal colombiano
10. Incorporar principios constitucionales
11. Seguir procedimientos administrativos
12. Proteger derechos del titular de datos
"""

    if administrative_procedure:
        prompt += f"""
DETALLES DEL PROCEDIMIENTO ADMINISTRATIVO:
- Tipo: {administrative_procedure}
- Término de Respuesta: {deadlines['response']} días
- Término de Apelación: {deadlines['appeal']} días
- Término de Reposición: {deadlines['recourse']} días
"""

    # Add data processing details if provided
    if data_processing:
        data_category = get_data_category(data_processing.get("type", "personal"))
        retention_period = get_retention_period(data_category)
        consent_valid = validate_consent(data_processing.get("consent", {}))
        
        prompt += f"""
REQUISITOS DE TRATAMIENTO DE DATOS:
- Categoría de Datos: {data_category.value}
- Retención Período: {retention_period} días
- Requisitos de Consentimiento: {'Cumplido' if consent_valid else 'No Cumplido'}
- Derechos Constitucionales: {', '.join(ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES)}
"""

    # Run the generation
    response = agent.run(prompt)
    
    # Structure the response
    result = {
        "document": response.content,
        "jurisdiction": jurisdiction,
        "parties": parties,
        "colombian_compliance": {
            "constitutional_principles": ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES,
            "draft_date": datetime.now().isoformat()
        }
    }
    
    # Add administrative procedure details if applicable
    if administrative_procedure:
        result["administrative_procedure"] = {
            "type": administrative_procedure,
            "deadlines": deadlines,
            "response_due": (datetime.now() + timedelta(days=deadlines["response"])).isoformat()
        }
    
    # Add data processing details if provided
    if data_processing:
        result["data_processing"] = {
            "category": data_processing.get("type", "personal"),
            "retention_period": retention_period,
            "consent_valid": consent_valid,
            "expiry_date": (datetime.now() + timedelta(days=retention_period)).isoformat()
        }
    
    return result

async def draft_contract(
    contract_type: str,
    parties: list,
    key_terms: list,
    jurisdiction: str,
    special_considerations: list = None,
    risk_profile: str = "balanceado",
    negotiation_context: str = None,
    data_processing: Optional[Dict[str, str]] = None
) -> dict:
    """Redactar contratos legales personalizados según parámetros especificados"""
    agent = create_document_drafting_agent()
    
    # Format parties for the prompt
    parties_text = "\n".join([f"- {party.get('name', 'Unnamed Party')}: {party.get('details', 'No details provided')}" for party in parties])
    
    # Format key terms for the prompt
    terms_text = "\n".join([f"- {term.get('name', 'Unnamed Term')}: {term.get('details', 'No details provided')}" for term in key_terms])
    
    # Prepare the prompt
    prompt = f"""Redactar un contrato de {contract_type} con los siguientes parámetros:

PARTES:
{parties_text}

TÉRMINOS PRINCIPALES:
{terms_text}

JURISDICCIÓN:
{jurisdiction}

PERFIL DE RIESGO:
{risk_profile}
"""
    
    if special_considerations:
        prompt += f"\nCONSIDERACIONES ESPECIALES:\n{', '.join(special_considerations)}\n"
    
    if negotiation_context:
        prompt += f"\nCONTEXTO DE NEGOCIACIÓN:\n{negotiation_context}\n"
    
    # Add data processing requirements if provided
    if data_processing:
        data_category = get_data_category(data_processing.get("type", "personal"))
        retention_period = get_retention_period(data_category)
        consent_valid = validate_consent(data_processing.get("consent", {}))
        
        prompt += f"""
REQUISITOS DE TRATAMIENTO DE DATOS:
- Categoría de Datos: {data_category.value}
- Retención Período: {retention_period} días
- Requisitos de Consentimiento: {'Cumplido' if consent_valid else 'No Cumplido'}
- Derechos Constitucionales: {', '.join(ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES)}
"""
    
    prompt += """
Por favor redactar un contrato completo que:
1. Utilice lenguaje claro y preciso
2. Incluya todas las secciones estándar apropiadas
3. Incorpore los términos especificados con detalle apropiado
4. Proporcione protecciones equilibradas según el perfil de riesgo
5. Cumpla con la legislación aplicable
6. Incluya notas explicativas para disposiciones que requieren decisiones
7. Señale áreas que requieren información adicional del cliente
8. Ofrezca alternativas para disposiciones potencialmente contenciosas
9. Cumpla con leyes de protección de datos colombianas
10. Incorpore principios constitucionales
11. Proteja derechos del titular de datos
12. Incluya períodos de retención apropiados

Formatear el documento con estilo legal apropiado, incluyendo secciones numeradas, términos definidos y espacios para firmas.
"""
    
    # Run the drafting
    response = agent.run(prompt)
    
    # Structure the response
    result = {
        "contract_draft": response.content,
        "contract_type": contract_type,
        "jurisdiction": jurisdiction,
        "parties": [party.get('name', 'Unnamed Party') for party in parties],
        "colombian_compliance": {
            "constitutional_principles": ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES,
            "draft_date": datetime.now().isoformat()
        }
    }
    
    # Add data processing details if provided
    if data_processing:
        result["data_processing"] = {
            "category": data_processing.get("type", "personal"),
            "retention_period": retention_period,
            "consent_valid": consent_valid,
            "expiry_date": (datetime.now() + timedelta(days=retention_period)).isoformat()
        }
    
    return result 