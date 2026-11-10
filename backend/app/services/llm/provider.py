"""JobShield AI — Abstract LLM Provider Interface.

Defines the contract for pluggable LLM inference providers (Groq, OpenAI, Ollama, etc.).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class LLMProvider(ABC):
    """Abstract provider interface for structured chat completions."""

    @abstractmethod
    def generate_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        timeout_seconds: int = 30,
        response_format: str = "json_object",
    ) -> str:
        """Execute chat completion and return response string content."""
        pass

