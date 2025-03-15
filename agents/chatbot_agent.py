import datetime
from agno.agent import Agent
from config.database import get_agent_storage
from config.ai_models import get_model
from config.knowledge_base import get_knowledge_base

def create_chatbot_agent(
    practice_area: str = None,
    authentication_token: str = None
) -> Agent:
    """Create a specialized agent for client chat"""
    system_instructions = [
        "You are a client-facing FAQ chatbot for a law firm.",
        "Provide accurate, jurisdiction-specific general information",
        "Use plain language accessible to non-lawyers",
        "Include appropriate disclaimers about not providing legal advice",
        "Recognize when questions require attorney evaluation",
        "Maintain a helpful, informative tone"
    ]
    
    if practice_area:
        system_instructions.append(f"You specialize in {practice_area} law.")
    
    if authentication_token:
        system_instructions.append("The user is an authenticated client. You may provide more specific information.")
    else:
        system_instructions.append("The user is not authenticated. Provide only general information and encourage consultation with an attorney.")
    
    return Agent(
        name="Legal Assistant",
        role="Client-facing legal assistant",
        model=get_model("chatbot"),
        knowledge=get_knowledge_base(),
        search_knowledge=True,
        storage=get_agent_storage("chat_sessions"),
        instructions=system_instructions,
        markdown=True
    )

async def process_client_message(
    client_id: str,
    message: str,
    conversation_id: str = None,
    authentication_token: str = None,
    practice_area: str = None
) -> dict:
    """Process client messages and provide helpful legal information"""
    agent = create_chatbot_agent(practice_area, authentication_token)
    
    # Get conversation history if conversation_id is provided
    conversation_context = ""
    if conversation_id:
        conversation_context = f"This is a continuation of conversation {conversation_id}.\n\n"
    
    # Run the chat
    response = agent.run(conversation_context + message)
    
    # Generate a new conversation ID if not provided
    if not conversation_id:
        conversation_id = f"conv_{client_id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Add disclaimer
    disclaimer = "This information is general in nature and not specific legal advice for your situation."
    
    return {
        "response": response.content,
        "conversation_id": conversation_id,
        "disclaimer": disclaimer
    } 