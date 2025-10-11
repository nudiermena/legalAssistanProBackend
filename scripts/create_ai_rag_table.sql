-- Create RAG-optimized table in ai schema for legal documents
-- Run this SQL in your Supabase SQL Editor

-- Create the main table
CREATE TABLE IF NOT EXISTS ai.legal_documents_rag (
    id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    document_type TEXT,
    source_url TEXT,
    jurisdiction TEXT DEFAULT 'Colombia',
    language TEXT DEFAULT 'Spanish',
    publication_date TEXT,
    page_count INTEGER,
    word_count INTEGER,
    character_count INTEGER,
    tags TEXT[],
    source TEXT,
    scraped_at TIMESTAMP WITH TIME ZONE,
    status TEXT DEFAULT 'processed',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- RAG-specific fields
    content_chunks TEXT[],
    chunk_embeddings VECTOR(1024), -- For Mistral embeddings
    summary TEXT,
    key_terms TEXT[],
    legal_areas TEXT[],
    court_level TEXT,
    decision_type TEXT,
    relevance_score FLOAT DEFAULT 0.0
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_legal_documents_rag_title ON ai.legal_documents_rag USING gin(to_tsvector('spanish', title));
CREATE INDEX IF NOT EXISTS idx_legal_documents_rag_content ON ai.legal_documents_rag USING gin(to_tsvector('spanish', content));
CREATE INDEX IF NOT EXISTS idx_legal_documents_rag_type ON ai.legal_documents_rag(document_type);
CREATE INDEX IF NOT EXISTS idx_legal_documents_rag_jurisdiction ON ai.legal_documents_rag(jurisdiction);
CREATE INDEX IF NOT EXISTS idx_legal_documents_rag_tags ON ai.legal_documents_rag USING gin(tags);
CREATE INDEX IF NOT EXISTS idx_legal_documents_rag_legal_areas ON ai.legal_documents_rag USING gin(legal_areas);
CREATE INDEX IF NOT EXISTS idx_legal_documents_rag_created_at ON ai.legal_documents_rag(created_at);

-- Enable Row Level Security
ALTER TABLE ai.legal_documents_rag ENABLE ROW LEVEL SECURITY;

-- Create policies for authenticated users
CREATE POLICY "Enable read access for authenticated users" ON ai.legal_documents_rag
FOR SELECT USING (true);

CREATE POLICY "Enable insert for authenticated users" ON ai.legal_documents_rag
FOR INSERT WITH CHECK (true);

CREATE POLICY "Enable update for authenticated users" ON ai.legal_documents_rag
FOR UPDATE USING (true);

-- Create a function to search documents
CREATE OR REPLACE FUNCTION search_legal_documents(
    search_query TEXT,
    document_types TEXT[] DEFAULT NULL,
    jurisdictions TEXT[] DEFAULT NULL,
    limit_count INTEGER DEFAULT 10
)
RETURNS TABLE (
    id BIGINT,
    title TEXT,
    content TEXT,
    document_type TEXT,
    source_url TEXT,
    relevance_score FLOAT,
    rank REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ld.id,
        ld.title,
        ld.content,
        ld.document_type,
        ld.source_url,
        ld.relevance_score,
        ts_rank(
            to_tsvector('spanish', ld.title || ' ' || ld.content),
            plainto_tsquery('spanish', search_query)
        ) as rank
    FROM ai.legal_documents_rag ld
    WHERE 
        to_tsvector('spanish', ld.title || ' ' || ld.content) @@ plainto_tsquery('spanish', search_query)
        AND (document_types IS NULL OR ld.document_type = ANY(document_types))
        AND (jurisdictions IS NULL OR ld.jurisdiction = ANY(jurisdictions))
    ORDER BY rank DESC, ld.relevance_score DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Create a function for vector similarity search (when embeddings are available)
CREATE OR REPLACE FUNCTION search_legal_documents_by_embedding(
    query_embedding VECTOR(1024),
    limit_count INTEGER DEFAULT 10
)
RETURNS TABLE (
    id BIGINT,
    title TEXT,
    content TEXT,
    document_type TEXT,
    source_url TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ld.id,
        ld.title,
        ld.content,
        ld.document_type,
        ld.source_url,
        1 - (ld.chunk_embeddings <=> query_embedding) as similarity
    FROM ai.legal_documents_rag ld
    WHERE ld.chunk_embeddings IS NOT NULL
    ORDER BY ld.chunk_embeddings <=> query_embedding
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Grant necessary permissions
GRANT ALL ON ai.legal_documents_rag TO authenticated;
GRANT USAGE ON SCHEMA ai TO authenticated;
GRANT EXECUTE ON FUNCTION search_legal_documents TO authenticated;
GRANT EXECUTE ON FUNCTION search_legal_documents_by_embedding TO authenticated;
