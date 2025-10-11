-- =====================================================
-- ADD CHUNK COLUMNS TO VECTOR TABLES
-- Migration to add chunking metadata to existing tables
-- =====================================================

-- Add chunk-related columns to legal_documents_ai
ALTER TABLE legal_documents_ai ADD COLUMN IF NOT EXISTS chunk_index INTEGER;
ALTER TABLE legal_documents_ai ADD COLUMN IF NOT EXISTS chunk_content TEXT;
ALTER TABLE legal_documents_ai ADD COLUMN IF NOT EXISTS chunk_size INTEGER;
ALTER TABLE legal_documents_ai ADD COLUMN IF NOT EXISTS chunk_overlap INTEGER;
ALTER TABLE legal_documents_ai ADD COLUMN IF NOT EXISTS parent_document_id UUID;
ALTER TABLE legal_documents_ai ADD COLUMN IF NOT EXISTS total_chunks INTEGER;
ALTER TABLE legal_documents_ai ADD COLUMN IF NOT EXISTS chunk_metadata JSONB;

-- Add chunk-related columns to jurisprudence
ALTER TABLE jurisprudence ADD COLUMN IF NOT EXISTS chunk_index INTEGER;
ALTER TABLE jurisprudence ADD COLUMN IF NOT EXISTS chunk_content TEXT;
ALTER TABLE jurisprudence ADD COLUMN IF NOT EXISTS chunk_size INTEGER;
ALTER TABLE jurisprudence ADD COLUMN IF NOT EXISTS chunk_overlap INTEGER;
ALTER TABLE jurisprudence ADD COLUMN IF NOT EXISTS parent_document_id UUID;
ALTER TABLE jurisprudence ADD COLUMN IF NOT EXISTS total_chunks INTEGER;
ALTER TABLE jurisprudence ADD COLUMN IF NOT EXISTS chunk_metadata JSONB;

-- Add chunk-related columns to legal_terms
ALTER TABLE legal_terms ADD COLUMN IF NOT EXISTS chunk_index INTEGER;
ALTER TABLE legal_terms ADD COLUMN IF NOT EXISTS chunk_content TEXT;
ALTER TABLE legal_terms ADD COLUMN IF NOT EXISTS chunk_size INTEGER;
ALTER TABLE legal_terms ADD COLUMN IF NOT EXISTS chunk_overlap INTEGER;
ALTER TABLE legal_terms ADD COLUMN IF NOT EXISTS parent_document_id UUID;
ALTER TABLE legal_terms ADD COLUMN IF NOT EXISTS total_chunks INTEGER;
ALTER TABLE legal_terms ADD COLUMN IF NOT EXISTS chunk_metadata JSONB;

-- Add chunk-related columns to regulatory_frameworks
ALTER TABLE regulatory_frameworks ADD COLUMN IF NOT EXISTS chunk_index INTEGER;
ALTER TABLE regulatory_frameworks ADD COLUMN IF NOT EXISTS chunk_content TEXT;
ALTER TABLE regulatory_frameworks ADD COLUMN IF NOT EXISTS chunk_size INTEGER;
ALTER TABLE regulatory_frameworks ADD COLUMN IF NOT EXISTS chunk_overlap INTEGER;
ALTER TABLE regulatory_frameworks ADD COLUMN IF NOT EXISTS parent_document_id UUID;
ALTER TABLE regulatory_frameworks ADD COLUMN IF NOT EXISTS total_chunks INTEGER;
ALTER TABLE regulatory_frameworks ADD COLUMN IF NOT EXISTS chunk_metadata JSONB;

-- Add chunk-related columns to contract_knowledge
ALTER TABLE contract_knowledge ADD COLUMN IF NOT EXISTS chunk_index INTEGER;
ALTER TABLE contract_knowledge ADD COLUMN IF NOT EXISTS chunk_content TEXT;
ALTER TABLE contract_knowledge ADD COLUMN IF NOT EXISTS chunk_size INTEGER;
ALTER TABLE contract_knowledge ADD COLUMN IF NOT EXISTS chunk_overlap INTEGER;
ALTER TABLE contract_knowledge ADD COLUMN IF NOT EXISTS parent_document_id UUID;
ALTER TABLE contract_knowledge ADD COLUMN IF NOT EXISTS total_chunks INTEGER;
ALTER TABLE contract_knowledge ADD COLUMN IF NOT EXISTS chunk_metadata JSONB;

-- Add chunk-related columns to patent_knowledge
ALTER TABLE patent_knowledge ADD COLUMN IF NOT EXISTS chunk_index INTEGER;
ALTER TABLE patent_knowledge ADD COLUMN IF NOT EXISTS chunk_content TEXT;
ALTER TABLE patent_knowledge ADD COLUMN IF NOT EXISTS chunk_size INTEGER;
ALTER TABLE patent_knowledge ADD COLUMN IF NOT EXISTS chunk_overlap INTEGER;
ALTER TABLE patent_knowledge ADD COLUMN IF NOT EXISTS parent_document_id UUID;
ALTER TABLE patent_knowledge ADD COLUMN IF NOT EXISTS total_chunks INTEGER;
ALTER TABLE patent_knowledge ADD COLUMN IF NOT EXISTS chunk_metadata JSONB;

-- Add chunk-related columns to case_prediction_knowledge
ALTER TABLE case_prediction_knowledge ADD COLUMN IF NOT EXISTS chunk_index INTEGER;
ALTER TABLE case_prediction_knowledge ADD COLUMN IF NOT EXISTS chunk_content TEXT;
ALTER TABLE case_prediction_knowledge ADD COLUMN IF NOT EXISTS chunk_size INTEGER;
ALTER TABLE case_prediction_knowledge ADD COLUMN IF NOT EXISTS chunk_overlap INTEGER;
ALTER TABLE case_prediction_knowledge ADD COLUMN IF NOT EXISTS parent_document_id UUID;
ALTER TABLE case_prediction_knowledge ADD COLUMN IF NOT EXISTS total_chunks INTEGER;
ALTER TABLE case_prediction_knowledge ADD COLUMN IF NOT EXISTS chunk_metadata JSONB;

-- Add chunk-related columns to compliance_knowledge
ALTER TABLE compliance_knowledge ADD COLUMN IF NOT EXISTS chunk_index INTEGER;
ALTER TABLE compliance_knowledge ADD COLUMN IF NOT EXISTS chunk_content TEXT;
ALTER TABLE compliance_knowledge ADD COLUMN IF NOT EXISTS chunk_size INTEGER;
ALTER TABLE compliance_knowledge ADD COLUMN IF NOT EXISTS chunk_overlap INTEGER;
ALTER TABLE compliance_knowledge ADD COLUMN IF NOT EXISTS parent_document_id UUID;
ALTER TABLE compliance_knowledge ADD COLUMN IF NOT EXISTS total_chunks INTEGER;
ALTER TABLE compliance_knowledge ADD COLUMN IF NOT EXISTS chunk_metadata JSONB;

-- Add chunk-related columns to document_templates
ALTER TABLE document_templates ADD COLUMN IF NOT EXISTS chunk_index INTEGER;
ALTER TABLE document_templates ADD COLUMN IF NOT EXISTS chunk_content TEXT;
ALTER TABLE document_templates ADD COLUMN IF NOT EXISTS chunk_size INTEGER;
ALTER TABLE document_templates ADD COLUMN IF NOT EXISTS chunk_overlap INTEGER;
ALTER TABLE document_templates ADD COLUMN IF NOT EXISTS parent_document_id UUID;
ALTER TABLE document_templates ADD COLUMN IF NOT EXISTS total_chunks INTEGER;
ALTER TABLE document_templates ADD COLUMN IF NOT EXISTS chunk_metadata JSONB;

-- =====================================================
-- CREATE INDEXES FOR CHUNK-RELATED QUERIES
-- =====================================================

-- Indexes for chunk queries
CREATE INDEX IF NOT EXISTS idx_legal_documents_chunk_index ON legal_documents_ai(chunk_index);
CREATE INDEX IF NOT EXISTS idx_legal_documents_parent_id ON legal_documents_ai(parent_document_id);
CREATE INDEX IF NOT EXISTS idx_legal_documents_chunk_metadata ON legal_documents_ai USING GIN (chunk_metadata);

CREATE INDEX IF NOT EXISTS idx_jurisprudence_chunk_index ON jurisprudence(chunk_index);
CREATE INDEX IF NOT EXISTS idx_jurisprudence_parent_id ON jurisprudence(parent_document_id);
CREATE INDEX IF NOT EXISTS idx_jurisprudence_chunk_metadata ON jurisprudence USING GIN (chunk_metadata);

CREATE INDEX IF NOT EXISTS idx_legal_terms_chunk_index ON legal_terms(chunk_index);
CREATE INDEX IF NOT EXISTS idx_legal_terms_parent_id ON legal_terms(parent_document_id);
CREATE INDEX IF NOT EXISTS idx_legal_terms_chunk_metadata ON legal_terms USING GIN (chunk_metadata);

CREATE INDEX IF NOT EXISTS idx_regulatory_frameworks_chunk_index ON regulatory_frameworks(chunk_index);
CREATE INDEX IF NOT EXISTS idx_regulatory_frameworks_parent_id ON regulatory_frameworks(parent_document_id);
CREATE INDEX IF NOT EXISTS idx_regulatory_frameworks_chunk_metadata ON regulatory_frameworks USING GIN (chunk_metadata);

CREATE INDEX IF NOT EXISTS idx_contract_knowledge_chunk_index ON contract_knowledge(chunk_index);
CREATE INDEX IF NOT EXISTS idx_contract_knowledge_parent_id ON contract_knowledge(parent_document_id);
CREATE INDEX IF NOT EXISTS idx_contract_knowledge_chunk_metadata ON contract_knowledge USING GIN (chunk_metadata);

CREATE INDEX IF NOT EXISTS idx_patent_knowledge_chunk_index ON patent_knowledge(chunk_index);
CREATE INDEX IF NOT EXISTS idx_patent_knowledge_parent_id ON patent_knowledge(parent_document_id);
CREATE INDEX IF NOT EXISTS idx_patent_knowledge_chunk_metadata ON patent_knowledge USING GIN (chunk_metadata);

CREATE INDEX IF NOT EXISTS idx_case_prediction_chunk_index ON case_prediction_knowledge(chunk_index);
CREATE INDEX IF NOT EXISTS idx_case_prediction_parent_id ON case_prediction_knowledge(parent_document_id);
CREATE INDEX IF NOT EXISTS idx_case_prediction_chunk_metadata ON case_prediction_knowledge USING GIN (chunk_metadata);

CREATE INDEX IF NOT EXISTS idx_compliance_chunk_index ON compliance_knowledge(chunk_index);
CREATE INDEX IF NOT EXISTS idx_compliance_parent_id ON compliance_knowledge(parent_document_id);
CREATE INDEX IF NOT EXISTS idx_compliance_chunk_metadata ON compliance_knowledge USING GIN (chunk_metadata);

CREATE INDEX IF NOT EXISTS idx_document_templates_chunk_index ON document_templates(chunk_index);
CREATE INDEX IF NOT EXISTS idx_document_templates_parent_id ON document_templates(parent_document_id);
CREATE INDEX IF NOT EXISTS idx_document_templates_chunk_metadata ON document_templates USING GIN (chunk_metadata);

-- =====================================================
-- COMMENTS FOR NEW COLUMNS
-- =====================================================

COMMENT ON COLUMN legal_documents_ai.chunk_index IS 'Index of this chunk within the parent document (0-based)';
COMMENT ON COLUMN legal_documents_ai.chunk_content IS 'The actual chunk content for vector search';
COMMENT ON COLUMN legal_documents_ai.chunk_size IS 'Size of this chunk in characters';
COMMENT ON COLUMN legal_documents_ai.chunk_overlap IS 'Number of characters overlapping with previous chunk';
COMMENT ON COLUMN legal_documents_ai.parent_document_id IS 'ID of the original document this chunk belongs to';
COMMENT ON COLUMN legal_documents_ai.total_chunks IS 'Total number of chunks in the parent document';
COMMENT ON COLUMN legal_documents_ai.chunk_metadata IS 'Additional metadata about the chunk (e.g., section, paragraph, etc.)';

-- Apply same comments to other tables
COMMENT ON COLUMN jurisprudence.chunk_index IS 'Index of this chunk within the parent document (0-based)';
COMMENT ON COLUMN jurisprudence.chunk_content IS 'The actual chunk content for vector search';
COMMENT ON COLUMN jurisprudence.chunk_size IS 'Size of this chunk in characters';
COMMENT ON COLUMN jurisprudence.chunk_overlap IS 'Number of characters overlapping with previous chunk';
COMMENT ON COLUMN jurisprudence.parent_document_id IS 'ID of the original document this chunk belongs to';
COMMENT ON COLUMN jurisprudence.total_chunks IS 'Total number of chunks in the parent document';
COMMENT ON COLUMN jurisprudence.chunk_metadata IS 'Additional metadata about the chunk (e.g., section, paragraph, etc.)';
