from agno.agent import Agent
from agno.tools.googlesearch import GoogleSearchTools
from config.database import get_agent_storage
from config.ai_models import get_model
from config.knowledge_base import get_knowledge_base

def create_legal_diagnosis_agent() -> Agent:
    """Create a specialized agent for legal diagnosis"""
    return Agent(
        name="Legal Diagnostician",
        role="Personal legal assistant",
        model=get_model("legal_diagnosis"),
        knowledge=get_knowledge_base(),
        search_knowledge=True,
        storage=get_agent_storage("diagnosis_sessions"),
        tools=[GoogleSearchTools()],
        markdown=True
    )

async def diagnose_legal_issue(
    situation_description: str,
    jurisdiction: str,
    user_goal: str,
    timeline: str = None,
    financial_considerations: str = None
) -> dict:
    """Provide personalized legal guidance for consumers"""
    agent = create_legal_diagnosis_agent()
    
    # Prepare the prompt
    prompt = f"""Help me understand my legal situation and options:

MY SITUATION:
{situation_description}

LOCATION:
{jurisdiction}

MY GOAL:
{user_goal}
"""
    
    if timeline:
        prompt += f"\nTIMELINE:\n{timeline}\n"
    
    if financial_considerations:
        prompt += f"\nFINANCIAL CONSIDERATIONS:\n{financial_considerations}\n"
    
    prompt += """
As a personal legal assistant, please:
1. Identify the specific area(s) of law involved
2. Explain my basic legal rights and obligations in plain language
3. Outline potential approaches to address my situation
4. Describe typical processes and timeframes
5. Explain potential costs and financial considerations
6. Identify when I should consult with an attorney
7. Suggest questions I should ask when speaking with a lawyer
8. Provide relevant self-help resources if appropriate
9. Explain common pitfalls to avoid

Present this information in an accessible, non-threatening way that helps me understand my options without providing specific legal advice for my situation.
"""
    
    # Run the diagnosis
    response = agent.run(prompt)
    
    # Add disclaimer
    disclaimer = "This information is general in nature and not specific legal advice for your situation. Consider consulting with a qualified attorney for advice specific to your circumstances."
    
    # Structure the response
    return {
        "diagnosis": response.content,
        "jurisdiction": jurisdiction,
        "legal_area": "To be determined from analysis",
        "disclaimer": disclaimer
    } 