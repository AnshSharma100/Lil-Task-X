"""Deprecated NVIDIA helper kept for backwards compatibility import paths."""

from __future__ import annotations


class NvidiaAPIError(RuntimeError):
    """Raised when legacy NVIDIA utilities are invoked."""


def call_nvidia(*args, **kwargs):  # type: ignore[missing-return-type]
    raise NvidiaAPIError(
        "NVIDIA/NIM support has been removed. Switch to the Gemini + LangChain flow in src/agents/pm_agent.py."
    )
