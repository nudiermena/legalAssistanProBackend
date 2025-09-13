# Memory System for Legal AI Assistant

## Overview

This document describes the comprehensive memory system implemented for the Legal AI Assistant using Agno's memory capabilities with Supabase/PostgreSQL backend. The memory system provides persistent, personalized experiences across all agents.

## Memory System Architecture

### 1. Types of Memory

The system implements three types of memory as described in [Agno's Memory Documentation](https://docs.agno.com/agents/memory):

#### **Session Storage (Chat History)**

- Stores conversation history and session state
- Enables multi-turn conversations
- Persisted across execution cycles
- Uses PostgreSQL tables: `ai.agent_sessions`

#### **User Memories (User Preferences)**

- Stores insights and facts about users
- Enables personalized responses
- Similar to ChatGPT's memory feature
- Uses PostgreSQL tables: `ai.user_memories`

#### **Session Summaries (Chat Summary)**

- Condensed representations of sessions
- Useful when chat histories get too long
- Uses PostgreSQL tables: `ai.session_summaries`

### 2. Enhanced Agents with Memory

The following agents have been enhanced with memory capabilities:

#### **Chatbot Agent** (`agents/chatbot_agent.py`)

- **Memory Features:**

  - Conversation history persistence
  - User preference learning
  - Practice area specialization memory
  - Legal terminology preferences
  - Session continuity

- **Use Cases:**
  - Remembers user's legal expertise level
  - Adapts response complexity
  - Maintains conversation context
  - Learns preferred legal areas

#### **Contract Agent** (`agents/contract_agent.py`)

- **Memory Features:**

  - Contract analysis patterns
  - Risk assessment history
  - User's contract preferences
  - Compliance requirement memory
  - Legal term definitions

- **Use Cases:**
  - Remembers user's contract types
  - Learns risk tolerance patterns
  - Maintains compliance history
  - Adapts analysis depth

#### **Legal Research Agent** (`agents/legal_research_agent.py`)

- **Memory Features:**

  - Research topic preferences
  - Jurisdiction focus areas
  - Legal source preferences
  - Research methodology patterns

- **Use Cases:**
  - Remembers preferred jurisdictions
  - Learns research depth preferences
  - Maintains source credibility history
  - Adapts research scope

#### **Case Prediction Agent** (`agents/case_prediction_agent.py`)

- **Memory Features:**
  - Case type patterns
  - Prediction accuracy tracking
  - User's case history
  - Legal outcome preferences

#### **Compliance Agent** (`agents/compliance_agent.py`)

- **Memory Features:**
  - Compliance area focus
  - Regulatory requirement memory
  - Risk assessment patterns
  - Industry-specific knowledge

## Implementation Details

### 1. Configuration (`config/enhanced_agent_config.py`)

```python
# Enhanced configuration with memory capabilities
enhanced_config = {
    "memory": memory_system["memory"],
    "storage": memory_system["storage"],
    "add_history_to_messages": True,
    "num_history_runs": 5,
    "enable_user_memories": True,
    "enable_session_summaries": True,
    "enable_agentic_memory": True,
    "read_chat_history": True,
    "read_tool_call_history": True
}
```

### 2. Memory Manager (`config/memory_manager.py`)

Centralized memory operations:

```python
from config.memory_manager import (
    get_user_memories,
    add_user_memory,
    get_session_summary,
    get_memory_stats,
    get_agent_memory_context
)

# Get user memories
memories = get_user_memories("chatbot_agent", user_id)

# Get memory statistics
stats = get_memory_stats("contract_agent", user_id)

# Get memory context for prompts
context = get_agent_memory_context("legal_research_agent", user_id, session_id)
```

### 3. Database Schema (`memory_schema.sql`)

The memory system uses PostgreSQL with the following key tables:

- `ai.user_memories` - User-specific memories
- `ai.agent_sessions` - Session storage
- `ai.session_summaries` - Session summaries
- `ai.memory_statistics` - Performance metrics
- Agent-specific memory tables (e.g., `ai.chatbot_agent_memories`)

## Usage Examples

### 1. Creating an Agent with Memory

```python
from agents.chatbot_agent import create_chatbot_agent

# Create agent with memory capabilities
agent = create_chatbot_agent(
    user_id="user123",
    session_id="session456",
    practice_area="derecho_civil"
)
```

### 2. Processing Messages with Memory

```python
from agents.chatbot_agent import process_client_message

# Process message with memory context
response = await process_client_message(
    client_id="user123",
    message="¿Cuáles son mis derechos en un contrato de arrendamiento?",
    user_id="user123",
    session_id="session456",
    practice_area="derecho_civil"
)
```

### 3. Contract Analysis with Memory

```python
from agents.contract_agent import analyze_contract

# Analyze contract with user memory
result = await analyze_contract(
    contract_text=contract_content,
    contract_type="arrendamiento",
    parties=["arrendador", "arrendatario"],
    user_id="user123",
    session_id="session456"
)
```

### 4. Legal Research with Memory

```python
from agents.legal_research_agent import conduct_legal_research

# Conduct research with user preferences
research = await conduct_legal_research(
    research_topic="contratos de arrendamiento",
    jurisdiction="Colombia",
    user_id="user123",
    session_id="session456"
)
```

## Memory Features by Agent

### Chatbot Agent Memory Features

1. **Conversation History**

   - Remembers previous conversations
   - Maintains context across sessions
   - References past discussions

2. **User Preferences**

   - Legal expertise level
   - Preferred practice areas
   - Response complexity preferences
   - Language preferences

3. **Session Management**
   - Session continuity
   - Topic tracking
   - Question history

### Contract Agent Memory Features

1. **Contract Analysis Patterns**

   - Previous contract types analyzed
   - Risk assessment patterns
   - User's risk tolerance
   - Compliance focus areas

2. **Legal Knowledge**

   - Frequently used legal terms
   - Contract clause preferences
   - Jurisdiction-specific knowledge

3. **User Preferences**
   - Analysis depth preferences
   - Report format preferences
   - Risk level preferences

### Legal Research Agent Memory Features

1. **Research Patterns**

   - Preferred research topics
   - Jurisdiction focus
   - Source credibility preferences
   - Research depth preferences

2. **Knowledge Accumulation**

   - Previous research findings
   - Legal source preferences
   - Citation style preferences

3. **User Context**
   - Research purpose patterns
   - Time constraints
   - Output format preferences

## Benefits of the Memory System

### 1. Personalization

- Responses adapt to user's expertise level
- Remembers user preferences and patterns
- Provides consistent experience across sessions

### 2. Efficiency

- Reduces repetitive explanations
- Builds on previous interactions
- Accelerates analysis with context

### 3. Quality

- More accurate responses with context
- Better risk assessments with history
- Improved research relevance

### 4. User Experience

- Seamless conversation flow
- Consistent terminology usage
- Progressive learning and adaptation

## Setup and Configuration

### 1. Environment Variables

```bash
# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Database Configuration
DATABASE_URL=postgresql://postgres:password@host:port/database
```

### 2. Database Setup

Run the memory schema:

```bash
psql -h your_host -U your_user -d your_database -f memory_schema.sql
```

### 3. Agent Configuration

Each agent automatically uses memory when created with user_id and session_id parameters.

## Monitoring and Analytics

### Memory Statistics

Track memory usage and performance:

```python
from config.memory_manager import get_memory_stats

stats = get_memory_stats("chatbot_agent", user_id)
print(f"Total memories: {stats['total_memories']}")
print(f"Recent memories: {stats['recent_memories']}")
print(f"Last interaction: {stats['last_interaction']}")
```

### Performance Metrics

- Memory hit rate
- Session duration
- User engagement patterns
- Agent-specific metrics

## Security and Privacy

### 1. Data Protection

- All memory data stored in Supabase with RLS
- User-specific data isolation
- Automatic data retention policies

### 2. Privacy Controls

- Users can clear their memories
- Session data expires automatically
- GDPR-compliant data handling

### 3. Access Control

- Memory access requires user authentication
- Agent-specific memory isolation
- Secure session management

## Troubleshooting

### Common Issues

1. **Memory Not Working**

   - Check Supabase credentials
   - Verify database schema is created
   - Check agent configuration

2. **Performance Issues**

   - Monitor memory usage
   - Check database indexes
   - Review session cleanup

3. **Data Consistency**
   - Verify user_id consistency
   - Check session_id uniqueness
   - Monitor memory updates

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('config.memory_manager').setLevel(logging.DEBUG)
```

## Future Enhancements

### Planned Features

1. **Advanced Memory Types**

   - Semantic memory for legal concepts
   - Procedural memory for analysis patterns
   - Episodic memory for case histories

2. **Memory Optimization**

   - Automatic memory compression
   - Relevance-based memory pruning
   - Intelligent memory retrieval

3. **Cross-Agent Memory**

   - Shared user context across agents
   - Inter-agent memory synchronization
   - Unified user profiles

4. **Analytics and Insights**
   - Memory usage analytics
   - User behavior patterns
   - Performance optimization insights

## References

- [Agno Memory Documentation](https://docs.agno.com/agents/memory)
- [PostgreSQL Memory Database](https://docs.agno.com/reference/memory/storage/postgres)
- [Supabase Documentation](https://supabase.com/docs)

## Support

For issues or questions about the memory system:

1. Check the troubleshooting section
2. Review agent-specific documentation
3. Monitor memory statistics
4. Contact the development team
