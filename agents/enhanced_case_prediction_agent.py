"""
Enhanced Case Prediction Agent
Leverages comprehensive legal case metadata for improved predictions
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from langchain.agents import Agent
from langchain.tools import Tool
from langchain.schema import BaseMessage, HumanMessage, SystemMessage

from config.neo4j_kg import Neo4jKnowledgeGraph
from config.supabase_knowledge_base import SupabaseLegalKnowledgeBase, KnowledgeType
from config.ai_models import case_prediction_model

logger = logging.getLogger(__name__)

@dataclass
class EnhancedCasePredictionRequest:
    """Enhanced case prediction request with comprehensive metadata"""
    # Basic case information
    process_type: str
    legal_problem: str
    relevant_facts: str
    
    # Parties
    plaintiff: Optional[str] = None
    defendant: Optional[str] = None
    
    # Legal context
    legal_concepts: List[str] = None
    legal_area: Optional[str] = None
    supporting_normativity: List[str] = None
    
    # Court context
    court: Optional[str] = None
    jurisdiction: Optional[str] = None
    
    # Additional context
    challenged_act: Optional[str] = None
    legal_foundation_demand: Optional[str] = None
    legal_foundation_defense: Optional[str] = None
    
    def __post_init__(self):
        if self.legal_concepts is None:
            self.legal_concepts = []
        if self.supporting_normativity is None:
            self.supporting_normativity = []

class EnhancedCasePredictionAgent:
    """Enhanced case prediction agent with comprehensive legal analysis"""
    
    def __init__(self):
        self.kg = Neo4jKnowledgeGraph()
        self.knowledge_base = SupabaseLegalKnowledgeBase(mock_mode=False)
        
        # Initialize tools
        self.tools = self._create_tools()
        
        # Create agent
        self.agent = self._create_agent()
    
    def _create_tools(self) -> List[Tool]:
        """Create tools for the agent"""
        return [
            Tool(
                name="search_similar_cases",
                description="Search for similar cases based on legal concepts and facts",
                func=self._search_similar_cases
            ),
            Tool(
                name="analyze_legal_precedents",
                description="Analyze legal precedents and jurisprudence",
                func=self._analyze_legal_precedents
            ),
            Tool(
                name="evaluate_legal_arguments",
                description="Evaluate legal arguments and foundations",
                func=self._evaluate_legal_arguments
            ),
            Tool(
                name="assess_court_tendencies",
                description="Assess court tendencies and patterns",
                func=self._assess_court_tendencies
            ),
            Tool(
                name="calculate_success_probability",
                description="Calculate probability of success based on multiple factors",
                func=self._calculate_success_probability
            )
        ]
    
    def _create_agent(self) -> Agent:
        """Create the enhanced case prediction agent"""
        system_prompt = """You are an expert legal case prediction AI specialized in Colombian law. 
        You have access to comprehensive legal databases and can analyze cases using multiple dimensions:
        
        1. **Similar Case Analysis**: Find and analyze similar cases based on legal concepts, facts, and legal problems
        2. **Legal Precedent Analysis**: Evaluate relevant jurisprudence and legal precedents
        3. **Legal Argument Evaluation**: Assess the strength of legal arguments and foundations
        4. **Court Tendency Assessment**: Analyze patterns in specific courts and jurisdictions
        5. **Multi-factor Success Calculation**: Combine multiple factors to predict case outcomes
        
        When analyzing a case, consider:
        - Legal concepts involved and their precedential value
        - Similar cases and their outcomes
        - Court-specific tendencies and patterns
        - Legal argument strength and foundation
        - Procedural requirements and compliance
        - Jurisdictional factors and legal area specifics
        
        Provide detailed analysis with confidence scores and reasoning."""
        
        return Agent.from_llm_and_tools(
            llm=case_prediction_model,
            tools=self.tools,
            system_message=SystemMessage(content=system_prompt),
            verbose=True
        )
    
    async def predict_case_outcome(self, request: EnhancedCasePredictionRequest) -> Dict[str, Any]:
        """Predict case outcome using enhanced analysis"""
        try:
            # Create analysis prompt
            prompt = self._create_analysis_prompt(request)
            
            # Get agent response
            response = await self.agent.arun(prompt)
            
            # Extract structured prediction
            prediction = self._extract_prediction(response, request)
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error in case prediction: {e}")
            raise
    
    def _create_analysis_prompt(self, request: EnhancedCasePredictionRequest) -> str:
        """Create comprehensive analysis prompt"""
        prompt = f"""
        Analyze the following legal case and predict its outcome:
        
        **CASE INFORMATION:**
        - Process Type: {request.process_type}
        - Legal Problem: {request.legal_problem}
        - Relevant Facts: {request.relevant_facts}
        - Plaintiff: {request.plaintiff or 'Not specified'}
        - Defendant: {request.defendant or 'Not specified'}
        - Legal Concepts: {', '.join(request.legal_concepts) if request.legal_concepts else 'Not specified'}
        - Legal Area: {request.legal_area or 'Not specified'}
        - Court: {request.court or 'Not specified'}
        - Jurisdiction: {request.jurisdiction or 'Not specified'}
        
        **LEGAL CONTEXT:**
        - Challenged Act: {request.challenged_act or 'Not applicable'}
        - Legal Foundation (Demand): {request.legal_foundation_demand or 'Not specified'}
        - Legal Foundation (Defense): {request.legal_foundation_defense or 'Not specified'}
        - Supporting Normativity: {', '.join(request.supporting_normativity) if request.supporting_normativity else 'Not specified'}
        
        **ANALYSIS REQUIRED:**
        1. Search for similar cases and analyze their outcomes
        2. Evaluate legal precedents and jurisprudence
        3. Assess the strength of legal arguments
        4. Analyze court tendencies and patterns
        5. Calculate overall success probability
        
        **OUTPUT FORMAT:**
        Provide a comprehensive analysis including:
        - Predicted outcome (Favorable/Unfavorable/Partially Favorable)
        - Confidence score (0-100%)
        - Key factors supporting the prediction
        - Similar cases and their relevance
        - Legal precedents and their impact
        - Risk factors and potential challenges
        - Recommended legal strategy
        - Estimated case duration
        - Success probability breakdown by factor
        """
        
        return prompt
    
    def _search_similar_cases(self, query: str) -> str:
        """Search for similar cases"""
        try:
            # Use Neo4j to find similar cases
            similar_cases = self.kg.search_similar_cases_hybrid(
                query_text=query,
                top_k=10
            )
            
            if not similar_cases:
                return "No similar cases found in the database."
            
            # Format results
            results = []
            for case in similar_cases:
                results.append(f"""
                Case: {case.get('case_id', 'Unknown')}
                Court: {case.get('court_id', 'Unknown')}
                Outcome: {case.get('outcome', 'Unknown')}
                Similarity Score: {case.get('final_score', 0):.3f}
                """)
            
            return f"Found {len(similar_cases)} similar cases:\n" + "\n".join(results)
            
        except Exception as e:
            logger.error(f"Error searching similar cases: {e}")
            return f"Error searching similar cases: {str(e)}"
    
    def _analyze_legal_precedents(self, query: str) -> str:
        """Analyze legal precedents and jurisprudence"""
        try:
            # Search knowledge base for jurisprudence
            jurisprudence = self.knowledge_base.search_knowledge(
                query=f"jurisprudencia {query}",
                limit=10
            )
            
            if not jurisprudence.get('results'):
                return "No relevant jurisprudence found."
            
            # Format results
            results = []
            for juris in jurisprudence['results']:
                results.append(f"""
                Case: {juris.get('source', 'Unknown')}
                Summary: {juris.get('content', 'No summary')[:200]}...
                Relevance: {juris.get('score', 0):.3f}
                """)
            
            return f"Found {len(jurisprudence['results'])} relevant precedents:\n" + "\n".join(results)
            
        except Exception as e:
            logger.error(f"Error analyzing legal precedents: {e}")
            return f"Error analyzing legal precedents: {str(e)}"
    
    def _evaluate_legal_arguments(self, query: str) -> str:
        """Evaluate legal arguments and foundations"""
        try:
            # Search for legal terms and definitions
            legal_terms = self.knowledge_base.get_legal_terms(
                terms=query.split()[:5]  # Limit to first 5 terms
            )
            
            if not legal_terms:
                return "No legal definitions found for evaluation."
            
            # Format results
            results = []
            for term, definition in legal_terms.items():
                results.append(f"{term}: {definition}")
            
            return f"Legal definitions found:\n" + "\n".join(results)
            
        except Exception as e:
            logger.error(f"Error evaluating legal arguments: {e}")
            return f"Error evaluating legal arguments: {str(e)}"
    
    def _assess_court_tendencies(self, query: str) -> str:
        """Assess court tendencies and patterns"""
        try:
            # Use Neo4j to analyze court patterns
            court_analysis = self.kg.analyze_court_patterns(
                court_name=query,
                limit=20
            )
            
            if not court_analysis:
                return "No court tendency data available."
            
            # Format results
            results = []
            for pattern in court_analysis:
                results.append(f"""
                Pattern: {pattern.get('pattern_type', 'Unknown')}
                Frequency: {pattern.get('frequency', 0)}
                Success Rate: {pattern.get('success_rate', 0):.2%}
                """)
            
            return f"Court tendency analysis:\n" + "\n".join(results)
            
        except Exception as e:
            logger.error(f"Error assessing court tendencies: {e}")
            return f"Error assessing court tendencies: {str(e)}"
    
    def _calculate_success_probability(self, query: str) -> str:
        """Calculate success probability based on multiple factors"""
        try:
            # Use Neo4j to calculate success probability
            probability = self.kg.predict_outcome_from_graph({
                'legal_area': query,
                'procedure_type': query,
                'legal_concepts': query.split(),
                'court_id': query
            })
            
            if not probability:
                return "Unable to calculate success probability."
            
            return f"""
            Predicted Outcome: {probability.get('predicted_outcome', 'Unknown')}
            Confidence: {probability.get('confidence', 0):.2%}
            Details: {probability.get('details', [])}
            """
            
        except Exception as e:
            logger.error(f"Error calculating success probability: {e}")
            return f"Error calculating success probability: {str(e)}"
    
    def _extract_prediction(self, response: str, request: EnhancedCasePredictionRequest) -> Dict[str, Any]:
        """Extract structured prediction from agent response"""
        # This would parse the agent's response and extract structured data
        # For now, return a basic structure
        return {
            "predicted_outcome": "Favorable",  # Would be extracted from response
            "confidence_score": 0.75,  # Would be extracted from response
            "key_factors": [
                "Strong legal foundation",
                "Favorable precedent",
                "Clear legal problem"
            ],
            "similar_cases": [],  # Would be populated from search results
            "legal_precedents": [],  # Would be populated from jurisprudence search
            "risk_factors": [
                "Procedural requirements",
                "Court interpretation"
            ],
            "recommended_strategy": "Focus on constitutional arguments",
            "estimated_duration": "6-12 months",
            "success_probability_breakdown": {
                "legal_arguments": 0.8,
                "precedent_support": 0.7,
                "court_tendency": 0.6,
                "procedural_compliance": 0.9
            },
            "analysis_timestamp": datetime.now().isoformat(),
            "request_metadata": {
                "process_type": request.process_type,
                "legal_area": request.legal_area,
                "court": request.court
            }
        }
    
    def close(self):
        """Close connections"""
        if self.kg:
            self.kg.close()

# Example usage
if __name__ == "__main__":
    # Create enhanced case prediction request
    request = EnhancedCasePredictionRequest(
        process_type="ACCIÓN DE TUTELA",
        legal_problem="¿Es procedente la acción de tutela para declarar la suspensión de los efectos de una sanción de destitución e inhabilidad general interpuesta por parte de la Procuraduría General de la Nación?",
        relevant_facts="La Procuraduría General de la Nación declaró disciplinariamente responsable al Presidente del Concejo Distrital de Cartagena, imponiendo como sanción la destitución del cargo e inhabilidad para el ejercicio de función pública por veinte (20) años.",
        plaintiff="ADOLDO RAAD HERNÁNDEZ",
        defendant="PROCURADURÍA GENERAL DE LA NACIÓN",
        legal_concepts=["ACCIÓN DE TUTELA", "DEBIDO PROCESO", "ACCESO A LA ADMINISTRACIÓN DE JUSTICIA"],
        legal_area="Constitutional Law",
        supporting_normativity=["Artículo 86 de la Constitución Política", "Artículo 6º numeral 1° del Decreto 2591 de 1991"],
        court="CORTE CONSTITUCIONAL",
        jurisdiction="Constitutional"
    )
    
    # Create agent and predict
    agent = EnhancedCasePredictionAgent()
    
    try:
        prediction = agent.predict_case_outcome(request)
        print("Case Prediction:")
        print(f"Outcome: {prediction['predicted_outcome']}")
        print(f"Confidence: {prediction['confidence_score']:.2%}")
        print(f"Key Factors: {prediction['key_factors']}")
    finally:
        agent.close()
