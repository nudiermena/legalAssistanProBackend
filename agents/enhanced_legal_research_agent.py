"""
Enhanced Legal Research Agent
Inherits from BaseEnhancedAgent to provide reasoning, knowledge, storage, and memory
"""

from agents.base_enhanced_agent import BaseEnhancedAgent
from agno.tools.googlesearch import GoogleSearchTools
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)

class EnhancedLegalResearchAgent(BaseEnhancedAgent):
    """Enhanced legal research agent with all capabilities"""
    
    def __init__(self, user_id: str = None):
        super().__init__("legal_research", user_id)
    
    def get_agent_name(self) -> str:
        return "Investigador Jurídico Avanzado"
    
    def get_agent_role(self) -> str:
        return "Especialista en investigación jurídica con capacidades avanzadas"
    
    def get_model_name(self) -> str:
        return "legal_research"
    
    def get_tools(self) -> List:
        return [GoogleSearchTools()]
    
    def get_base_instructions(self) -> List[str]:
        return [
            # === INVESTIGACIÓN JURÍDICA ===
            "Realizar investigaciones jurídicas exhaustivas dentro del marco legal colombiano e internacional",
            "Analizar jurisprudencia, autos, legislación y artículos académicos",
            "Proporcionar citas precisas y sintetizar hallazgos en formato estructurado",
            "Buscar en bases de datos legales y fuentes oficiales",
            "Evaluar la relevancia y actualidad de las fuentes encontradas",
            
            # === ANÁLISIS DE FUENTES ===
            "Identificar fuentes primarias (leyes, decretos, sentencias)",
            "Localizar fuentes secundarias (doctrina, comentarios)",
            "Evaluar la autoridad y confiabilidad de las fuentes",
            "Verificar la vigencia de las normas y jurisprudencia",
            "Comparar diferentes interpretaciones doctrinales",
            
            # === SÍNTESIS Y ORGANIZACIÓN ===
            "Organizar la información por temas y subtemas",
            "Crear resúmenes ejecutivos de hallazgos relevantes",
            "Identificar tendencias jurisprudenciales",
            "Detectar contradicciones o vacíos normativos",
            "Proponer líneas de investigación adicionales",
            
            # === CUMPLIMIENTO COLOMBIANO ===
            "Aplicar principios constitucionales colombianos",
            "Considerar jurisprudencia de las Altas Cortes",
            "Incluir referencias a la Corte Constitucional",
            "Mencionar sentencias del Consejo de Estado",
            "Citar autos de la Corte Suprema de Justicia",
            
            # === FORMATO DE SALIDA ===
            "Estructurar la respuesta en secciones claras",
            "Incluir referencias bibliográficas completas",
            "Proporcionar enlaces a fuentes cuando sea posible",
            "Crear un índice de temas investigados",
            "Incluir un resumen ejecutivo al inicio"
        ]
    
    def _build_base_prompt(self, request_data: Dict[str, Any]) -> str:
        """Build the base prompt for legal research"""
        research_topic = request_data.get("research_topic", "")
        jurisdiction = request_data.get("jurisdiction", "Colombia")
        research_type = request_data.get("research_type", "general")
        specific_questions = request_data.get("specific_questions", [])
        date_range = request_data.get("date_range", "")
        
        prompt = f"""Realizar investigación jurídica sobre:

TEMA DE INVESTIGACIÓN: {research_topic}
JURISDICCIÓN: {jurisdiction}
TIPO DE INVESTIGACIÓN: {research_type}

"""
        
        if specific_questions:
            prompt += f"PREGUNTAS ESPECÍFICAS:\n"
            for i, question in enumerate(specific_questions, 1):
                prompt += f"{i}. {question}\n"
            prompt += "\n"
        
        if date_range:
            prompt += f"RANGO DE FECHAS: {date_range}\n\n"
        
        prompt += """INVESTIGACIÓN REQUERIDA:
1. Búsqueda de normativa aplicable
2. Análisis de jurisprudencia relevante
3. Revisión de doctrina autorizada
4. Identificación de tendencias jurisprudenciales
5. Detección de vacíos o contradicciones normativas
6. Propuesta de líneas de investigación adicionales

FORMATO DE RESPUESTA:
- Resumen ejecutivo
- Marco normativo aplicable
- Jurisprudencia relevante
- Doctrina autorizada
- Análisis y conclusiones
- Referencias bibliográficas
- Recomendaciones para investigación adicional
"""
        
        return prompt
    
    def _get_additional_context(self, request_data: Dict[str, Any]) -> str:
        """Get additional context for legal research"""
        additional_context = ""
        
        # Add research history if available
        if self.memory.get("case_context", {}).get("research_history"):
            history = self.memory["case_context"]["research_history"]
            additional_context += f"\nHISTORIAL DE INVESTIGACIONES PREVIAS:\n{history}\n"
        
        # Add legal terms cache for context
        if self.memory.get("legal_terms_cache"):
            terms = list(self.memory["legal_terms_cache"].keys())[:5]  # Top 5 terms
            additional_context += f"\nTÉRMINOS LEGALES RECIENTES: {', '.join(terms)}\n"
        
        return additional_context
    
    async def research_legal_topic(
        self,
        research_topic: str,
        jurisdiction: str = "Colombia",
        research_type: str = "general",
        specific_questions: Optional[List[str]] = None,
        date_range: Optional[str] = None,
        include_jurisprudence: bool = True,
        include_doctrine: bool = True,
        include_legislation: bool = True
    ) -> Dict[str, Any]:
        """Conduct enhanced legal research on a specific topic"""
        
        request_data = {
            "type": "legal_research",
            "research_topic": research_topic,
            "jurisdiction": jurisdiction,
            "research_type": research_type,
            "specific_questions": specific_questions or [],
            "date_range": date_range,
            "include_jurisprudence": include_jurisprudence,
            "include_doctrine": include_doctrine,
            "include_legislation": include_legislation
        }
        
        return await self.process_request(request_data)
    
    async def search_jurisprudence(
        self,
        topic: str,
        court: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        keywords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Search for specific jurisprudence"""
        
        request_data = {
            "type": "jurisprudence_search",
            "research_topic": f"Jurisprudencia sobre {topic}",
            "jurisdiction": "Colombia",
            "research_type": "jurisprudence",
            "specific_questions": [
                f"¿Cuáles son las principales sentencias sobre {topic}?",
                f"¿Qué criterios han establecido los tribunales sobre {topic}?",
                f"¿Existen tendencias jurisprudenciales sobre {topic}?"
            ],
            "court": court,
            "date_from": date_from,
            "date_to": date_to,
            "keywords": keywords or []
        }
        
        return await self.process_request(request_data)
    
    async def analyze_legal_trends(
        self,
        area_of_law: str,
        time_period: str = "últimos 5 años",
        include_statistics: bool = True
    ) -> Dict[str, Any]:
        """Analyze legal trends in a specific area"""
        
        request_data = {
            "type": "trend_analysis",
            "research_topic": f"Tendencias en {area_of_law}",
            "jurisdiction": "Colombia",
            "research_type": "trend_analysis",
            "specific_questions": [
                f"¿Cuáles son las principales tendencias en {area_of_law}?",
                f"¿Cómo ha evolucionado la jurisprudencia en {area_of_law}?",
                f"¿Qué cambios normativos han impactado {area_of_law}?"
            ],
            "time_period": time_period,
            "include_statistics": include_statistics
        }
        
        return await self.process_request(request_data)
    
    def _extract_legal_terms(self, content: str) -> Dict[str, str]:
        """Enhanced legal terms extraction for research agent"""
        legal_terms = super()._extract_legal_terms(content)
        
        # Add research-specific terms
        research_patterns = [
            r'Corte\s+Constitucional',
            r'Consejo\s+de\s+Estado',
            r'Corte\s+Suprema\s+de\s+Justicia',
            r'Tribunal\s+Administrativo',
            r'Juzgado\s+[A-Za-z]+',
            r'Proceso\s+[A-Za-z]+',
            r'Recurso\s+de\s+[A-Za-z]+',
            r'Acción\s+de\s+[A-Za-z]+'
        ]
        
        for pattern in research_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                legal_terms[match] = "Término de investigación encontrado"
        
        return legal_terms

def create_enhanced_legal_research_agent(user_id: str = None) -> EnhancedLegalResearchAgent:
    """Create an enhanced legal research agent instance"""
    return EnhancedLegalResearchAgent(user_id)

async def research_legal_topic_enhanced(
    research_topic: str,
    user_id: str = None,
    jurisdiction: str = "Colombia",
    research_type: str = "general",
    specific_questions: Optional[List[str]] = None,
    date_range: Optional[str] = None
) -> Dict[str, Any]:
    """Enhanced legal research with all capabilities"""
    agent = create_enhanced_legal_research_agent(user_id)
    return await agent.research_legal_topic(
        research_topic=research_topic,
        jurisdiction=jurisdiction,
        research_type=research_type,
        specific_questions=specific_questions,
        date_range=date_range
    ) 