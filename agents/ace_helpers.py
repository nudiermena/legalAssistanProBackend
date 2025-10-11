"""
ACE (Agentic Context Engineering) Helper Functions
Implements helper functions for the ACE framework integration in the chatbot agent
"""

import re
from typing import List, Optional
from agents.chatbot_agent import ACEContextManager, ContextType, ContextPriority

async def generate_ace_context_from_message(
    ace_context_manager: ACEContextManager,
    message: str,
    practice_area: Optional[str],
    file_content: Optional[str]
):
    """Generate ACE context modules from the user message"""
    
    # Extract legal terms and concepts
    legal_terms = extract_legal_terms_from_message(message)
    if legal_terms:
        context_content = f"Términos legales identificados: {', '.join(legal_terms)}"
        ace_context_manager.add_context_module(
            content=context_content,
            context_type=ContextType.LEGAL_KNOWLEDGE,
            priority=ContextPriority.HIGH,
            metadata={"extracted_terms": legal_terms, "source": "user_message"}
        )
    
    # Extract user preferences and patterns
    user_preferences = extract_user_preferences_from_message(message)
    if user_preferences:
        context_content = f"Preferencias del usuario: {', '.join(user_preferences)}"
        ace_context_manager.add_context_module(
            content=context_content,
            context_type=ContextType.USER_PREFERENCES,
            priority=ContextPriority.MEDIUM,
            metadata={"preferences": user_preferences, "source": "user_message"}
        )
    
    # Add practice area context
    if practice_area:
        context_content = f"Área de práctica legal: {practice_area}"
        ace_context_manager.add_context_module(
            content=context_content,
            context_type=ContextType.LEGAL_KNOWLEDGE,
            priority=ContextPriority.HIGH,
            metadata={"practice_area": practice_area, "source": "user_input"}
        )
    
    # Add file content context if provided
    if file_content:
        context_content = f"Contenido de archivo adjunto: {file_content[:500]}..."
        ace_context_manager.add_context_module(
            content=context_content,
            context_type=ContextType.LEGAL_KNOWLEDGE,
            priority=ContextPriority.HIGH,
            metadata={"file_content": True, "source": "attached_file"}
        )

def extract_legal_terms_from_message(message: str) -> List[str]:
    """Extract legal terms from the message"""
    legal_keywords = [
        'derecho', 'ley', 'código', 'norma', 'jurídico', 'legal', 'legislación',
        'contrato', 'arrendamiento', 'trabajo', 'familia', 'comercial', 'penal',
        'constitucional', 'administrativo', 'tributario', 'civil', 'laboral',
        'demanda', 'sentencia', 'fallo', 'resolución', 'decreto', 'reglamento',
        'proceso', 'procedimiento', 'instancia', 'término', 'plazo', 'vigencia',
        'recurso', 'apelación', 'tutela', 'amparo', 'habeas corpus'
    ]
    
    found_terms = []
    message_lower = message.lower()
    
    for term in legal_keywords:
        if term in message_lower:
            found_terms.append(term)
    
    return found_terms

def extract_user_preferences_from_message(message: str) -> List[str]:
    """Extract user preferences and patterns from the message"""
    preferences = []
    
    # Check for complexity preferences
    if any(word in message.lower() for word in ['simple', 'básico', 'fácil', 'entendible']):
        preferences.append("prefiere_explicaciones_simples")
    
    if any(word in message.lower() for word in ['detallado', 'completo', 'técnico', 'específico']):
        preferences.append("prefiere_explicaciones_detalladas")
    
    # Check for format preferences
    if any(word in message.lower() for word in ['ejemplo', 'caso', 'situación']):
        preferences.append("prefiere_ejemplos_prácticos")
    
    if any(word in message.lower() for word in ['documento', 'plantilla', 'formato']):
        preferences.append("necesita_documentos")
    
    return preferences

def build_ace_context_instructions(relevant_context: List) -> str:
    """Build ACE context instructions from relevant context modules"""
    if not relevant_context:
        return ""
    
    instructions_parts = [
        "=== CONTEXTO DINÁMICO ACE (AGENTIC CONTEXT ENGINEERING) ===",
        "Utiliza el siguiente contexto evolutivo para proporcionar respuestas más precisas y personalizadas:"
    ]
    
    # Group by context type
    by_type = {}
    for module in relevant_context:
        context_type = module.context_type.value
        if context_type not in by_type:
            by_type[context_type] = []
        by_type[context_type].append(module)
    
    for context_type, modules in by_type.items():
        instructions_parts.append(f"\n**{context_type.replace('_', ' ').title()}:**")
        for module in modules[:3]:  # Show top 3 modules per type
            instructions_parts.append(f"  - {module.content[:150]}...")
        if len(modules) > 3:
            instructions_parts.append(f"  - ... y {len(modules) - 3} módulos más")
    
    instructions_parts.append("\n**Instrucciones de uso del contexto:**")
    instructions_parts.append("- Adapta tu respuesta basándote en las preferencias del usuario identificadas")
    instructions_parts.append("- Mantén coherencia con conversaciones previas y referencias legales mencionadas")
    instructions_parts.append("- Evoluciona tu comprensión del contexto del usuario con cada interacción")
    instructions_parts.append("- NO repitas textualmente el contexto, úsalo para personalizar la respuesta")
    
    return "\n".join(instructions_parts)

async def update_ace_context_from_response(
    ace_context_manager: ACEContextManager,
    message: str,
    response: str,
    practice_area: Optional[str]
):
    """Update ACE context based on the agent's response"""
    
    # Add successful interaction to conversation history
    conversation_entry = f"Usuario: {message[:100]}... | Asistente: {response[:100]}..."
    ace_context_manager.add_context_module(
        content=conversation_entry,
        context_type=ContextType.CONVERSATION_HISTORY,
        priority=ContextPriority.MEDIUM,
        metadata={"interaction_type": "successful", "practice_area": practice_area}
    )
    
    # Extract and store any legal references mentioned
    legal_references = extract_legal_references_from_response(response)
    if legal_references:
        for reference in legal_references:
            ace_context_manager.add_context_module(
                content=f"Referencia legal: {reference}",
                context_type=ContextType.LEGAL_KNOWLEDGE,
                priority=ContextPriority.HIGH,
                metadata={"reference_type": "legal_citation", "source": "agent_response"}
            )

def extract_legal_references_from_response(response: str) -> List[str]:
    """Extract legal references from the response"""
    # Pattern to match legal references like "Ley 123 de 2023", "Código Civil", etc.
    patterns = [
        r'Ley \d+ de \d{4}',
        r'Código \w+',
        r'Sentencia [A-Z]-\d+ de \d{4}',
        r'Decreto \d+ de \d{4}',
        r'Circular \d+ de \d{4}'
    ]
    
    references = []
    for pattern in patterns:
        matches = re.findall(pattern, response)
        references.extend(matches)
    
    return references
