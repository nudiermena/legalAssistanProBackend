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
import os
import json
import logging
from fastapi import HTTPException
from models.request_models import ContractReviewRequest
from models.response_models import format_response, handle_error
from agno.tools.googlesearch import GoogleSearchTools
#import openai // not needed
import re

logger = logging.getLogger(__name__)

def create_contract_agent() -> Agent:
    """Create a specialized agent for contract review"""
    return Agent(
        name="Analista de Contratos",
        role="Especialista en análisis contractual",
        model=get_model("contract_review"),
        tools=[GoogleSearchTools()],
        knowledge=get_knowledge_base(),
        search_knowledge=True,
        #storage=get_agent_storage("contract_sessions"),
        instructions=[
            # "Analizar contratos según normativa colombiana",
            # "Verificar cumplimiento del Código Civil y Comercial",
            # "Evaluar cláusulas según jurisprudencia vigente",
            # "Identificar elementos esenciales del contrato",
            # "Verificar capacidad y consentimiento de las partes",
            # "Evaluar objeto y causa lícita",
            # "Analizar obligaciones y responsabilidades",
            # "Verificar cláusulas de protección de datos",
            # "Evaluar mecanismos de terminación",
            # "Revisar jurisdicción y competencia",
            # "Analizar cláusulas compromisorias",
            # "Verificar requisitos de forma y solemnidades",
            # "Evaluar garantías y seguros requeridos",
            # "Analizar cláusulas de indemnidad",
            # "Verificar cumplimiento regulatorio sectorial",
            
             # === MARCO NORMATIVO Y LEGAL ===
        "Analizar contratos aplicando la normativa colombiana vigente (Código Civil, Código de Comercio, Código General del Proceso)",
        "Verificar cumplimiento de la Ley 80 de 1993 (Estatuto General de Contratación Pública) cuando aplique",
        "Evaluar conformidad con el régimen de protección de datos (Ley 1581 de 2012 - Habeas Data)",
        "Aplicar jurisprudencia vinculante de la Corte Suprema de Justicia, Consejo de Estado y Corte Constitucional",
        
        # === ESTRUCTURA CONTRACTUAL ===
        "Verificar la presencia y validez de elementos esenciales: consentimiento, objeto, causa y solemnidades",
        "Evaluar la capacidad jurídica de las partes contratantes y posibles limitaciones",
        "Analizar la descripción del objeto contractual verificando su determinación, posibilidad y licitud",
        "Examinar la causa del contrato asegurando su existencia, veracidad y licitud",
        
        # === CLÁUSULAS Y CONDICIONES ===
        "Revisar exhaustivamente obligaciones, derechos y responsabilidades de cada parte",
        "Evaluar cláusulas de penalización, multas y apremios por incumplimiento",
        "Analizar términos de duración, renovación, prórroga y terminación del contrato",
        "Verificar cláusulas de fuerza mayor, caso fortuito y teoría de la imprevisión",
        "Examinar mecanismos de garantías (pólizas, fiducias, cartas de crédito)",
        
        # === ASPECTOS PROCEDIMENTALES ===
        "Verificar cumplimiento de requisitos de forma según el tipo contractual",
        "Evaluar cláusulas de competencia, jurisdicción y ley aplicable",
        "Analizar mecanismos alternativos de solución de conflictos (arbitraje, conciliación, amigable composición)",
        "Revisar procedimientos de notificación, comunicaciones y entrega de documentos",
        
        # === CUMPLIMIENTO REGULATORIO ===
        "Verificar cumplimiento de normativa sectorial específica (financiera, salud, educación, etc.)",
        "Evaluar conformidad con regulaciones laborales cuando aplique",
        "Analizar aspectos tributarios y fiscales del contrato",
        "Verificar cumplimiento de normas ambientales y de sostenibilidad",
        
        # === GESTIÓN DE RIESGOS ===
        "Identificar y evaluar riesgos legales, operacionales y financieros",
        "Analizar cláusulas de indemnidad, exoneración y limitación de responsabilidad",
        "Verificar coherencia entre el clausulado y los anexos del contrato",
        "Evaluar mecanismos de modificación, adición y cesión contractual",
        
        # === REPORTE Y RECOMENDACIONES ===
        "Generar informes estructurados con hallazgos, observaciones y recomendaciones",
        "Clasificar observaciones por nivel de riesgo (alto, medio, bajo)",
        "Proponer redacciones alternativas para cláusulas deficientes",
        "Incluir referencias normativas y jurisprudenciales específicas",
        "Sugerir acciones correctivas y medidas de mitigación de riesgos",
            (
                "Al final de tu análisis, incluye un bloque de código JSON con la siguiente estructura:\n"
                "```json\n"
                "{\n"
                "  \"summary\": \"...resumen ejecutivo...\",\n"
                "  \"risk_scores\": {\"overall\": \"Medio\", \"legal\": \"Medio\", \"compliance\": \"Alto\", \"data_protection\": \"Medio\"},\n"
                "  \"clauses\": [\n"
                "    {\"type\": \"success\", \"name\": \"Cláusula de confidencialidad\", \"comment\": \"\", \"references\": [\"Ley 1581 de 2012\"]},\n"
                "    {\"type\": \"warning\", \"name\": \"Términos de pago\", \"comment\": \"Plazo ambiguo...\", \"references\": [\"Art. 882 del Código de Comercio\"]},\n"
                "    {\"type\": \"danger\", \"name\": \"Cláusula de terminación\", \"comment\": \"Condiciones de terminación unilateral potencialmente abusivas...\", \"references\": [\"Sentencia C-1008/2010 de la Corte Constitucional\"]}\n"
                "  ],\n"
                "  \"recommendations\": [\n"
                "    \"Aclarar los términos de pago especificando fechas concretas según el Art. 882 del Código de Comercio.\",\n"
                "    \"Revisar y detallar las obligaciones de las partes para evitar ambigüedades en las responsabilidades según la Ley 1480 de 2011.\",\n"
                "    \"Modificar la cláusula de terminación para asegurar condiciones equitativas para ambas partes según la doctrina de la Corte Constitucional.\"\n"
                "  ]\n"
                "}\n"
                "```\n"
                "En cada recomendación, incluye la referencia a la ley, decreto o jurisprudencia relevante (por ejemplo: 'Art. 882 del Código de Comercio', 'Ley 1480 de 2011', 'Sentencia C-1008/2010 de la Corte Constitucional').\n"
                "En cada cláusula identificada en el bloque JSON, agrega un campo 'references' que sea una lista de leyes, decretos o sentencias relevantes para esa cláusula.\n"
                "Usa los tipos: `success` (verde), `warning` (amarillo), `danger` (rojo) para las cláusulas."
            )
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
1. Resumen ejecutivo conciso (máximo 500 palabras)
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
    metrics = extract_analysis_metrics(response.content)
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
        },
        "risk_level": metrics["risk_level"],
        "num_clauses": metrics["num_clauses"],
        "num_risks": metrics["num_risks"],
        "compliance": metrics["compliance"]
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

def extract_json_from_markdown(text: str):
    match = re.search(r"```json\s*([\s\S]+?)```", text)
    if match:
        json_str = match.group(1)
        try:
            return json.loads(json_str)
        except Exception as e:
            raise ValueError(f"Error parsing JSON from agent: {e}")
    return None

async def analyze_contract_file(
    file_path: Optional[str] = None,
    text: Optional[str] = None,
    file_type: Optional[str] = None,
    contract_type: Optional[str] = None,
    language: str = "es",
    jurisdiction: str = "Colombia",
    analysis_options: Optional[dict] = None,
    instructions: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze a contract file or text and provide legal insights.
    
    Args:
        file_path: Path to the contract file
        text: Contract text content
        file_type: MIME type of the file
        contract_type: Type of the contract
        language: Language of the contract
        jurisdiction: Jurisdiction of the contract
        analysis_options: Additional options for analysis
        instructions: Optional instructions for analysis
        
    Returns:
        Dict containing analysis results
    """
    try:
        if not file_path and not text:
            raise ValueError("Either file_path or text must be provided")
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            content = text

        # Call the real analysis function
        analysis_response = await analyze_contract(
            contract_text=content,
            contract_type=contract_type,
            parties=[],  # Add parties if you have them
            specific_concerns=analysis_options.get("specificConcerns") if analysis_options else None,
            relevant_regulations=analysis_options.get("relevantRegulations") if analysis_options else None,
            data_processing=analysis_options.get("dataProcessing") if analysis_options else None
        )

        # Try to extract structured JSON from the agent's response
        structured = extract_json_from_markdown(analysis_response["summary"] if isinstance(analysis_response, dict) and "summary" in analysis_response else analysis_response)
        if structured:
            return structured
        # Fallback: return the old structure
        return {
            "status": "success",
            "message": "Análisis completado exitosamente",
            "data": analysis_response
        }
    except Exception as e:
        logger.error(f"Error analyzing contract: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing contract: {str(e)}"
        )

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

def extract_analysis_metrics(summary: str) -> dict:
    # Extract risk level
    risk_level_match = re.search(r'(?i)riesgo\s*potencial(?:es)?(?:\s*por\s*cl[aá]usula)?[\s\S]*?\*\*(Bajo|Medio|Alto)\*\*', summary)
    risk_level = risk_level_match.group(1) if risk_level_match else "Bajo"
    # Count clauses
    num_clauses = len(re.findall(r'Cl[aá]usula', summary, re.IGNORECASE))
    # Count risks
    num_risks = len(re.findall(r'Riesgo', summary, re.IGNORECASE))
    # Compliance: 100% if "cumple" or "alineadas" found, else 0
    compliance = 100 if re.search(r'cumple|alinead[ao]s?', summary, re.IGNORECASE) else 0
    return {
        "risk_level": risk_level,
        "num_clauses": num_clauses,
        "num_risks": num_risks,
        "compliance": compliance
    }

# Add to all agents:
# Implement decision explanation mechanisms
# Add transparency in processing
# Include user consent controls