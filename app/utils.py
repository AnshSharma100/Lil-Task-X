"""Utility helpers for Lil Task X."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
_CLONE_ROOT = Path(tempfile.gettempdir()) / "lil_task_x" / "repos"


def ensure_directories() -> None:
    """Ensure local temp directories exist for cloning."""
    _CLONE_ROOT.mkdir(parents=True, exist_ok=True)


def get_clone_root() -> Path:
    """Return the base path that hosts temporary cloned repositories."""
    ensure_directories()
    return _CLONE_ROOT


def ensure_env_loaded() -> None:
    """Load variables from .env once."""
    # Feature 5 story — centralise .env handling for deployment and ops consistency.
    if os.getenv("_LIL_TASK_ENV_LOADED"):
        return

    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    os.environ["_LIL_TASK_ENV_LOADED"] = "1"


def get_github_token() -> str | None:
    """Return the GitHub token if present, confirming once."""
    ensure_env_loaded()
    token = os.getenv("GITHUB_TOKEN")
    if token and not os.getenv("_LIL_TASK_TOKEN_CONFIRMED"):
        print("✅ GitHub token loaded")
        os.environ["_LIL_TASK_TOKEN_CONFIRMED"] = "1"
    return token
def read_features(path: Path | None = None) -> List[Dict[str, Any]]:
    """Load features from the JSON file if available."""
    if path is None:
        path = PROJECT_ROOT / "features.json"

    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as handle:
        data: Any = json.load(handle)

    return list(_extract_features(data))


def _extract_features(node: Any) -> Iterable[Dict[str, Any]]:
    if isinstance(node, dict):
        if "feature_name" in node or (
            "name" in node and ("description" in node or "stories" in node or "tags" in node)
        ):
            yield _normalise_feature_block(node)
        else:
            for value in node.values():
                yield from _extract_features(value)
    elif isinstance(node, list):
        for item in node:
            yield from _extract_features(item)
    else:
        return


def _normalise_feature_block(entry: Dict[str, Any]) -> Dict[str, Any]:
    name = entry.get("feature_name") or entry.get("name") or "Unnamed Feature"
    description = entry.get("description") or _first_story_summary(entry.get("stories"))
    tags = _collect_labels(entry.get("stories"))
    if not tags and entry.get("labels"):
        tags = list({str(label) for label in entry.get("labels", [])})

    return {
        "name": name,
        "description": description or "",
        "tags": tags,
    }


def _first_story_summary(stories: Any) -> str:
    if isinstance(stories, list):
        for story in stories:
            if isinstance(story, dict):
                summary = story.get("summary")
                if summary:
                    return str(summary)
    return ""


def _collect_labels(stories: Any) -> List[str]:
    labels: Set[str] = set()
    if isinstance(stories, list):
        for story in stories:
            if isinstance(story, dict):
                for label in story.get("labels", []) or []:
                    labels.add(str(label))
    return sorted(labels)
def build_snippet(content: str, max_chars: int = 5000) -> str:
    """Return a shortened snippet for previews."""
    content = content.strip()
    if len(content) <= max_chars:
        return content
    return f"{content[: max_chars - 3]}..."
