# PostgreSQL Memory Setup Guide for Legal AI Assistant

## 🎯 Overview

This guide helps you set up PostgreSQL memory integration using your existing schemas:

- `memory_schema.sql` - For user memories and session data
- `knowledge_base_schema.sql` - For legal knowledge search

## 📋 Prerequisites

### 1. Supabase Setup

Ensure your Supabase project has the required schemas:

```sql
-- Run memory_schema.sql in your Supabase SQL editor
-- This creates the ai schema with memory tables

-- Run knowledge_base_schema.sql in your Supabase SQL editor
-- This creates the knowledge base tables with vector support
```

### 2. Environment Configuration

Create a `.env` file with your Supabase credentials:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# Database Configuration
DATABASE_URL=postgresql://postgres.your-project-ref:your-password@aws-0-region.pooler.supabase.com:6543/postgres

# Development Settings
ENABLE_VECTOR_DB=true
USE_SQLITE_FALLBACK=false
```

## 🚀 Quick Start

### 1. Test the Integration

Run the comprehensive test script:

```bash
python test_postgres_memory_integration.py
```

Expected output:

```
✅ Memory instance created for chatbot_agent
✅ Memory instance created for contract_agent
✅ Memory added for chatbot_agent
✅ Retrieved 1 memories for chatbot_agent
✅ Session data stored successfully
✅ Knowledge search for 'contrato laboral': 3 results
🎉 All tests passed!
```

### 2. Use in Your Agents

```python
from postgres_memory import (
    get_memory_instance,
    add_user_memory,
    get_user_memories,
    search_knowledge_base
)

# Initialize memory for an agent
memory = get_memory_instance("chatbot_agent")

# Add user memory
add_user_memory(
    agent_name="chatbot_agent",
    user_id="user_123",
    memory_content="El usuario prefiere respuestas en español",
    topics=["preferences", "language"]
)

# Get user memories
memories = get_user_memories("chatbot_agent", "user_123")

# Search knowledge base
results = search_knowledge_base("contrato laboral", limit=5)
```

## 📊 Schema Integration

### Memory Schema (`memory_schema.sql`)

The PostgreSQL memory system uses these tables:

#### Core Memory Tables:

- `ai.user_memories` - General user memories
- `ai.agent_sessions` - Session data storage
- `ai.session_summaries` - Session summaries

#### Agent-Specific Tables:

- `ai.chatbot_agent_memories` - Chatbot memories
- `ai.contract_agent_memories` - Contract analysis memories
- `ai.legal_research_agent_memories` - Legal research memories
- `ai.case_prediction_agent_memories` - Case prediction memories
- `ai.compliance_agent_memories` - Compliance memories
- `ai.document_drafting_agent_memories` - Document drafting memories
- `ai.demand_letter_agent_memories` - Demand letter memories
- `ai.patent_agent_memories` - Patent memories
- `ai.regulatory_agent_memories` - Regulatory memories
- `ai.whistleblower_agent_memories` - Whistleblower memories

### Knowledge Base Schema (`knowledge_base_schema.sql`)

The system searches these knowledge tables:

#### Core Knowledge Tables:

- `legal_documents_ai` - Laws, decrees, regulations
- `jurisprudence` - Court decisions and precedents
- `legal_terms` - Legal terminology and definitions
- `regulatory_frameworks` - Sector-specific regulations

#### Agent-Specific Knowledge:

- `contract_knowledge` - Contract analysis knowledge
- `patent_knowledge` - Intellectual property knowledge
- `case_prediction_knowledge` - Case outcome prediction
- `compliance_knowledge` - Compliance requirements
- `document_templates` - Legal document templates

## 🔧 Configuration Options

### Memory System Configuration

```python
# In postgres_memory.py
class LegalAIPostgresMemory:
    def __init__(self, agent_name: str = "default"):
        # Automatically uses agent-specific tables
        # Falls back to SQLite if PostgreSQL unavailable
```

### Environment Variables

```bash
# Enable/disable features
ENABLE_VECTOR_DB=true          # Enable vector database features
USE_SQLITE_FALLBACK=false      # Use SQLite fallback for development
DEBUG_MODE=true               # Enable debug logging

# Database settings
DATABASE_URL=your_supabase_url
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

## 📝 Usage Examples

### 1. Basic Memory Operations

```python
from postgres_memory import get_memory_instance

# Get memory instance for an agent
memory = get_memory_instance("chatbot_agent")

# Add memory
memory.add_user_memory(
    user_id="user_123",
    memory_content="User prefers Spanish language",
    topics=["language", "preferences"]
)

# Get memories
memories = memory.get_user_memories("user_123", limit=10)
```

### 2. Session Management

```python
from postgres_memory import store_session_data, get_session_data

# Store session data
session_data = {
    "conversation_history": [
        {"role": "user", "content": "¿Cuáles son los requisitos?"},
        {"role": "assistant", "content": "Los requisitos incluyen..."}
    ],
    "user_preferences": {"language": "español"}
}

store_session_data("chatbot_agent", "user_123", "session_001", session_data)

# Retrieve session data
session = get_session_data("chatbot_agent", "user_123", "session_001")
```

### 3. Knowledge Base Search

```python
from postgres_memory import search_knowledge_base

# Search legal knowledge
results = search_knowledge_base("contrato laboral", limit=5)

for result in results:
    print(f"Source: {result['source']}")
    print(f"Title: {result['title']}")
    print(f"Content: {result['content'][:100]}...")
    print(f"Similarity: {result['similarity']}")
```

### 4. Agent-Specific Memories

```python
memory = get_memory_instance("contract_agent")

# Get agent-specific memories
agent_memories = memory.get_agent_specific_memories("user_123", limit=10)

for memory in agent_memories:
    print(f"Memory: {memory['memory']}")
    print(f"Created: {memory['created_at']}")
    print(f"Metadata: {memory['metadata']}")
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Connection Errors

```
Error: could not translate host name "db.luiiwyzjtkqnmnzqghoz.supabase.co"
```

**Solution**: Check your Supabase URL format and credentials

#### 2. Missing Tables

```
Error: relation "ai.chatbot_agent_memories" does not exist
```

**Solution**: Run the `memory_schema.sql` in your Supabase SQL editor

#### 3. Vector Database Issues

```
Warning: agno.vectordb.postgres not available
```

**Solution**: This is expected in development. The system falls back to text search.

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test Individual Components

```bash
# Test PostgreSQL memory only
python test_postgres_memory.py

# Test memory manager integration
python test_agent_config_fix.py

# Test full integration
python test_postgres_memory_integration.py
```

## 🎯 Integration with Agents

### Update Agent Configuration

```python
# In config/enhanced_agent_config.py
def get_enhanced_agent_config(agent_name: str) -> Dict[str, Any]:
    config = {
        "memory": get_memory_instance(agent_name),  # Use PostgreSQL memory
        "knowledge_base": True,
        "search_knowledge": True,
        # ... other config
    }
    return config
```

### Use in Agent Code

```python
# In your agent files
from postgres_memory import get_memory_instance

class ChatbotAgent:
    def __init__(self):
        self.memory = get_memory_instance("chatbot_agent")

    def process_message(self, user_id: str, message: str):
        # Get user memories
        memories = self.memory.get_user_memories(user_id)

        # Add new memory
        self.memory.add_user_memory(
            user_id=user_id,
            memory_content=f"User asked about: {message}",
            topics=["conversation", "query"]
        )

        # Search knowledge base
        knowledge = self.memory.search_knowledge_base(message)

        # Process with context
        return self.generate_response(message, memories, knowledge)
```

## 📈 Performance Optimization

### 1. Connection Pooling

```python
# The system automatically uses SQLAlchemy connection pooling
# Configure in your environment:
DATABASE_URL=postgresql://user:pass@host:port/db?pool_size=10&max_overflow=20
```

### 2. Memory Caching

```python
# Memory instances are cached globally
memory = get_memory_instance("chatbot_agent")  # Cached instance
```

### 3. Batch Operations

```python
# For bulk operations, use direct database access
with memory.session_factory() as session:
    # Batch insert memories
    session.add_all(memories)
    session.commit()
```

## 🎉 Success Indicators

Your PostgreSQL memory integration is working correctly when:

✅ **Memory Operations**: Adding and retrieving memories works
✅ **Session Storage**: Session data persists across requests
✅ **Knowledge Search**: Legal knowledge search returns results
✅ **Agent-Specific**: Each agent has its own memory space
✅ **Fallback System**: SQLite fallback works when PostgreSQL unavailable
✅ **Error Handling**: Graceful degradation on connection issues

## 🚀 Next Steps

1. **Populate Knowledge Base**: Add legal documents to your knowledge tables
2. **Configure Vector Search**: Set up vector embeddings for better search
3. **Monitor Performance**: Track memory usage and search performance
4. **Scale Up**: Add more agents and memory types as needed

Your PostgreSQL memory system is now ready for production use! 🎯
