"""Connector for Nemotron served via vLLM."""
from __future__ import annotations

from typing import Any, Dict, Optional

import requests

DEFAULT_ENDPOINT = "http://localhost:8000/v1"
DEFAULT_MODEL = "nvidia/NVIDIA-Nemotron-Nano-9B-v2"


class NemotronClient:
    """Lightweight client for the Nemotron OpenAI-compatible endpoint."""

    def __init__(self, base_url: str = DEFAULT_ENDPOINT, model: str = DEFAULT_MODEL, timeout: int = 60) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def analyze_feature_with_llm(self, feature_name: str, code_snippet: str) -> Optional[str]:
        """Ask the LLM how the code snippet supports a given feature."""
        prompt = (
            "You are helping map features to code. "
            "Explain in concise bullet points how the provided code relates to the feature."
        )
        user_content = (
            f"Feature: {feature_name}\n"
            f"Code Snippet:\n{code_snippet}\n"
        )

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_content},
            ],
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException:
            return None

        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            return None
        message = choices[0].get("message")
        return message.get("content") if isinstance(message, dict) else None
