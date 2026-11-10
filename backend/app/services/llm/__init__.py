"""JobShield AI — LLM Services Package."""

from backend.app.services.llm.explanation_service import (
    generate_deterministic_fallback_explanation,
    generate_grounded_explanation,
)
from backend.app.services.llm.groq_provider import GroqLLMProvider
from backend.app.services.llm.prompt_builder import build_explanation_prompt
from backend.app.services.llm.provider import LLMProvider

__all__ = [
    "LLMProvider",
    "GroqLLMProvider",
    "build_explanation_prompt",
    "generate_grounded_explanation",
    "generate_deterministic_fallback_explanation",
]

