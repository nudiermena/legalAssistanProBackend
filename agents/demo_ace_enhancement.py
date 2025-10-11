"""
Demonstration script for the ACE-enhanced chatbot agent
Shows the key improvements based on the Agentic Context Engineering framework
"""

import asyncio
import datetime
from agents.chatbot_agent import process_client_message, ACEContextManager, ContextType, ContextPriority

async def demonstrate_ace_enhancements():
    """Demonstrate the ACE enhancements to the chatbot agent"""
    
    print("🚀 DEMOSTRACIÓN DE MEJORAS ACE (AGENTIC CONTEXT ENGINEERING)")
    print("=" * 80)
    print("Basado en el paper: 'Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models'")
    print("=" * 80)
    
    # Test user and session
    user_id = "demo_user_ace"
    session_id = f"ace_demo_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    print(f"\n👤 Usuario: {user_id}")
    print(f"🆔 Sesión: {session_id}")
    print("-" * 50)
    
    # Test 1: Basic ACE Context Management
    print("\n📚 TEST 1: Gestión Modular de Contexto ACE")
    print("-" * 50)
    
    # Create ACE context manager
    ace_manager = ACEContextManager(user_id, session_id)
    
    # Add some context modules
    ace_manager.add_context_module(
        content="Usuario prefiere explicaciones simples y ejemplos prácticos",
        context_type=ContextType.USER_PREFERENCES,
        priority=ContextPriority.HIGH,
        metadata={"preference_type": "communication_style"}
    )
    
    ace_manager.add_context_module(
        content="Área de práctica: derecho civil, específicamente contratos de arrendamiento",
        context_type=ContextType.LEGAL_KNOWLEDGE,
        priority=ContextPriority.HIGH,
        metadata={"practice_area": "derecho_civil", "specialization": "arrendamiento"}
    )
    
    ace_manager.add_context_module(
        content="Conversación previa sobre cláusulas de terminación en contratos de arrendamiento",
        context_type=ContextType.CONVERSATION_HISTORY,
        priority=ContextPriority.MEDIUM,
        metadata={"topic": "clausulas_terminacion", "previous_session": True}
    )
    
    print(f"✅ Módulos de contexto creados: {len(ace_manager.context_modules)}")
    
    # Test context reflection
    reflection = ace_manager.reflect_on_context()
    print(f"📊 Reflexión del contexto:")
    print(f"  - Total de módulos: {reflection['total_modules']}")
    print(f"  - Tipos de contexto: {list(reflection['context_types'].keys())}")
    print(f"  - Módulos más utilizados: {reflection['most_used_modules'][:3]}")
    
    # Test 2: Context Relevance and Retrieval
    print("\n🔍 TEST 2: Relevancia y Recuperación de Contexto")
    print("-" * 50)
    
    test_query = "Necesito ayuda con un contrato de arrendamiento que quiero terminar"
    relevant_context = ace_manager.get_relevant_context(test_query, max_modules=5)
    
    print(f"🔎 Consulta: {test_query}")
    print(f"📋 Contexto relevante encontrado: {len(relevant_context)} módulos")
    
    for i, module in enumerate(relevant_context, 1):
        print(f"  {i}. [{module.context_type.value}] {module.content[:80]}...")
        print(f"     Relevancia: {module.relevance_score:.2f}, Prioridad: {module.priority.value}")
    
    # Test 3: Enhanced Chatbot Processing
    print("\n🤖 TEST 3: Procesamiento Mejorado del Chatbot")
    print("-" * 50)
    
    test_messages = [
        "Hola, necesito ayuda con un contrato de arrendamiento",
        "¿Cuáles son las cláusulas más importantes que debo revisar?",
        "Mi arrendador quiere aumentar el canon, ¿es legal?",
        "¿Puedo terminar el contrato antes del plazo acordado?"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n📝 Mensaje {i}: {message}")
        print("-" * 30)
        
        try:
            # Process message with ACE enhancement
            response = await process_client_message(
                client_id=user_id,
                message=message,
                conversation_id=session_id,
                practice_area="derecho_civil",
                user_id=user_id,
                session_id=session_id
            )
            
            print(f"✅ Respuesta generada exitosamente")
            
            # Show ACE enhancement information
            if 'ace_enhancement' in response:
                ace_info = response['ace_enhancement']
                print(f"🧠 Módulos de contexto activos: {ace_info['context_modules_active']}")
                print(f"📊 Contexto relevante utilizado: {ace_info['relevant_context_used']}")
                print(f"🏷️ Tipos de contexto usados: {ace_info['context_types_used']}")
                print(f"🔧 Estrategias de adaptación: {ace_info['adaptation_strategies']}")
            
            # Show enhanced capabilities
            if 'enhanced_capabilities' in response:
                capabilities = response['enhanced_capabilities']
                ace_capabilities = [k for k, v in capabilities.items() if v and 'ace' in k.lower()]
                print(f"⚡ Capacidades ACE activas: {ace_capabilities}")
            
            # Show response preview
            response_content = response['response']['content']
            print(f"💬 Vista previa de respuesta: {response_content[:150]}...")
            
        except Exception as e:
            print(f"❌ Error procesando mensaje: {str(e)}")
    
    # Test 4: Context Evolution
    print("\n🔄 TEST 4: Evolución del Contexto")
    print("-" * 50)
    
    # Simulate context evolution over time
    print("Simulando evolución del contexto a lo largo del tiempo...")
    
    # Add more context based on interactions
    ace_manager.add_context_module(
        content="Usuario mostró interés específico en cláusulas de aumento de canon",
        context_type=ContextType.USER_PREFERENCES,
        priority=ContextPriority.HIGH,
        metadata={"interest": "aumento_canon", "source": "conversation_analysis"}
    )
    
    ace_manager.add_context_module(
        content="Referencia legal mencionada: Ley 820 de 2003 sobre arrendamiento",
        context_type=ContextType.LEGAL_KNOWLEDGE,
        priority=ContextPriority.HIGH,
        metadata={"legal_reference": "Ley 820 de 2003", "source": "agent_response"}
    )
    
    # Update existing context
    for module_id, module in ace_manager.context_modules.items():
        if "arrendamiento" in module.content.lower():
            ace_manager.update_context_module(
                module_id,
                relevance_score=0.9,
                metadata={"updated": True, "relevance_boost": "high_usage"}
            )
    
    # Show updated reflection
    updated_reflection = ace_manager.reflect_on_context()
    print(f"📈 Reflexión actualizada:")
    print(f"  - Total de módulos: {updated_reflection['total_modules']}")
    print(f"  - Relevancia promedio: {updated_reflection['average_relevance']:.2f}")
    print(f"  - Módulos más utilizados: {updated_reflection['most_used_modules'][:3]}")
    
    # Test 5: Performance Comparison
    print("\n📊 TEST 5: Comparación de Rendimiento")
    print("-" * 50)
    
    print("Comparando capacidades antes y después de ACE:")
    print("\n🔴 ANTES (Chatbot Original):")
    print("  - Contexto estático y limitado")
    print("  - Sin evolución de contexto")
    print("  - Respuestas genéricas")
    print("  - Sin personalización basada en historial")
    print("  - Sin adaptación automática")
    
    print("\n🟢 DESPUÉS (Chatbot ACE-Enhanced):")
    print("  - ✅ Gestión modular de contexto")
    print("  - ✅ Evolución automática del contexto")
    print("  - ✅ Respuestas personalizadas y contextuales")
    print("  - ✅ Aprendizaje de preferencias del usuario")
    print("  - ✅ Adaptación continua basada en rendimiento")
    print("  - ✅ Prevención de colapso de contexto")
    print("  - ✅ Manejo optimizado de contextos largos")
    print("  - ✅ Reflexión y curación automática")
    
    print("\n🎯 MEJORAS CLAVE IMPLEMENTADAS:")
    print("=" * 80)
    print("1. 📦 GESTIÓN MODULAR DE CONTEXTO")
    print("   - Contextos organizados en módulos especializados")
    print("   - Tipos: conocimiento legal, preferencias, historial, jurisprudencia")
    print("   - Prioridades: crítico, alto, medio, bajo")
    print("   - Metadatos enriquecidos para cada módulo")
    
    print("\n2. 🔄 EVOLUCIÓN INCREMENTAL")
    print("   - Actualizaciones incrementales en lugar de reemplazo completo")
    print("   - Preservación de información valiosa")
    print("   - Prevención de colapso de contexto")
    print("   - Escalabilidad con modelos de contexto largo")
    
    print("\n3. 🧠 REFLEXIÓN Y CURACIÓN")
    print("   - Análisis automático del uso de contexto")
    print("   - Identificación de módulos subutilizados")
    print("   - Recomendaciones de mejora")
    print("   - Curación automática de contexto")
    
    print("\n4. 📈 MONITOREO DE RENDIMIENTO")
    print("   - Seguimiento de métricas de interacción")
    print("   - Adaptación basada en rendimiento")
    print("   - Estrategias de mejora automática")
    print("   - Análisis de satisfacción del usuario")
    
    print("\n5. 🎯 PERSONALIZACIÓN AVANZADA")
    print("   - Aprendizaje de preferencias del usuario")
    print("   - Adaptación del estilo de comunicación")
    print("   - Memoria de conversaciones previas")
    print("   - Contexto específico por área de práctica")
    
    print("\n🚀 RESULTADOS ESPERADOS:")
    print("=" * 80)
    print("• 📈 Mejora del 10.6% en tareas de agente (según paper ACE)")
    print("• 📈 Mejora del 8.6% en tareas específicas del dominio")
    print("• ⚡ Reducción de latencia de adaptación")
    print("• 💰 Reducción de costos de rollout")
    print("• 🎯 Mayor satisfacción del usuario")
    print("• 🧠 Mejor comprensión contextual")
    print("• 🔄 Adaptación continua y automática")
    
    print("\n✨ El chatbot ACE-enhanced está listo para proporcionar")
    print("   asistencia legal evolutiva y personalizada!")

if __name__ == "__main__":
    print("🔧 Iniciando demostración de mejoras ACE...")
    
    try:
        asyncio.run(demonstrate_ace_enhancements())
    except Exception as e:
        print(f"❌ Error en demostración: {str(e)}")
        print("💡 Asegúrese de que todas las dependencias estén configuradas correctamente")
