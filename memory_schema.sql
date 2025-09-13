-- Memory System Schema for Legal AI Assistant
-- This schema supports Agno's memory system with PostgreSQL/Supabase

-- Create schema for AI memory system
CREATE SCHEMA IF NOT EXISTS ai;

-- User Memories Table
-- Stores personalized memories for each user across different agents
CREATE TABLE IF NOT EXISTS ai.user_memories (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    agent_name VARCHAR(100) NOT NULL,
    memory_content TEXT NOT NULL,
    memory_type VARCHAR(50) DEFAULT 'general',
    relevance_score FLOAT DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    -- Indexes for efficient querying
    CONSTRAINT idx_user_memories_user_agent UNIQUE(user_id, agent_name, memory_content),
    CONSTRAINT idx_user_memories_user_id_idx ON user_memories(user_id),
    CONSTRAINT idx_user_memories_agent_name_idx ON user_memories(agent_name),
    CONSTRAINT idx_user_memories_created_at_idx ON user_memories(created_at)
);

-- Session Storage Table
-- Stores conversation history and session state for each agent
CREATE TABLE IF NOT EXISTS ai.agent_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    agent_name VARCHAR(100) NOT NULL,
    session_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    team_session_id VARCHAR(255),
    
    -- Indexes for efficient querying
    CONSTRAINT idx_agent_sessions_session_id UNIQUE(session_id),
    CONSTRAINT idx_agent_sessions_user_id_idx ON agent_sessions(user_id),
    CONSTRAINT idx_agent_sessions_agent_name_idx ON agent_sessions(agent_name),
    CONSTRAINT idx_agent_sessions_created_at_idx ON agent_sessions(created_at)
);

-- Session Summaries Table
-- Stores condensed summaries of sessions for long-term memory
CREATE TABLE IF NOT EXISTS ai.session_summaries (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    session_id VARCHAR(255) NOT NULL,
    agent_name VARCHAR(100) NOT NULL,
    summary_content TEXT NOT NULL,
    key_topics TEXT[] DEFAULT '{}',
    sentiment_score FLOAT DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes for efficient querying
    CONSTRAINT idx_session_summaries_user_session UNIQUE(user_id, session_id),
    CONSTRAINT idx_session_summaries_user_id_idx ON session_summaries(user_id),
    CONSTRAINT idx_session_summaries_agent_name_idx ON session_summaries(agent_name),
    CONSTRAINT idx_session_summaries_created_at_idx ON session_summaries(created_at)
);

-- Memory Statistics Table
-- Tracks memory usage and performance metrics
CREATE TABLE IF NOT EXISTS ai.memory_statistics (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    agent_name VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    total_memories INTEGER DEFAULT 0,
    new_memories INTEGER DEFAULT 0,
    session_count INTEGER DEFAULT 0,
    avg_session_duration INTERVAL,
    memory_hit_rate FLOAT DEFAULT 0.0,
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
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
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
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
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
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
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
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
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
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
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
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
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
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
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
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
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
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    memory_content TEXT NOT NULL,
    regulatory_bodies TEXT[] DEFAULT '{}',
    compliance_areas TEXT[] DEFAULT '{}',
    regulatory_changes TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT idx_regulatory_memories_user_id_idx ON regulatory_agent_memories(user_id)
);

-- Whistleblower Agent Memories
CREATE TABLE IF NOT EXISTS ai.whistleblower_agent_memories (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    memory_content TEXT NOT NULL,
    whistleblower_types TEXT[] DEFAULT '{}',
    protection_mechanisms TEXT[] DEFAULT '{}',
    legal_frameworks TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT idx_whistleblower_memories_user_id_idx ON whistleblower_agent_memories(user_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_memories_relevance ON ai.user_memories(relevance_score DESC);
CREATE INDEX IF NOT EXISTS idx_user_memories_type ON ai.user_memories(memory_type);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_expires ON ai.agent_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_session_summaries_sentiment ON ai.session_summaries(sentiment_score DESC);
CREATE INDEX IF NOT EXISTS idx_memory_statistics_hit_rate ON ai.memory_statistics(memory_hit_rate DESC);

-- Enable Row Level Security (RLS) on all AI tables
ALTER TABLE ai.user_memories ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai.agent_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai.session_summaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai.memory_statistics ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai.chatbot_agent_memories ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai.contract_agent_memories ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai.legal_research_agent_memories ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai.case_prediction_agent_memories ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai.compliance_agent_memories ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai.document_drafting_agent_memories ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai.demand_letter_agent_memories ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai.patent_agent_memories ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai.regulatory_agent_memories ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai.whistleblower_agent_memories ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for user data isolation
-- Users can only access their own data

-- User Memories policies
CREATE POLICY "Users can view own user_memories" ON ai.user_memories
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own user_memories" ON ai.user_memories
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own user_memories" ON ai.user_memories
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own user_memories" ON ai.user_memories
    FOR DELETE USING (auth.uid() = user_id);

-- Agent Sessions policies
CREATE POLICY "Users can view own agent_sessions" ON ai.agent_sessions
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own agent_sessions" ON ai.agent_sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own agent_sessions" ON ai.agent_sessions
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own agent_sessions" ON ai.agent_sessions
    FOR DELETE USING (auth.uid() = user_id);

-- Session Summaries policies
CREATE POLICY "Users can view own session_summaries" ON ai.session_summaries
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own session_summaries" ON ai.session_summaries
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own session_summaries" ON ai.session_summaries
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own session_summaries" ON ai.session_summaries
    FOR DELETE USING (auth.uid() = user_id);

-- Memory Statistics policies
CREATE POLICY "Users can view own memory_statistics" ON ai.memory_statistics
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own memory_statistics" ON ai.memory_statistics
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own memory_statistics" ON ai.memory_statistics
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own memory_statistics" ON ai.memory_statistics
    FOR DELETE USING (auth.uid() = user_id);

-- Agent-specific memory policies (example for chatbot_agent_memories)
CREATE POLICY "Users can view own chatbot_memories" ON ai.chatbot_agent_memories
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own chatbot_memories" ON ai.chatbot_agent_memories
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own chatbot_memories" ON ai.chatbot_agent_memories
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own chatbot_memories" ON ai.chatbot_agent_memories
    FOR DELETE USING (auth.uid() = user_id);

-- Similar policies for all other agent memory tables
-- (contract_agent_memories, legal_research_agent_memories, etc.)
-- This ensures users can only access their own data

-- Create functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic timestamp updates
CREATE TRIGGER update_user_memories_updated_at 
    BEFORE UPDATE ON ai.user_memories 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_sessions_updated_at 
    BEFORE UPDATE ON ai.agent_sessions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function to clean up expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM ai.agent_sessions 
    WHERE expires_at IS NOT NULL AND expires_at < NOW();
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create a scheduled job to clean up expired sessions (if using pg_cron)
-- SELECT cron.schedule('cleanup-expired-sessions', '0 2 * * *', 'SELECT cleanup_expired_sessions();');

-- Grant permissions (adjust as needed for your Supabase setup)
-- GRANT USAGE ON SCHEMA ai TO authenticated;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA ai TO authenticated;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA ai TO authenticated; 