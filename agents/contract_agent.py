from agno.agent import Agent
from config.database import get_agent_storage
from config.ai_models import get_model
from config.knowledge_base import get_knowledge_base
from config.colombian_compliance import (
    ColombianDataProtection,
    ColombianLegalFramework,
    get_data_category,
    validate_consent,
    get_retention_period
)
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
#import openai // not needed

def create_contract_agent() -> Agent:
    """Create a specialized agent for contract review"""
    return Agent(
        name="Analista de Contratos",
        role="Especialista en análisis contractual",
        model=get_model("contract_review"),
        knowledge=get_knowledge_base(),
        search_knowledge=True,
        storage=get_agent_storage("contract_sessions"),
        instructions=[
            "Analizar contratos según normativa colombiana",
            "Verificar cumplimiento del Código Civil y Comercial",
            "Evaluar cláusulas según jurisprudencia vigente",
            "Identificar elementos esenciales del contrato",
            "Verificar capacidad y consentimiento de las partes",
            "Evaluar objeto y causa lícita",
            "Analizar obligaciones y responsabilidades",
            "Verificar cláusulas de protección de datos",
            "Evaluar mecanismos de terminación",
            "Revisar jurisdicción y competencia",
            "Analizar cláusulas compromisorias",
            "Verificar requisitos de forma y solemnidades",
            "Evaluar garantías y seguros requeridos",
            "Analizar cláusulas de indemnidad",
            "Verificar cumplimiento regulatorio sectorial"
        ],
        markdown=True
    )

async def analyze_contract(
    contract_text: str,
    contract_type: str,
    parties: List[str],
    specific_concerns: Optional[List[str]] = None,
    relevant_regulations: Optional[List[str]] = None,
    data_processing: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    """Analyze a contract and provide detailed insights with Colombian compliance"""
    agent = create_contract_agent()
    
    # Update prompt in Spanish
    prompt = f"""Analizar el siguiente contrato de {contract_type} entre {', '.join(parties)}:

{contract_text}

Por favor proporcionar:
1. Resumen ejecutivo conciso (máximo 150 palabras)
2. Obligaciones principales de cada parte con referencia a cláusulas específicas
3. Fechas críticas y plazos
4. Cláusulas inusuales o no estándar según práctica comercial
5. Riesgos potenciales por cláusula con nivel de severidad (Bajo/Medio/Alto)
6. Evaluación de cumplimiento legal colombiano
7. Cumplimiento de protección de datos (Ley 1581 de 2012)
8. Alineación con principios constitucionales
9. Validez de cláusulas según normativa vigente
10. Requisitos de forma y solemnidades
11. Mecanismos de resolución de conflictos
12. Causales de terminación y efectos
13. Régimen de responsabilidad aplicable
14. Garantías y seguros requeridos
15. Jurisdicción y competencia
"""
    
    if specific_concerns:
        prompt += f"\nEnfocarse particularmente en cláusulas relacionadas con: {', '.join(specific_concerns)}"
    
    if relevant_regulations:
        prompt += f"\n\nEvaluar cumplimiento de las siguientes regulaciones: {', '.join(relevant_regulations)}"
    
    if data_processing:
        data_category = get_data_category(data_processing.get("type", "personal"))
        retention_period = get_retention_period(data_category)
        consent_valid = validate_consent(data_processing.get("consent", {}))
        
        prompt += f"""

ANÁLISIS DE TRATAMIENTO DE DATOS:
- Categoría de Datos: {data_category.value}
- Período de Retención Requerido: {retention_period} días
- Cumplimiento de Consentimiento: {'Válido' if consent_valid else 'Inválido'}
- Principios Constitucionales: {', '.join(ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES)}
- Requisitos de Autorización: {ColombianDataProtection.AUTHORIZATION_REQUIREMENTS}
- Derechos del Titular: {ColombianDataProtection.DATA_SUBJECT_RIGHTS}
- Medidas de Seguridad: {ColombianDataProtection.SECURITY_MEASURES}
"""
    
    # Run the analysis
    response = agent.run(prompt)
    
    # Structure the response
    result = {
        "summary": response.content,
        "contract_type": contract_type,
        "parties": parties,
        "specific_concerns_addressed": specific_concerns if specific_concerns else [],
        "regulations_evaluated": relevant_regulations if relevant_regulations else [],
        "colombian_compliance": {
            "data_protection": bool(data_processing),
            "constitutional_principles": ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES,
            "analysis_date": datetime.now().isoformat()
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

async def analyze_contract_file(
    contract_text: str,
    contract_type: str,
    analysis_options: dict,
    specific_concerns: List[str],
    risk_analysis: dict,
    compliance_checks: dict
) -> dict:
    """
    Analyze contract with specific filters applied
    """
    result = {}
    
    try:
        # Risk Analysis
        if any(risk_analysis.values()):
            result["risk_assessment"] = await analyze_risks(
                contract_text,
                include_financial=risk_analysis["include_financial"],
                include_legal=risk_analysis["include_legal"],
                include_compliance=risk_analysis["include_compliance"]
            )
        
        # Clause Extraction
        if any(analysis_options["clause_extraction"].values()):
            result["extracted_clauses"] = await extract_clauses(
                contract_text,
                extract_important=analysis_options["clause_extraction"]["important"],
                extract_obligations=analysis_options["clause_extraction"]["obligations"],
                extract_termination=analysis_options["clause_extraction"]["termination"]
            )
        
        # Compliance Check
        if any(compliance_checks.values()):
            result["compliance_analysis"] = await check_compliance(
                contract_text,
                check_regulatory=compliance_checks["check_regulatory"],
                check_internal=compliance_checks["check_internal"],
                check_industry=compliance_checks["check_industry"]
            )
        
        return result
    except Exception as e:
        print(f"Error in analyze_contract_file: {str(e)}")
        raise

async def analyze_risks(
    contract_text: str,
    include_financial: bool = True,
    include_legal: bool = True,
    include_compliance: bool = True
) -> Dict[str, Any]:
    """Analyze contract risks based on selected options"""
    agent = create_contract_agent()
    
    # Build the prompt based on selected risk types
    risk_types = []
    if include_financial:
        risk_types.append("financieros")
    if include_legal:
        risk_types.append("legales")
    if include_compliance:
        risk_types.append("de cumplimiento")
    
    risk_prompt = f"""Analiza el siguiente contrato y evalúa los riesgos {', '.join(risk_types)}.
    
Contrato:
{contract_text}

Proporciona:
1. Nivel general de riesgo (bajo, medio, alto)
2. Lista de riesgos identificados
3. Impacto potencial de cada riesgo

Responde en formato JSON exactamente así:
{{
    "nivel_riesgo": "bajo/medio/alto",
    "riesgos_identificados": ["riesgo 1", "riesgo 2", ...],
    "impacto_potencial": "descripción del impacto"
}}
"""

    try:
        response = await agent.arun(risk_prompt)
        return eval(response.content)
    except Exception as e:
        print(f"Error in risk analysis: {str(e)}")
        return {
            "nivel_riesgo": "no determinado",
            "riesgos_identificados": [],
            "impacto_potencial": "No se pudo determinar"
        }

async def extract_clauses(
    contract_text: str,
    extract_important: bool = True,
    extract_obligations: bool = True,
    extract_termination: bool = True
) -> Dict[str, List[str]]:
    """Extract relevant clauses based on selected options"""
    agent = create_contract_agent()
    
    clause_types = []
    if extract_important:
        clause_types.append("importantes")
    if extract_obligations:
        clause_types.append("obligaciones")
    if extract_termination:
        clause_types.append("términos de finalización")
    
    clause_prompt = f"""Analiza el siguiente contrato y extrae las cláusulas {', '.join(clause_types)}.

Contrato:
{contract_text}

Proporciona las cláusulas en formato JSON exactamente así:
{{
    "clausulas_criticas": ["cláusula 1", "cláusula 2", ...],
    "obligaciones": ["obligación 1", "obligación 2", ...],
    "terminos_finalizacion": ["término 1", "término 2", ...]
}}
"""

    try:
        response = await agent.arun(clause_prompt)
        return eval(response.content)
    except Exception as e:
        print(f"Error in clause extraction: {str(e)}")
        return {
            "clausulas_criticas": [],
            "obligaciones": [],
            "terminos_finalizacion": []
        }

async def check_compliance(
    contract_text: str,
    check_regulatory: bool = True,
    check_internal: bool = True,
    check_industry: bool = True
) -> Dict[str, Any]:
    """Check contract compliance based on selected options"""
    agent = create_contract_agent()
    
    compliance_types = []
    if check_regulatory:
        compliance_types.append("normativa regulatoria")
    if check_internal:
        compliance_types.append("políticas internas")
    if check_industry:
        compliance_types.append("estándares de la industria")
    
    compliance_prompt = f"""Analiza el cumplimiento del siguiente contrato respecto a {', '.join(compliance_types)}.

Contrato:
{contract_text}

Proporciona el análisis en formato JSON exactamente así:
{{
    "status": "compliant/non_compliant",
    "framework_version": "2024.1",
    "incumplimientos": ["incumplimiento 1", "incumplimiento 2", ...],
    "recomendaciones": ["recomendación 1", "recomendación 2", ...]
}}
"""

    try:
        response = await agent.arun(compliance_prompt)
        return eval(response.content)
    except Exception as e:
        print(f"Error in compliance check: {str(e)}")
        return {
            "status": "unknown",
            "framework_version": "2024.1",
            "incumplimientos": [],
            "recomendaciones": []
        }

def extract_critical_clauses(analysis: str) -> List[str]:
    """Extract critical clauses from analysis"""
    # Implementation needed
    return []

def extract_obligations(analysis: str) -> List[str]:
    """Extract main obligations from analysis"""
    # Implementation needed
    return []

def assess_risk_level(analysis: str) -> str:
    """Assess overall risk level"""
    # Implementation needed
    return "medio"

def extract_risks(analysis: str) -> List[str]:
    """Extract identified risks"""
    # Implementation needed
    return []

def assess_impact(analysis: str) -> str:
    """Assess potential impact"""
    # Implementation needed
    return "significativo"

def extract_recommendations(analysis: str) -> List[str]:
    """Extract recommendations"""
    # Implementation needed
    return []

# Add to all agents:
# Implement decision explanation mechanisms
# Add transparency in processing
# Include user consent controls