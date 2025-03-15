import httpx
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.knowledge.pdf_url import PDFUrlKnowledgeBase
from agno.vectordb.pgvector import PgVector
from agno.storage.agent.postgres import PostgresAgentStorage
from agno.knowledge.combined import CombinedKnowledgeBase
from agno.knowledge.website import WebsiteKnowledgeBase
from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from agno.tools.googlesearch import GoogleSearchTools
import os
from agno.vectordb.qdrant import Qdrant
import asyncio
from agno.tools.query_generator import QueryGenerator
from agno.tools.patent_ranker import PatentRanker
from agno.templates import Templates

app = FastAPI()

db_url = "postgresql+psycopg://postgres:postgres@localhost:5432/ai_legal_vector"

api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.si5dt8LrrOg1cIngEUoDg15xVcqWmoq6fm9mJIfmDJA"
qdrant_url = "https://1a0aea0b-e070-4e05-981e-4a23be0d7150.us-west-2-0.aws.cloud.qdrant.io"
openai_key = os.getenv("OPENAI_API_KEY")
print(openai_key)

collection_name = "legal_documents"

vector_db = Qdrant(
    collection=collection_name,
    url=qdrant_url,
    api_key=api_key,
)

pdf_knowledge_base = PDFUrlKnowledgeBase(
    urls=["https://biblioteca.gafilat.org/wp-content/uploads/2024/07/Recomendaciones-metodologia-actDIC2023.pdf"],
    vector_db=vector_db
)

pdf_knowledge_base = PDFUrlKnowledgeBase(
    urls=["https://biblioteca.gafilat.org/wp-content/uploads/2024/07/Recomendaciones-metodologia-actDIC2023.pdf"],
    vector_db=vector_db)

websiteKnowledgeBase = WebsiteKnowledgeBase(
    urls=["https://www.supersociedades.gov.co/web/nuestra-entidad/cap-10-autocontrol-y-gesti%C3%B3n-del-riesgo-integral",
          "https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=175606",
          "https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=43292"
          ],
    vector_db=vector_db)

# websiteKnowledgeBase = WebsiteKnowledgeBase(
#     urls=["https://www.supersociedades.gov.co/web/nuestra-entidad/cap-10-autocontrol-y-gesti%C3%B3n-del-riesgo-integral",
#           "https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=175606",
#           "https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=43292"
#           ],
#     vector_db=PgVector(table_name="website_documents", db_url=db_url))

# Combine knowledge bases
# knowledge_base = CombinedKnowledgeBase(
#     sources=[pdf_knowledge_base, websiteKnowledgeBase],
#     vector_db=PgVector(table_name="combined_documents", db_url=db_url),
# )

knowledge_base = CombinedKnowledgeBase(
    sources=[pdf_knowledge_base, websiteKnowledgeBase],
    vector_db=vector_db
)


# client = httpx.Client(timeout=120)  # Aumenta el tiempo de espera a 30 segundos
# response = client.get("https://api.openai.com/v1/completions")
# print(response.text)


knowledge_base.load(recreate=False)

legal_researcher = Agent(
    name="Legal Researcher",
    role="Legal research specialist",
    model=OpenAIChat(id="gpt-4o", timeout=8000),
    tools=[GoogleSearchTools()],
    knowledge=knowledge_base,
    search_knowledge=True,
    storage=PostgresAgentStorage(table_name="agent_sessions", db_url=db_url),
    instructions=["""
                        Objective: Conduct in-depth legal research, summarize case law, and provide insights into statutes, regulations, and legal precedents.
                        "You are a highly skilled Legal Research Specialist with expertise in case law analysis, statutory interpretation, and legal doctrine synthesis. Your role is to provide in-depth legal research by analyzing relevant laws, court rulings, and legal literature to help users find authoritative legal sources. Given a legal question or topic, you should:
                        Identify Relevant Legal Sources: Search and summarize applicable statutes, regulations, and case laws from multiple jurisdictions.
                        Analyze Case Precedents: Extract key legal principles, holdings, and judicial reasoning from relevant cases.
                        Summarize Legal Literature: Provide concise yet detailed overviews of scholarly articles, legal opinions, and treatises.
                        Compare and Contrast Jurisdictions: Highlight differences and similarities in laws across multiple jurisdictions when applicable.
                        Provide Citations and References: Ensure all findings are backed by authoritative legal sources with proper citations.
                        Offer Clear and Neutral Explanations: Break down complex legal jargon into plain language while maintaining legal accuracy.""",
                  "Infer the language and intent of the document and give me the response or answer in the same language of the document",
                  "Find and cite relevant legal cases and precedents",
                  "Provide detailed research summaries with sources",
                  "Reference specific sections from the uploaded document",
                  "Always search the knowledge base for relevant information"
                  ],
    show_tool_calls=True,
    markdown=True
)


async def format_response(data: Dict[str, any]) -> BaseResponse:
    return BaseResponse(
        status="success",
        timestamp=datetime.now(),
        data=data
    )


async def handle_error(e: Exception) -> Dict[str, any]:
    return {
        "status": "error",
        "timestamp": datetime.now(),
        "error": str(e)
    }

agent = Agent(
    model=OpenAIChat(
        id="gpt-4o"),
    description="You are a helpful assistant.",
    markdown=True,
)


@app.get("/ask")
async def ask(query: str):
    response = agent.run(query)
    return {"response": response.content}

# New endpoints


@app.post("/api/legal-analysis")
async def legal_analysis(request):
    try:
        analysis = legal_researcher.run(
            f"Analyze the following legal document (type: {request.document_type}): {request.content}")
        return await format_response({"analysis": analysis.content})
    except Exception as e:
        raise HTTPException(status_code=500, detail=await handle_error(e))

# Pseudocode for legal issue diagnosis endpoint
async def diagnose_legal_issue(
    situation_description: str,
    jurisdiction: str,
    user_goal: str,
    timeline: Optional[str] = None,
    financial_considerations: Optional[str] = None
):
    # 1. Identify legal domain and sub-issues
    legal_domains = domain_classifier.classify(
        description=situation_description,
        jurisdiction=jurisdiction
    )
    
    # 2. Retrieve relevant legal information
    legal_information = await legal_database.get_information(
        domains=legal_domains,
        jurisdiction=jurisdiction
    )
    
    # 3. Identify applicable self-help resources
    self_help_resources = await resource_finder.find(
        domains=legal_domains,
        jurisdiction=jurisdiction,
        user_goal=user_goal
    )
    
    # 4. Determine if attorney consultation is recommended
    attorney_recommendation = recommendation_engine.assess_attorney_need(
        domains=legal_domains,
        situation_description=situation_description,
        timeline=timeline,
        complexity=assess_complexity(situation_description)
    )
    
    # 5. Generate comprehensive response with LLM
    diagnosis_result = await llm_client.generate(
        model="claude-3-haiku-20240307",
        prompt=templates.legal_issue_diagnosis(
            situation_description=situation_description,
            jurisdiction=jurisdiction,
            user_goal=user_goal,
            timeline=timeline,
            financial_considerations=financial_considerations,
            legal_domains=legal_domains,
            legal_information=legal_information,
            self_help_resources=self_help_resources,
            attorney_recommendation=attorney_recommendation
        ),
        temperature=0.1
    )
    
    return {
        "diagnosis": diagnosis_result
    }

# Pseudocode for demand letter generation endpoint
async def generate_demand_letter(
    debtor_info: Dict[str, str],
    debt_details: Dict[str, str],
    collection_history: List[Dict],
    jurisdiction: str,
    compliance_requirements: List[str],
    client_tone_preference: str = "professional"
):
    # 1. Verify compliance requirements for jurisdiction
    jurisdiction_requirements = await compliance_database.get_requirements(
        jurisdiction=jurisdiction,
        document_type="demand_letter"
    )
    
    # 2. Validate debtor information
    validated_debtor_info = await address_validator.validate(debtor_info)
    
    # 3. Select appropriate template based on parameters
    template = template_selector.select(
        debt_type=debt_details["type"],
        jurisdiction=jurisdiction,
        collection_stage=determine_collection_stage(collection_history),
        tone=client_tone_preference
    )
    
    # 4. Generate required disclosures
    disclosures = disclosure_generator.generate(
        jurisdiction=jurisdiction,
        debt_type=debt_details["type"],
        debt_amount=debt_details["amount"],
        compliance_requirements=compliance_requirements + jurisdiction_requirements
    )
    
    # 5. Generate demand letter with LLM
    letter_content = await llm_client.generate(
        model="claude-3-haiku-20240307",
        prompt=templates.demand_letter(
            debtor_info=validated_debtor_info,
            debt_details=debt_details,
            collection_history=collection_history,
            jurisdiction=jurisdiction,
            disclosures=disclosures,
            client_tone_preference=client_tone_preference,
            template=template
        ),
        temperature=0.3
    )
    
    # 6. Verify compliance of generated letter
    compliance_check = compliance_checker.check(
        letter_content=letter_content,
        jurisdiction=jurisdiction,
        compliance_requirements=compliance_requirements + jurisdiction_requirements
    )
    
    if not compliance_check["compliant"]:
        # Regenerate with compliance issues fixed
        letter_content = await llm_client.generate(
            model="claude-3-haiku-20240307",
            prompt=templates.demand_letter_fix_compliance(
                original_letter=letter_content,
                compliance_issues=compliance_check["issues"],
                debtor_info=validated_debtor_info,
                debt_details=debt_details,
                disclosures=disclosures
            ),
            temperature=0.2
        )
    
    # 7. Format letter for printing/sending
    formatted_letter = document_formatter.format(
        content=letter_content,
        document_type="demand_letter"
    )
    
    return {
        "letter": formatted_letter,
        "compliance_verification": compliance_check,
        "mailing_info": validated_debtor_info
    }

# Pseudocode for whistleblower report analysis endpoint
async def analyze_whistleblower_report(
    report_content: str,
    company_context: Dict[str, str],
    applicable_policies: List[str],
    regulatory_framework: List[str],
    prior_related_issues: Optional[List[Dict]] = None
):
    # 1. Anonymize report to remove PII
    anonymized_report = anonymizer.anonymize(report_content)
    
    # 2. Extract key allegations and evidence
    allegations = allegation_extractor.extract(anonymized_report)
    
    # 3. Categorize issues and assess severity
    categorization = issue_categorizer.categorize(
        allegations=allegations,
        company_context=company_context,
        regulatory_framework=regulatory_framework
    )
    
    # 4. Assess credibility based on report details
    credibility_assessment = credibility_assessor.assess(
        anonymized_report=anonymized_report,
        allegations=allegations,
        prior_related_issues=prior_related_issues
    )
    
    # 5. Identify regulatory implications
    regulatory_implications = regulation_analyzer.analyze(
        allegations=allegations,
        regulatory_framework=regulatory_framework
    )
    
    # 6. Generate comprehensive analysis with LLM
    analysis_result = await llm_client.analyze(
        model="claude-3-sonnet-20240229",
        prompt=templates.whistleblower_analysis(
            anonymized_report=anonymized_report,
            allegations=allegations,
            categorization=categorization,
            credibility_assessment=credibility_assessment,
            company_context=company_context,
            applicable_policies=applicable_policies,
            regulatory_implications=regulatory_implications,
            prior_related_issues=prior_related_issues
        ),
        temperature=0.1
    )
    
    # 7. Generate investigation plan
    investigation_plan = await llm_client.generate(
        model="claude-3-sonnet-20240229",
        prompt=templates.investigation_plan(
            allegations=allegations,
            categorization=categorization,
            company_context=company_context
        ),
        temperature=0.2
    )
    
    # 8. Log analysis (without original report content)
    await audit_logger.log(
        action="report_analysis",
        report_id=generate_id(),
        categorization=categorization,
        severity=categorization["severity"]
    )
    
    return {
        "analysis": analysis_result,
        "investigation_plan": investigation_plan,
        "categorization": categorization,
        "credibility_assessment": credibility_assessment,
        "regulatory_implications": regulatory_implications
    }

# Pseudocode for contract drafting endpoint
async def draft_contract(
    contract_type: str,
    parties: List[Dict[str, str]],
    key_terms: List[Dict[str, str]],
    jurisdiction: str,
    special_considerations: Optional[List[str]] = None,
    risk_profile: str = "balanced",
    negotiation_context: Optional[str] = None
):
    # 1. Retrieve contract template and standard clauses
    template = await template_library.get_template(
        contract_type=contract_type,
        jurisdiction=jurisdiction
    )
    
    standard_clauses = await clause_library.get_clauses(
        contract_type=contract_type,
        jurisdiction=jurisdiction,
        risk_profile=risk_profile
    )
    
    # 2. Generate customized clauses for key terms
    customized_clauses = {}
    for term in key_terms:
        customized_clause = await llm_client.generate(
            model="claude-3-opus-20240229",
            prompt=templates.clause_generation(
                contract_type=contract_type,
                term=term,
                jurisdiction=jurisdiction,
                risk_profile=risk_profile
            ),
            temperature=0.3
        )
        customized_clauses[term["name"]] = customized_clause
    
    # 3. Generate complete contract draft
    contract_draft = await llm_client.generate(
        model="claude-3-opus-20240229",
        prompt=templates.contract_drafting(
            contract_type=contract_type,
            parties=parties,
            key_terms=key_terms,
            jurisdiction=jurisdiction,
            standard_clauses=standard_clauses,
            customized_clauses=customized_clauses,
            special_considerations=special_considerations,
            risk_profile=risk_profile,
            negotiation_context=negotiation_context,
            template=template
        ),
        temperature=0.2
    )
    
    # 4. Post-process for proper formatting
    formatted_contract = document_formatter.format(
        contract_draft=contract_draft,
        contract_type=contract_type
    )
    
    # 5. Generate alternative clauses for potentially contentious provisions
    alternative_clauses = {}
    contentious_provisions = clause_analyzer.identify_contentious(
        contract_draft=contract_draft,
        contract_type=contract_type,
        negotiation_context=negotiation_context
    )
    
    for provision in contentious_provisions:
        alternatives = await llm_client.generate(
            model="claude-3-opus-20240229",
            prompt=templates.alternative_clauses(
                provision=provision,
                contract_type=contract_type,
                risk_profile=risk_profile,
                negotiation_context=negotiation_context
            ),
            temperature=0.4
        )
        alternative_clauses[provision] = alternatives
    
    return {
        "contract_draft": formatted_contract,
        "alternative_clauses": alternative_clauses,
        "explanatory_notes": clause_analyzer.generate_notes(contract_draft)
    }

# Pseudocode for patent prior art search endpoint
async def search_prior_art(
    invention_description: str,
    technical_features: List[str],
    proposed_claims: Optional[List[str]] = None,
    relevant_fields: List[str] = None,
    filing_timeline: Optional[str] = None
):
    # 1. Generate search queries from invention description and features
    search_queries = query_generator.generate_patent_queries(
        invention_description=invention_description,
        technical_features=technical_features,
        relevant_fields=relevant_fields
    )
    
    # 2. Search patent databases with generated queries
    search_results = await asyncio.gather(*[
        patent_database.search(query=query) for query in search_queries
    ])
    
    # 3. Deduplicate and rank results
    ranked_patents = patent_ranker.rank(
        search_results=search_results,
        technical_features=technical_features,
        proposed_claims=proposed_claims
    )
    
    # 4. Analyze top patents for relevance to invention
    analyzed_patents = []
    for patent in ranked_patents[:20]:  # Analyze top 20 patents
        patent_analysis = await llm_client.analyze(
            model="claude-3-opus-20240229",
            prompt=templates.patent_analysis(
                patent=patent,
                invention_description=invention_description,
                technical_features=technical_features,
                proposed_claims=proposed_claims
            ),
            temperature=0.1
        )
        analyzed_patents.append({
            "patent": patent,
            "analysis": patent_analysis
        })
    
    # 5. Generate comprehensive prior art report
    prior_art_report = await llm_client.analyze(
        model="claude-3-opus-20240229",
        prompt=templates.prior_art_report(
            invention_description=invention_description,
            technical_features=technical_features,
            proposed_claims=proposed_claims,
            analyzed_patents=analyzed_patents,
            filing_timeline=filing_timeline
        ),
        temperature=0.2
    )
    
    return {
        "report": prior_art_report,
        "analyzed_patents": analyzed_patents,
        "search_queries_used": search_queries
    }

# Pseudocode for case prediction endpoint
async def predict_case_outcome(
    case_type: str,
    jurisdiction: str,
    key_facts: List[str],
    legal_issues: List[str],
    judge_name: Optional[str] = None,
    opposing_counsel: Optional[str] = None,
    relevant_precedents: Optional[List[str]] = None
):
    # 1. Retrieve similar historical cases
    similar_cases = await case_database.find_similar_cases(
        case_type=case_type,
        jurisdiction=jurisdiction,
        key_facts=key_facts,
        legal_issues=legal_issues,
        judge_name=judge_name
    )
    
    # 2. Extract outcome patterns
    outcome_statistics = analytics_engine.analyze_outcomes(similar_cases)
    
    # 3. If judge provided, get judge-specific analytics
    judge_analytics = None
    if judge_name:
        judge_analytics = await judge_database.get_analytics(
            judge_name=judge_name,
            case_type=case_type,
            legal_issues=legal_issues
        )
    
    # 4. If opposing counsel provided, analyze their history
    counsel_analytics = None
    if opposing_counsel:
        counsel_analytics = await counsel_database.get_analytics(
            counsel_name=opposing_counsel,
            case_type=case_type,
            jurisdiction=jurisdiction
        )
    
    # 5. Generate prediction and analysis with LLM
    prediction_result = await llm_client.analyze(
        model="gpt-4o",  # or fine-tuned version
        prompt=templates.case_prediction(
            case_type=case_type,
            jurisdiction=jurisdiction,
            key_facts=key_facts,
            legal_issues=legal_issues,
            similar_cases=similar_cases,
            outcome_statistics=outcome_statistics,
            judge_analytics=judge_analytics,
            counsel_analytics=counsel_analytics,
            relevant_precedents=relevant_precedents
        ),
        temperature=0.2
    )
    
    # 6. Structure the prediction with confidence levels
    structured_prediction = prediction_parser.parse_with_confidence(prediction_result)
    
    # 7. Generate visualizations
    visualizations = visualization_generator.create(
        outcome_statistics=outcome_statistics,
        structured_prediction=structured_prediction
    )
    
    return {
        "prediction": structured_prediction,
        "supporting_data": {
            "similar_case_count": len(similar_cases),
            "outcome_statistics": outcome_statistics,
            "judge_analytics": judge_analytics,
            "counsel_analytics": counsel_analytics
        },
        "visualizations": visualizations
    }

# Pseudocode for legal chatbot endpoint
async def process_client_message(
    client_id: str,
    message: str,
    conversation_id: Optional[str] = None,
    authentication_token: Optional[str] = None,
    practice_area: Optional[str] = None
):
    # 1. Authenticate client if token provided
    if authentication_token:
        client = await auth_service.verify_client(authentication_token)
        if client and client.id != client_id:
            raise AuthenticationError("Invalid authentication")
    
    # 2. Retrieve or create conversation history
    conversation = await conversation_store.get_or_create(
        conversation_id=conversation_id,
        client_id=client_id
    )
    
    # 3. Apply appropriate guardrails based on conversation type
    guardrails = guardrail_service.get_guardrails(
        practice_area=practice_area,
        is_authenticated=bool(authentication_token)
    )
    
    # 4. For authenticated clients, retrieve case information if relevant
    case_info = None
    if authentication_token and conversation.is_case_related:
        case_info = await case_management_system.get_client_case_info(client_id)
    
    # 5. Generate response with LLM
    response = await llm_client.chat(
        model="gpt-4o",  # or "claude-3-haiku-20240307" for high volume
        messages=conversation.messages + [{"role": "user", "content": message}],
        system_message=templates.chatbot_system_message(
            practice_area=practice_area,
            guardrails=guardrails,
            case_info=case_info
        ),
        temperature=0.7  # Higher temperature for more conversational feel
    )
    
    # 6. Store conversation update
    await conversation_store.add_message(
        conversation_id=conversation.id,
        role="user",
        content=message
    )
    await conversation_store.add_message(
        conversation_id=conversation.id,
        role="assistant",
        content=response
    )
    
    # 7. Log interaction for analytics
    await analytics_service.log_interaction(
        client_id=client_id,
        conversation_id=conversation.id,
        message=message,
        response=response,
        practice_area=practice_area
    )
    
    return {
        "response": response,
        "conversation_id": conversation.id,
        "disclaimer": guardrails.disclaimer
    }

# Pseudocode for regulatory change analysis endpoint
async def analyze_regulatory_change(
    regulation_text: str,
    effective_date: str,
    industry: str,
    business_operations: List[str],
    current_compliance_status: Dict[str, str]
):
    # 1. Extract key requirements from regulation
    requirements = requirement_extractor.extract(regulation_text)
    
    # 2. Map requirements to business operations
    operation_impacts = requirement_mapper.map_to_operations(
        requirements=requirements,
        business_operations=business_operations
    )
    
    # 3. Assess current compliance status against new requirements
    compliance_gaps = compliance_assessor.identify_gaps(
        requirements=requirements,
        current_status=current_compliance_status
    )
    
    # 4. Generate implementation difficulty scores
    implementation_assessment = difficulty_assessor.assess(
        requirements=requirements,
        business_operations=business_operations,
        industry=industry
    )
    
    # 5. Generate comprehensive analysis with LLM
    analysis_result = await llm_client.analyze(
        model="claude-3-sonnet-20240229",
        prompt=templates.regulatory_analysis(
            regulation_text=regulation_text,
            effective_date=effective_date,
            industry=industry,
            business_operations=business_operations,
            requirements=requirements,
            operation_impacts=operation_impacts,
            compliance_gaps=compliance_gaps,
            implementation_assessment=implementation_assessment
        ),
        temperature=0.1
    )
    
    # 6. Structure the response for executive presentation
    structured_analysis = response_formatter.format_for_executives(analysis_result)
    
    return structured_analysis

# Pseudocode for legal research endpoint
async def conduct_legal_research(
    jurisdiction: str,
    legal_issue: str,
    relevant_facts: List[str],
    timeframe: Optional[str] = None,
    case_law_only: bool = False
):
    # 1. Formulate search queries based on the legal issue
    search_queries = query_generator.generate(
        legal_issue=legal_issue,
        jurisdiction=jurisdiction,
        relevant_facts=relevant_facts
    )
    
    # 2. Retrieve relevant legal documents from knowledge base
    search_results = await asyncio.gather(*[
        legal_database.search(
            query=query,
            jurisdiction=jurisdiction,
            document_types=["case_law", "statutes", "regulations"] if not case_law_only else ["case_law"],
            timeframe=timeframe
        ) for query in search_queries
    ])
    
    # 3. Rank and filter results
    relevant_documents = document_ranker.rank_and_filter(
        search_results=search_results,
        legal_issue=legal_issue,
        relevant_facts=relevant_facts
    )
    
    # 4. Generate research analysis with LLM
    research_analysis = await llm_client.analyze(
        model="claude-3-opus-20240229",
        prompt=templates.legal_research(
            legal_issue=legal_issue,
            jurisdiction=jurisdiction,
            relevant_facts=relevant_facts,
            relevant_documents=relevant_documents
        ),
        temperature=0.2
    )
    
    # 5. Verify citations and format properly
    verified_analysis = citation_verifier.verify_and_format(research_analysis)
    
    return verified_analysis

# Pseudocode for contract review endpoint
async def analyze_contract(
    contract_text: str,
    contract_type: str,
    parties: List[str],
    specific_concerns: Optional[List[str]] = None,
    relevant_regulations: Optional[List[str]] = None
):
    # 1. Parse document structure
    parsed_document = document_processor.parse(contract_text)
    
    # 2. Extract clauses and metadata
    clauses = clause_extractor.extract(parsed_document)
    
    # 3. Generate embeddings for similarity search
    clause_embeddings = embedding_model.embed_batch([c.text for c in clauses])
    
    # 4. For compliance checks, retrieve relevant regulatory requirements
    if relevant_regulations:
        regulatory_requirements = knowledge_base.get_requirements(relevant_regulations)
    
    # 5. Perform LLM analysis with structured prompt
    analysis_result = await llm_client.analyze(
        model="claude-3-opus-20240229",
        prompt=templates.contract_review(
            contract_text=contract_text,
            contract_type=contract_type,
            parties=parties,
            clauses=clauses,
            specific_concerns=specific_concerns,
            regulatory_requirements=regulatory_requirements if relevant_regulations else None
        ),
        temperature=0.1  # Low temperature for more deterministic output
    )
    
    # 6. Post-process and structure the response
    structured_analysis = response_parser.parse_contract_analysis(analysis_result)
    
    return structured_analysis
