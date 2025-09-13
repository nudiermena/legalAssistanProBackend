# Enhanced Legal AI Agents

This document explains the enhanced capabilities added to your legal AI agents, implementing **Reasoning**, **Knowledge**, **Storage**, and **Memory** features.

## 🚀 Enhanced Capabilities Overview

### 1. **Reasoning** 🤔

- **What it does**: Agents "think" before responding and analyze the results of their actions
- **Benefits**: Improved reliability and quality of responses
- **Implementation**:
  - Step-by-step analysis process
  - Multiple perspective evaluation
  - Confidence level assessment
  - Alternative scenario exploration

### 2. **Knowledge** 📚

- **What it does**: Domain-specific information that agents search at runtime (RAG - Retrieval Augmented Generation)
- **Benefits**: Better decisions and accurate responses based on current legal information
- **Implementation**:
  - Vector database integration (Pinecone/Memory)
  - Colombian legal knowledge sources
  - PDF and website knowledge bases
  - Real-time legal information retrieval

### 3. **Storage** 💾

- **What it does**: Saves session history and state in a database
- **Benefits**: Enables multi-turn, long-term conversations and stateful agents
- **Implementation**:
  - PostgreSQL agent storage
  - Session persistence
  - Conversation history tracking
  - State management across sessions

### 4. **Memory** 🧠

- **What it does**: Stores and recalls information from previous interactions
- **Benefits**: Learns user preferences and personalizes responses
- **Implementation**:
  - User preference tracking
  - Conversation history
  - Case context preservation
  - Legal terms caching

## 📁 File Structure

```
agents/
├── base_enhanced_agent.py          # Base class with all capabilities
├── enhanced_contract_agent.py      # Enhanced contract analysis
├── enhanced_legal_research_agent.py # Enhanced legal research
└── [other enhanced agents...]

config/
├── enhanced_agent_config.py        # Enhanced configuration system
└── [existing config files...]

test_enhanced_agents.py             # Test script for capabilities
requirements_enhanced.txt           # Additional dependencies
```

## 🛠️ Installation

### 1. Install Enhanced Dependencies

```bash
pip install -r requirements_enhanced.txt
```

### 2. Environment Variables

Add these to your `.env` file:

```env
# Vector Database (Optional - falls back to in-memory)
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX=legal-knowledge

# Database (Required for storage)
DATABASE_URL=postgresql://user:password@localhost:5432/legal_assistant

# Debug Mode (Optional)
DEBUG_MODE=true
```

## 🎯 Usage Examples

### Enhanced Contract Agent

```python
from agents.enhanced_contract_agent import create_enhanced_contract_agent

# Create agent for specific user
agent = create_enhanced_contract_agent(user_id="user_123")

# Analyze contract with enhanced capabilities
result = await agent.analyze_contract(
    contract_text="CONTRATO DE ARRENDAMIENTO...",
    contract_type="Arrendamiento",
    parties=["Juan Pérez", "María García"],
    specific_concerns=["Términos de pago", "Caución"],
    relevant_regulations=["Ley 820 de 2003", "Código Civil"]
)

# Check enhanced features
print(result['enhanced_features'])
# Output: {
#   'reasoning_used': True,
#   'knowledge_searched': True,
#   'memory_accessed': True,
#   'storage_persisted': True
# }

# Get memory summary
memory = agent.get_memory_summary()
print(f"Total interactions: {memory['total_interactions']}")
```

### Enhanced Legal Research Agent

```python
from agents.enhanced_legal_research_agent import create_enhanced_legal_research_agent

# Create research agent
agent = create_enhanced_legal_research_agent(user_id="user_456")

# Conduct legal research
result = await agent.research_legal_topic(
    research_topic="Protección de datos personales en contratos",
    jurisdiction="Colombia",
    research_type="compliance",
    specific_questions=[
        "¿Qué requisitos establece la Ley 1581 de 2012?",
        "¿Cuáles son las sanciones por incumplimiento?"
    ],
    date_range="últimos 3 años"
)

# Search specific jurisprudence
jurisprudence = await agent.search_jurisprudence(
    topic="protección de datos personales",
    court="Corte Constitucional",
    date_from="2020-01-01",
    date_to="2024-12-31"
)
```

### Creating Custom Enhanced Agents

```python
from agents.base_enhanced_agent import BaseEnhancedAgent
from agno.tools.googlesearch import GoogleSearchTools

class EnhancedComplianceAgent(BaseEnhancedAgent):
    def __init__(self, user_id: str = None):
        super().__init__("compliance", user_id)

    def get_agent_name(self) -> str:
        return "Analista de Cumplimiento Avanzado"

    def get_agent_role(self) -> str:
        return "Especialista en cumplimiento regulatorio con capacidades avanzadas"

    def get_model_name(self) -> str:
        return "compliance"

    def get_tools(self) -> List:
        return [GoogleSearchTools()]

    def get_base_instructions(self) -> List[str]:
        return [
            "Analizar cumplimiento normativo colombiano",
            "Evaluar requisitos de protección de datos",
            # ... more instructions
        ]

    def _build_base_prompt(self, request_data: Dict[str, Any]) -> str:
        # Build your specific prompt
        return f"Analizar cumplimiento: {request_data.get('topic')}"

# Usage
agent = EnhancedComplianceAgent(user_id="user_789")
result = await agent.process_request({
    "type": "compliance_analysis",
    "topic": "Ley 1581 de 2012",
    "company_type": "SME"
})
```

## 🧪 Testing Enhanced Capabilities

Run the test script to see all capabilities in action:

```bash
python test_enhanced_agents.py
```

This will test:

- ✅ Contract analysis with reasoning
- ✅ Legal research with knowledge search
- ✅ Memory persistence across sessions
- ✅ Enhanced features comparison

## 📊 Capability Comparison

| Feature                | Basic Agent  | Enhanced Agent                |
| ---------------------- | ------------ | ----------------------------- |
| **Reasoning**          | ❌ No        | ✅ Step-by-step analysis      |
| **Knowledge**          | ❌ Static    | ✅ Dynamic RAG search         |
| **Storage**            | ❌ In-memory | ✅ Database persistence       |
| **Memory**             | ❌ No        | ✅ User preferences & history |
| **Personalization**    | ❌ No        | ✅ Context-aware responses    |
| **Session Management** | ❌ No        | ✅ Multi-turn conversations   |

## 🔧 Configuration Options

### Vector Database Options

1. **Pinecone (Production)**

   ```python
   # Set environment variables
   PINECONE_API_KEY=your_key
   PINECONE_ENVIRONMENT=your_env
   PINECONE_INDEX=legal-knowledge
   ```

2. **In-Memory (Development)**
   ```python
   # Automatically falls back if Pinecone not configured
   ```

### Knowledge Sources

The system includes these Colombian legal sources:

- **PDFs**: Official legal documents
- **Websites**: Government legal portals
- **Jurisprudence**: Court decisions
- **Legislation**: Current laws and regulations

### Memory Configuration

Memory includes:

- User preferences (language, detail level, risk tolerance)
- Conversation history (last 10 interactions)
- Case context (current case information)
- Legal terms cache (frequently used terms)

## 🚀 Migration from Basic Agents

### Step 1: Update Imports

```python
# Old
from agents.contract_agent import analyze_contract

# New
from agents.enhanced_contract_agent import create_enhanced_contract_agent
```

### Step 2: Update Function Calls

```python
# Old
result = await analyze_contract(contract_text, contract_type, parties)

# New
agent = create_enhanced_contract_agent(user_id)
result = await agent.analyze_contract(contract_text, contract_type, parties)
```

### Step 3: Add User Context

```python
# Enhanced agents work better with user context
agent = create_enhanced_contract_agent(user_id="user_123")
```

## 🎯 Benefits for Your Legal AI System

### For Users:

- **Personalized Experience**: Agents remember preferences and past interactions
- **Better Accuracy**: Enhanced reasoning and knowledge search
- **Consistent Quality**: Persistent learning and improvement
- **Context Awareness**: Agents understand user's legal situation

### For Developers:

- **Scalable Architecture**: Base class for easy agent creation
- **Modular Design**: Each capability can be enabled/disabled
- **Extensible**: Easy to add new knowledge sources or memory types
- **Testable**: Comprehensive testing framework

### For Business:

- **Higher User Satisfaction**: More relevant and accurate responses
- **Reduced Support**: Better self-service capabilities
- **Competitive Advantage**: Advanced AI capabilities
- **Data Insights**: Rich interaction data for improvement

## 🔮 Future Enhancements

### Planned Features:

- **Multi-modal Knowledge**: Images, audio, video processing
- **Advanced Reasoning**: Chain-of-thought, tree-of-thoughts
- **Collaborative Memory**: Shared knowledge across agents
- **Real-time Updates**: Live legal information feeds
- **Advanced Analytics**: Usage patterns and optimization

### Integration Opportunities:

- **Document Management**: Direct integration with legal document systems
- **Case Management**: Integration with legal practice management software
- **Compliance Monitoring**: Real-time regulatory change detection
- **Client Portal**: Enhanced user interface for agent interactions

## 🆘 Troubleshooting

### Common Issues:

1. **Database Connection Error**

   ```bash
   # Check DATABASE_URL in .env
   # Ensure PostgreSQL is running
   ```

2. **Pinecone Connection Error**

   ```bash
   # Falls back to in-memory automatically
   # Check API keys if using Pinecone
   ```

3. **Memory Not Persisting**

   ```python
   # Ensure user_id is provided
   agent = create_enhanced_contract_agent(user_id="unique_user_id")
   ```

4. **Knowledge Search Not Working**
   ```python
   # Check internet connection for web sources
   # Verify PDF URLs are accessible
   ```

## 📞 Support

For questions or issues with enhanced agents:

1. Check the test script output
2. Review environment variables
3. Check database connectivity
4. Verify knowledge source accessibility

---

**Ready to enhance your legal AI system?** 🚀

Start with the test script to see the capabilities in action, then gradually migrate your existing agents to use the enhanced features!
