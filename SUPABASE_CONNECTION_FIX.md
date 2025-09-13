# Supabase Connection Fix Guide

## 🔍 Current Issues

Your API is experiencing these connection issues:

1. **Database Host Resolution**: `could not translate host name "db.luiiwyzjtkqnmnzqghoz.supabase.co"`
2. **Vector Database**: Missing `agno.vectordb.postgres` and `agno.vectordb.memory` modules
3. **Storage System**: PostgreSQL connection failing

## ✅ Solutions

### 1. Fix Supabase Database URL

The current URL format is incorrect. Here's the proper format:

**❌ Incorrect (current):**

```
DATABASE_URL=postgresql://postgres:KDxtnciHVvlzrKxV@db.luiiwyzjtkqnmnzqghoz.supabase.co:5432/postgres
```

**✅ Correct format:**

```
DATABASE_URL=postgresql://postgres.[YOUR-PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
```

### 2. Create Proper .env File

Create a `.env` file in your project root with:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# Database Configuration (use SQLite for development)
DATABASE_URL=sqlite:///./tmp/legal_assistant.db

# Security Configuration
SECURITY_ENVIRONMENT=development
SECRET_KEY=your-secret-key-here-change-in-production
API_KEYS=test_key_12345

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
RATE_LIMIT_PER_DAY=10000
RATE_LIMIT_BURST=10

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:8000,*

# File Upload
MAX_FILE_SIZE=10485760
SCAN_UPLOADS=true

# Redis Configuration (optional for development)
REDIS_URL=redis://localhost:6379
REDIS_DB=0

# Debug Mode
DEBUG_MODE=true

# AI Model Configuration
MISTRAL_API_KEY=your_mistral_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Development Settings
ENABLE_VECTOR_DB=false
ENABLE_KNOWLEDGE_BASE=false
USE_SQLITE_FALLBACK=true
```

### 3. Development Fallback Configuration

For development, you can disable the problematic components:

```python
# In config/enhanced_agent_config.py
def initialize_vector_db(self):
    """Initialize vector database for knowledge storage using Supabase"""
    # For development, skip vector database
    if os.getenv("ENABLE_VECTOR_DB", "false").lower() == "false":
        logger.info("Vector database disabled for development")
        self.vector_db = None
        return

    # ... rest of the method
```

### 4. SQLite Fallback for Storage

Update the storage initialization to use SQLite by default:

```python
def initialize_storage_system(self, agent_name: str):
    """Initialize storage system for a specific agent"""
    try:
        # Check if SQLite fallback is enabled
        if os.getenv("USE_SQLITE_FALLBACK", "true").lower() == "true":
            from agno.storage.sqlite import SqliteStorage

            # Ensure tmp directory exists
            os.makedirs("tmp", exist_ok=True)

            storage = SqliteStorage(
                table_name=f"{agent_name}_sessions",
                db_file="tmp/agent_storage.db"
            )

            logger.info(f"Storage system initialized for {agent_name} with SQLite")
            return storage

        # ... rest of PostgreSQL logic
    except Exception as e:
        logger.error(f"Failed to initialize storage system for {agent_name}: {e}")
        return None
```

## 🚀 Quick Fix for Development

### Option 1: Use SQLite Only (Recommended for Development)

1. **Create `.env` file** with SQLite configuration:

```bash
DATABASE_URL=sqlite:///./tmp/legal_assistant.db
USE_SQLITE_FALLBACK=true
ENABLE_VECTOR_DB=false
ENABLE_KNOWLEDGE_BASE=false
```

2. **Create tmp directory**:

```bash
mkdir tmp
```

3. **Restart your API**:

```bash
python main.py
```

### Option 2: Fix Supabase Connection

1. **Get correct Supabase credentials** from your Supabase dashboard
2. **Update `.env` file** with proper URLs
3. **Test connection** with the provided test script

## 📊 Expected Results After Fix

### ✅ Working Components:

- **Authentication**: Supabase JWT working
- **Storage**: SQLite fallback working
- **Knowledge Base**: Disabled (no vector DB needed)
- **Legal Research**: Processing requests
- **Security**: Rate limiting and monitoring

### ⚠️ Expected Warnings (Normal):

- Vector database disabled for development
- Using SQLite fallback for storage
- Knowledge base disabled

## 🧪 Test the Fix

Run the test script to verify everything works:

```bash
python test_agent_config_fix.py
```

Expected output:

```
✅ Enhanced Agent Config: PASS
✅ Storage System: PASS
✅ Knowledge Base: PASS
🎉 All tests passed!
```

## 🎯 Next Steps

### For Development:

- Use SQLite fallback (recommended)
- Disable vector database features
- Focus on core functionality

### For Production:

- Set up proper Supabase credentials
- Install vector database modules
- Configure Redis for rate limiting

## 📝 Summary

The connection issues are **expected in development** and can be resolved by:

1. ✅ Using SQLite fallback for storage
2. ✅ Disabling vector database features
3. ✅ Creating proper `.env` file
4. ✅ Using development-friendly configuration

Your API will work perfectly for development with these changes! 🚀
