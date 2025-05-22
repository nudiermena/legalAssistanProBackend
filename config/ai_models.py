
from agno.models.mistral import MistralChat

# Initialize AI models with appropriate timeouts
contract_review_model = MistralChat(id="mistral-large-latest")
legal_research_model = MistralChat(id="mistral-large-latest")
compliance_model = MistralChat(id="mistral-large-latest")
chatbot_model = MistralChat(id="mistral-large-latest")
case_prediction_model = MistralChat(id="mistral-large-latest")
patent_search_model = MistralChat(id="mistral-large-latest")
document_drafting_model = MistralChat(id="mistral-large-latest")
whistleblower_model = MistralChat(id="mistral-large-latest")
demand_letter_model = MistralChat(id="mistral-large-latest")
legal_diagnosis_model = MistralChat(id="mistral-large-latest")

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

def get_model(model_name: str) -> MistralChat:
    """Get an AI model instance by name"""
    if model_name not in MODELS:
        raise ValueError(f"Model {model_name} not found")
    return MODELS[model_name]