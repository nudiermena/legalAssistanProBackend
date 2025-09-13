# 🚀 SETUP AND DEPLOYMENT GUIDE FOR COLOMBIAN LEGAL AI KNOWLEDGE BASE

## 📋 **PREREQUISITES**

### **Required Accounts and Services**

- [Supabase Account](https://supabase.com/) (Free tier available)
- [OpenAI API Key](https://platform.openai.com/) (for embeddings)
- Python 3.8+ installed
- Git for version control

### **Required Python Packages**

```bash
pip install supabase openai agno python-dotenv asyncio
```

## 🗄️ **STEP 1: SUPABASE PROJECT SETUP**

### **1.1 Create Supabase Project**

1. Go to [Supabase Dashboard](https://app.supabase.com/)
2. Click "New Project"
3. Choose organization and enter project details
4. Set database password (save it securely)
5. Choose region (recommend: closest to Colombia)
6. Wait for project creation (2-3 minutes)

### **1.2 Get Project Credentials**

1. Go to Project Settings → API
2. Copy the following:
   - Project URL
   - Service Role Key (anon key for public access)
   - Project API Key

### **1.3 Enable Required Extensions**

1. Go to SQL Editor in Supabase Dashboard
2. Run the following commands:

```sql
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "vector";
```

## 🏗️ **STEP 2: DATABASE SCHEMA SETUP**

### **2.1 Create Database Schema**

1. In Supabase SQL Editor, run the complete schema from `knowledge_base_schema.sql`
2. Verify all tables are created successfully
3. Check that indexes are created properly

### **2.2 Verify Schema Creation**

```sql
-- Check if tables exist
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name LIKE '%knowledge%';

-- Check if extensions are enabled
SELECT * FROM pg_extension WHERE extname IN ('uuid-ossp', 'pg_trgm', 'vector');
```

## 🔧 **STEP 3: ENVIRONMENT CONFIGURATION**

### **3.1 Create Environment File**

Create `.env` file in your project root:

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
SUPABASE_ANON_KEY=your_anon_key

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Knowledge Base Configuration
KNOWLEDGE_BASE_EMBEDDING_MODEL=text-embedding-3-small
KNOWLEDGE_BASE_SEARCH_LIMIT=10
KNOWLEDGE_BASE_SIMILARITY_THRESHOLD=0.7

# Logging Configuration
LOG_LEVEL=INFO
```

### **3.2 Load Environment Variables**

```python
# In your main application file
import os
from dotenv import load_dotenv

load_dotenv()

# Verify environment variables
required_vars = [
    'SUPABASE_URL',
    'SUPABASE_SERVICE_ROLE_KEY',
    'OPENAI_API_KEY'
]

for var in required_vars:
    if not os.getenv(var):
        raise ValueError(f"Missing required environment variable: {var}")
```

## 📊 **STEP 4: KNOWLEDGE BASE POPULATION**

### **4.1 Run Initial Population Script**

```bash
# Navigate to scripts directory
cd scripts

# Run the population script
python populate_knowledge_base.py
```

### **4.2 Verify Data Population**

```sql
-- Check data in tables
SELECT COUNT(*) FROM legal_documents;
SELECT COUNT(*) FROM jurisprudence;
SELECT COUNT(*) FROM legal_terms;
SELECT COUNT(*) FROM contract_knowledge;
```

### **4.3 Test Knowledge Base Search**

```python
# Test script to verify knowledge base functionality
import asyncio
from config.supabase_knowledge_base import create_supabase_knowledge_base

async def test_knowledge_base():
    kb = create_supabase_knowledge_base()

    # Test search
    results = await kb.search("habeas data", limit=5)
    print(f"Found {len(results)} results for 'habeas data'")

    # Test legal terms
    terms = await kb.get_legal_terms(["habeas data", "due process"])
    print(f"Found {len(terms)} legal terms")

if __name__ == "__main__":
    asyncio.run(test_knowledge_base())
```

## 🤖 **STEP 5: AGENT INTEGRATION**

### **5.1 Update Agent Configuration**

Update your existing agents to use the knowledge base:

```python
# Example: Update contract_agent.py
from config.knowledge_base_integration import create_agent_knowledge_integration

def create_contract_agent() -> Agent:
    # Create knowledge integration
    knowledge_integration = create_agent_knowledge_integration("contract_agent")

    return Agent(
        name="Analista de Contratos avanzado",
        role="Especialista en análisis contractual con capacidades avanzadas",
        model=get_model("contract_review"),
        tools=[GoogleSearchTools()],
        knowledge=knowledge_integration,  # Add knowledge integration
        search_knowledge=True,
        instructions=[
            # ... existing instructions ...
        ],
        markdown=True
    )
```

### **5.2 Test Agent Knowledge Integration**

```python
# Test script for agent knowledge integration
import asyncio
from config.knowledge_base_integration import AgentKnowledgeHelper

async def test_agent_knowledge():
    helper = AgentKnowledgeHelper("contract_agent")

    # Test prompt enhancement
    base_prompt = "Analizar el siguiente contrato de arrendamiento"
    enhanced_prompt = await helper.enhance_prompt_with_knowledge(base_prompt)
    print("Enhanced prompt:", enhanced_prompt)

    # Test legal terms
    terms = await helper.get_relevant_legal_terms("contrato de arrendamiento")
    print("Relevant terms:", terms)

if __name__ == "__main__":
    asyncio.run(test_agent_knowledge())
```

## 🔍 **STEP 6: TESTING AND VALIDATION**

### **6.1 Create Test Suite**

```python
# tests/test_knowledge_base.py
import pytest
import asyncio
from config.supabase_knowledge_base import create_supabase_knowledge_base

@pytest.mark.asyncio
async def test_knowledge_search():
    kb = create_supabase_knowledge_base()
    results = await kb.search("constitución", limit=5)
    assert len(results) > 0
    assert all(hasattr(r, 'content') for r in results)

@pytest.mark.asyncio
async def test_legal_terms():
    kb = create_supabase_knowledge_base()
    terms = await kb.get_legal_terms(["habeas data"])
    assert "habeas data" in terms
    assert len(terms["habeas data"]) > 0

@pytest.mark.asyncio
async def test_jurisprudence():
    kb = create_supabase_knowledge_base()
    jurisprudence = await kb.get_jurisprudence(
        topic="datos personales",
        limit=5
    )
    assert len(jurisprudence) >= 0  # May be empty initially
```

### **6.2 Run Tests**

```bash
# Install pytest
pip install pytest pytest-asyncio

# Run tests
pytest tests/ -v
```

## 📈 **STEP 7: MONITORING AND ANALYTICS**

### **7.1 Set Up Monitoring**

```python
# monitoring/knowledge_base_monitor.py
import asyncio
import logging
from datetime import datetime
from config.supabase_knowledge_base import create_supabase_knowledge_base

class KnowledgeBaseMonitor:
    def __init__(self):
        self.kb = create_supabase_knowledge_base()
        self.logger = logging.getLogger(__name__)

    async def check_knowledge_base_health(self):
        """Check knowledge base health and performance"""
        try:
            # Test search functionality
            start_time = datetime.now()
            results = await self.kb.search("test", limit=1)
            search_time = (datetime.now() - start_time).total_seconds()

            # Log metrics
            self.logger.info(f"Knowledge base health check - Search time: {search_time}s, Results: {len(results)}")

            return {
                "status": "healthy",
                "search_time": search_time,
                "results_count": len(results),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Knowledge base health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Run health check
async def main():
    monitor = KnowledgeBaseMonitor()
    health = await monitor.check_knowledge_base_health()
    print("Health check result:", health)

if __name__ == "__main__":
    asyncio.run(main())
```

### **7.2 Set Up Analytics Dashboard**

```sql
-- Create analytics views
CREATE VIEW knowledge_usage_analytics AS
SELECT
    agent_name,
    COUNT(*) as total_searches,
    AVG(search_duration_ms) as avg_search_time,
    COUNT(CASE WHEN response_quality_score >= 4 THEN 1 END) as high_quality_responses
FROM knowledge_search_logs
GROUP BY agent_name;

CREATE VIEW knowledge_popularity AS
SELECT
    knowledge_table,
    COUNT(*) as usage_count,
    AVG(success_rate) as avg_success_rate
FROM agent_knowledge_usage
GROUP BY knowledge_table
ORDER BY usage_count DESC;
```

## 🔄 **STEP 8: AUTOMATED UPDATES**

### **8.1 Create Update Scripts**

```python
# scripts/update_knowledge_base.py
import asyncio
import logging
from datetime import datetime
from config.supabase_knowledge_base import create_supabase_knowledge_base

class KnowledgeBaseUpdater:
    def __init__(self):
        self.kb = create_supabase_knowledge_base()
        self.logger = logging.getLogger(__name__)

    async def update_legal_documents(self):
        """Update legal documents from official sources"""
        # Implementation for automated updates
        pass

    async def update_jurisprudence(self):
        """Update jurisprudence from court websites"""
        # Implementation for automated updates
        pass

    async def run_daily_updates(self):
        """Run daily knowledge base updates"""
        self.logger.info("Starting daily knowledge base updates")

        try:
            await self.update_legal_documents()
            await self.update_jurisprudence()

            self.logger.info("Daily updates completed successfully")

        except Exception as e:
            self.logger.error(f"Daily updates failed: {e}")

# Schedule daily updates
async def main():
    updater = KnowledgeBaseUpdater()
    await updater.run_daily_updates()

if __name__ == "__main__":
    asyncio.run(main())
```

### **8.2 Set Up Cron Jobs**

```bash
# Add to crontab for daily updates
0 2 * * * cd /path/to/your/project && python scripts/update_knowledge_base.py

# Add to crontab for health checks
*/30 * * * * cd /path/to/your/project && python monitoring/knowledge_base_monitor.py
```

## 🚀 **STEP 9: DEPLOYMENT**

### **9.1 Production Environment Setup**

```bash
# Create production environment file
cp .env .env.production

# Update production environment variables
# Use production Supabase project
# Use production OpenAI API key
# Set appropriate log levels
```

### **9.2 Docker Deployment**

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

```yaml
# docker-compose.yml
version: "3.8"
services:
  legal-ai:
    build: .
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
```

### **9.3 Cloud Deployment**

```bash
# Deploy to cloud platform (example for Heroku)
heroku create legal-ai-knowledge-base
heroku config:set SUPABASE_URL=$SUPABASE_URL
heroku config:set SUPABASE_SERVICE_ROLE_KEY=$SUPABASE_SERVICE_ROLE_KEY
heroku config:set OPENAI_API_KEY=$OPENAI_API_KEY
git push heroku main
```

## 📊 **STEP 10: PERFORMANCE OPTIMIZATION**

### **10.1 Database Optimization**

```sql
-- Create additional indexes for performance
CREATE INDEX CONCURRENTLY idx_legal_documents_updated_at
ON legal_documents(updated_at);

CREATE INDEX CONCURRENTLY idx_jurisprudence_decision_date
ON jurisprudence(decision_date);

-- Analyze tables for query optimization
ANALYZE legal_documents;
ANALYZE jurisprudence;
ANALYZE legal_terms;
```

### **10.2 Caching Implementation**

```python
# config/cache.py
import redis
import json
from typing import Any, Optional

class KnowledgeCache:
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379, db=0)

    def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        value = self.redis.get(key)
        return json.loads(value) if value else None

    def set(self, key: str, value: Any, expire: int = 3600):
        """Set cached value with expiration"""
        self.redis.setex(key, expire, json.dumps(value))

    def delete(self, key: str):
        """Delete cached value"""
        self.redis.delete(key)
```

## 🔒 **STEP 11: SECURITY AND COMPLIANCE**

### **11.1 Security Configuration**

```python
# config/security.py
import os
from typing import List

class SecurityConfig:
    @staticmethod
    def get_allowed_origins() -> List[str]:
        """Get allowed CORS origins"""
        return os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')

    @staticmethod
    def get_api_rate_limit() -> int:
        """Get API rate limit per minute"""
        return int(os.getenv('API_RATE_LIMIT', '100'))

    @staticmethod
    def get_max_search_results() -> int:
        """Get maximum search results per query"""
        return int(os.getenv('MAX_SEARCH_RESULTS', '50'))
```

### **11.2 Data Privacy Compliance**

```python
# config/privacy.py
from datetime import datetime, timedelta

class PrivacyConfig:
    @staticmethod
    def get_data_retention_days() -> int:
        """Get data retention period in days"""
        return int(os.getenv('DATA_RETENTION_DAYS', '365'))

    @staticmethod
    def should_anonymize_logs() -> bool:
        """Check if logs should be anonymized"""
        return os.getenv('ANONYMIZE_LOGS', 'true').lower() == 'true'

    @staticmethod
    def get_privacy_policy_url() -> str:
        """Get privacy policy URL"""
        return os.getenv('PRIVACY_POLICY_URL', '')
```

## 📝 **STEP 12: DOCUMENTATION AND MAINTENANCE**

### **12.1 API Documentation**

```python
# Create API documentation using FastAPI
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI(title="Colombian Legal AI Knowledge Base API")

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Colombian Legal AI Knowledge Base API",
        version="1.0.0",
        description="API for accessing Colombian legal knowledge base",
        routes=app.routes,
    )

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

### **12.2 Maintenance Schedule**

```python
# scripts/maintenance.py
import asyncio
import logging
from datetime import datetime, timedelta
from config.supabase_knowledge_base import create_supabase_knowledge_base

class KnowledgeBaseMaintenance:
    def __init__(self):
        self.kb = create_supabase_knowledge_base()
        self.logger = logging.getLogger(__name__)

    async def cleanup_old_logs(self):
        """Clean up old search logs"""
        retention_days = 90
        cutoff_date = datetime.now() - timedelta(days=retention_days)

        # Implementation for cleaning old logs
        pass

    async def optimize_database(self):
        """Optimize database performance"""
        # Implementation for database optimization
        pass

    async def run_maintenance(self):
        """Run maintenance tasks"""
        self.logger.info("Starting knowledge base maintenance")

        try:
            await self.cleanup_old_logs()
            await self.optimize_database()

            self.logger.info("Maintenance completed successfully")

        except Exception as e:
            self.logger.error(f"Maintenance failed: {e}")

# Run maintenance
async def main():
    maintenance = KnowledgeBaseMaintenance()
    await maintenance.run_maintenance()

if __name__ == "__main__":
    asyncio.run(main())
```

## ✅ **VERIFICATION CHECKLIST**

- [ ] Supabase project created and configured
- [ ] Database schema deployed successfully
- [ ] Environment variables configured
- [ ] Initial knowledge base populated
- [ ] Agent integration implemented
- [ ] Tests passing
- [ ] Monitoring configured
- [ ] Security measures implemented
- [ ] Documentation completed
- [ ] Deployment successful

## 🆘 **TROUBLESHOOTING**

### **Common Issues**

1. **Supabase Connection Error**

   - Verify project URL and API keys
   - Check network connectivity
   - Ensure Supabase project is active

2. **OpenAI API Error**

   - Verify API key is valid
   - Check API quota and billing
   - Ensure correct model name

3. **Database Schema Errors**

   - Check PostgreSQL version compatibility
   - Verify extensions are enabled
   - Review error logs for specific issues

4. **Performance Issues**
   - Check database indexes
   - Monitor query performance
   - Implement caching if needed

### **Support Resources**

- [Supabase Documentation](https://supabase.com/docs)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Agno Framework Documentation](https://docs.agno.com/)

---

_This setup guide provides a comprehensive approach to deploying the Colombian Legal AI Knowledge Base. Follow each step carefully and verify completion before proceeding to the next step._
