-- Migration to fix user_id data type in AI schema tables
-- Change from VARCHAR(255) to UUID to match auth.users(id)

-- First, drop existing indexes that reference user_id
DROP INDEX IF EXISTS ai.idx_user_memories_user_id_idx;
DROP INDEX IF EXISTS ai.idx_agent_sessions_user_id_idx;
DROP INDEX IF EXISTS ai.idx_session_summaries_user_id_idx;
DROP INDEX IF EXISTS ai.idx_memory_statistics_user_id_idx;
DROP INDEX IF EXISTS ai.idx_chatbot_memories_user_id_idx;
DROP INDEX IF EXISTS ai.idx_contract_memories_user_id_idx;
DROP INDEX IF EXISTS ai.idx_research_memories_user_id_idx;
DROP INDEX IF EXISTS ai.idx_case_prediction_memories_user_id_idx;
DROP INDEX IF EXISTS ai.idx_compliance_memories_user_id_idx;
DROP INDEX IF EXISTS ai.idx_document_drafting_memories_user_id_idx;
DROP INDEX IF EXISTS ai.idx_demand_letter_memories_user_id_idx;
DROP INDEX IF EXISTS ai.idx_patent_memories_user_id_idx;
DROP INDEX IF EXISTS ai.idx_regulatory_memories_user_id_idx;
DROP INDEX IF EXISTS ai.idx_whistleblower_memories_user_id_idx;

-- Drop unique constraints that reference user_id
ALTER TABLE ai.user_memories DROP CONSTRAINT IF EXISTS idx_user_memories_user_agent;
ALTER TABLE ai.agent_sessions DROP CONSTRAINT IF EXISTS idx_agent_sessions_session_id;
ALTER TABLE ai.session_summaries DROP CONSTRAINT IF EXISTS idx_session_summaries_user_session;
ALTER TABLE ai.memory_statistics DROP CONSTRAINT IF EXISTS idx_memory_statistics_user_agent_date;

-- Change user_id column data type to UUID in all AI tables
ALTER TABLE ai.user_memories ALTER COLUMN user_id TYPE UUID USING user_id::UUID;
ALTER TABLE ai.agent_sessions ALTER COLUMN user_id TYPE UUID USING user_id::UUID;
ALTER TABLE ai.session_summaries ALTER COLUMN user_id TYPE UUID USING user_id::UUID;
ALTER TABLE ai.memory_statistics ALTER COLUMN user_id TYPE UUID USING user_id::UUID;
ALTER TABLE ai.chatbot_agent_memories ALTER COLUMN user_id TYPE UUID USING user_id::UUID;
ALTER TABLE ai.contract_agent_memories ALTER COLUMN user_id TYPE UUID USING user_id::UUID;
ALTER TABLE ai.legal_research_agent_memories ALTER COLUMN user_id TYPE UUID USING user_id::UUID;
ALTER TABLE ai.case_prediction_agent_memories ALTER COLUMN user_id TYPE UUID USING user_id::UUID;
ALTER TABLE ai.compliance_agent_memories ALTER COLUMN user_id TYPE UUID USING user_id::UUID;
ALTER TABLE ai.document_drafting_agent_memories ALTER COLUMN user_id TYPE UUID USING user_id::UUID;
ALTER TABLE ai.demand_letter_agent_memories ALTER COLUMN user_id TYPE UUID USING user_id::UUID;
ALTER TABLE ai.patent_agent_memories ALTER COLUMN user_id TYPE UUID USING user_id::UUID;
ALTER TABLE ai.regulatory_agent_memories ALTER COLUMN user_id TYPE UUID USING user_id::UUID;
ALTER TABLE ai.whistleblower_agent_memories ALTER COLUMN user_id TYPE UUID USING user_id::UUID;

-- Add foreign key constraints to link to auth.users
ALTER TABLE ai.user_memories ADD CONSTRAINT fk_user_memories_user_id 
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE ai.agent_sessions ADD CONSTRAINT fk_agent_sessions_user_id 
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE ai.session_summaries ADD CONSTRAINT fk_session_summaries_user_id 
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE ai.memory_statistics ADD CONSTRAINT fk_memory_statistics_user_id 
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE ai.chatbot_agent_memories ADD CONSTRAINT fk_chatbot_memories_user_id 
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE ai.contract_agent_memories ADD CONSTRAINT fk_contract_memories_user_id 
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE ai.legal_research_agent_memories ADD CONSTRAINT fk_legal_research_memories_user_id 
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE ai.case_prediction_agent_memories ADD CONSTRAINT fk_case_prediction_memories_user_id 
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE ai.compliance_agent_memories ADD CONSTRAINT fk_compliance_memories_user_id 
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE ai.document_drafting_agent_memories ADD CONSTRAINT fk_document_drafting_memories_user_id 
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE ai.demand_letter_agent_memories ADD CONSTRAINT fk_demand_letter_memories_user_id 
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE ai.patent_agent_memories ADD CONSTRAINT fk_patent_memories_user_id 
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE ai.regulatory_agent_memories ADD CONSTRAINT fk_regulatory_memories_user_id 
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE ai.whistleblower_agent_memories ADD CONSTRAINT fk_whistleblower_memories_user_id 
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;

-- Recreate unique constraints
ALTER TABLE ai.user_memories ADD CONSTRAINT idx_user_memories_user_agent 
    UNIQUE(user_id, agent_name, memory_content);
ALTER TABLE ai.agent_sessions ADD CONSTRAINT idx_agent_sessions_session_id 
    UNIQUE(session_id);
ALTER TABLE ai.session_summaries ADD CONSTRAINT idx_session_summaries_user_session 
    UNIQUE(user_id, session_id);
ALTER TABLE ai.memory_statistics ADD CONSTRAINT idx_memory_statistics_user_agent_date 
    UNIQUE(user_id, agent_name, date);

-- Recreate indexes
CREATE INDEX idx_user_memories_user_id_idx ON ai.user_memories(user_id);
CREATE INDEX idx_agent_sessions_user_id_idx ON ai.agent_sessions(user_id);
CREATE INDEX idx_session_summaries_user_id_idx ON ai.session_summaries(user_id);
CREATE INDEX idx_memory_statistics_user_id_idx ON ai.memory_statistics(user_id);
CREATE INDEX idx_chatbot_memories_user_id_idx ON ai.chatbot_agent_memories(user_id);
CREATE INDEX idx_contract_memories_user_id_idx ON ai.contract_agent_memories(user_id);
CREATE INDEX idx_research_memories_user_id_idx ON ai.legal_research_agent_memories(user_id);
CREATE INDEX idx_case_prediction_memories_user_id_idx ON ai.case_prediction_agent_memories(user_id);
CREATE INDEX idx_compliance_memories_user_id_idx ON ai.compliance_agent_memories(user_id);
CREATE INDEX idx_document_drafting_memories_user_id_idx ON ai.document_drafting_agent_memories(user_id);
CREATE INDEX idx_demand_letter_memories_user_id_idx ON ai.demand_letter_agent_memories(user_id);
CREATE INDEX idx_patent_memories_user_id_idx ON ai.patent_agent_memories(user_id);
CREATE INDEX idx_regulatory_memories_user_id_idx ON ai.regulatory_agent_memories(user_id);
CREATE INDEX idx_whistleblower_memories_user_id_idx ON ai.whistleblower_agent_memories(user_id);

-- Enable Row Level Security (RLS) on AI tables
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
CREATE POLICY "Users can view own user_memories" ON ai.user_memories
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own user_memories" ON ai.user_memories
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own user_memories" ON ai.user_memories
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own user_memories" ON ai.user_memories
    FOR DELETE USING (auth.uid() = user_id);

-- Similar policies for agent_sessions
CREATE POLICY "Users can view own agent_sessions" ON ai.agent_sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own agent_sessions" ON ai.agent_sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own agent_sessions" ON ai.agent_sessions
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own agent_sessions" ON ai.agent_sessions
    FOR DELETE USING (auth.uid() = user_id);

-- Similar policies for session_summaries
CREATE POLICY "Users can view own session_summaries" ON ai.session_summaries
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own session_summaries" ON ai.session_summaries
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own session_summaries" ON ai.session_summaries
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own session_summaries" ON ai.session_summaries
    FOR DELETE USING (auth.uid() = user_id);

-- Similar policies for memory_statistics
CREATE POLICY "Users can view own memory_statistics" ON ai.memory_statistics
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own memory_statistics" ON ai.memory_statistics
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own memory_statistics" ON ai.memory_statistics
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own memory_statistics" ON ai.memory_statistics
    FOR DELETE USING (auth.uid() = user_id);

-- Policies for agent-specific memory tables (example for chatbot_agent_memories)
CREATE POLICY "Users can view own chatbot_memories" ON ai.chatbot_agent_memories
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own chatbot_memories" ON ai.chatbot_agent_memories
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own chatbot_memories" ON ai.chatbot_agent_memories
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own chatbot_memories" ON ai.chatbot_agent_memories
    FOR DELETE USING (auth.uid() = user_id);

-- Add similar policies for all other agent memory tables
-- (contract_agent_memories, legal_research_agent_memories, etc.)
-- This ensures users can only access their own data 