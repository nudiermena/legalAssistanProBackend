-- =====================================================
-- LEGAL AI ASSISTANT KNOWLEDGE BASE SCHEMA
-- Supabase PostgreSQL Schema for Colombian Legal AI
-- =====================================================

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "vector";

-- =====================================================
-- CORE KNOWLEDGE TABLES
-- =====================================================

-- Legal Documents and Legislation
CREATE TABLE legal_documents_ai (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    document_type VARCHAR(100) NOT NULL, -- 'law', 'decree', 'resolution', 'circular', 'constitution'
    document_number VARCHAR(50),
    year INTEGER,
    jurisdiction VARCHAR(100) DEFAULT 'Colombia',
    content TEXT NOT NULL,
    summary TEXT,
    keywords TEXT[],
    tags TEXT[],
    source_url TEXT,
    official_gazette_reference VARCHAR(200),
    effective_date DATE,
    amendment_date DATE,
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'amended', 'repealed', 'pending'
    vector_embedding VECTOR(1024), -- Mistral embedding dimension
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Jurisprudence and Court Decisions
CREATE TABLE jurisprudence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_number VARCHAR(100),
    court VARCHAR(200) NOT NULL, -- 'Corte Constitucional', 'Corte Suprema', 'Consejo de Estado'
    decision_type VARCHAR(100), -- 'sentencia', 'auto', 'concepto'
    decision_date DATE,
    topic VARCHAR(500),
    summary TEXT,
    full_text TEXT,
    key_holdings TEXT[],
    legal_principles TEXT[],
    cited_laws TEXT[],
    cited_precedents TEXT[],
    relevance_score DECIMAL(3,2),
    tags TEXT[],
    source_url TEXT,
    vector_embedding VECTOR(1024), -- Mistral embedding dimension
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Legal Terms and Definitions
CREATE TABLE legal_terms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    term VARCHAR(200) NOT NULL UNIQUE,
    definition TEXT NOT NULL,
    legal_area VARCHAR(100), -- 'civil', 'commercial', 'constitutional', 'administrative', 'labor'
    source_document VARCHAR(200),
    related_terms TEXT[],
    examples TEXT[],
    vector_embedding VECTOR(1024), -- Mistral embedding dimension
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Regulatory Frameworks
CREATE TABLE regulatory_frameworks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    framework_name VARCHAR(200) NOT NULL,
    sector VARCHAR(100), -- 'financial', 'healthcare', 'education', 'technology', 'environmental'
    description TEXT,
    applicable_laws TEXT[],
    compliance_requirements TEXT[],
    authority VARCHAR(200),
    effective_date DATE,
    status VARCHAR(50) DEFAULT 'active',
    vector_embedding VECTOR(1024), -- Mistral embedding dimension
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- AGENT-SPECIFIC KNOWLEDGE TABLES
-- =====================================================

-- Contract Analysis Knowledge
CREATE TABLE contract_knowledge (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clause_type VARCHAR(100), -- 'confidentiality', 'payment', 'termination', 'liability'
    standard_clause TEXT,
    legal_requirements TEXT[],
    risk_factors TEXT[],
    recommended_language TEXT,
    applicable_laws TEXT[],
    jurisprudence_references TEXT[],
    industry_specific_considerations JSONB,
    vector_embedding VECTOR(1024), -- Mistral embedding dimension
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Patent and IP Knowledge
CREATE TABLE patent_knowledge (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patent_type VARCHAR(100), -- 'invention', 'utility_model', 'design', 'trademark'
    requirements TEXT[],
    protection_period INTEGER,
    application_requirements TEXT[],
    examination_criteria TEXT[],
    international_treaties TEXT[],
    sic_requirements TEXT[],
    technical_classifications TEXT[],
    vector_embedding VECTOR(1024), -- Mistral embedding dimension
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Case Prediction Knowledge
CREATE TABLE case_prediction_knowledge (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_type VARCHAR(100), -- 'civil', 'commercial', 'labor', 'administrative', 'constitutional'
    success_factors TEXT[],
    risk_factors TEXT[],
    average_duration_months INTEGER,
    success_rate DECIMAL(5,4),
    key_precedents TEXT[],
    procedural_requirements TEXT[],
    evidence_requirements TEXT[],
    vector_embedding VECTOR(1024), -- Mistral embedding dimension
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Compliance Knowledge
CREATE TABLE compliance_knowledge (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    compliance_area VARCHAR(100), -- 'data_protection', 'labor', 'environmental', 'financial'
    applicable_laws TEXT[],
    requirements TEXT[],
    penalties TEXT[],
    compliance_procedures TEXT[],
    documentation_requirements TEXT[],
    audit_requirements TEXT[],
    vector_embedding VECTOR(1024), -- Mistral embedding dimension
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Document Templates
CREATE TABLE document_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_name VARCHAR(200) NOT NULL,
    document_type VARCHAR(100), -- 'contract', 'demand_letter', 'legal_opinion', 'policy'
    template_content TEXT NOT NULL,
    required_sections TEXT[],
    optional_sections TEXT[],
    legal_requirements TEXT[],
    jurisdiction VARCHAR(100) DEFAULT 'Colombia',
    industry_specific BOOLEAN DEFAULT FALSE,
    industry VARCHAR(100),
    complexity_level VARCHAR(50), -- 'simple', 'standard', 'complex'
    vector_embedding VECTOR(1024), -- Mistral embedding dimension
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- KNOWLEDGE RELATIONSHIPS AND METADATA
-- =====================================================

-- Knowledge Categories
CREATE TABLE knowledge_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    parent_category_id UUID REFERENCES knowledge_categories(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Knowledge Sources
CREATE TABLE knowledge_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_name VARCHAR(200) NOT NULL,
    source_type VARCHAR(100), -- 'official_gazette', 'court_website', 'academic_journal', 'legal_database'
    url TEXT,
    reliability_score DECIMAL(3,2),
    last_updated DATE,
    update_frequency VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Knowledge Relationships
CREATE TABLE knowledge_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_table VARCHAR(100) NOT NULL,
    source_id UUID NOT NULL,
    target_table VARCHAR(100) NOT NULL,
    target_id UUID NOT NULL,
    relationship_type VARCHAR(100), -- 'cites', 'amends', 'supersedes', 'relates_to'
    relationship_strength DECIMAL(3,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- AGENT INTERACTION AND LEARNING
-- =====================================================

-- Agent Knowledge Usage
CREATE TABLE agent_knowledge_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_name VARCHAR(100) NOT NULL,
    knowledge_table VARCHAR(100) NOT NULL,
    knowledge_id UUID NOT NULL,
    usage_count INTEGER DEFAULT 1,
    last_used TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    success_rate DECIMAL(5,4),
    user_feedback_score INTEGER, -- 1-5 scale
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Knowledge Search Logs
CREATE TABLE knowledge_search_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_name VARCHAR(100) NOT NULL,
    user_id UUID,
    search_query TEXT NOT NULL,
    search_results JSONB,
    response_quality_score INTEGER, -- 1-5 scale
    search_duration_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Vector similarity search indexes
CREATE INDEX idx_legal_documents_vector ON legal_documents USING ivfflat (vector_embedding vector_cosine_ops);
CREATE INDEX idx_jurisprudence_vector ON jurisprudence USING ivfflat (vector_embedding vector_cosine_ops);
CREATE INDEX idx_legal_terms_vector ON legal_terms USING ivfflat (vector_embedding vector_cosine_ops);
CREATE INDEX idx_regulatory_frameworks_vector ON regulatory_frameworks USING ivfflat (vector_embedding vector_cosine_ops);
CREATE INDEX idx_contract_knowledge_vector ON contract_knowledge USING ivfflat (vector_embedding vector_cosine_ops);
CREATE INDEX idx_patent_knowledge_vector ON patent_knowledge USING ivfflat (vector_embedding vector_cosine_ops);
CREATE INDEX idx_case_prediction_knowledge_vector ON case_prediction_knowledge USING ivfflat (vector_embedding vector_cosine_ops);
CREATE INDEX idx_compliance_knowledge_vector ON compliance_knowledge USING ivfflat (vector_embedding vector_cosine_ops);
CREATE INDEX idx_document_templates_vector ON document_templates USING ivfflat (vector_embedding vector_cosine_ops);

-- Text search indexes
CREATE INDEX idx_legal_documents_title_gin ON legal_documents USING gin (title gin_trgm_ops);
CREATE INDEX idx_legal_documents_content_gin ON legal_documents USING gin (content gin_trgm_ops);
CREATE INDEX idx_jurisprudence_topic_gin ON jurisprudence USING gin (topic gin_trgm_ops);
CREATE INDEX idx_jurisprudence_summary_gin ON jurisprudence USING gin (summary gin_trgm_ops);
CREATE INDEX idx_legal_terms_term_gin ON legal_terms USING gin (term gin_trgm_ops);

-- Regular indexes
CREATE INDEX idx_legal_documents_type_status ON legal_documents(document_type, status);
CREATE INDEX idx_jurisprudence_court_date ON jurisprudence(court, decision_date);
CREATE INDEX idx_legal_terms_area ON legal_terms(legal_area);
CREATE INDEX idx_regulatory_frameworks_sector ON regulatory_frameworks(sector);
CREATE INDEX idx_contract_knowledge_clause_type ON contract_knowledge(clause_type);
CREATE INDEX idx_patent_knowledge_type ON patent_knowledge(patent_type);
CREATE INDEX idx_case_prediction_knowledge_type ON case_prediction_knowledge(case_type);
CREATE INDEX idx_compliance_knowledge_area ON compliance_knowledge(compliance_area);
CREATE INDEX idx_document_templates_type ON document_templates(document_type);

-- =====================================================
-- FUNCTIONS AND TRIGGERS
-- =====================================================

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers
CREATE TRIGGER update_legal_documents_updated_at BEFORE UPDATE ON legal_documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_jurisprudence_updated_at BEFORE UPDATE ON jurisprudence FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_legal_terms_updated_at BEFORE UPDATE ON legal_terms FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_regulatory_frameworks_updated_at BEFORE UPDATE ON regulatory_frameworks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_contract_knowledge_updated_at BEFORE UPDATE ON contract_knowledge FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_patent_knowledge_updated_at BEFORE UPDATE ON patent_knowledge FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_case_prediction_knowledge_updated_at BEFORE UPDATE ON case_prediction_knowledge FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_compliance_knowledge_updated_at BEFORE UPDATE ON compliance_knowledge FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_document_templates_updated_at BEFORE UPDATE ON document_templates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_agent_knowledge_usage_updated_at BEFORE UPDATE ON agent_knowledge_usage FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- SAMPLE DATA INSERTION
-- =====================================================

-- Insert sample knowledge categories
INSERT INTO knowledge_categories (category_name, description) VALUES
('Constitutional Law', 'Constitutional principles and fundamental rights'),
('Civil Law', 'Civil code and civil procedures'),
('Commercial Law', 'Commercial code and business regulations'),
('Labor Law', 'Labor regulations and employment law'),
('Administrative Law', 'Administrative procedures and government regulations'),
('Intellectual Property', 'Patents, trademarks, and copyright law'),
('Data Protection', 'Privacy and data protection regulations'),
('Compliance', 'Regulatory compliance and risk management');

-- Insert sample legal terms
INSERT INTO legal_terms (term, definition, legal_area, source_document) VALUES
('Habeas Data', 'Derecho fundamental a conocer, actualizar y rectificar las informaciones que se hayan recogido sobre ellas en bancos de datos', 'constitutional', 'Constitución Política Artículo 15'),
('Due Process', 'Garantía constitucional que asegura el derecho a un proceso justo y equitativo', 'constitutional', 'Constitución Política Artículo 29'),
('Good Faith', 'Principio general del derecho que obliga a actuar con honestidad y lealtad', 'civil', 'Código Civil Artículo 83'),
('Force Majeure', 'Evento extraordinario e imprevisible que exime de responsabilidad', 'commercial', 'Código de Comercio Artículo 64');

-- =====================================================
-- ROW LEVEL SECURITY (RLS)
-- =====================================================

-- Enable RLS on all tables
ALTER TABLE legal_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE jurisprudence ENABLE ROW LEVEL SECURITY;
ALTER TABLE legal_terms ENABLE ROW LEVEL SECURITY;
ALTER TABLE regulatory_frameworks ENABLE ROW LEVEL SECURITY;
ALTER TABLE contract_knowledge ENABLE ROW LEVEL SECURITY;
ALTER TABLE patent_knowledge ENABLE ROW LEVEL SECURITY;
ALTER TABLE case_prediction_knowledge ENABLE ROW LEVEL SECURITY;
ALTER TABLE compliance_knowledge ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_knowledge_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_search_logs ENABLE ROW LEVEL SECURITY;

-- Create policies for public read access (knowledge base is public)
CREATE POLICY "Public read access" ON legal_documents FOR SELECT USING (true);
CREATE POLICY "Public read access" ON jurisprudence FOR SELECT USING (true);
CREATE POLICY "Public read access" ON legal_terms FOR SELECT USING (true);
CREATE POLICY "Public read access" ON regulatory_frameworks FOR SELECT USING (true);
CREATE POLICY "Public read access" ON contract_knowledge FOR SELECT USING (true);
CREATE POLICY "Public read access" ON patent_knowledge FOR SELECT USING (true);
CREATE POLICY "Public read access" ON case_prediction_knowledge FOR SELECT USING (true);
CREATE POLICY "Public read access" ON compliance_knowledge FOR SELECT USING (true);
CREATE POLICY "Public read access" ON document_templates FOR SELECT USING (true);

-- Create policies for authenticated users to insert usage data
CREATE POLICY "Authenticated users can insert usage" ON agent_knowledge_usage FOR INSERT WITH CHECK (auth.role() = 'authenticated');
CREATE POLICY "Authenticated users can insert logs" ON knowledge_search_logs FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- =====================================================
-- COMMENTS
-- =====================================================

COMMENT ON TABLE legal_documents IS 'Core legal documents including laws, decrees, and regulations';
COMMENT ON TABLE jurisprudence IS 'Court decisions and legal precedents from Colombian courts';
COMMENT ON TABLE legal_terms IS 'Legal terminology and definitions for AI agents';
COMMENT ON TABLE regulatory_frameworks IS 'Sector-specific regulatory frameworks and compliance requirements';
COMMENT ON TABLE contract_knowledge IS 'Specialized knowledge for contract analysis and drafting';
COMMENT ON TABLE patent_knowledge IS 'Intellectual property and patent-related knowledge';
COMMENT ON TABLE case_prediction_knowledge IS 'Knowledge for predicting legal case outcomes';
COMMENT ON TABLE compliance_knowledge IS 'Compliance and regulatory knowledge';
COMMENT ON TABLE document_templates IS 'Legal document templates and forms';
COMMENT ON TABLE agent_knowledge_usage IS 'Tracks how agents use knowledge for learning and optimization';
COMMENT ON TABLE knowledge_search_logs IS 'Logs of knowledge searches for analytics and improvement'; 