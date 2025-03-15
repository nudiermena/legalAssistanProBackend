from agno.agent import Agent
from config.database import get_agent_storage
from config.ai_models import get_model
from config.knowledge_base import get_knowledge_base
from typing import Dict, List

def create_demand_letter_agent() -> Agent:
    """Create a specialized agent for demand letter generation"""
    return Agent(
        name="Demand Letter Generator",
        role="Debt collection specialist",
        model=get_model("demand_letter"),
        knowledge=get_knowledge_base(),
        search_knowledge=True,
        storage=get_agent_storage("letter_sessions"),
        markdown=True
    )

async def generate_demand_letter(
    debtor_info: Dict[str, str],
    debt_details: Dict[str, str],
    collection_history: List[Dict],
    jurisdiction: str,
    compliance_requirements: List[str],
    client_tone_preference: str = "professional"
) -> Dict[str, str]:
    """Generate legally compliant demand letters for debt collection"""
    agent = create_demand_letter_agent()
    
    # Format debtor info for the prompt
    debtor_info_text = "\n".join([f"- {key}: {value}" for key, value in debtor_info.items()])
    
    # Format debt details for the prompt
    debt_details_text = "\n".join([f"- {key}: {value}" for key, value in debt_details.items()])
    
    # Format collection history for the prompt
    collection_history_text = "\n".join([f"- {attempt.get('date', 'No date')}: {attempt.get('action', 'No action')} - {attempt.get('response', 'No response')}" for attempt in collection_history])
    
    # Prepare the prompt
    prompt = f"""Create a debt collection demand letter with the following parameters:

DEBTOR INFORMATION:
{debtor_info_text}

DEBT DETAILS:
{debt_details_text}

COLLECTION HISTORY:
{collection_history_text}

JURISDICTION:
{jurisdiction}

COMPLIANCE REQUIREMENTS:
{', '.join(compliance_requirements)}

CLIENT TONE PREFERENCE:
{client_tone_preference}

Please generate a demand letter that:
1. Clearly states the amount owed and origin of the debt
2. Includes all legally required disclosures for the jurisdiction
3. Provides payment options and contact information
4. Sets a specific deadline for response
5. Outlines potential next steps if payment is not received
6. Maintains a professional tone that preserves business relationships
7. Complies with all applicable collection laws
8. Includes proper validation notice if required

The letter should be ready for letterhead and signature with appropriate formatting for professional correspondence.
"""
    
    # Run the generation
    response = agent.run(prompt)
    
    # Structure the response
    return {
        "letter": response.content,
        "debtor_name": debtor_info.get('name', 'Unnamed Debtor'),
        "amount_due": debt_details.get('amount', 'Unknown Amount'),
        "jurisdiction": jurisdiction
    } 