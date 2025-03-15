from agno.agent import Agent
from config.database import get_agent_storage
from config.ai_models import get_model
from config.knowledge_base import get_knowledge_base
from typing import Dict, List, Optional

def create_contract_agent() -> Agent:
    """Create a specialized agent for contract review"""
    return Agent(
        name="Contract Analyzer",
        role="Contract analysis specialist",
        model=get_model("contract_review"),
        knowledge=get_knowledge_base(),
        search_knowledge=True,
        storage=get_agent_storage("contract_sessions"),
        markdown=True
    )

async def analyze_contract(
    contract_text: str,
    contract_type: str,
    parties: List[str],
    specific_concerns: Optional[List[str]] = None,
    relevant_regulations: Optional[List[str]] = None
) -> Dict[str, str]:
    """Analyze a contract and provide detailed insights"""
    agent = create_contract_agent()
    
    # Prepare the prompt with all relevant details
    prompt = f"""Analyze the following {contract_type} contract between {', '.join(parties)}:

{contract_text}

Please provide:
1. A concise executive summary (max 150 words)
2. Key obligations for each party with reference to specific sections
3. Critical dates and deadlines
4. Unusual or non-standard clauses compared to industry norms
5. Potential risks identified by clause with severity rating (Low/Medium/High)
"""
    
    # Add specific concerns if provided
    if specific_concerns:
        prompt += f"\nFocus particularly on clauses related to: {', '.join(specific_concerns)}"
    
    # Add compliance check if regulations provided
    if relevant_regulations:
        prompt += f"\n\nAlso evaluate compliance with the following regulations: {', '.join(relevant_regulations)}"
    
    # Run the analysis
    response = agent.run(prompt)
    
    # Structure the response
    return {
        "summary": response.content,
        "contract_type": contract_type,
        "parties": parties,
        "specific_concerns_addressed": specific_concerns if specific_concerns else [],
        "regulations_evaluated": relevant_regulations if relevant_regulations else []
    } 