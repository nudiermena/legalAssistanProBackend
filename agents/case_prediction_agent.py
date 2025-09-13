from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from agno.agent import Agent
from agno.tools.googlesearch import GoogleSearchTools
from config.database import get_agent_storage
from config.ai_models import get_model
from config.knowledge_base_integration import (
    create_agent_knowledge_integration,
    AgentKnowledgeHelper
)
from frameworks.colombian_legal_framework import ColombianLegalFramework
from models.case_prediction import CasePredictionRequest

class CasePredictionAgent(Agent):
    def __init__(self):
        # Create knowledge base integration
        knowledge_integration = create_agent_knowledge_integration("case_prediction_agent")
        
        super().__init__(
            model=get_model("case_prediction"),
            tools=[GoogleSearchTools()],
            knowledge=knowledge_integration,
            search_knowledge=True,
            storage=get_agent_storage("case_prediction_sessions")
        )
        self.framework = ColombianLegalFramework()
        self.get_legal_term = lambda x: ""  # TODO: Implement or import get_legal_term
        self.get_administrative_deadline = lambda x: 15  # TODO: Implement or import get_administrative_deadline
        self.knowledge_helper = AgentKnowledgeHelper("case_prediction_agent")

    async def predict_case(self, request: CasePredictionRequest) -> Dict[str, Any]:
        """
        Predicts the outcome and provides analysis for a legal case with knowledge base integration.
        """
        try:
            # Get relevant knowledge from knowledge base
            case_knowledge = await self.knowledge_helper.integration.get_agent_specific_knowledge("cases")
            
            # Get relevant jurisprudence
            jurisprudence = await self.knowledge_helper.integration.get_jurisprudence(
                topic=request.case_type,
                limit=5
            )
            
            # Get relevant legal terms
            legal_terms = self.knowledge_helper._extract_potential_terms(
                " ".join(request.key_facts + request.legal_issues)
            )
            legal_definitions = {}
            if legal_terms:
                legal_definitions = await self.knowledge_helper.get_relevant_legal_terms(
                    " ".join(request.key_facts + request.legal_issues)
                )
            
            # Create the analysis prompt
            prompt = self._create_analysis_prompt(request, case_knowledge, jurisprudence, legal_definitions)
            
            # Get the AI analysis
            response = await self.arun(prompt)
            
            # Extract the content from the response
            ai_analysis = response.content if hasattr(response, 'content') else str(response)
            
            # Process and structure the response
            prediction = {
                "probability_of_success": self._calculate_success_probability(request),
                "estimated_duration": self._estimate_case_duration(request),
                "key_recommendations": self._generate_recommendations(request),
                "risk_factors": self._identify_risk_factors(request),
                "suggested_strategy": self._suggest_legal_strategy(request),
                "ai_analysis": ai_analysis,
                "timestamp": datetime.now().isoformat(),
                "knowledge_base_usage": {
                    "case_knowledge_found": len(case_knowledge),
                    "jurisprudence_found": len(jurisprudence),
                    "legal_terms_found": len(legal_definitions),
                    "knowledge_sources": [
                        {"type": "case_knowledge", "count": len(case_knowledge)},
                        {"type": "jurisprudence", "count": len(jurisprudence)},
                        {"type": "legal_terms", "count": len(legal_definitions)}
                    ]
                }
            }

            return prediction

        except Exception as e:
            raise Exception(f"Error predicting case: {str(e)}")

    def _create_analysis_prompt(self, request: CasePredictionRequest, case_knowledge: List[Dict], jurisprudence: List[Dict], legal_definitions: Dict[str, str]) -> str:
        """Creates a detailed prompt for AI analysis with knowledge base context"""
        prompt = f"""Analizar el siguiente caso legal y proporcionar una evaluación detallada:

TIPO DE CASO: {self.framework.get_case_type_name(request.case_type)}
JURISDICCIÓN: {request.jurisdiction}
HECHOS RELEVANTES:
{chr(10).join(f"- {fact}" for fact in request.key_facts)}

PROBLEMAS JURÍDICOS:
{chr(10).join(f"- {issue}" for issue in request.legal_issues)}

{f'JUEZ: {request.judge_name}' if request.judge_name else ''}
{f'CONTRAPARTE: {request.opposing_counsel}' if request.opposing_counsel else ''}

{f'PRECEDENTES RELEVANTES:' if request.relevant_precedents else ''}
{chr(10).join(f"- {precedent}" for precedent in (request.relevant_precedents or []))}

{f'PROCEDIMIENTO ADMINISTRATIVO: {self.framework.get_administrative_procedure_name(request.administrative_procedure)}' if request.administrative_procedure else ''}
"""
        
        # Add knowledge base context
        if case_knowledge:
            prompt += "\nCONOCIMIENTO DE CASOS SIMILARES:\n"
            for knowledge in case_knowledge[:3]:  # Top 3 most relevant
                prompt += f"- {knowledge.get('content', '')[:200]}...\n"
        
        if jurisprudence:
            prompt += "\nJURISPRUDENCIA RELEVANTE:\n"
            for jur in jurisprudence[:3]:  # Top 3 most relevant
                prompt += f"- {jur.get('topic', 'N/A')}: {jur.get('summary', '')[:200]}...\n"
        
        if legal_definitions:
            prompt += "\nTÉRMINOS LEGALES RELEVANTES:\n"
            for term, definition in legal_definitions.items():
                prompt += f"- {term}: {definition}\n"
        
        prompt += """
Por favor proporcionar:
1. Análisis de viabilidad jurídica
2. Probabilidad de éxito estimada
3. Factores críticos que pueden influir en el resultado
4. Estrategias recomendadas
5. Riesgos potenciales
6. Recomendaciones específicas

Presentar el análisis en formato estructurado y detallado."""

        return prompt

    def _calculate_success_probability(self, request: CasePredictionRequest) -> float:
        """Calculate the estimated probability of success based on multiple factors"""
        base_probability = 0.5  # Start with neutral probability
        
        # Adjust based on case type and jurisdiction
        case_type_factors = {
            "proceso_laboral": 0.1,  # Labor cases tend to favor employees
            "proceso_civil": 0.0,    # Neutral
            "proceso_penal": -0.1,   # Criminal cases are more challenging
            "proceso_administrativo": -0.05,
            "proceso_comercial": 0.0
        }
        
        # Add case type adjustment
        base_probability += case_type_factors.get(request.case_type, 0.0)
        
        # Adjust based on number of supporting facts and legal issues
        fact_strength = min(len(request.key_facts) * 0.05, 0.2)  # Max 20% boost from facts
        base_probability += fact_strength
        
        # Reduce probability based on complexity (number of legal issues)
        complexity_penalty = min(len(request.legal_issues) * 0.03, 0.15)
        base_probability -= complexity_penalty
        
        # Adjust based on precedents if available
        if request.relevant_precedents:
            precedent_boost = min(len(request.relevant_precedents) * 0.05, 0.15)
            base_probability += precedent_boost
        
        # Ensure probability stays between 0 and 1
        return max(min(base_probability, 1.0), 0.0)

    def _estimate_case_duration(self, request: CasePredictionRequest) -> Dict[str, Any]:
        """Estimate case duration based on type and complexity"""
        # Base duration in months for each case type
        base_durations = {
            "proceso_laboral": {"min": 4, "max": 8},
            "proceso_civil": {"min": 6, "max": 12},
            "proceso_penal": {"min": 8, "max": 18},
            "proceso_administrativo": {"min": 12, "max": 24},
            "proceso_comercial": {"min": 6, "max": 15}
        }
        
        base = base_durations.get(request.case_type, {"min": 6, "max": 12})
        
        # Adjust for complexity
        complexity_factor = len(request.legal_issues) * 0.5  # Each issue adds 2 weeks
        
        # Adjust for administrative procedure
        admin_procedure_factor = 3 if request.administrative_procedure else 0
        
        min_months = base["min"] + complexity_factor + admin_procedure_factor
        max_months = base["max"] + complexity_factor + admin_procedure_factor
        
        # Calculate confidence based on available information
        confidence = 0.9
        if len(request.key_facts) < 3:
            confidence -= 0.1
        if len(request.legal_issues) > 5:
            confidence -= 0.1
        if not request.relevant_precedents:
            confidence -= 0.1
        
        return {
            "min_months": round(min_months),
            "max_months": round(max_months),
            "confidence": round(confidence, 2)
        }

    def _generate_recommendations(self, request: CasePredictionRequest) -> list[str]:
        """Generate specific recommendations based on case details"""
        recommendations = []
        
        # Basic recommendations based on case type
        case_type_recs = {
            "proceso_laboral": [
                "Recopilar documentación laboral completa (contratos, nóminas, comunicaciones)",
                "Verificar cumplimiento de normativas laborales específicas",
                "Considerar peritaje para cálculos de prestaciones"
            ],
            "proceso_civil": [
                "Asegurar documentación probatoria de obligaciones civiles",
                "Evaluar posibilidad de medidas cautelares",
                "Preparar cronología detallada de hechos"
            ],
            "proceso_penal": [
                "Recopilar evidencia forense disponible",
                "Identificar y contactar testigos potenciales",
                "Preparar línea de tiempo detallada de eventos"
            ]
        }
        recommendations.extend(case_type_recs.get(request.case_type, []))
        
        # Add recommendations based on case complexity
        if len(request.legal_issues) > 3:
            recommendations.append("Considerar la división del caso en etapas manejables")
            recommendations.append("Preparar informes específicos para cada problema jurídico")
        
        # Add recommendations based on available precedents
        if not request.relevant_precedents:
            recommendations.append("Realizar búsqueda exhaustiva de jurisprudencia similar")
        
        # Add administrative procedure recommendations
        if request.administrative_procedure:
            recommendations.extend([
                "Verificar plazos administrativos aplicables",
                "Preparar recursos administrativos preventivamente",
                "Mantener registro detallado de comunicaciones administrativas"
            ])
        
        return recommendations

    def _identify_risk_factors(self, request: CasePredictionRequest) -> list[Dict[str, Any]]:
        """Identify specific risk factors based on case details"""
        risk_factors = []
        
        # Assess complexity risk
        if len(request.legal_issues) > 3:
            risk_factors.append({
                "factor": "Complejidad del caso",
                "risk_level": "alto" if len(request.legal_issues) > 5 else "medio",
                "description": f"Caso involucra {len(request.legal_issues)} problemas jurídicos distintos"
            })
        
        # Assess precedent risk
        if not request.relevant_precedents:
            risk_factors.append({
                "factor": "Falta de precedentes",
                "risk_level": "alto",
                "description": "No se identificaron precedentes jurídicos relevantes"
            })
        
        # Assess procedural risks
        if request.administrative_procedure:
            risk_factors.append({
                "factor": "Procedimiento administrativo",
                "risk_level": "medio",
                "description": "Requiere cumplimiento de plazos y procedimientos específicos"
            })
        
        # Assess documentation risks
        if len(request.key_facts) < 3:
            risk_factors.append({
                "factor": "Base factual limitada",
                "risk_level": "alto",
                "description": "Cantidad limitada de hechos documentados"
            })
        
        # Add case-type specific risks
        case_type_risks = {
            "proceso_laboral": {
                "factor": "Carga probatoria",
                "risk_level": "medio",
                "description": "Necesidad de documentación laboral exhaustiva"
            },
            "proceso_penal": {
                "factor": "Estándar probatorio",
                "risk_level": "alto",
                "description": "Requiere prueba más allá de duda razonable"
            }
        }
        
        if request.case_type in case_type_risks:
            risk_factors.append(case_type_risks[request.case_type])
        
        return risk_factors

    def _suggest_legal_strategy(self, request: CasePredictionRequest) -> Dict[str, Any]:
        """Suggest detailed legal strategy based on case specifics"""
        # Define base strategy based on case type
        case_strategies = {
            "proceso_laboral": {
                "primary": "Enfoque en documentación y cumplimiento normativo laboral",
                "actions": [
                    "Recopilar documentación laboral completa",
                    "Analizar cumplimiento de normativas laborales",
                    "Preparar cálculos de prestaciones"
                ]
            },
            "proceso_civil": {
                "primary": "Estrategia probatoria documental",
                "actions": [
                    "Asegurar evidencia documental",
                    "Preparar testimonios clave",
                    "Evaluar medidas cautelares"
                ]
            },
            "proceso_penal": {
                "primary": "Defensa técnica exhaustiva",
                "actions": [
                    "Analizar elementos del tipo penal",
                    "Preparar teoría del caso",
                    "Evaluar pruebas disponibles"
                ]
            }
        }
        
        base_strategy = case_strategies.get(request.case_type, {
            "primary": "Enfoque en evidencia documental",
            "actions": ["Preparar documentación probatoria"]
        })
        
        # Adjust strategy based on case complexity
        alternative_strategies = []
        if len(request.legal_issues) > 3:
            alternative_strategies.append("Dividir caso en fases procesales")
        
        if request.administrative_procedure:
            alternative_strategies.append("Agotar vía administrativa previamente")
        
        if not request.relevant_precedents:
            alternative_strategies.append("Buscar jurisprudencia favorable")
        
        # Add specific actions based on case details
        key_actions = base_strategy["actions"].copy()
        
        if request.judge_name:
            key_actions.append("Analizar criterios previos del juez asignado")
        
        if request.opposing_counsel:
            key_actions.append("Estudiar estrategias comunes de la contraparte")
        
        return {
            "primary_strategy": base_strategy["primary"],
            "alternative_strategies": alternative_strategies,
            "key_actions": key_actions,
            "priority_level": "alta" if len(request.legal_issues) > 3 else "media",
            "timeline": "inmediata" if request.administrative_procedure else "regular"
        }

def create_case_prediction_agent() -> CasePredictionAgent:
    """Creates and returns a new instance of the CasePredictionAgent"""
    return CasePredictionAgent()

async def predict_case_outcome(
    case_type: str,
    jurisdiction: str,
    key_facts: list,
    legal_issues: list,
    judge_name: str = None,
    opposing_counsel: str = None,
    relevant_precedents: list = None,
    administrative_procedure: Optional[str] = None,
    legal_terms: Optional[List[str]] = None
) -> Dict[str, str]:
    """Predict case outcomes and provide litigation strategy recommendations"""
    agent = create_case_prediction_agent()
    
    # Get Colombian legal terms if provided
    legal_term_definitions = {}
    if legal_terms:
        legal_term_definitions = {term: agent.get_legal_term(term) for term in legal_terms if agent.get_legal_term(term)}
    
    # Get administrative deadlines if applicable
    deadlines = {}
    if administrative_procedure:
        response_time = agent.get_administrative_deadline("response_time")
        appeal_time = agent.get_administrative_deadline("appeal_time")
        recourse_time = agent.get_administrative_deadline("recourse_time")
        deadlines = {
            "response": response_time,
            "appeal": appeal_time,
            "recourse": recourse_time
        }
    
    # Add CONSTITUTIONAL_PRINCIPLES to the framework class if not present
    if not hasattr(ColombianLegalFramework, 'CONSTITUTIONAL_PRINCIPLES'):
        ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES = [
            "Dignidad humana",
            "Debido proceso",
            "Igualdad ante la ley",
            "Presunción de inocencia",
            "Derecho de defensa",
            "Acceso a la justicia"
        ]
    
    # Prepare the prompt
    prompt = f"""Analizar los siguientes detalles del caso y predecir el resultado probable:

TIPO DE CASO: {case_type}
JURISDICCIÓN: {jurisdiction}
HECHOS RELEVANTES: {', '.join(key_facts)}
PROBLEMAS JURÍDICOS: {', '.join(legal_issues)}
"""
    
    if judge_name:
        prompt += f"JUEZ/MAGISTRADO: {judge_name}\n"
    
    if opposing_counsel:
        prompt += f"CONTRAPARTE: {opposing_counsel}\n"
    
    if relevant_precedents:
        prompt += f"PRECEDENTES RELEVANTES: {', '.join(relevant_precedents)}\n"
    
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
    
    prompt += """
Con base en estos elementos, favor proporcionar:
1. Evaluación probabilística de posibles resultados
2. Factores determinantes de la predicción
3. Análisis de casos similares en esta jurisdicción
4. Fortalezas y debilidades de la posición jurídica
5. Impacto de variaciones fácticas en la predicción
6. Estrategia litigiosa recomendada
7. Rango estimado para conciliación
8. Incertidumbres críticas que podrían afectar el resultado
9. Análisis de principios constitucionales aplicables
10. Requisitos procedimentales administrativos
11. Consideraciones de protección de datos
12. Implicaciones de derechos constitucionales
13. Análisis de precedentes vinculantes
14. Evaluación de riesgos procesales
15. Recomendaciones probatorias

Presentar este análisis en formato adecuado para asesorar sobre riesgo litigioso.
"""
    
    # Extract content from response
    response = await agent.arun(prompt)
    content = response.content if hasattr(response, 'content') else str(response)
    
    # Structure the response
    result = {
        "prediction": content,
        "case_type": case_type,
        "jurisdiction": jurisdiction,
        "key_factors": key_facts,
        "colombian_compliance": {
            "constitutional_principles": ColombianLegalFramework.CONSTITUTIONAL_PRINCIPLES,
            "prediction_date": datetime.now().isoformat()
        }
    }
    
    if judge_name:
        result["judge"] = judge_name
    
    if opposing_counsel:
        result["opposing_counsel"] = opposing_counsel
    
    if relevant_precedents:
        result["relevant_precedents"] = relevant_precedents
    
    if legal_term_definitions:
        result["legal_terms"] = legal_term_definitions
    
    if administrative_procedure:
        result["administrative_procedure"] = {
            "type": administrative_procedure,
            "deadlines": deadlines,
            "response_due": (datetime.now() + timedelta(days=deadlines["response"])).isoformat()
        }
    
    return result 

async def analyze_relevant_laws(agent: Agent, case_details: dict) -> dict:
    """Analyze relevant laws for the case using the agent"""
    prompt = f"""Analizar las leyes relevantes para el siguiente caso:

TIPO DE CASO: {case_details['case_type']}
JURISDICCIÓN: {case_details['jurisdiction']}
HECHOS RELEVANTES: {', '.join(case_details['key_facts'])}
PROBLEMAS JURÍDICOS: {', '.join(case_details['legal_issues'])}

Por favor proporcionar:
1. Leyes específicas aplicables al caso
2. Artículos relevantes de cada ley
3. Jurisprudencia relacionada
4. Interpretación normativa aplicable
5. Posibles conflictos normativos
6. Jerarquía normativa aplicable

Presentar el análisis en formato JSON con la siguiente estructura:
{{
    "leyes": [
        {{
            "nombre": "nombre de la ley",
            "articulos": ["art. X", "art. Y"],
            "relevancia": "explicación de relevancia"
        }}
    ],
    "jurisprudencia": [
        {{
            "referencia": "referencia de la sentencia",
            "relevancia": "explicación de relevancia"
        }}
    ]
}}
"""
    
    response = await agent.arun(prompt)
    return response.content if hasattr(response, 'content') else str(response)

async def analyze_similar_cases_from_altas_cortes(agent: Agent, case_details: dict) -> dict:
    """Find and analyze similar previous cases"""
    prompt = f"""Buscar y analizar sentencias previas similares al siguiente caso:

TIPO DE CASO: {case_details['case_type']}
JURISDICCIÓN: {case_details['jurisdiction']}
HECHOS RELEVANTES: {', '.join(case_details['key_facts'])}
PROBLEMAS JURÍDICOS: {', '.join(case_details['legal_issues'])}

Por favor proporcionar:
1. Sentencias similares de las altas cortes
2. Precedentes vinculantes aplicables
3. Línea jurisprudencial relevante
4. Criterios de similitud
5. Diferencias relevantes
6. Impacto en el caso actual

Presentar el análisis en formato JSON con la siguiente estructura:
{{
    "sentencias": [
        {{
            "referencia": "número de sentencia",
            "tribunal": "nombre del tribunal",
            "fecha": "fecha de la sentencia",
            "similitud": "porcentaje de similitud",
            "relevancia": "explicación de la relevancia",
            "criterios_clave": ["criterio 1", "criterio 2"]
        }}
    ],
    "linea_jurisprudencial": {{
        "tema": "tema principal",
        "evolucion": ["sentencia 1", "sentencia 2"],
        "criterio_actual": "criterio vigente"
    }}
}}
"""
    
    response = await agent.arun(prompt)
    return response.content if hasattr(response, 'content') else str(response) 