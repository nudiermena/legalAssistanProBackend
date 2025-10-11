-- Create ai schema and legal_documents_rag table
-- Run this in Supabase SQL Editor

-- Step 1: Create ai schema
CREATE SCHEMA IF NOT EXISTS ai;

-- Step 2: Create the legal_documents_rag table
CREATE TABLE IF NOT EXISTS ai.legal_documents_rag (
    id TEXT PRIMARY KEY,
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
    summary TEXT,
    key_terms TEXT[],
    legal_areas TEXT[],
    court_level TEXT,
    decision_type TEXT,
    relevance_score FLOAT DEFAULT 0.0,

    -- Additional metadata
    law_number TEXT,
    law_year TEXT,
    decree_number TEXT,
    decree_year TEXT,
    resolution_number TEXT,
    resolution_year TEXT,
    filename TEXT
);

-- Step 3: Grant permissions
GRANT ALL ON SCHEMA ai TO postgres;
GRANT ALL ON ALL TABLES IN SCHEMA ai TO postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA ai TO postgres;

-- Step 4: Verify table creation
SELECT 'ai.legal_documents_rag table created successfully' as status;
SELECT COUNT(*) as table_exists FROM information_schema.tables 
WHERE table_schema = 'ai' AND table_name = 'legal_documents_rag';
