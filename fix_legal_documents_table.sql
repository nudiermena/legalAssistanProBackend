-- Create a view that maps our existing legal_documents_ai schema to PgVector expectations
-- This way we don't modify the original table

-- Drop the view if it exists
DROP VIEW IF EXISTS ai.legal_documents_ai_pgvector;

-- Create a view that maps our columns to PgVector expected columns
CREATE VIEW ai.legal_documents_ai_pgvector AS
SELECT 
    id,
    title as name,  -- Map title to name
    jsonb_build_object(
        'document_type', document_type,
        'document_number', document_number,
        'year', year,
        'jurisdiction', jurisdiction,
        'summary', summary,
        'keywords', keywords,
        'tags', tags,
        'source_url', source_url,
        'official_gazette_reference', official_gazette_reference,
        'effective_date', effective_date,
        'amendment_date', amendment_date,
        'status', status
    ) as meta_data,  -- Create meta_data from existing columns
    content,
    vector_embedding as embedding,  -- Map vector_embedding to embedding
    jsonb_build_object(
        'created_at', created_at,
        'updated_at', updated_at
    ) as usage,  -- Create usage from timestamps
    created_at,
    updated_at
FROM ai.legal_documents_ai;

-- Grant permissions on the view
GRANT SELECT ON ai.legal_documents_ai_pgvector TO authenticated;
GRANT SELECT ON ai.legal_documents_ai_pgvector TO anon;

-- Verify the view structure
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_schema = 'ai' 
AND table_name = 'legal_documents_ai_pgvector' 
ORDER BY ordinal_position;
