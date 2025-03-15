from agno.models.openai import OpenAIChat

# Initialize AI models with appropriate timeouts
contract_review_model = OpenAIChat(id="gpt-4", timeout=8000)
legal_research_model = OpenAIChat(id="gpt-4", timeout=8000)
compliance_model = OpenAIChat(id="gpt-4", timeout=8000)
chatbot_model = OpenAIChat(id="gpt-4", timeout=5000)
case_prediction_model = OpenAIChat(id="gpt-4", timeout=5000)
patent_search_model = OpenAIChat(id="gpt-4", timeout=8000)
document_drafting_model = OpenAIChat(id="gpt-4", timeout=8000)
whistleblower_model = OpenAIChat(id="gpt-4", timeout=5000)
demand_letter_model = OpenAIChat(id="gpt-4")
legal_diagnosis_model = OpenAIChat(id="gpt-4", timeout=3000)

#contract_review_model = OpenAIChat(id="gpt-4", timeout=8000)
#legal_research_model = OpenAIChat(id="gpt-4", timeout=8000)
#compliance_model = OpenAIChat(id="claude-3-sonnet-20240229", timeout=8000)
#chatbot_model = OpenAIChat(id="gpt-4", timeout=5000)
#case_prediction_model = OpenAIChat(id="gpt-4", timeout=5000)
#patent_search_model = OpenAIChat(id="claude-3-opus-20240229", timeout=8000)
#document_drafting_model = OpenAIChat(id="claude-3-opus-20240229", timeout=8000)
#whistleblower_model = OpenAIChat(id="claude-3-sonnet-20240229", timeout=5000)
#demand_letter_model = Claude(id="claude-3-7-sonnet-20250219")
#legal_diagnosis_model = OpenAIChat(id="claude-3-haiku-20240307", timeout=3000)

# Model mapping for easy access
MODELS = {
    "contract_review": contract_review_model,
    "legal_research": legal_research_model,
    "compliance": compliance_model,
    "chatbot": chatbot_model,
    "case_prediction": case_prediction_model,
    "patent_search": patent_search_model,
    "document_drafting": document_drafting_model,
    "whistleblower": whistleblower_model,
    "demand_letter": demand_letter_model,
    "legal_diagnosis": legal_diagnosis_model
}

def get_model(model_name: str) -> OpenAIChat:
    """Get an AI model instance by name"""
    if model_name not in MODELS:
        raise ValueError(f"Model {model_name} not found")
    return MODELS[model_name]