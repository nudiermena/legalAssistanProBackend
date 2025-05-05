from typing import List, Dict, Any, Optional
from datetime import datetime

class Agent:
    def __init__(
        self,
        name: str,
        role: str,
        model: Any,
        knowledge: Any,
        search_knowledge: bool = True,
        storage: Any = None,
        instructions: List[str] = None,
        markdown: bool = False
    ):
        self.name = name
        self.role = role
        self.model = model
        self.knowledge = knowledge
        self.search_knowledge = search_knowledge
        self.storage = storage
        self.instructions = instructions or []
        self.markdown = markdown
        self.created_at = datetime.now()

    def run(self, prompt: str) -> Dict[str, Any]:
        """
        Run the agent with the given prompt
        """
        # Process the prompt using the model
        response = self.model.generate(prompt)
        
        # Search knowledge base if enabled
        if self.search_knowledge:
            knowledge_results = self.knowledge.search(prompt)
            response = self._combine_with_knowledge(response, knowledge_results)
        
        # Store the interaction if storage is configured
        if self.storage:
            self.storage.store({
                "prompt": prompt,
                "response": response,
                "timestamp": datetime.now().isoformat()
            })
        
        return {
            "content": response,
            "metadata": {
                "agent_name": self.name,
                "role": self.role,
                "timestamp": datetime.now().isoformat()
            }
        }

    def _combine_with_knowledge(self, response: str, knowledge_results: List[str]) -> str:
        """
        Combine the model response with knowledge base results
        """
        if not knowledge_results:
            return response
        
        combined = f"{response}\n\nReferencias adicionales:\n"
        for i, result in enumerate(knowledge_results, 1):
            combined += f"{i}. {result}\n"
        
        return combined 