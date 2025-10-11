# Complete AI Schema Setup and Data Ingestion

## Overview
This guide will help you create the ai schema, legal_documents_rag table, and ingest all legal documents.

## Files Generated
- `create_ai_table_final.sql` - Creates the ai schema and table
- `ingest_ai_documents.sql` - Inserts all legal documents
- `legal_documents_rag_upload.csv` - CSV file for manual upload (alternative)

## Step-by-Step Process

### Step 1: Create the AI Schema and Table
1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project: `luiiwyzjtkqnmnzqghoz`
3. Navigate to **SQL Editor**
4. Open `create_ai_table_final.sql`
5. Copy and paste the entire contents
6. Click **Run** to execute
7. Verify you see "ai.legal_documents_rag table created successfully"

### Step 2: Ingest the Legal Documents
1. In the same SQL Editor
2. Open `ingest_ai_documents.sql`
3. Copy and paste the entire contents
4. Click **Run** to execute
5. Verify you see the document counts and sample data

### Step 3: Verify the Setup
Run these queries to verify everything worked:

```sql
-- Check total documents
SELECT COUNT(*) as total_documents FROM ai.legal_documents_rag;

-- Check document types
SELECT document_type, COUNT(*) as count 
FROM ai.legal_documents_rag 
GROUP BY document_type;

-- Sample documents
SELECT title, document_type, word_count, filename
FROM ai.legal_documents_rag 
LIMIT 5;
```

## Expected Results
- **Total documents:** 26
- **Document types:** Ley (Laws)
- **Legal areas:** Various Colombian legal areas
- **Years covered:** 1992-2025

## Alternative: CSV Upload
If SQL execution fails, you can use the CSV file:
1. Go to **Table Editor**
2. Select `ai.legal_documents_rag` table
3. Click **Import**
4. Upload `legal_documents_rag_upload.csv`

## Troubleshooting

### If table creation fails:
- Check that you have admin permissions
- Verify you're in the correct Supabase project
- Try running the SQL in smaller parts

### If ingestion fails:
- Check for syntax errors in the SQL
- Try running INSERT statements in smaller batches
- Verify all required columns exist

### If CSV upload fails:
- Check that the table exists first
- Verify column names match exactly
- Check for special characters in the data

## Next Steps
Once completed successfully:
1. Your Legal AI Assistant will have access to 26 legal documents
2. RAG functionality will be available
3. Legal research and analysis will work
4. Document search and retrieval will be operational

🎉 **Ready to power your Legal AI Assistant!**
