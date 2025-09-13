#!/usr/bin/env python3
"""
Test Knowledge Base Integration for All Agents
This script tests that all agents are properly integrated with the Supabase knowledge base
"""

import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.contract_agent import analyze_contract
from agents.legal_research_agent import conduct_legal_research
from agents.patent_agent import analyze_patent
from agents.case_prediction_agent import predict_case_outcome
from agents.compliance_agent import analyze_regulatory_change, assess_compliance_status
from agents.document_drafting_agent import draft_custom_document
from config.knowledge_base_integration import create_agent_knowledge_integration, AgentKnowledgeHelper

class KnowledgeBaseIntegrationTester:
    """Test knowledge base integration for all agents"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = datetime.now()
    
    async def test_knowledge_base_connectivity(self):
        """Test basic knowledge base connectivity"""
        print("🔍 Testing Knowledge Base Connectivity...")
        
        try:
            # Test basic knowledge base creation
            kb = create_agent_knowledge_integration("contract_agent")
            
            # Test search functionality
            results = await kb.search_knowledge("habeas data", limit=3)
            
            if results and results.get("results"):
                print("✅ Knowledge base connectivity: SUCCESS")
                print(f"   Found {len(results['results'])} results for 'habeas data'")
                return True
            else:
                print("❌ Knowledge base connectivity: FAILED - No results found")
                return False
                
        except Exception as e:
            print(f"❌ Knowledge base connectivity: FAILED - {e}")
            return False
    
    async def test_contract_agent(self):
        """Test contract agent knowledge base integration"""
        print("\n📋 Testing Contract Agent...")
        
        try:
            result = await analyze_contract(
                contract_text="""
                CONTRATO DE ARRENDAMIENTO
                Entre los suscritos, por una parte:
                [NOMBRE DEL ARRENDADOR], mayor de edad, identificado con cédula de ciudadanía No. [NÚMERO], 
                domiciliado en [DIRECCIÓN], a quien en adelante se le denominará "EL ARRENDADOR";
                
                Y por la otra parte:
                [NOMBRE DEL ARRENDATARIO], mayor de edad, identificado con cédula de ciudadanía No. [NÚMERO], 
                domiciliado en [DIRECCIÓN], a quien en adelante se le denominará "EL ARRENDATARIO";
                
                Se celebra el presente contrato de arrendamiento bajo las siguientes cláusulas:
                
                PRIMERA: OBJETO. El arrendador cede en arrendamiento al arrendatario el inmueble ubicado en [DIRECCIÓN COMPLETA], 
                por el término de [DURACIÓN] meses, a partir del [FECHA DE INICIO].
                
                SEGUNDA: CANON DE ARRENDAMIENTO. El canon mensual será de $[MONTO] ([MONTO EN LETRAS]), 
                pagadero por anticipado dentro de los primeros cinco días de cada mes.
                """,
                contract_type="arrendamiento",
                parties=["Arrendador", "Arrendatario"],
                specific_concerns=["confidencialidad", "terminación"]
            )
            
            # Check for knowledge base usage
            if "knowledge_base_usage" in result:
                kb_usage = result["knowledge_base_usage"]
                print("✅ Contract Agent: SUCCESS")
                print(f"   Legal terms found: {kb_usage.get('legal_terms_found', 0)}")
                print(f"   Contract clauses found: {kb_usage.get('contract_clauses_referenced', 0)}")
                print(f"   Jurisprudence found: {kb_usage.get('jurisprudence_cited', 0)}")
                return True
            else:
                print("❌ Contract Agent: FAILED - No knowledge base usage data")
                return False
                
        except Exception as e:
            print(f"❌ Contract Agent: FAILED - {e}")
            return False
    
    async def test_legal_research_agent(self):
        """Test legal research agent knowledge base integration"""
        print("\n🔬 Testing Legal Research Agent...")
        
        try:
            result = await conduct_legal_research(
                research_topic="protección de datos personales",
                jurisdiction="Colombia",
                specific_areas=["habeas data", "consentimiento"],
                timeframe="2020-2024"
            )
            
            # Check for knowledge base usage
            if "knowledge_base_usage" in result:
                kb_usage = result["knowledge_base_usage"]
                print("✅ Legal Research Agent: SUCCESS")
                print(f"   Legal terms found: {kb_usage.get('legal_terms_found', 0)}")
                print(f"   Jurisprudence found: {kb_usage.get('jurisprudence_found', 0)}")
                print(f"   Legal documents found: {kb_usage.get('legal_documents_found', 0)}")
                return True
            else:
                print("❌ Legal Research Agent: FAILED - No knowledge base usage data")
                return False
                
        except Exception as e:
            print(f"❌ Legal Research Agent: FAILED - {e}")
            return False
    
    async def test_patent_agent(self):
        """Test patent agent knowledge base integration"""
        print("\n📜 Testing Patent Agent...")
        
        try:
            result = await analyze_patent(
                patent_text="""
                INVENCIÓN: Sistema de gestión de datos personales
                
                DESCRIPCIÓN: La presente invención se refiere a un sistema informático para la gestión 
                segura de datos personales conforme a la normativa colombiana de protección de datos.
                
                RECLAMACIONES:
                1. Un sistema de gestión de datos personales que comprende:
                   - Módulo de autorización de tratamiento
                   - Módulo de almacenamiento seguro
                   - Módulo de derechos del titular
                   - Módulo de auditoría y trazabilidad
                """,
                patent_type="invention",
                jurisdiction="Colombia",
                technical_field="tecnología de la información"
            )
            
            # Check for knowledge base usage
            if "knowledge_base_usage" in result:
                kb_usage = result["knowledge_base_usage"]
                print("✅ Patent Agent: SUCCESS")
                print(f"   Patent knowledge found: {kb_usage.get('patent_knowledge_found', 0)}")
                print(f"   Legal terms found: {kb_usage.get('legal_terms_found', 0)}")
                print(f"   Jurisprudence found: {kb_usage.get('jurisprudence_found', 0)}")
                return True
            else:
                print("❌ Patent Agent: FAILED - No knowledge base usage data")
                return False
                
        except Exception as e:
            print(f"❌ Patent Agent: FAILED - {e}")
            return False
    
    async def test_case_prediction_agent(self):
        """Test case prediction agent knowledge base integration"""
        print("\n🎯 Testing Case Prediction Agent...")
        
        try:
            result = await predict_case_outcome(
                case_type="proceso_laboral",
                jurisdiction="Colombia",
                key_facts=[
                    "Despido sin justa causa",
                    "Falta de preaviso",
                    "No pago de prestaciones sociales"
                ],
                legal_issues=[
                    "Estabilidad laboral reforzada",
                    "Indemnización por despido",
                    "Prestaciones sociales"
                ],
                judge_name="Juez Laboral",
                opposing_counsel="Abogado de la empresa"
            )
            
            # Check for knowledge base usage
            if "knowledge_base_usage" in result:
                kb_usage = result["knowledge_base_usage"]
                print("✅ Case Prediction Agent: SUCCESS")
                print(f"   Case knowledge found: {kb_usage.get('case_knowledge_found', 0)}")
                print(f"   Jurisprudence found: {kb_usage.get('jurisprudence_found', 0)}")
                print(f"   Legal terms found: {kb_usage.get('legal_terms_found', 0)}")
                return True
            else:
                print("❌ Case Prediction Agent: FAILED - No knowledge base usage data")
                return False
                
        except Exception as e:
            print(f"❌ Case Prediction Agent: FAILED - {e}")
            return False
    
    async def test_compliance_agent(self):
        """Test compliance agent knowledge base integration"""
        print("\n📊 Testing Compliance Agent...")
        
        try:
            result = await analyze_regulatory_change(
                regulation_text="""
                NUEVA REGULACIÓN: Circular Única SIC sobre Protección de Datos Personales
                
                La Superintendencia de Industria y Comercio establece nuevos requisitos para el 
                tratamiento de datos personales en el sector financiero, incluyendo medidas de 
                seguridad adicionales y procedimientos de autorización más estrictos.
                """,
                effective_date="2024-01-01",
                industry="financiero",
                business_operations=["préstamos", "inversiones", "seguros"],
                current_compliance_status={
                    "política_datos": "implementada",
                    "autorizaciones": "pendiente",
                    "medidas_seguridad": "básicas"
                }
            )
            
            # Check for knowledge base usage
            if "knowledge_base_usage" in result:
                kb_usage = result["knowledge_base_usage"]
                print("✅ Compliance Agent: SUCCESS")
                print(f"   Compliance knowledge found: {kb_usage.get('compliance_knowledge_found', 0)}")
                print(f"   Regulatory frameworks found: {kb_usage.get('regulatory_frameworks_found', 0)}")
                print(f"   Legal terms found: {kb_usage.get('legal_terms_found', 0)}")
                return True
            else:
                print("❌ Compliance Agent: FAILED - No knowledge base usage data")
                return False
                
        except Exception as e:
            print(f"❌ Compliance Agent: FAILED - {e}")
            return False
    
    async def test_document_drafting_agent(self):
        """Test document drafting agent knowledge base integration"""
        print("\n📝 Testing Document Drafting Agent...")
        
        try:
            result = await draft_custom_document(
                document_type="contrato de confidencialidad",
                description="Contrato de confidencialidad para empleados de empresa tecnológica",
                parties=[
                    {"name": "Empresa ABC S.A.S.", "identification": "900123456-7", "role": "Revelador"},
                    {"name": "Juan Pérez", "identification": "12345678", "role": "Receptor"}
                ],
                key_points=[
                    "Protección de información confidencial",
                    "Duración de la obligación",
                    "Medidas de seguridad",
                    "Sanciones por incumplimiento"
                ],
                industry="technology",
                jurisdiction="Colombia",
                complexity="standard"
            )
            
            # Check for knowledge base usage
            if "knowledge_base_usage" in result:
                kb_usage = result["knowledge_base_usage"]
                print("✅ Document Drafting Agent: SUCCESS")
                print(f"   Document templates found: {kb_usage.get('document_templates_found', 0)}")
                print(f"   Legal terms found: {kb_usage.get('legal_terms_found', 0)}")
                print(f"   Legal documents found: {kb_usage.get('legal_documents_found', 0)}")
                return True
            else:
                print("❌ Document Drafting Agent: FAILED - No knowledge base usage data")
                return False
                
        except Exception as e:
            print(f"❌ Document Drafting Agent: FAILED - {e}")
            return False
    
    async def test_agent_knowledge_helper(self):
        """Test AgentKnowledgeHelper functionality"""
        print("\n🛠️ Testing AgentKnowledgeHelper...")
        
        try:
            helper = AgentKnowledgeHelper("contract_agent")
            
            # Test legal terms extraction
            terms = helper._extract_potential_terms("contrato de arrendamiento con cláusula de confidencialidad")
            if terms:
                print(f"✅ Legal terms extraction: SUCCESS - Found {len(terms)} terms")
            else:
                print("❌ Legal terms extraction: FAILED - No terms found")
                return False
            
            # Test legal definitions lookup
            definitions = await helper.get_relevant_legal_terms("habeas data due process")
            if definitions:
                print(f"✅ Legal definitions lookup: SUCCESS - Found {len(definitions)} definitions")
            else:
                print("❌ Legal definitions lookup: FAILED - No definitions found")
                return False
            
            # Test prompt enhancement
            enhanced_prompt = await helper.enhance_prompt_with_knowledge(
                "Analizar el siguiente contrato de arrendamiento"
            )
            if "KNOWLEDGE CONTEXT" in enhanced_prompt:
                print("✅ Prompt enhancement: SUCCESS")
            else:
                print("❌ Prompt enhancement: FAILED")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ AgentKnowledgeHelper: FAILED - {e}")
            return False
    
    async def run_all_tests(self):
        """Run all knowledge base integration tests"""
        print("🚀 Starting Knowledge Base Integration Tests")
        print("=" * 60)
        
        tests = [
            ("Knowledge Base Connectivity", self.test_knowledge_base_connectivity),
            ("Contract Agent", self.test_contract_agent),
            ("Legal Research Agent", self.test_legal_research_agent),
            ("Patent Agent", self.test_patent_agent),
            ("Case Prediction Agent", self.test_case_prediction_agent),
            ("Compliance Agent", self.test_compliance_agent),
            ("Document Drafting Agent", self.test_document_drafting_agent),
            ("AgentKnowledgeHelper", self.test_agent_knowledge_helper)
        ]
        
        results = {}
        total_tests = len(tests)
        passed_tests = 0
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results[test_name] = result
                if result:
                    passed_tests += 1
            except Exception as e:
                print(f"❌ {test_name}: FAILED - {e}")
                results[test_name] = False
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name}: {status}")
        
        print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All tests passed! Knowledge base integration is working correctly.")
        else:
            print("⚠️ Some tests failed. Please check the knowledge base configuration.")
        
        # Save results
        self.save_test_results(results, passed_tests, total_tests)
        
        return passed_tests == total_tests
    
    def save_test_results(self, results, passed_tests, total_tests):
        """Save test results to file"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        report = f"""
# KNOWLEDGE BASE INTEGRATION TEST REPORT

## Test Summary
- **Date**: {end_time.strftime('%Y-%m-%d %H:%M:%S')}
- **Duration**: {duration.total_seconds():.2f} seconds
- **Total Tests**: {total_tests}
- **Passed**: {passed_tests}
- **Failed**: {total_tests - passed_tests}
- **Success Rate**: {(passed_tests/total_tests)*100:.1f}%

## Test Results

"""
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            report += f"- {test_name}: {status}\n"
        
        report += f"""
## Recommendations

"""
        
        if passed_tests == total_tests:
            report += """
✅ All tests passed successfully! The knowledge base integration is working correctly.

### Next Steps:
1. Deploy to production environment
2. Monitor knowledge base usage
3. Add more legal knowledge to the base
4. Optimize search queries based on usage patterns
"""
        else:
            report += """
⚠️ Some tests failed. Please check:

1. **Environment Variables**: Ensure SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, and MISTRAL_API_KEY are set
2. **Knowledge Base Schema**: Verify the database schema is deployed in Supabase
3. **Knowledge Base Population**: Ensure the knowledge base is populated with data
4. **Network Connectivity**: Check if the application can reach Supabase
5. **API Limits**: Verify Mistral API key has sufficient credits

### Debugging Steps:
1. Check the knowledge base connectivity test first
2. Verify Supabase project is active and accessible
3. Test individual agent functions
4. Check logs for specific error messages
"""
        
        with open('knowledge_base_test_report.md', 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n📄 Test report saved to: knowledge_base_test_report.md")

async def main():
    """Main function to run all tests"""
    tester = KnowledgeBaseIntegrationTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎉 All knowledge base integration tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the configuration.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 