-- Check the actual column structure of ai.legal_documents_rag table
-- Run this in Supabase SQL Editor to see all columns

-- Get detailed column information
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default,
    character_maximum_length
FROM information_schema.columns 
WHERE table_schema = 'ai' AND table_name = 'legal_documents_rag'
ORDER BY ordinal_position;

-- Check specifically for RAG-related columns
SELECT 
    column_name, 
    data_type,
    'RAG Column' as column_type
FROM information_schema.columns 
WHERE table_schema = 'ai' 
AND table_name = 'legal_documents_rag'
AND (column_name LIKE '%chunk%' OR column_name LIKE '%embed%' OR column_name LIKE '%vector%')
ORDER BY column_name;

-- Get a sample record to see the actual data structure
SELECT * FROM ai.legal_documents_rag LIMIT 1;



