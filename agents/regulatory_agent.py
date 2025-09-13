from agno.agent import Agent
from config.database import get_agent_storage
from config.ai_models import get_model
from config.knowledge_base_integration import (
    create_agent_knowledge_integration,
    AgentKnowledgeHelper
)
from config.colombian_compliance import (
    ColombianLegalFramework,
    get_legal_term,
    get_data_category,
    validate_consent
)
from typing import Dict, List, Optional
from datetime import datetime

def create_regulatory_agent() -> Agent:
    """Create a specialized agent for regulatory agent with knowledge base integration"""
    # Create knowledge base integration
    knowledge_integration = create_agent_knowledge_integration("regulatory_agent")
    """Create a specialized agent for regulatory analysis"""
    return Agent(
        name="Especialista en Análisis Regulatorio",
        role="Especialista en cumplimiento normativo colombiano con acceso a base de conocimiento legal",
        model=get_model("regulatory"),
        knowledge=knowledge_integration,
        search_knowledge=True,
        storage=get_agent_storage("regulatory_sessions"),
        instructions=[
                        # === KNOWLEDGE BASE INTEGRATION ===
            "Utiliza la base de conocimiento legal para obtener información actualizada y relevante",
            "Consulta términos legales específicos y sus definiciones de la base de conocimiento",
            "Busca en jurisprudencia y documentos legales almacenados en el sistema",
            "Aplica mejores prácticas documentadas en la base de conocimiento",
            "Cita fuentes específicas y referencias normativas de la base de conocimiento",
            
"Analizar marco regulatorio sectorial colombiano",
            "Evaluar cumplimiento de requisitos específicos",
            "Identificar riesgos regulatorios y de cumplimiento",
            "Verificar licencias y permisos requeridos",
            "Asegurar cumplimiento de normas técnicas colombianas",
            "Considerar conceptos de autoridades competentes",
            "Evaluar impacto de nueva normatividad",
            "Proponer estrategias de compliance",
            "Proteger derechos constitucionales colectivos",
            "Mantener actualización normativa permanente",
            "Verificar regímenes especiales aplicables",
            "Evaluar requisitos ambientales y sociales",
            "Considerar normativa territorial",
            "Analizar obligaciones de reporte",
            "Recomendar controles de cumplimiento"
        ],
        markdown=True
    )

async def analyze_regulatory_compliance(
    organization_type: str,
    jurisdiction: str,
    regulatory_framework: List[str],
    data_processing: Optional[Dict[str, str]] = None,
    specific_requirements: Optional[List[str]] = None,
    legal_terms: Optional[List[str]] = None
) -> Dict[str, str]:
    """Analizar cumplimiento regulatorio según marco normativo colombiano"""
    agent = create_regulatory_agent()

    # Create knowledge helper for enhanced analysis
    knowledge_helper = AgentKnowledgeHelper("regulatory_agent")
    
    # Get relevant knowledge from knowledge base
    knowledge_results = await knowledge_helper.integration.search_knowledge(
        query="analyze regulatory compliance",
        limit=5
    )
    
    # Get relevant legal terms
    legal_terms = knowledge_helper._extract_potential_terms(str(locals()))
    legal_definitions = {}
    if legal_terms:
        legal_definitions = await knowledge_helper.get_relevant_legal_terms(str(locals()))

    
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
    
    # Update prompt in Spanish
    prompt = f"""Analizar el cumplimiento regulatorio para la siguiente organización:

TIPO DE ORGANIZACIÓN: {organization_type}
JURISDICCIÓN: {jurisdiction}
MARCO REGULATORIO: {', '.join(regulatory_framework)}
"""
    
    if specific_requirements:
        prompt += f"\nREQUISITOS ESPECÍFICOS:\n{', '.join(specific_requirements)}\n"
    
    prompt += f"""
MARCO JURÍDICO COLOMBIANO:
- Principios Constitucionales: {', '.join(ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES)}
- Autoridades Competentes:
  * Superintendencias aplicables
  * Entidades de vigilancia y control
  * Autoridades territoriales
  * Entes reguladores sectoriales

RÉGIMEN REGULATORIO:
1. Normativa General:
   - Constitución Política
   - Leyes marco
   - Decretos reglamentarios
   - Resoluciones aplicables

2. Normativa Sectorial:
   - Regulación específica
   - Circulares y conceptos
   - Normas técnicas
   - Estándares sectoriales

3. Normativa Territorial:
   - Ordenanzas departamentales
   - Acuerdos municipales
   - Decretos locales
   - Planes de ordenamiento
"""
    
    if legal_term_definitions:
        prompt += "\nTÉRMINOS JURÍDICOS RELEVANTES:\n"
        for term, definition in legal_term_definitions.items():
            prompt += f"- {term}: {definition}\n"
    
    if data_processing:
        prompt += f"""
REQUISITOS DE TRATAMIENTO DE DATOS:
- Categoría de Datos: {data_compliance['category']}
- Cumplimiento de Consentimiento: {'Válido' if data_compliance['consent_valid'] else 'Inválido'}
- Derechos Constitucionales: {', '.join(ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES)}
- Régimen de Protección:
  * Ley 1581 de 2012
  * Decreto 1377 de 2013
  * Circulares SIC
  * Guías de responsabilidad demostrada
"""
    
    prompt += """
Por favor proporcionar:
1. Análisis de regulación aplicable:
   - Normativa general
   - Regulación sectorial
   - Disposiciones territoriales
   - Actos administrativos relevantes

2. Evaluación de requisitos de cumplimiento:
   - Licencias requeridas
   - Permisos necesarios
   - Autorizaciones especiales
   - Registros obligatorios

3. Análisis de brechas:
   - Cumplimiento actual
   - Requisitos pendientes
   - Acciones correctivas
   - Planes de mejora

4. Evaluación de riesgos:
   - Riesgos regulatorios
   - Riesgos sancionatorios
   - Riesgos reputacionales
   - Impacto potencial

5. Recomendaciones de cumplimiento:
   - Acciones inmediatas
   - Medidas preventivas
   - Controles internos
   - Mejores prácticas

6. Cronograma de implementación:
   - Priorización de acciones
   - Plazos de cumplimiento
   - Hitos principales
   - Seguimiento

7. Recursos necesarios:
   - Recursos humanos
   - Recursos tecnológicos
   - Recursos financieros
   - Capacitación requerida

8. Análisis constitucional:
   - Principios aplicables
   - Derechos fundamentales
   - Mecanismos de protección
   - Jurisprudencia relevante

9. Procedimientos administrativos:
   - Trámites requeridos
   - Términos aplicables
   - Recursos procedentes
   - Autoridades competentes

10. Protección de datos:
    - Políticas requeridas
    - Autorizaciones necesarias
    - Medidas de seguridad
    - Procedimientos internos

11. Derechos constitucionales:
    - Derechos afectados
    - Mecanismos de garantía
    - Acciones preventivas
    - Protocolos de atención

12. Cumplimiento terminológico:
    - Definiciones aplicables
    - Interpretaciones autorizadas
    - Alcance normativo
    - Referencias técnicas

Presentar este análisis en formato adecuado para asesoría en cumplimiento regulatorio.
"""
    
    # Run the analysis
    response = agent.run(prompt)
    
    # Structure the response in Spanish
    result = {
        "analisis": response.content,
        "tipo_organizacion": organization_type,
        "jurisdiccion": jurisdiction,
        "marco_regulatorio": regulatory_framework,
        "cumplimiento_colombiano": {
            "principios_constitucionales": ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES,
            "fecha_analisis": datetime.now().isoformat()
        }
    }
    
    if specific_requirements:
        result["requisitos_especificos"] = specific_requirements
    
    if legal_term_definitions:
        result["terminos_juridicos"] = legal_term_definitions
    
    if data_processing:
        result["tratamiento_datos"] = {
            "categoria": data_compliance["category"],
            "consentimiento_valido": data_compliance["consent_valid"]
        }
    
    return result 