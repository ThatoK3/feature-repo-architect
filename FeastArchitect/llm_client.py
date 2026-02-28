"""
Simplified Groq LLM Client for Feast Architect
"""
import os
import json
from typing import Dict, Optional
from dataclasses import dataclass, asdict




# Not secured - but since this is a dummy project...
GROQ_API_KEY ='xxxx'
# Ensure it's in environment
os.environ['GROQ_API_KEY'] = GROQ_API_KEY


try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


@dataclass
class LLMContext:
    """Context about the repository for LLM queries."""
    repo_name: str = "Unknown"
    node_count: int = 0
    edge_count: int = 0
    data_sources: int = 0
    entities: int = 0
    feature_views: int = 0
    services: int = 0
    
    def to_dict(self) -> Dict:
        return asdict(self)


class GroqLLMClient:
    """Simple Groq API client."""
    
    DEFAULT_MODEL = "llama-3.3-70b-versatile"
    
    SYSTEM_PROMPTS = {
        "default": "You are a Feast feature store expert. Provide concise, actionable advice.",
        "generate_code": "You are a Feast code generation expert. Output valid Python code.",
        "optimize": "You are a Feast performance expert. Focus on TTL, materialization, and serving.",
        "lineage": "You are a data lineage expert. Trace data flow from source to service.",
        "validate": "You are a Feast validator. Check for errors and anti-patterns."
    }
    
    def __init__(self, api_key: Optional[str] = None):
        if not GROQ_AVAILABLE:
            raise RuntimeError("Install groq: pip install groq")
        
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise RuntimeError("Set GROQ_API_KEY environment variable")
        
        self.client = Groq(api_key=self.api_key)
    
    def query(
        self,
        message: str,
        context: Optional[LLMContext] = None,
        query_type: str = "default",
        stream: bool = False
    ) -> Dict:
        """Send query to Groq API."""
        
        # Build system prompt
        system = self.SYSTEM_PROMPTS.get(query_type, self.SYSTEM_PROMPTS["default"])
        if context:
            system += f"\n\nRepository: {context.repo_name} ({context.node_count} nodes, {context.edge_count} edges)"
        
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": message}
        ]
        
        completion = self.client.chat.completions.create(
            model=self.DEFAULT_MODEL,
            messages=messages,
            temperature=0.7,
            max_completion_tokens=2048,
            stream=stream
        )
        
        if stream:
            return completion  # Generator
        
        return {
            "response": completion.choices[0].message.content,
            "model": self.DEFAULT_MODEL,
            "usage": {
                "prompt_tokens": completion.usage.prompt_tokens if completion.usage else 0,
                "completion_tokens": completion.usage.completion_tokens if completion.usage else 0,
                "total_tokens": completion.usage.total_tokens if completion.usage else 0
            },
            "query_type": query_type
        }
    
    def quick_query(self, message: str) -> str:
        """Simple query returning just text."""
        return self.query(message, stream=False)["response"]


# Singleton instance
_llm_client = None

def get_llm_client():
    """Get or create singleton client."""
    global _llm_client
    if _llm_client is None:
        _llm_client = GroqLLMClient()
    return _llm_client
