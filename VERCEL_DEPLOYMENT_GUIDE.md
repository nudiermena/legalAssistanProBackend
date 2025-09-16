# Vercel Deployment Optimization Guide

## Overview

This guide explains the optimizations made to reduce the serverless function size for Vercel deployment.

## Files Excluded from Deployment

### 1. `.vercelignore` File

Created a comprehensive `.vercelignore` file that excludes:

- **Development files**: `scripts/`, `docs/`, `legal_beto/`, `tmp/`
- **Testing files**: `test_*.py`, `*_test.py`, `debug_*.py`
- **Database files**: `*.db`, `*.sqlite3`, migration files
- **Large data files**: `*.csv`, `*.json`, processed documents
- **Specific agents**: `whistleblower_agent.py`, `patent_agent.py`
- **Knowledge base scripts**: `populate_knowledge_base*.py`
- **Docker files**: `Dockerfile`, `docker-compose.*`
- **Static files**: `static/`, `templates/`

### 2. Updated `vercel.json`

- Added `includeFiles` to explicitly include only necessary directories
- Set `maxLambdaSize` to 250mb
- Added function timeout configuration
- Uses deployment-specific requirements file

### 3. Deployment-Specific Requirements

Created `requirements-vercel.txt` with only essential dependencies:

- Core FastAPI dependencies
- AI/ML libraries (agno, mistralai, groq)
- Database drivers (SQLAlchemy, psycopg2, asyncpg)
- Security libraries
- Document processing (minimal)

### 4. Simplified Endpoints

Updated endpoints to remove dependencies on excluded agents:

- **`whistleblower_analysis.py`**: Simplified to return basic responses
- **`patent_search.py`**: Simplified to return basic responses

## Deployment Steps

1. **Commit all changes**:

   ```bash
   git add .
   git commit -m "Optimize for Vercel deployment"
   git push origin nmena-vercel-deploy
   ```

2. **Deploy to Vercel**:

   - The deployment will automatically use the optimized configuration
   - Vercel will use `requirements-vercel.txt` for dependencies
   - Only essential files will be included in the serverless function

3. **Monitor deployment**:
   - Check Vercel dashboard for build logs
   - Verify function size is under 250MB
   - Test API endpoints to ensure they work

## Expected Results

- **Reduced bundle size**: Excluding large files and unnecessary dependencies
- **Faster deployment**: Only essential files are processed
- **Lower memory usage**: Simplified endpoints with basic functionality
- **Maintained API compatibility**: All endpoints still respond with expected structure

## Notes

- The simplified endpoints return basic responses but maintain the same API structure
- Full functionality can be restored by re-adding the excluded agents when needed
- The deployment is optimized for the 250MB Vercel limit
- All core functionality (contract review, legal research, etc.) remains intact

## Troubleshooting

If deployment still fails:

1. Check Vercel build logs for specific errors
2. Verify all imports in `api/index.py` are available
3. Ensure environment variables are set in Vercel dashboard
4. Consider further reducing dependencies if needed
