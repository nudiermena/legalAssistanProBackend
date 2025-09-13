"""
Enhanced Contract Agent with Reasoning, Knowledge, Storage, and Memory
"""

from agno.agent import Agent
from config.enhanced_agent_config import (
    get_enhanced_agent_config,
    get_agent_memory,
    update_agent_memory
)
from config.ai_models import get_model
from config.colombian_compliance import (
    ColombianDataProtection,
    ColombianLegalFramework,
    get_data_category,
    validate_consent,
    get_retention_period
)
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import os as os_module
import json
import logging
from fastapi import HTTPException
from models.request_models import ContractReviewRequest
from models.response_models import format_response, handle_error
from agno.tools.googlesearch import GoogleSearchTools
import re

logger = logging.getLogger(__name__)

class EnhancedContractAgent:
    """Enhanced contract agent with reasoning, knowledge, storage, and memory"""
    
    def __init__(self, user_id: str = None):
        self.user_id = user_id
        self.agent_name = "contract_agent"
        self.agent = None
        self.memory = get_agent_memory(self.agent_name)
        self.initialize_agent()
    
    def initialize_agent(self):
        """Initialize the enhanced agent with all capabilities"""
        try:
            # Get enhanced configuration
            config = get_enhanced_agent_config(self.agent_name)
            
            # Create agent with enhanced capabilities
            self.agent = Agent(
                name="Analista de Contratos Avanzado",
                role="Especialista en análisis contractual con capacidades avanzadas",
                model=get_model("contract_review"),
                tools=[GoogleSearchTools()],
                knowledge=config["knowledge"],
                search_knowledge=config["search_knowledge"],
                storage=config["storage"],
                reasoning=config["reasoning"],
                show_tool_calls=config["show_tool_calls"],
                debug_mode=config["debug_mode"],
                instructions=self._get_enhanced_instructions(),
                markdown=True
            )
            
            logger.info(f"Enhanced contract agent initialized for user: {self.user_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize enhanced contract agent: {e}")
            raise
    
    def _get_enhanced_instructions(self) -> List[str]:
        """Get enhanced instructions with reasoning capabilities"""
        return [
            # === REASONING CAPABILITIES ===
            "Antes de responder, analiza el contexto completo del contrato y la situación del usuario",
            "Evalúa múltiples perspectivas legales antes de llegar a conclusiones",
            "Considera el historial de interacciones previas con el usuario",
            "Aplica razonamiento deductivo para identificar riesgos ocultos",
            "Utiliza el conocimiento legal almacenado para fundamentar tus análisis",
            
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
            
            # === MEMORY AND PERSONALIZATION ===
            "Considera las preferencias del usuario basándote en interacciones previas",
            "Adapta el nivel de detalle según la experiencia legal del usuario",
            "Mantén consistencia con análisis previos del mismo usuario",
            "Aprende de los patrones de riesgo identificados en contratos similares",
            
            # === REPORTE Y RECOMENDACIONES ===
            "Generar informes estructurados con hallazgos, observaciones y recomendaciones",
            "Clasificar observaciones por nivel de riesgo (alto, medio, bajo)",
            "Proponer redacciones alternativas para cláusulas deficientes",
            "Incluir referencias normativas y jurisprudenciales específicas",
            "Sugerir acciones correctivas y medidas de mitigación de riesgos",
            
            # === OUTPUT FORMAT ===
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
                "  ],\n"
                "  \"reasoning\": {\n"
                "    \"analysis_steps\": [\"Paso 1: Identificación de elementos esenciales\", \"Paso 2: Evaluación de riesgos\"],\n"
                "    \"confidence_level\": \"Alto\",\n"
                "    \"alternative_scenarios\": [\"Escenario 1: Cláusula modificada\", \"Escenario 2: Cláusula eliminada\"]\n"
                "  }\n"
                "}\n"
                "```\n"
                "En cada recomendación, incluye la referencia a la ley, decreto o jurisprudencia relevante.\n"
                "En cada cláusula identificada, agrega un campo 'references' con leyes relevantes.\n"
                "Usa los tipos: `success` (verde), `warning` (amarillo), `danger` (rojo) para las cláusulas.\n"
                "Incluye el campo 'reasoning' para mostrar tu proceso de análisis."
            )
        ]
    
    def _get_context_from_memory(self) -> str:
        """Get relevant context from agent memory"""
        context_parts = []
        
        # Add user preferences
        if self.memory.get("user_preferences"):
            prefs = self.memory["user_preferences"]
            context_parts.append(f"Preferencias del usuario: {json.dumps(prefs, ensure_ascii=False)}")
        
        # Add recent conversation history
        if self.memory.get("conversation_history"):
            recent_history = self.memory["conversation_history"][-3:]  # Last 3 interactions
            context_parts.append(f"Historial reciente: {json.dumps(recent_history, ensure_ascii=False)}")
        
        # Add case context
        if self.memory.get("case_context"):
            context_parts.append(f"Contexto del caso: {json.dumps(self.memory['case_context'], ensure_ascii=False)}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def _update_memory(self, interaction_data: Dict[str, Any]):
        """Update agent memory with new interaction data"""
        try:
            # Update conversation history
            if "conversation_history" not in self.memory:
                self.memory["conversation_history"] = []
            
            self.memory["conversation_history"].append({
                "timestamp": datetime.now().isoformat(),
                "user_id": self.user_id,
                "interaction_type": interaction_data.get("type", "contract_analysis"),
                "contract_type": interaction_data.get("contract_type"),
                "risk_level": interaction_data.get("risk_level"),
                "key_findings": interaction_data.get("key_findings", [])
            })
            
            # Keep only last 10 interactions
            if len(self.memory["conversation_history"]) > 10:
                self.memory["conversation_history"] = self.memory["conversation_history"][-10:]
            
            # Update case context
            if "case_context" not in self.memory:
                self.memory["case_context"] = {}
            
            self.memory["case_context"].update({
                "last_contract_type": interaction_data.get("contract_type"),
                "last_risk_level": interaction_data.get("risk_level"),
                "total_analyses": self.memory["case_context"].get("total_analyses", 0) + 1
            })
            
            # Update memory in the system
            update_agent_memory(self.agent_name, self.memory)
            
            logger.info(f"Memory updated for user {self.user_id}")
            
        except Exception as e:
            logger.error(f"Failed to update memory: {e}")
    
    async def analyze_contract(
        self,
        contract_text: str,
        contract_type: str,
        parties: List[str],
        specific_concerns: Optional[List[str]] = None,
        relevant_regulations: Optional[List[str]] = None,
        data_processing: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Analyze contract with enhanced capabilities"""
        try:
            # Get context from memory
            memory_context = self._get_context_from_memory()
            
            # Build enhanced prompt
            prompt = f"""Analizar el siguiente contrato con capacidades avanzadas:

CONTEXTO DEL USUARIO:
{memory_context}

CONTRATO:
Tipo: {contract_type}
Partes: {', '.join(parties)}
Texto: {contract_text}

ANÁLISIS REQUERIDO:
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

REASONING: Explica tu proceso de análisis paso a paso.
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
            
            # Run analysis with enhanced agent
            response = await self.agent.arun(prompt)
            
            # Extract structured data
            structured_result = self._extract_structured_data(response.content)
            
            # Extract metrics
            metrics = self._extract_analysis_metrics(response.content)
            
            # Build result
            result = {
                "summary": response.content,
                "structured_analysis": structured_result,
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
                "compliance": metrics["compliance"],
                "enhanced_features": {
                    "reasoning_used": True,
                    "knowledge_searched": True,
                    "memory_accessed": bool(memory_context),
                    "storage_persisted": True
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
            
            # Update memory with this interaction
            self._update_memory({
                "type": "contract_analysis",
                "contract_type": contract_type,
                "risk_level": metrics["risk_level"],
                "key_findings": structured_result.get("clauses", [])[:3]  # Top 3 findings
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error in enhanced contract analysis: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error analyzing contract: {str(e)}"
            )
    
    def _extract_structured_data(self, content: str) -> Dict[str, Any]:
        """Extract structured JSON data from agent response"""
        try:
            # Look for JSON block in the response
            json_match = re.search(r"```json\s*([\s\S]+?)```", content)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
            return {}
        except Exception as e:
            logger.warning(f"Failed to extract structured data: {e}")
            return {}
    
    def _extract_analysis_metrics(self, summary: str) -> dict:
        """Extract metrics from analysis summary"""
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

def create_enhanced_contract_agent(user_id: str = None) -> EnhancedContractAgent:
    """Create an enhanced contract agent instance"""
    return EnhancedContractAgent(user_id)

async def analyze_contract_enhanced(
    contract_text: str,
    contract_type: str,
    parties: List[str],
    user_id: str = None,
    specific_concerns: Optional[List[str]] = None,
    relevant_regulations: Optional[List[str]] = None,
    data_processing: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Enhanced contract analysis with all capabilities"""
    agent = create_enhanced_contract_agent(user_id)
    return await agent.analyze_contract(
        contract_text=contract_text,
        contract_type=contract_type,
        parties=parties,
        specific_concerns=specific_concerns,
        relevant_regulations=relevant_regulations,
        data_processing=data_processing
    ) 