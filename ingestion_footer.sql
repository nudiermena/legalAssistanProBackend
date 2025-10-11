-- Legal Documents RAG Data Ingestion - Footer
-- Verification queries

-- Verify ingestion
SELECT 'Ingestion completed successfully' as status;
SELECT COUNT(*) as total_documents FROM ai.legal_documents_rag;
SELECT document_type, COUNT(*) as count FROM ai.legal_documents_rag GROUP BY document_type;

-- Check for RAG columns
SELECT 
    'RAG columns check' as status,
    COUNT(*) as total_records,
    COUNT(CASE WHEN chunk_embeddings IS NOT NULL THEN 1 END) as records_with_embeddings,
    COUNT(CASE WHEN content_chunks IS NOT NULL THEN 1 END) as records_with_content_chunks
FROM ai.legal_documents_rag;

-- Sample data
SELECT 
    id,
    title, 
    document_type, 
    CASE WHEN chunk_embeddings IS NOT NULL THEN 'Has embeddings' ELSE 'No embeddings' END as embedding_status,
    CASE WHEN content_chunks IS NOT NULL THEN array_length(content_chunks, 1) ELSE 0 END as chunk_count
FROM ai.legal_documents_rag 
LIMIT 5;
