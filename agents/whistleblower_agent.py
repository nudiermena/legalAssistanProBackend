import datetime
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
    get_retention_period
)
from typing import Dict, List, Optional
from datetime import datetime, timedelta

def create_whistleblower_agent() -> Agent:
    """Create a specialized agent for whistleblower agent with knowledge base integration"""
    # Create knowledge base integration
    knowledge_integration = create_agent_knowledge_integration("whistleblower_agent")
    """Create a specialized agent for whistleblower protection"""
    return Agent(
        name="Especialista en Protección al Denunciante",
        role="Especialista en protección de denunciantes con acceso a base de conocimiento legal",
        model=get_model("whistleblower"),
        knowledge=knowledge_integration,
        search_knowledge=True,
        storage=get_agent_storage("whistleblower_sessions"),
        instructions=[
                        # === KNOWLEDGE BASE INTEGRATION ===
            "Utiliza la base de conocimiento legal para obtener información actualizada y relevante",
            "Consulta términos legales específicos y sus definiciones de la base de conocimiento",
            "Busca en jurisprudencia y documentos legales almacenados en el sistema",
            "Aplica mejores prácticas documentadas en la base de conocimiento",
            "Cita fuentes específicas y referencias normativas de la base de conocimiento",
            
"Analizar denuncias y brindar orientación de protección",
            "Garantizar cumplimiento de leyes anticorrupción",
            "Proteger derechos y confidencialidad del denunciante",
            "Establecer procedimientos claros de denuncia",
            "Implementar medidas contra represalias",
            "Aplicar Ley 1778 de 2016 (Antisoborno)",
            "Cumplir Ley 1952 de 2019 (CGD)",
            "Seguir directrices de la Secretaría de Transparencia",
            "Proteger datos personales según Ley 1581",
            "Garantizar anonimato cuando sea solicitado",
            "Asegurar cadena de custodia probatoria",
            "Mantener reserva de la información",
            "Implementar canales seguros de denuncia",
            "Establecer protocolos de investigación",
            "Garantizar debido proceso"
        ],
        markdown=True
    )

async def analyze_whistleblower_report(
    report_content: str,
    report_type: str,
    jurisdiction: str,
    data_processing: Optional[Dict[str, str]] = None,
    specific_concerns: Optional[List[str]] = None
) -> Dict[str, str]:
    """Analizar denuncia con cumplimiento normativo colombiano"""
    agent = create_whistleblower_agent()

    # Create knowledge helper for enhanced analysis
    knowledge_helper = AgentKnowledgeHelper("whistleblower_agent")
    
    # Get relevant knowledge from knowledge base
    knowledge_results = await knowledge_helper.integration.search_knowledge(
        query="analyze whistleblower report",
        limit=5
    )
    
    # Get relevant legal terms
    legal_terms = knowledge_helper._extract_potential_terms(str(locals()))
    legal_definitions = {}
    if legal_terms:
        legal_definitions = await knowledge_helper.get_relevant_legal_terms(str(locals()))

    
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
    prompt = f"""Analizar la siguiente denuncia:

TIPO DE DENUNCIA: {report_type}
JURISDICCIÓN: {jurisdiction}

CONTENIDO DE LA DENUNCIA:
{report_content}

Por favor proporcionar:
1. Evaluación de validez y credibilidad:
   - Elementos probatorios
   - Fuentes de verificación
   - Consistencia del relato
   - Documentación soporte

2. Análisis de posibles infracciones:
   - Normativa aplicable
   - Conductas tipificadas
   - Sanciones previstas
   - Autoridades competentes

3. Medidas de protección requeridas:
   - Protección laboral
   - Protección física
   - Reserva de identidad
   - Garantías procesales

4. Procedimientos de denuncia:
   - Canales disponibles
   - Requisitos formales
   - Términos aplicables
   - Autoridades receptoras

5. Medidas anti-represalias:
   - Protecciones laborales
   - Garantías de estabilidad
   - Mecanismos de seguimiento
   - Acciones preventivas

6. Cronograma de investigación:
   - Etapas procesales
   - Plazos previstos
   - Actuaciones requeridas
   - Términos legales

7. Protección de datos personales:
   - Tratamiento autorizado
   - Medidas de seguridad
   - Período de retención
   - Derechos del titular
"""
    
    if specific_concerns:
        prompt += f"\nPREOCUPACIONES ESPECÍFICAS:\n{', '.join(specific_concerns)}\n"
    
    # Add data processing analysis if provided
    if data_processing:
        prompt += f"""
ANÁLISIS DE PROCESAMIENTO DE DATOS:
- Categoría de Datos: {data_compliance['category']}
- Período de Retención Requerido: {data_compliance['retention_period']} días
- Cumplimiento del Consentimiento: {'Válido' if data_compliance['consent_valid'] else 'Inválido'}
- Derechos Constitucionales: {', '.join(ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES)}
"""
    
    # Add Colombian legal framework requirements
    prompt += f"""
MARCO NORMATIVO COLOMBIANO:
- Principios Constitucionales: {', '.join(ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES)}
"""
    
    # Run the analysis
    response = agent.run(prompt)
    
    # Structure the response
    result = {
        "análisis": response.content,
        "tipo_denuncia": report_type,
        "jurisdiccion": jurisdiction,
        "cumplimiento_colombiano": {
            "principios_constitucionales": ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES,
            "fecha_análisis": datetime.now().isoformat()
        }
    }
    
    if specific_concerns:
        result["preocupaciones_específicas"] = specific_concerns
    
    # Add data processing details if provided
    if data_processing:
        result["procesamiento_datos"] = {
            "categoria": data_compliance["category"],
            "periodo_retencion": data_compliance["retention_period"],
            "consentimiento_valido": data_compliance["consent_valid"],
            "fecha_expiracion": (datetime.now() + timedelta(days=data_compliance["retention_period"])).isoformat()
        }
    
    return result

async def draft_whistleblower_policy(
    organization_type: str,
    jurisdiction: str,
    specific_requirements: Optional[List[str]] = None,
    data_processing: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    """Redactar política de denuncias según normativa colombiana"""
    agent = create_whistleblower_agent()

    # Create knowledge helper for enhanced analysis
    knowledge_helper = AgentKnowledgeHelper("whistleblower_agent")
    
    # Get relevant knowledge from knowledge base
    knowledge_results = await knowledge_helper.integration.search_knowledge(
        query="draft whistleblower policy",
        limit=5
    )
    
    # Get relevant legal terms
    legal_terms = knowledge_helper._extract_potential_terms(str(locals()))
    legal_definitions = {}
    if legal_terms:
        legal_definitions = await knowledge_helper.get_relevant_legal_terms(str(locals()))

    
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
    prompt = f"""Redactar política de denuncias para:

TIPO DE ORGANIZACIÓN: {organization_type}
JURISDICCIÓN: {jurisdiction}

La política debe incluir:
1. Procedimientos de denuncia:
   - Canales habilitados
   - Requisitos mínimos
   - Proceso de recepción
   - Confirmación de recibido

2. Medidas de protección:
   - Confidencialidad
   - Anonimato
   - Protección laboral
   - Garantías procesales

3. Disposiciones anti-represalias:
   - Prohibiciones expresas
   - Sanciones aplicables
   - Medidas preventivas
   - Seguimiento

4. Procedimientos de investigación:
   - Etapas del proceso
   - Responsables
   - Plazos
   - Garantías

5. Requisitos documentales:
   - Formatos establecidos
   - Evidencias requeridas
   - Cadena de custodia
   - Archivo y conservación

6. Protección de datos:
   - Autorización de tratamiento
   - Medidas de seguridad
   - Períodos de retención
   - Derechos ARCO

7. Marco normativo aplicable:
   - Ley 1778 de 2016
   - Ley 1952 de 2019
   - Ley 1581 de 2012
   - Directrices ST
"""
    
    if specific_requirements:
        prompt += f"\nREQUISITOS ESPECÍFICOS:\n{', '.join(specific_requirements)}\n"
    
    # Add data processing analysis if provided
    if data_processing:
        prompt += f"""
ANÁLISIS DE PROCESAMIENTO DE DATOS:
- Categoría de Datos: {data_compliance['category']}
- Período de Retención Requerido: {data_compliance['retention_period']} días
- Cumplimiento del Consentimiento: {'Cumplido' if data_compliance['consent_valid'] else 'No Cumplido'}
- Derechos Constitucionales: {', '.join(ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES)}
"""
    
    # Add Colombian legal framework requirements
    prompt += f"""
MARCO NORMATIVO COLOMBIANO:
- Principios Constitucionales: {', '.join(ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES)}
"""
    
    # Run the drafting
    response = agent.run(prompt)
    
    # Structure the response in Spanish
    result = {
        "politica": response.content,
        "tipo_organizacion": organization_type,
        "jurisdiccion": jurisdiction,
        "cumplimiento_colombiano": {
            "principios_constitucionales": ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES,
            "fecha_elaboracion": datetime.now().isoformat()
        }
    }
    
    if specific_requirements:
        result["requisitos_especificos"] = specific_requirements
    
    # Add data processing details if provided
    if data_processing:
        result["tratamiento_datos"] = {
            "categoria": data_compliance["category"],
            "periodo_retencion": data_compliance["retention_period"],
            "consentimiento_valido": data_compliance["consent_valid"],
            "fecha_expiracion": (datetime.now() + timedelta(days=data_compliance["retention_period"])).isoformat()
        }
    
    return result 