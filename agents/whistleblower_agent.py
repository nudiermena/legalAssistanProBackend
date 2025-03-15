import datetime
from agno.agent import Agent
from config.database import get_agent_storage
from config.ai_models import get_model
from config.knowledge_base import get_knowledge_base

def create_whistleblower_agent() -> Agent:
    """Create a specialized agent for whistleblower analysis"""
    return Agent(
        name="Ethics Analyst",
        role="Whistleblower report specialist",
        model=get_model("whistleblower"),
        knowledge=get_knowledge_base(),
        search_knowledge=True,
        storage=get_agent_storage("whistleblower_sessions"),
        markdown=True
    )

async def analyze_whistleblower_report(
    report_content: str,
    company_context: dict,
    applicable_policies: list,
    regulatory_framework: list,
    prior_related_issues: list = None
) -> dict:
    """Analyze whistleblower reports for severity, credibility, and regulatory implications"""
    agent = create_whistleblower_agent()
    
    # Format company context for the prompt
    company_context_text = "\n".join([f"- {key}: {value}" for key, value in company_context.items()])
    
    # Format prior issues if provided
    prior_issues_text = ""
    if prior_related_issues:
        prior_issues_text = "\n".join([f"- {issue.get('description', 'No description')}: {issue.get('outcome', 'No outcome provided')}" for issue in prior_related_issues])
    
    # Prepare the prompt
    prompt = f"""Analyze the following whistleblower report for severity, credibility, and recommended actions:

REPORT CONTENT:
{report_content}

COMPANY CONTEXT:
{company_context_text}

APPLICABLE POLICIES:
{', '.join(applicable_policies)}

REGULATORY FRAMEWORK:
{', '.join(regulatory_framework)}
"""
    
    if prior_related_issues:
        prompt += f"\nPRIOR RELATED ISSUES:\n{prior_issues_text}\n"
    
    prompt += """
Please provide:
1. Issue categorization and severity assessment
2. Initial credibility analysis based on:
   - Specificity of allegations
   - Corroborating information provided
   - Internal consistency of the report
   - Knowledge demonstrated about internal processes
3. Regulatory implications assessment
4. Recommended immediate actions to:
   - Preserve evidence
   - Mitigate ongoing harm
   - Meet regulatory obligations
5. Investigation plan including:
   - Suggested investigation scope
   - Key witnesses to interview
   - Documents to review
   - Subject matter experts to consult
6. Communications recommendations for:
   - Reporter acknowledgment
   - Management notification
   - Potential regulatory disclosure
7. Risk assessment of potential outcomes

Format this as a confidential investigation brief for the Ethics & Compliance team.
"""
    
    # Run the analysis
    response = agent.run(prompt)
    
    # Structure the response
    return {
        "analysis": response.content,
        "report_id": f"WB-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
        "confidentiality": "HIGH"
    } 