from agno.agent import Agent
from config.database import get_agent_storage
from config.ai_models import get_model
from config.knowledge_base_integration import (
    create_agent_knowledge_integration,
    AgentKnowledgeHelper
)
from config.colombian_compliance import (
    ColombianDataProtection,
    ColombianLegalFramework,
    get_data_category,
    validate_consent,
    get_retention_period,
    get_administrative_deadline
)
from typing import Dict, List, Optional
from datetime import datetime, timedelta

def create_compliance_agent() -> Agent:
    """Create a specialized agent for compliance analysis with knowledge base integration"""
    # Create knowledge base integration
    knowledge_integration = create_agent_knowledge_integration("compliance_agent")
    
    return Agent(
        name="Analista de Cumplimiento",
        role="Especialista en cumplimiento regulatorio con acceso a base de conocimiento legal",
        model=get_model("compliance"),
        knowledge=knowledge_integration,
        search_knowledge=True,
        storage=get_agent_storage("compliance_sessions"),
        instructions=[
            # === KNOWLEDGE BASE INTEGRATION ===
            "Utiliza la base de conocimiento legal para obtener información actualizada sobre cumplimiento regulatorio",
            "Consulta términos legales específicos relacionados con cumplimiento y sus definiciones",
            "Busca en marcos regulatorios y jurisprudencia relevante sobre cumplimiento",
            "Aplica mejores prácticas de cumplimiento documentadas en el sistema",
            "Cita fuentes específicas y referencias normativas de la base de conocimiento",
            
            "Analizar cumplimiento normativo colombiano",
            "Evaluar requisitos de protección de datos personales",
            "Verificar conformidad con Ley 1581 de 2012",
            "Aplicar estándares de la SIC y otras autoridades",
            "Evaluar políticas de tratamiento de datos",
            "Verificar autorizaciones y consentimientos",
            "Analizar medidas de seguridad de la información",
            "Revisar procedimientos administrativos",
            "Evaluar cumplimiento constitucional",
            "Verificar requisitos sectoriales específicos",
            "Analizar riesgos de incumplimiento",
            "Recomendar medidas correctivas",
            "Evaluar impacto en derechos fundamentales",
            "Verificar períodos de retención de datos",
            "Asegurar transparencia en el tratamiento"
        ],
        markdown=True
    )

async def analyze_regulatory_change(
    regulation_text: str,
    effective_date: str,
    industry: str,
    business_operations: list,
    current_compliance_status: dict,
    data_processing: Optional[Dict[str, str]] = None
) -> dict:
    """Analyze regulatory changes and their impact on business operations with knowledge base integration"""
    agent = create_compliance_agent()
    
    # Create knowledge helper for enhanced analysis
    knowledge_helper = AgentKnowledgeHelper("compliance_agent")
    
    # Get relevant compliance knowledge from knowledge base
    compliance_knowledge = await knowledge_helper.integration.get_agent_specific_knowledge("compliance")
    
    # Get relevant regulatory frameworks
    regulatory_frameworks = await knowledge_helper.integration.get_agent_specific_knowledge("frameworks")
    
    # Get relevant legal terms
    legal_terms = knowledge_helper._extract_potential_terms(regulation_text)
    legal_definitions = {}
    if legal_terms:
        legal_definitions = await knowledge_helper.get_relevant_legal_terms(regulation_text)
    
    # Format current compliance status for the prompt
    compliance_status_text = "\n".join([f"- {key}: {value}" for key, value in current_compliance_status.items()])
    
    # Get data processing details if provided
    data_compliance = {}
    if data_processing:
        data_category = get_data_category(data_processing.get("type", "personal"))
        retention_period = get_retention_period(data_category)
        consent_valid = validate_consent(data_processing.get("consent", {}))
        data_compliance = {
            "category": data_category.value,
            "retention_period": retention_period,
            "consent_valid": consent_valid
        }
    
    # Prepare the prompt
    prompt = f"""Analizar el siguiente cambio regulatorio y su impacto en la operación:

NUEVA REGULACIÓN:
{regulation_text}

FECHA DE VIGENCIA: {effective_date}
SECTOR: {industry}
OPERACIONES: {', '.join(business_operations)}
ESTADO ACTUAL DE CUMPLIMIENTO:
{compliance_status_text}

Por favor proporcionar:
1. Resumen ejecutivo de cambios principales
2. Áreas/departamentos afectados
3. Cambios operativos requeridos con nivel de dificultad
4. Sistemas tecnológicos que requieren actualización
5. Nuevos requisitos de documentación y registro
6. Necesidades de capacitación del personal
7. Cronograma de acciones priorizadas
8. Costos estimados y recursos necesarios
9. Impactos competitivos potenciales
10. Estrategia de cumplimiento recomendada
11. Evaluación de conformidad con marco legal colombiano
12. Alineación con principios constitucionales
13. Cumplimiento de protección de datos (Ley 1581 de 2012)
14. Requisitos de procedimientos administrativos
15. Medidas de seguridad requeridas
"""
    
    # Add knowledge base context
    if compliance_knowledge:
        prompt += "\n\nCONOCIMIENTO DE CUMPLIMIENTO DE REFERENCIA:\n"
        for knowledge in compliance_knowledge[:3]:  # Top 3 most relevant
            prompt += f"- {knowledge.get('content', '')[:200]}...\n"
    
    if regulatory_frameworks:
        prompt += "\nMARCO REGULATORIO RELEVANTE:\n"
        for framework in regulatory_frameworks[:2]:  # Top 2 most relevant
            prompt += f"- {framework.get('content', '')[:200]}...\n"
    
    if legal_definitions:
        prompt += "\nTÉRMINOS LEGALES RELEVANTES:\n"
        for term, definition in legal_definitions.items():
            prompt += f"- {term}: {definition}\n"
    
    # Add data processing analysis if provided
    if data_processing:
        prompt += f"""
ANÁLISIS DE TRATAMIENTO DE DATOS:
- Categoría de Datos: {data_compliance['category']}
- Período de Retención Requerido: {data_compliance['retention_period']} días
- Cumplimiento de Consentimiento: {'Válido' if data_compliance['consent_valid'] else 'Inválido'}
- Derechos Constitucionales: {', '.join(ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES)}
"""
    
    # Run the analysis
    response = agent.run(prompt)
    
    # Structure the response
    result = {
        "analysis": response.content,
        "regulation_summary": regulation_text[:200] + "...",
        "effective_date": effective_date,
        "industry": industry,
        "colombian_compliance": {
            "constitutional_principles": ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES,
            "analysis_date": datetime.now().isoformat()
        },
        "knowledge_base_usage": {
            "compliance_knowledge_found": len(compliance_knowledge),
            "regulatory_frameworks_found": len(regulatory_frameworks),
            "legal_terms_found": len(legal_definitions),
            "knowledge_sources": [
                {"type": "compliance_knowledge", "count": len(compliance_knowledge)},
                {"type": "regulatory_frameworks", "count": len(regulatory_frameworks)},
                {"type": "legal_terms", "count": len(legal_definitions)}
            ]
        }
    }
    
    # Add data processing details if provided
    if data_processing:
        result["data_processing"] = {
            "category": data_compliance["category"],
            "retention_period": data_compliance["retention_period"],
            "consent_valid": data_compliance["consent_valid"],
            "expiry_date": (datetime.now() + timedelta(days=data_compliance["retention_period"])).isoformat()
        }
    
    return result

async def assess_compliance_status(
    business_operations: List[str],
    current_policies: Dict[str, str],
    regulatory_framework: str,
    data_processing: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    """Assess current compliance status with Colombian requirements and knowledge base integration"""
    agent = create_compliance_agent()
    
    # Create knowledge helper for enhanced analysis
    knowledge_helper = AgentKnowledgeHelper("compliance_agent")
    
    # Get relevant compliance knowledge from knowledge base
    compliance_knowledge = await knowledge_helper.integration.get_agent_specific_knowledge("compliance")
    
    # Get relevant legal terms
    legal_terms = knowledge_helper._extract_potential_terms(
        " ".join(business_operations + list(current_policies.values()))
    )
    legal_definitions = {}
    if legal_terms:
        legal_definitions = await knowledge_helper.get_relevant_legal_terms(
            " ".join(business_operations + list(current_policies.values()))
        )
    
    # Format current policies for the prompt
    policies_text = "\n".join([f"- {key}: {value}" for key, value in current_policies.items()])
    
    # Get data processing details if provided
    data_compliance = {}
    if data_processing:
        data_category = get_data_category(data_processing.get("type", "personal"))
        retention_period = get_retention_period(data_category)
        consent_valid = validate_consent(data_processing.get("consent", {}))
        data_compliance = {
            "category": data_category.value,
            "retention_period": retention_period,
            "consent_valid": consent_valid
        }
    
    # Prepare the prompt
    prompt = f"""Evaluar el estado de cumplimiento para las siguientes operaciones:

OPERACIONES:
{', '.join(business_operations)}

POLÍTICAS ACTUALES:
{policies_text}

MARCO REGULATORIO:
{regulatory_framework}

Por favor proporcionar:
1. Calificación general de cumplimiento
2. Brechas de cumplimiento identificadas
3. Actualizaciones requeridas de políticas
4. Mejoras necesarias en procesos
5. Requisitos de documentación
6. Recomendaciones de capacitación
7. Evaluación de riesgos
8. Implicaciones de costos
9. Cronograma de cumplimiento
10. Conformidad con marco legal colombiano
11. Alineación con principios constitucionales
12. Cumplimiento de protección de datos
13. Conformidad con procedimientos administrativos
14. Medidas de seguridad implementadas
15. Gestión de autorizaciones y consentimientos
"""
    
    # Add knowledge base context
    if compliance_knowledge:
        prompt += "\n\nCONOCIMIENTO DE CUMPLIMIENTO DE REFERENCIA:\n"
        for knowledge in compliance_knowledge[:3]:  # Top 3 most relevant
            prompt += f"- {knowledge.get('content', '')[:200]}...\n"
    
    if legal_definitions:
        prompt += "\nTÉRMINOS LEGALES RELEVANTES:\n"
        for term, definition in legal_definitions.items():
            prompt += f"- {term}: {definition}\n"
    
    # Add data processing analysis if provided
    if data_processing:
        prompt += f"""
ANÁLISIS DE TRATAMIENTO DE DATOS:
- Categoría de Datos: {data_compliance['category']}
- Período de Retención Requerido: {data_compliance['retention_period']} días
- Cumplimiento de Consentimiento: {'Válido' if data_compliance['consent_valid'] else 'Inválido'}
- Derechos Constitucionales: {', '.join(ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES)}
"""
    
    # Run the analysis
    response = agent.run(prompt)
    
    # Structure the response
    result = {
        "analysis": response.content,
        "business_operations": business_operations,
        "regulatory_framework": regulatory_framework,
        "colombian_compliance": {
            "constitutional_principles": ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES,
            "analysis_date": datetime.now().isoformat()
        },
        "knowledge_base_usage": {
            "compliance_knowledge_found": len(compliance_knowledge),
            "legal_terms_found": len(legal_definitions),
            "knowledge_sources": [
                {"type": "compliance_knowledge", "count": len(compliance_knowledge)},
                {"type": "legal_terms", "count": len(legal_definitions)}
            ]
        }
    }
    
    # Add data processing details if provided
    if data_processing:
        result["data_processing"] = {
            "category": data_compliance["category"],
            "retention_period": data_compliance["retention_period"],
            "consent_valid": data_compliance["consent_valid"],
            "expiry_date": (datetime.now() + timedelta(days=data_compliance["retention_period"])).isoformat()
        }
    
    return result 