-- Updated Memory Schema for Legal AI Assistant
-- References public.profiles table instead of auth.users

-- Create schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS ai;

-- User Memories Table
CREATE TABLE IF NOT EXISTS ai.user_memories (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    memory_content TEXT NOT NULL,
    topics TEXT[] DEFAULT '{}',
    memory_type VARCHAR(50) DEFAULT 'general',
    relevance_score FLOAT DEFAULT 1.0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes for efficient querying
    CONSTRAINT idx_user_memories_user_id_idx ON user_memories(user_id),
    CONSTRAINT idx_user_memories_topics_idx ON user_memories USING GIN(topics),
    CONSTRAINT idx_user_memories_memory_type_idx ON user_memories(memory_type),
    CONSTRAINT idx_user_memories_relevance_score_idx ON user_memories(relevance_score),
    CONSTRAINT idx_user_memories_created_at_idx ON user_memories(created_at)
);

-- Agent Sessions Table
CREATE TABLE IF NOT EXISTS ai.agent_sessions (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    agent_name VARCHAR(100) NOT NULL,
    session_id VARCHAR(255) UN NULL,
    session_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes for efficient querying
    CONSTRAINT idx_agent_sessions_user_id_idx ON agent_sessions(user_id),
    CONSTRAINT idx_agent_sessions_agent_name_idx ON agent_sessions(agent_name),
    CONSTRAINT idx_agent_sessions_session_id_idx ON agent_sessions(session_id),
    CONSTRAINT idx_agent_sessions_created_at_idx ON agent_sessions(created_at)
);

-- Session Summaries Table
CREATE TABLE IF NOT EXISTS ai.session_summaries (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    session_id VARCHAR(255) NOT NULL,
    summary_content TEXT NOT NULL,
    key_points TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes for efficient querying
    CONSTRAINT idx_session_summaries_user_id_idx ON session_summaries(user_id),
    CONSTRAINT idx_session_summaries_session_id_idx ON session_summaries(session_id),
    CONSTRAINT idx_session_summaries_created_at_idx ON session_summaries(created_at)
);

-- Memory Statistics Table
CREATE TABLE IF NOT EXISTS ai.memory_statistics (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    agent_name VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    total_memories INTEGER DEFAULT 0,
    memory_types JSONB DEFAULT '{}',
    average_relevance_score FLOAT DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes for efficient querying
    CONSTRAINT idx_memory_statistics_user_agent_date UNIQUE(user_id, agent_name, date),
    CONSTRAINT idx_memory_statistics_user_id_idx ON memory_statistics(user_id),
    CONSTRAINT idx_memory_statistics_agent_name_idx ON memory_statistics(agent_name),
    CONSTRAINT idx_memory_statistics_date_idx ON memory_statistics(date)
);

-- Agent-specific memory tables for different agents
-- Chatbot Agent Memories
CREATE TABLE IF NOT EXISTS ai.chatbot_agent_memories (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    memory_content TEXT NOT NULL,
    conversation_context TEXT,
    practice_area VARCHAR(100),
    legal_terms TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT idx_chatbot_memories_user_id_idx ON chatbot_agent_memories(user_id),
    CONSTRAINT idx_chatbot_memories_practice_area_idx ON chatbot_agent_memories(practice_area)
);

-- Contract Agent Memories
CREATE TABLE IF NOT EXISTS ai.contract_agent_memories (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    memory_content TEXT NOT NULL,
    contract_type VARCHAR(100),
    risk_patterns TEXT[] DEFAULT '{}',
    compliance_issues TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT idx_contract_memories_user_id_idx ON contract_agent_memories(user_id),
    CONSTRAINT idx_contract_memories_contract_type_idx ON contract_agent_memories(contract_type)
);

-- Legal Research Agent Memories
CREATE TABLE IF NOT EXISTS ai.legal_research_agent_memories (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    memory_content TEXT NOT NULL,
    research_topics TEXT[] DEFAULT '{}',
    legal_sources TEXT[] DEFAULT '{}',
    jurisdiction VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT idx_research_memories_user_id_idx ON legal_research_agent_memories(user_id),
    CONSTRAINT idx_research_memories_jurisdiction_idx ON legal_research_agent_memories(jurisdiction)
);

-- Case Prediction Agent Memories
CREATE TABLE IF NOT EXISTS ai.case_prediction_agent_memories (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    memory_content TEXT NOT NULL,
    case_patterns TEXT[] DEFAULT '{}',
    prediction_accuracy FLOAT DEFAULT 0.0,
    case_types TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT idx_case_prediction_memories_user_id_idx ON case_prediction_agent_memories(user_id)
);

-- Compliance Agent Memories
CREATE TABLE IF NOT EXISTS ai.compliance_agent_memories (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    memory_content TEXT NOT NULL,
    compliance_areas TEXT[] DEFAULT '{}',
    regulatory_requirements TEXT[] DEFAULT '{}',
    risk_level VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT idx_compliance_memories_user_id_idx ON compliance_agent_memories(user_id),
    CONSTRAINT idx_compliance_memories_risk_level_idx ON compliance_agent_memories(risk_level)
);

-- Document Drafting Agent Memories
CREATE TABLE IF NOT EXISTS ai.document_drafting_agent_memories (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    memory_content TEXT NOT NULL,
    document_types TEXT[] DEFAULT '{}',
    drafting_style TEXT,
    legal_terminology TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT idx_document_drafting_memories_user_id_idx ON document_drafting_agent_memories(user_id),
    CONSTRAINT idx_document_drafting_memories_document_types_idx ON document_drafting_agent_memories(document_types)
);

-- Demand Letter Agent Memories
CREATE TABLE IF NOT EXISTS ai.demand_letter_agent_memories (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    memory_content TEXT NOT NULL,
    demand_types TEXT[] DEFAULT '{}',
    legal_basis TEXT[] DEFAULT '{}',
    settlement_patterns TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT idx_demand_letter_memories_user_id_idx ON demand_letter_agent_memories(user_id)
);

-- Patent Agent Memories
CREATE TABLE IF NOT EXISTS ai.patent_agent_memories (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    memory_content TEXT NOT NULL,
    patent_categories TEXT[] DEFAULT '{}',
    technical_fields TEXT[] DEFAULT '{}',
    prior_art_patterns TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT idx_patent_memories_user_id_idx ON patent_agent_memories(user_id)
);

-- Regulatory Agent Memories
CREATE TABLE IF NOT EXISTS ai.regulatory_agent_memories (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    memory_content TEXT NOT NULL,
    regulatory_areas TEXT[] DEFAULT '{}',
    compliance_requirements TEXT[] DEFAULT '{}',
    risk_assessments TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT idx_regulatory_memories_user_id_idx ON regulatory_agent_memories(user_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_memories_user_id ON ai.user_memories(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_user_id ON ai.agent_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_session_summaries_user_id ON ai.session_summaries(user_id);
CREATE INDEX IF NOT EXISTS idx_memory_statistics_user_id ON ai.memory_statistics(user_id);

-- Create GIN indexes for array fields
CREATE INDEX IF NOT EXISTS idx_user_memories_topics_gin ON ai.user_memories USING GIN(topics);
CREATE INDEX IF NOT EXISTS idx_chatbot_memories_legal_terms_gin ON ai.chatbot_agent_memories USING GIN(legal_terms);
CREATE INDEX IF NOT EXISTS idx_contract_memories_risk_patterns_gin ON ai.contract_agent_memories USING GIN(risk_patterns);
CREATE INDEX IF NOT EXISTS idx_contract_memories_compliance_issues_gin ON ai.contract_agent_memories USING GIN(compliance_issues);

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON SCHEMA ai TO your_role;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA ai TO your_role;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA ai TO your_role;
