from agno.agent import Agent
from config.database import get_agent_storage
from config.ai_models import get_model
from config.knowledge_base import get_knowledge_base
from typing import Dict, List, Optional

def create_document_drafting_agent() -> Agent:
    """Create a specialized agent for document drafting"""
    return Agent(
        name="Document Drafter",
        role="Legal document drafting specialist",
        model=get_model("document_drafting"),
        knowledge=get_knowledge_base(),
        search_knowledge=True,
        storage=get_agent_storage("drafting_sessions"),
        markdown=True
    )

async def draft_document(
    document_content: str,
    document_context: dict,
    parties: List[str],
    jurisdiction: str,
    special_considerations: Optional[List[str]] = None
) -> Dict[str, str]:
    """Draft legal documents with proper formatting and clauses"""
    agent = create_document_drafting_agent()
    
    # Format parties for the prompt
    parties_text = "\n".join([f"- {party}" for party in parties])
    
    # Format special considerations if provided
    considerations_text = "\n".join([f"- {consideration}" for consideration in special_considerations]) if special_considerations else "None specified"
    
    # Prepare the prompt
    prompt = f"""Draft a legal document with the following parameters:

DOCUMENT CONTENT:
{document_content}

DOCUMENT CONTEXT:
{document_context}

PARTIES INVOLVED:
{parties_text}

JURISDICTION:
{jurisdiction}

SPECIAL CONSIDERATIONS:
{considerations_text}

Please ensure the document:
1. Uses proper legal language and formatting
2. Includes all necessary clauses and provisions
3. Complies with jurisdiction-specific requirements
4. Addresses all special considerations
5. Clearly defines terms and conditions
6. Includes proper signature blocks and dates
7. Has appropriate section numbering and organization
8. Includes any required notices or disclosures

The document should be ready for review and signature."""

    # Run the generation
    response = agent.run(prompt)
    
    # Structure the response
    return {
        "document": response.content,
        "jurisdiction": jurisdiction,
        "parties": parties
    }

async def draft_contract(
    contract_type: str,
    parties: list,
    key_terms: list,
    jurisdiction: str,
    special_considerations: list = None,
    risk_profile: str = "balanced",
    negotiation_context: str = None
) -> dict:
    """Draft customized legal contracts based on specified parameters"""
    agent = create_document_drafting_agent()
    
    # Format parties for the prompt
    parties_text = "\n".join([f"- {party.get('name', 'Unnamed Party')}: {party.get('details', 'No details provided')}" for party in parties])
    
    # Format key terms for the prompt
    terms_text = "\n".join([f"- {term.get('name', 'Unnamed Term')}: {term.get('details', 'No details provided')}" for term in key_terms])
    
    # Prepare the prompt
    prompt = f"""Draft a {contract_type} agreement with the following parameters:

PARTIES:
{parties_text}

KEY TERMS:
{terms_text}

JURISDICTION:
{jurisdiction}

RISK PROFILE:
{risk_profile}
"""
    
    if special_considerations:
        prompt += f"\nSPECIAL CONSIDERATIONS:\n{', '.join(special_considerations)}\n"
    
    if negotiation_context:
        prompt += f"\nNEGOTIATION CONTEXT:\n{negotiation_context}\n"
    
    prompt += """
Please draft a complete contract that:
1. Uses clear, precise language accessible to business users
2. Includes all standard sections appropriate for this contract type
3. Incorporates the specified key terms with appropriate detail
4. Provides balanced protections appropriate to the risk profile
5. Complies with relevant laws in the specified jurisdiction
6. Includes explanatory notes for provisions requiring business decisions
7. Flags areas where additional client input would be valuable
8. Offers alternative language options for potentially contentious provisions

Format the document with proper legal document styling, including numbered sections, defined terms, and signature blocks.
"""
    
    # Run the drafting
    response = agent.run(prompt)
    
    # Structure the response
    return {
        "contract_draft": response.content,
        "contract_type": contract_type,
        "jurisdiction": jurisdiction,
        "parties": [party.get('name', 'Unnamed Party') for party in parties]
    } 