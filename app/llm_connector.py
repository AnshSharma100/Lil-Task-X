"""Connector for NVIDIA NIM or local Nemotron endpoints."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
import re
from typing import Any, Dict, Optional

import requests

from .utils import ensure_env_loaded

DEFAULT_REMOTE_ENDPOINT = "https://integrate.api.nvidia.com/v1"
DEFAULT_LOCAL_ENDPOINT = "http://localhost:8000/v1"
DEFAULT_MODEL = "nvidia/nemotron-nano-12b-v2-vl"


@dataclass(slots=True)
class LLMEvaluationResult:
    score: Optional[float]
    summary: Optional[str]


class NemotronClient:
    """Lightweight client for the Nemotron OpenAI-compatible endpoint."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 60,
        api_key: Optional[str] = None,
    ) -> None:
        ensure_env_loaded()
        resolved_key = api_key or os.getenv("NIM_API_KEY") or os.getenv("NVIDIA_API_KEY")
        env_base_url = os.getenv("NIM_BASE_URL")

        if base_url:
            resolved_base = base_url
        elif env_base_url:
            resolved_base = env_base_url
        elif resolved_key:
            resolved_base = DEFAULT_REMOTE_ENDPOINT
        else:
            resolved_base = DEFAULT_LOCAL_ENDPOINT

        self.base_url = resolved_base.rstrip("/")
        self.model = model or os.getenv("NIM_MODEL") or DEFAULT_MODEL
        self.timeout = timeout
        self.api_key = resolved_key
        if self.base_url.startswith(DEFAULT_REMOTE_ENDPOINT) and not self.api_key:
            raise ValueError(
                "NIM_API_KEY (or NVIDIA_API_KEY) is required for the hosted NVIDIA endpoint."
            )

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
            "temperature": 0.2,
            "top_p": 0.95,
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self._make_headers(),
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

    def evaluate_feature_match(
        self,
        feature: Dict[str, Any],
        file_path: str,
        code_snippet: str,
    ) -> LLMEvaluationResult:
        """Use Nemotron to score how strongly the code matches the feature requirements."""
        feature_name = feature.get("name") or feature.get("feature_name") or "Unnamed Feature"
        description = feature.get("description") or ""
        tags = feature.get("tags") or []

        system_prompt = (
            "You evaluate whether a code snippet implements a feature. "
            "Respond with JSON containing `score` (0.0 to 1.0) and `summary` explaining the rationale."
            " Score 1.0 means the code fully delivers the feature; 0.0 means it is unrelated."
        )

        tag_line = ", ".join(map(str, tags)) if tags else "(none)"
        user_content = (
            f"Feature Name: {feature_name}\n"
            f"Feature Description: {description}\n"
            f"Feature Labels/Tags: {tag_line}\n"
            f"Repository File Path: {file_path}\n"
            "Provide your JSON response after reviewing the following code snippet:\n"
            "```\n"
            f"{code_snippet}\n"
            "```"
        )

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.1,
            "top_p": 0.9,
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self._make_headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException:
            return LLMEvaluationResult(score=None, summary=None)

        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            return LLMEvaluationResult(score=None, summary=None)

        message = choices[0].get("message")
        if not isinstance(message, dict):
            return LLMEvaluationResult(score=None, summary=None)

        content = message.get("content", "")
        parsed = _parse_llm_json(content)
        if parsed is None:
            return LLMEvaluationResult(score=None, summary=None)

        score = parsed.get("score")
        summary = parsed.get("summary")
        try:
            score_value = float(score) if score is not None else None
        except (TypeError, ValueError):
            score_value = None

        return LLMEvaluationResult(score=score_value, summary=summary if isinstance(summary, str) else None)

    def _make_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers


def _parse_llm_json(response_text: str) -> Optional[Dict[str, Any]]:
    candidate = response_text.strip()

    match = re.search(r"```(?:json)?\s*(.*?)\s*```", candidate, flags=re.DOTALL | re.IGNORECASE)
    if match:
        candidate = match.group(1)

    candidate = candidate.strip()

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None
