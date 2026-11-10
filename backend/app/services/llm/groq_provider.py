"""JobShield AI — Groq Cloud LLM Provider.

Integrates with Groq's high-speed inference API (Llama 3.3 / Llama 3.1) or any
OpenAI-compatible chat completion endpoint.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

import httpx

from backend.app.core.config import settings
from backend.app.services.llm.provider import LLMProvider

logger = logging.getLogger("jobshield.llm.groq")


class GroqLLMProvider(LLMProvider):
    """Groq Cloud API provider implementation."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: str = "https://api.groq.com/openai/v1",
    ):
        self.api_key = api_key or settings.LLM_API_KEY
        self.model = model or settings.LLM_MODEL or "llama-3.3-70b-versatile"
        self.base_url = base_url.rstrip("/")

    @property
    def is_available(self) -> bool:
        """Check if an API key is configured."""
        return bool(self.api_key and self.api_key.strip() and self.api_key != "your_groq_api_key_here")

    def generate_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        timeout_seconds: int = 30,
        response_format: str = "json_object",
    ) -> str:
        """Execute chat completion and return response text."""
        if not self.is_available:
            raise ValueError("Groq API key is not configured or empty.")

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 2048,
        }

        if response_format == "json_object":
            payload["response_format"] = {"type": "json_object"}

        with httpx.Client(timeout=float(timeout_seconds)) as client:
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                logger.error(f"Groq API error {resp.status_code}: {resp.text}")
                resp.raise_for_status()

            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                raise ValueError("Groq API returned an empty choices array.")

            return choices[0]["message"]["content"]

