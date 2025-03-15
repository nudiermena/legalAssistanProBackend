from agno.agent import Agent
from agno.tools.googlesearch import GoogleSearchTools
from config.database import get_agent_storage
from config.ai_models import get_model
from config.knowledge_base import get_knowledge_base

def create_case_prediction_agent() -> Agent:
    """Create a specialized agent for case prediction"""
    return Agent(
        name="Case Predictor",
        role="Litigation outcome analyst",
        model=get_model("case_prediction"),
        knowledge=get_knowledge_base(),
        search_knowledge=True,
        storage=get_agent_storage("prediction_sessions"),
        tools=[GoogleSearchTools()],
        markdown=True
    )

async def predict_case_outcome(
    case_type: str,
    jurisdiction: str,
    key_facts: list,
    legal_issues: list,
    judge_name: str = None,
    opposing_counsel: str = None,
    relevant_precedents: list = None
) -> dict:
    """Predict case outcomes and provide litigation strategy recommendations"""
    agent = create_case_prediction_agent()
    
    # Prepare the prompt
    prompt = f"""Analyze the following case details and predict the likely outcome:

CASE TYPE: {case_type}
JURISDICTION: {jurisdiction}
KEY FACTS: {', '.join(key_facts)}
LEGAL ISSUES: {', '.join(legal_issues)}
"""
    
    if judge_name:
        prompt += f"JUDGE: {judge_name}\n"
    
    if opposing_counsel:
        prompt += f"OPPOSING COUNSEL: {opposing_counsel}\n"
    
    if relevant_precedents:
        prompt += f"RELEVANT PRECEDENT: {', '.join(relevant_precedents)}\n"
    
    prompt += """
Based on these inputs, please provide:
1. A probability assessment for different potential outcomes
2. The key factors driving your prediction
3. Analysis of how similar cases have been decided in this jurisdiction
4. Specific strengths and weaknesses of our position
5. How different fact patterns might change the prediction
6. Suggested litigation strategy based on the prediction
7. Settlement value range assessment
8. Critical uncertainties that could significantly impact the outcome

Present this analysis in a format suitable for advising a client on litigation risk.
"""
    
    # Run the prediction
    response = agent.run(prompt)
    
    # Structure the response
    return {
        "prediction": response.content,
        "case_type": case_type,
        "jurisdiction": jurisdiction,
        "key_factors": key_facts
    } 