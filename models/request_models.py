from typing import Dict, List, Optional
from pydantic import BaseModel

class ContractReviewRequest(BaseModel):
    """Request model for contract review"""
    text: Optional[str] = None
    instructions: Optional[str] = None

class LegalResearchRequest(BaseModel):
    jurisdiction: str
    legal_issue: str
    relevant_facts: List[str]
    timeframe: Optional[str] = None
    case_law_only: bool = False

class RegulatoryChangeRequest(BaseModel):
    regulation_text: str
    effective_date: str
    industry: str
    business_operations: List[str]
    current_compliance_status: Dict[str, str]

class LegalChatbotRequest(BaseModel):
    client_id: str
    message: str
    conversation_id: Optional[str] = None
    authentication_token: Optional[str] = None
    practice_area: Optional[str] = None

class CasePredictionRequest(BaseModel):
    case_type: str
    jurisdiction: str
    key_facts: List[str]
    legal_issues: List[str]
    judge_name: Optional[str] = None
    opposing_counsel: Optional[str] = None
    relevant_precedents: Optional[List[str]] = None

class PatentSearchRequest(BaseModel):
    invention_description: str
    technical_features: List[str]
    proposed_claims: Optional[List[str]] = None
    relevant_fields: Optional[List[str]] = None
    filing_timeline: Optional[str] = None

class DocumentDraftingRequest(BaseModel):
    document_type: str
    parties: Dict[str, str]
    key_terms: Dict[str, str]
    jurisdiction: str
    special_considerations: Optional[List[str]] = None
    risk_profile: str = "medium"
    negotiation_context: Optional[str] = None

class WhistleblowerAnalysisRequest(BaseModel):
    report_content: str
    company_context: Dict[str, str]
    applicable_policies: List[str]
    regulatory_framework: List[str]
    prior_related_issues: Optional[List[Dict]] = None

class DemandLetterRequest(BaseModel):
    debtor_info: Dict[str, str]
    debt_details: Dict[str, str]
    collection_history: List[Dict]
    jurisdiction: str
    compliance_requirements: List[str]
    client_tone_preference: str = "professional"

class LegalDiagnosisRequest(BaseModel):
    situation_description: str
    jurisdiction: str
    user_goal: str
    timeline: Optional[str] = None
    financial_considerations: Optional[str] = None

class ChatRequest(BaseModel):
    """Request model for chat interactions"""
    message: str
    instructions: Optional[str] = None
    context: Optional[dict] = None 