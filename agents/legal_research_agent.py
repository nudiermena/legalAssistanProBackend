from agno.agent import Agent
from agno.tools.googlesearch import GoogleSearchTools
from config.database import get_agent_storage
from config.ai_models import get_model
from config.knowledge_base import get_knowledge_base

def create_legal_research_agent() -> Agent:
    """Create a specialized agent for legal research"""
    return Agent(
        name="Legal Researcher",
        role="Legal research specialist",
        model=get_model("legal_research"),
        tools=[GoogleSearchTools()],
        knowledge=get_knowledge_base(),
        search_knowledge=True,
        storage=get_agent_storage("agent_sessions"),
        instructions=[
            "Conduct in-depth legal research, summarize case law, and provide insights into statutes, regulations, and legal precedents.",
            "Infer the language and intent of the document and give me the response or answer in the same language of the document",
            "Find and cite relevant legal cases and precedents",
            "Provide detailed research summaries with sources",
            "Reference specific sections from the uploaded document",
            "Always search the knowledge base for relevant information"
        ],
        show_tool_calls=True,
        markdown=True
    )

async def conduct_legal_research(
    jurisdiction: str,
    legal_issue: str,
    relevant_facts: list,
    timeframe: str = None,
    case_law_only: bool = False
) -> str:
    """Conduct comprehensive legal research on a specific issue"""
    agent = create_legal_research_agent()
    
    # Prepare the prompt with all relevant details
    prompt = f"""I need comprehensive legal research on the following issue:

JURISDICTION: {jurisdiction}
ISSUE: {legal_issue}
RELEVANT FACTS: {', '.join(relevant_facts)}
"""
    
    if timeframe:
        prompt += f"TIMEFRAME: {timeframe}\n"
    
    if case_law_only:
        prompt += "Please focus only on case law, not statutes or regulations.\n"
    
    prompt += """
Please provide:
1. A summary of the current state of the law on this issue
2. Analysis of 3-5 seminal cases that establish the governing principles
3. Discussion of any circuit splits or jurisdictional differences
4. Identification of cases with similar fact patterns to our situation
5. Counter arguments and contrary authority we should be prepared to address
6. Statutory or regulatory provisions that interact with this case law
7. Emerging trends or recent developments that might signal a shift in the courts' approach

For each case, include the full citation, a concise summary of relevant facts, the court's holding, and key reasoning. Emphasize language we might quote in a brief.
"""
    
    # Run the research
    response = agent.run(prompt)
    
    return response.content 