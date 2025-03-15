from agno.agent import Agent
from agno.tools.googlesearch import GoogleSearchTools
from config.database import get_agent_storage
from config.ai_models import get_model
from config.knowledge_base import get_knowledge_base

class QueryGenerator:
    def generate_patent_queries(self, invention_description: str, technical_features: list, relevant_fields: list = None) -> list:
        """Generate search queries for patent search based on invention description and features"""
        queries = []
        
        # Basic query from description
        queries.append(invention_description[:100])
        
        # Queries from technical features
        for feature in technical_features:
            queries.append(feature)
            
        # Combine features with fields if provided
        if relevant_fields:
            for field in relevant_fields:
                for feature in technical_features[:2]:  # Limit combinations
                    queries.append(f"{field} {feature}")
        
        return queries[:5]  # Limit to 5 queries

def create_patent_agent() -> Agent:
    """Create a specialized agent for patent search"""
    return Agent(
        name="Patent Searcher",
        role="Patent prior art specialist",
        model=get_model("patent_search"),
        knowledge=get_knowledge_base(),
        search_knowledge=True,
        storage=get_agent_storage("patent_sessions"),
        tools=[GoogleSearchTools()],
        markdown=True
    )

async def search_prior_art(
    invention_description: str,
    technical_features: list,
    proposed_claims: list = None,
    relevant_fields: list = None,
    filing_timeline: str = None
) -> dict:
    """Search for prior art related to patent applications"""
    agent = create_patent_agent()
    query_generator = QueryGenerator()
    
    # Generate search queries based on invention description and features
    search_queries = query_generator.generate_patent_queries(
        invention_description=invention_description,
        technical_features=technical_features,
        relevant_fields=relevant_fields if relevant_fields else []
    )
    
    # Prepare the prompt
    prompt = f"""Conduct a comprehensive prior art analysis for the following invention:

INVENTION DESCRIPTION:
{invention_description}

KEY TECHNICAL FEATURES:
{', '.join(technical_features)}
"""
    
    if proposed_claims:
        prompt += f"\nPROPOSED CLAIMS:\n{', '.join(proposed_claims)}\n"
    
    if relevant_fields:
        prompt += f"\nRELEVANT FIELDS:\n{', '.join(relevant_fields)}\n"
    
    if filing_timeline:
        prompt += f"\nFILING TIMELINE:\n{filing_timeline}\n"
    
    prompt += f"\nSEARCH QUERIES USED:\n{', '.join(search_queries)}\n"
    
    prompt += """
For your analysis:
1. Identify the most relevant potential prior art references
2. For each reference, analyze:
   - Specific overlap with our invention's claims
   - Critical differences that might maintain patentability
   - Filing/priority dates relative to our timeline
   - Assignee/inventor information
3. Map each reference to specific claims/features of our invention
4. Suggest claim modifications to overcome identified prior art
5. Assess patentability likelihood for key features
6. Identify white space opportunities for focusing claims
7. Flag any potential obviousness combinations of references

Organize findings by potential impact on patentability, from most concerning to least concerning references.
"""
    
    # Run the search
    response = agent.run(prompt)
    
    return {
        "report": response.content,
        "search_queries_used": search_queries,
        "invention_summary": invention_description[:200] + "..."
    } 