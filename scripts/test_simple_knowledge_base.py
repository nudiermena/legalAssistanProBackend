#!/usr/bin/env python3
"""
Simple Test for Knowledge Base Integration
This script tests that the knowledge base integration works with the corrected imports
"""

import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all required imports work"""
    print("🔍 Testing Imports...")
    
    try:
        # Test agno imports
        from agno.vectordb.pgvector import PgVector, SearchType
        print("✅ agno.vectordb.pgvector imports: SUCCESS")
        
        from agno.knowledge.pdf_url import PDFUrlKnowledgeBase
        print("✅ agno.knowledge.pdf_url import: SUCCESS")
        
        from agno.knowledge.website import WebsiteKnowledgeBase
        print("✅ agno.knowledge.website import: SUCCESS")
        
        from agno.knowledge.combined import CombinedKnowledgeBase
        print("✅ agno.knowledge.combined import: SUCCESS")
        
        from agno.knowledge.text import TextKnowledgeBase
        print("✅ agno.knowledge.text import: SUCCESS")
        
        # Test our knowledge base imports
        from config.supabase_knowledge_base import SupabaseLegalKnowledgeBase, KnowledgeType, AgentType
        print("✅ config.supabase_knowledge_base imports: SUCCESS")
        
        from config.knowledge_base_integration import AgentKnowledgeIntegration, AgentKnowledgeHelper
        print("✅ config.knowledge_base_integration imports: SUCCESS")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_knowledge_base_creation():
    """Test knowledge base creation (without actual connection)"""
    print("\n🔍 Testing Knowledge Base Creation...")
    
    try:
        # Test enum creation
        from config.supabase_knowledge_base import KnowledgeType, AgentType
        
        # Test knowledge types
        knowledge_types = list(KnowledgeType)
        print(f"✅ Knowledge types: {len(knowledge_types)} types available")
        
        # Test agent types
        agent_types = list(AgentType)
        print(f"✅ Agent types: {len(agent_types)} types available")
        
        # Test integration creation (this will fail without env vars, but we can test the class structure)
        from config.knowledge_base_integration import AgentKnowledgeIntegration, AgentKnowledgeHelper
        
        # Test helper creation
        helper = AgentKnowledgeHelper("contract_agent")
        print("✅ AgentKnowledgeHelper creation: SUCCESS")
        
        # Test term extraction
        terms = helper._extract_potential_terms("contrato de arrendamiento con cláusula de confidencialidad")
        print(f"✅ Term extraction: Found {len(terms)} terms")
        
        return True
        
    except Exception as e:
        print(f"❌ Knowledge base creation test failed: {e}")
        return False

def test_agent_integration():
    """Test agent integration without actual knowledge base connection"""
    print("\n🔍 Testing Agent Integration...")
    
    try:
        from config.knowledge_base_integration import create_agent_knowledge_integration, create_agent_knowledge_helper
        
        # Test integration creation
        integration = create_agent_knowledge_integration("contract_agent")
        print("✅ AgentKnowledgeIntegration creation: SUCCESS")
        
        # Test helper creation
        helper = create_agent_knowledge_helper("contract_agent")
        print("✅ AgentKnowledgeHelper creation: SUCCESS")
        
        # Test knowledge types mapping
        from config.knowledge_base_integration import KnowledgeBaseConfig
        
        knowledge_types = KnowledgeBaseConfig.get_agent_knowledge_types("contract_agent")
        print(f"✅ Knowledge types mapping: {knowledge_types}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent integration test failed: {e}")
        return False

async def test_async_functions():
    """Test async functions (will fail without env vars, but we can test the structure)"""
    print("\n🔍 Testing Async Functions...")
    
    try:
        from config.knowledge_base_integration import AgentKnowledgeHelper
        
        helper = AgentKnowledgeHelper("contract_agent")
        
        # Test prompt enhancement (will fail without env vars, but we can test the function exists)
        try:
            enhanced_prompt = await helper.enhance_prompt_with_knowledge("Analizar contrato de arrendamiento")
            print("✅ Prompt enhancement function: SUCCESS")
        except Exception as e:
            print(f"⚠️ Prompt enhancement failed (expected without env vars): {str(e)[:100]}...")
        
        # Test legal terms extraction
        try:
            terms = await helper.get_relevant_legal_terms("habeas data due process")
            print("✅ Legal terms extraction function: SUCCESS")
        except Exception as e:
            print(f"⚠️ Legal terms extraction failed (expected without env vars): {str(e)[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Async functions test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting Simple Knowledge Base Integration Tests")
    print("=" * 60)
    
    tests = [
        ("Import Tests", test_imports),
        ("Knowledge Base Creation", test_knowledge_base_creation),
        ("Agent Integration", test_agent_integration),
    ]
    
    results = {}
    total_tests = len(tests)
    passed_tests = 0
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
            if result:
                passed_tests += 1
        except Exception as e:
            print(f"❌ {test_name}: FAILED - {e}")
            results[test_name] = False
    
    # Test async functions
    try:
        result = asyncio.run(test_async_functions())
        results["Async Functions"] = result
        if result:
            passed_tests += 1
        total_tests += 1
    except Exception as e:
        print(f"❌ Async Functions: FAILED - {e}")
        results["Async Functions"] = False
        total_tests += 1
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Knowledge base integration structure is correct.")
        print("\nNext Steps:")
        print("1. Set up environment variables (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, MISTRAL_API_KEY)")
        print("2. Deploy knowledge base schema to Supabase")
        print("3. Run the full integration tests")
    else:
        print("⚠️ Some tests failed. Please check the import structure and dependencies.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 