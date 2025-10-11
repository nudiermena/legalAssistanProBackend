-- Check and Create ai.legal_documents_rag Table Structure
-- Run this in Supabase SQL Editor to check table structure and create proper ingestion

-- Step 1: Check if ai schema exists
SELECT 'Checking ai schema...' as status;
SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'ai';

-- Step 2: Check tables in ai schema
SELECT 'Checking tables in ai schema...' as status;
SELECT table_name FROM information_schema.tables WHERE table_schema = 'ai';

-- Step 3: Check if legal_documents_rag table exists in ai schema
SELECT 'Checking legal_documents_rag table in ai schema...' as status;
SELECT 
    table_name,
    table_schema
FROM information_schema.tables 
WHERE table_schema = 'ai' AND table_name = 'legal_documents_rag';

-- Step 4: Get column information for ai.legal_documents_rag (if it exists)
SELECT 'Getting column information for ai.legal_documents_rag...' as status;
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default,
    character_maximum_length
FROM information_schema.columns 
WHERE table_schema = 'ai' AND table_name = 'legal_documents_rag'
ORDER BY ordinal_position;

-- Step 5: Check for RAG-specific columns
SELECT 'Checking for RAG-specific columns...' as status;
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_schema = 'ai' 
AND table_name = 'legal_documents_rag'
AND (column_name LIKE '%chunk%' OR column_name LIKE '%embed%' OR column_name LIKE '%vector%')
ORDER BY column_name;

-- Step 6: If table doesn't exist, create it with proper structure
-- (This will only run if the table doesn't exist)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'ai' AND table_name = 'legal_documents_rag'
    ) THEN
        -- Create the table with proper RAG structure
        CREATE TABLE ai.legal_documents_rag (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT,
            document_type TEXT,
            source_url TEXT,
            jurisdiction TEXT DEFAULT 'Colombia',
            language TEXT DEFAULT 'Spanish',
            publication_date TEXT,
            page_count INTEGER DEFAULT 0,
            word_count INTEGER DEFAULT 0,
            character_count INTEGER DEFAULT 0,
            tags TEXT[],
            source TEXT,
            scraped_at TIMESTAMP WITH TIME ZONE,
            status TEXT DEFAULT 'processed',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            content_chunks TEXT[],
            summary TEXT,
            key_terms TEXT[],
            legal_areas TEXT[],
            court_level TEXT,
            decision_type TEXT,
            relevance_score FLOAT DEFAULT 0.0,
            law_number TEXT,
            law_year TEXT,
            decree_number TEXT,
            decree_year TEXT,
            resolution_number TEXT,
            resolution_year TEXT,
            filename TEXT,
            chunk_embeddings FLOAT[],
            chunk_content TEXT[]
        );
        
        -- Grant permissions
        GRANT ALL ON TABLE ai.legal_documents_rag TO postgres;
        GRANT ALL ON TABLE ai.legal_documents_rag TO authenticated;
        GRANT ALL ON TABLE ai.legal_documents_rag TO anon;
        
        -- Enable RLS
        ALTER TABLE ai.legal_documents_rag ENABLE ROW LEVEL SECURITY;
        
        -- Create RLS policies
        CREATE POLICY "Enable read access for all users" ON ai.legal_documents_rag
            FOR SELECT USING (true);
            
        CREATE POLICY "Enable insert for authenticated users only" ON ai.legal_documents_rag
            FOR INSERT WITH CHECK (auth.role() = 'authenticated');
            
        CREATE POLICY "Enable update for authenticated users only" ON ai.legal_documents_rag
            FOR UPDATE USING (auth.role() = 'authenticated');
            
        CREATE POLICY "Enable delete for authenticated users only" ON ai.legal_documents_rag
            FOR DELETE USING (auth.role() = 'authenticated');
        
        RAISE NOTICE 'Table ai.legal_documents_rag created successfully with RAG structure';
    ELSE
        RAISE NOTICE 'Table ai.legal_documents_rag already exists';
    END IF;
END $$;

-- Step 7: Verify table creation and get final structure
SELECT 'Final table structure verification...' as status;
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_schema = 'ai' AND table_name = 'legal_documents_rag'
ORDER BY ordinal_position;

-- Step 8: Check for RAG-specific columns
SELECT 'RAG-specific columns found:' as status;
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_schema = 'ai' 
AND table_name = 'legal_documents_rag'
AND (column_name LIKE '%chunk%' OR column_name LIKE '%embed%' OR column_name LIKE '%vector%')
ORDER BY column_name;

-- Step 9: Test table access
SELECT 'Testing table access...' as status;
SELECT COUNT(*) as record_count FROM ai.legal_documents_rag;



