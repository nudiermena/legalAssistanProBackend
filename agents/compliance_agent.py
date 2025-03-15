from agno.agent import Agent
from config.database import get_agent_storage
from config.ai_models import get_model
from config.knowledge_base import get_knowledge_base

def create_compliance_agent() -> Agent:
    """Create a specialized agent for compliance analysis"""
    return Agent(
        name="Compliance Analyst",
        role="Regulatory compliance specialist",
        model=get_model("compliance"),
        knowledge=get_knowledge_base(),
        search_knowledge=True,
        storage=get_agent_storage("compliance_sessions"),
        markdown=True
    )

async def analyze_regulatory_change(
    regulation_text: str,
    effective_date: str,
    industry: str,
    business_operations: list,
    current_compliance_status: dict
) -> dict:
    """Analyze regulatory changes and their impact on business operations"""
    agent = create_compliance_agent()
    
    # Format current compliance status for the prompt
    compliance_status_text = "\n".join([f"- {key}: {value}" for key, value in current_compliance_status.items()])
    
    # Prepare the prompt
    prompt = f"""Analyze the following regulatory change and its impact on our business:

NEW REGULATION:
{regulation_text}

EFFECTIVE DATE: {effective_date}
INDUSTRY: {industry}
BUSINESS OPERATIONS: {', '.join(business_operations)}
CURRENT COMPLIANCE STATUS:
{compliance_status_text}

Please provide:
1. A plain-language summary of the key changes (executive level)
2. Specific business functions/departments affected
3. Required operational changes with implementation difficulty rating
4. Technology systems that need updating
5. New documentation/record-keeping requirements
6. Training needs for staff
7. Timeline of required actions with prioritization
8. Estimated compliance costs and resource requirements
9. Potential competitive impacts (advantages or disadvantages)
10. Recommendations for compliance strategy

Format this as an actionable compliance briefing for our executive team.
"""
    
    # Run the analysis
    response = agent.run(prompt)
    
    return {
        "analysis": response.content,
        "regulation_summary": regulation_text[:200] + "...",
        "effective_date": effective_date,
        "industry": industry
    } 