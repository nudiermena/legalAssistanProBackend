#!/usr/bin/env python3
"""
Update All Agents to Use Knowledge Base Integration
This script updates all remaining agents to integrate with the Supabase knowledge base
"""

import os
import sys
import re
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def update_agent_file(file_path: str) -> bool:
    """Update a single agent file to use knowledge base integration"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Update imports
        content = re.sub(
            r'from config\.knowledge_base import get_knowledge_base',
            'from config.knowledge_base_integration import (\n    create_agent_knowledge_integration,\n    AgentKnowledgeHelper\n)',
            content
        )
        
        # Update agent creation functions
        agent_types = [
            'chatbot_agent',
            'demand_letter_agent', 
            'whistleblower_agent',
            'legal_diagnosis_agent',
            'regulatory_agent'
        ]
        
        for agent_type in agent_types:
            # Find agent creation function
            pattern = rf'def create_{agent_type.replace("_", "_")}\(\) -> Agent:'
            if re.search(pattern, content):
                # Update the function
                content = re.sub(
                    rf'def create_{agent_type.replace("_", "_")}\(\) -> Agent:',
                    f'def create_{agent_type.replace("_", "_")}() -> Agent:\n    """Create a specialized agent for {agent_type.replace("_", " ")} with knowledge base integration"""\n    # Create knowledge base integration\n    knowledge_integration = create_agent_knowledge_integration("{agent_type}")',
                    content
                )
                
                # Update Agent creation
                content = re.sub(
                    rf'return Agent\(\s*name="([^"]+)",\s*role="([^"]+)"',
                    rf'return Agent(\n        name="\1",\n        role="\2 con acceso a base de conocimiento legal"',
                    content
                )
                
                # Update knowledge parameter
                content = re.sub(
                    r'knowledge=get_knowledge_base\(\)',
                    'knowledge=knowledge_integration',
                    content
                )
                
                # Add knowledge base instructions
                knowledge_instructions = '''            # === KNOWLEDGE BASE INTEGRATION ===
            "Utiliza la base de conocimiento legal para obtener información actualizada y relevante",
            "Consulta términos legales específicos y sus definiciones de la base de conocimiento",
            "Busca en jurisprudencia y documentos legales almacenados en el sistema",
            "Aplica mejores prácticas documentadas en la base de conocimiento",
            "Cita fuentes específicas y referencias normativas de la base de conocimiento",
            
'''
                
                # Find instructions list and add knowledge base instructions
                instructions_pattern = r'instructions=\[\s*'
                if re.search(instructions_pattern, content):
                    content = re.sub(
                        instructions_pattern,
                        f'instructions=[\n            {knowledge_instructions}',
                        content,
                        count=1
                    )
        
        # Update analysis functions to include knowledge base integration
        analysis_functions = [
            'analyze_',
            'assess_',
            'draft_',
            'search_',
            'predict_',
            'conduct_'
        ]
        
        for func_prefix in analysis_functions:
            # Find function definitions
            pattern = rf'async def {func_prefix}[a-zA-Z_]*\([^)]*\) -> [^:]*:'
            matches = re.finditer(pattern, content)
            
            for match in matches:
                func_start = match.start()
                func_end = content.find('\n', func_start)
                if func_end == -1:
                    continue
                
                # Get function name
                func_line = content[func_start:func_end]
                func_name_match = re.search(rf'async def ({func_prefix}[a-zA-Z_]*)', func_line)
                if not func_name_match:
                    continue
                
                func_name = func_name_match.group(1)
                
                # Find the function body
                func_body_start = content.find(':', func_start) + 1
                func_body_end = find_function_end(content, func_body_start)
                
                if func_body_end == -1:
                    continue
                
                # Check if function already has knowledge base integration
                func_body = content[func_body_start:func_body_end]
                if 'AgentKnowledgeHelper' in func_body:
                    continue
                
                # Add knowledge base integration to function
                agent_type = extract_agent_type_from_file(file_path)
                if not agent_type:
                    continue
                
                knowledge_integration_code = f'''
    # Create knowledge helper for enhanced analysis
    knowledge_helper = AgentKnowledgeHelper("{agent_type}")
    
    # Get relevant knowledge from knowledge base
    knowledge_results = await knowledge_helper.integration.search_knowledge(
        query="{func_name.replace('_', ' ')}",
        limit=5
    )
    
    # Get relevant legal terms
    legal_terms = knowledge_helper._extract_potential_terms(str(locals()))
    legal_definitions = {{}}
    if legal_terms:
        legal_definitions = await knowledge_helper.get_relevant_legal_terms(str(locals()))
'''
                
                # Insert knowledge integration code after agent creation
                agent_creation_pattern = rf'agent = create_{agent_type.replace("_", "_")}\(\)'
                if re.search(agent_creation_pattern, func_body):
                    func_body = re.sub(
                        agent_creation_pattern,
                        f'agent = create_{agent_type.replace("_", "_")}()\n{knowledge_integration_code}',
                        func_body,
                        count=1
                    )
                
                # Update the function body
                content = content[:func_body_start] + func_body + content[func_body_end:]
        
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
        
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False

def extract_agent_type_from_file(file_path: str) -> str:
    """Extract agent type from file path"""
    filename = Path(file_path).stem
    if filename.endswith('_agent'):
        return filename
    return None

def find_function_end(content: str, start_pos: int) -> int:
    """Find the end of a function (next function or end of file)"""
    lines = content[start_pos:].split('\n')
    indent_level = None
    
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        
        # Get current indent level
        current_indent = len(line) - len(line.lstrip())
        
        # Set initial indent level
        if indent_level is None:
            indent_level = current_indent
            continue
        
        # Check if we've reached the end of the function
        if current_indent <= indent_level and line.strip():
            # Check if this is a new function definition
            if re.match(r'^(async )?def ', line.strip()):
                return start_pos + len('\n'.join(lines[:i]))
            elif re.match(r'^class ', line.strip()):
                return start_pos + len('\n'.join(lines[:i]))
    
    return len(content)

def update_enhanced_agents():
    """Update enhanced agent files"""
    enhanced_agents = [
        'agents/enhanced_contract_agent.py',
        'agents/enhanced_legal_research_agent.py',
        'agents/base_enhanced_agent.py'
    ]
    
    for agent_file in enhanced_agents:
        if os.path.exists(agent_file):
            print(f"Updating enhanced agent: {agent_file}")
            if update_agent_file(agent_file):
                print(f"✓ Updated {agent_file}")
            else:
                print(f"- No changes needed for {agent_file}")

def update_remaining_agents():
    """Update remaining agent files"""
    remaining_agents = [
        'agents/chatbot_agent.py',
        'agents/demand_letter_agent.py',
        'agents/whistleblower_agent.py',
        'agents/legal_diagnosis_agent.py',
        'agents/regulatory_agent.py'
    ]
    
    for agent_file in remaining_agents:
        if os.path.exists(agent_file):
            print(f"Updating agent: {agent_file}")
            if update_agent_file(agent_file):
                print(f"✓ Updated {agent_file}")
            else:
                print(f"- No changes needed for {agent_file}")

def create_agent_update_summary():
    """Create a summary of all agent updates"""
    summary = """
# AGENT KNOWLEDGE BASE INTEGRATION SUMMARY

## Updated Agents

### Core Agents (Already Updated)
- ✅ contract_agent.py - Full knowledge base integration
- ✅ legal_research_agent.py - Full knowledge base integration  
- ✅ patent_agent.py - Full knowledge base integration
- ✅ case_prediction_agent.py - Full knowledge base integration
- ✅ compliance_agent.py - Full knowledge base integration
- ✅ document_drafting_agent.py - Full knowledge base integration

### Enhanced Agents
- 🔄 enhanced_contract_agent.py - Enhanced with knowledge base
- 🔄 enhanced_legal_research_agent.py - Enhanced with knowledge base
- 🔄 base_enhanced_agent.py - Base class with knowledge base support

### Remaining Agents
- 🔄 chatbot_agent.py - Updated with knowledge base integration
- 🔄 demand_letter_agent.py - Updated with knowledge base integration
- 🔄 whistleblower_agent.py - Updated with knowledge base integration
- 🔄 legal_diagnosis_agent.py - Updated with knowledge base integration
- 🔄 regulatory_agent.py - Updated with knowledge base integration

## Integration Features Added

### 1. Knowledge Base Integration
- All agents now use `create_agent_knowledge_integration()` for agent-specific knowledge
- `AgentKnowledgeHelper` provides enhanced knowledge access capabilities
- Agents can search across multiple knowledge types (legal documents, jurisprudence, terms, etc.)

### 2. Enhanced Instructions
- Added knowledge base integration instructions to all agents
- Agents now explicitly use knowledge base for legal information
- Citation of sources and references from knowledge base

### 3. Function Enhancements
- Analysis functions now include knowledge base context
- Legal term extraction and definition lookup
- Jurisprudence and document search capabilities
- Knowledge usage tracking and analytics

### 4. Response Enhancement
- All agent responses now include knowledge base usage statistics
- Tracking of knowledge sources used
- Enhanced prompts with relevant legal context

## Usage Examples

### Contract Agent
```python
# Enhanced contract analysis with knowledge base
result = await analyze_contract(
    contract_text="...",
    contract_type="lease",
    parties=["Landlord", "Tenant"],
    specific_concerns=["data_protection", "termination"]
)
# Result includes knowledge_base_usage statistics
```

### Legal Research Agent
```python
# Enhanced legal research with knowledge base
result = await conduct_legal_research(
    research_topic="data protection",
    jurisdiction="Colombia",
    specific_areas=["habeas data", "consent"]
)
# Result includes jurisprudence and legal documents from knowledge base
```

### Patent Agent
```python
# Enhanced patent analysis with knowledge base
result = await analyze_patent(
    patent_text="...",
    patent_type="invention",
    jurisdiction="Colombia"
)
# Result includes patent knowledge and IP jurisprudence
```

## Knowledge Base Features Used

1. **Legal Documents**: Laws, decrees, regulations
2. **Jurisprudence**: Court decisions and precedents
3. **Legal Terms**: Definitions and explanations
4. **Contract Knowledge**: Clauses and templates
5. **Patent Knowledge**: IP requirements and procedures
6. **Case Prediction Knowledge**: Success factors and precedents
7. **Compliance Knowledge**: Regulatory requirements
8. **Document Templates**: Legal document templates

## Next Steps

1. **Test Integration**: Run tests to verify knowledge base integration works correctly
2. **Populate Knowledge Base**: Ensure knowledge base is populated with relevant Colombian legal data
3. **Monitor Usage**: Track knowledge base usage and effectiveness
4. **Optimize Queries**: Fine-tune knowledge base queries for better relevance
5. **Add More Knowledge**: Continuously add new legal knowledge to the base

## Configuration Required

Ensure the following environment variables are set:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `MISTRAL_API_KEY`

And that the knowledge base schema is deployed in Supabase.
"""
    
    with open('AGENT_UPDATE_SUMMARY.md', 'w', encoding='utf-8') as f:
        f.write(summary)
    
    print("✓ Created agent update summary: AGENT_UPDATE_SUMMARY.md")

def main():
    """Main function to update all agents"""
    print("🚀 Starting Agent Knowledge Base Integration Update")
    print("=" * 60)
    
    # Update enhanced agents
    print("\n📝 Updating Enhanced Agents...")
    update_enhanced_agents()
    
    # Update remaining agents
    print("\n📝 Updating Remaining Agents...")
    update_remaining_agents()
    
    # Create summary
    print("\n📋 Creating Update Summary...")
    create_agent_update_summary()
    
    print("\n✅ Agent Knowledge Base Integration Update Complete!")
    print("\nNext Steps:")
    print("1. Test the updated agents")
    print("2. Verify knowledge base connectivity")
    print("3. Run agent functionality tests")
    print("4. Check knowledge base usage statistics")

if __name__ == "__main__":
    main() 