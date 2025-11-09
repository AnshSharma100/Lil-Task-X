"""Feature-to-code mapping utilities."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from difflib import SequenceMatcher

from .repo_scanner import ScannedFile


@dataclass(slots=True)
class FeatureMatch:
    """Holds mapping information between a feature and code files."""

    feature_name: str
    description: str
    matches: List[Dict[str, Any]]


def map_features_to_code(
    features: Iterable[Dict[str, Any]],
    repo_files: Iterable[ScannedFile],
    llm_client: Optional[Any] = None,
    max_matches: int = 5,
) -> List[FeatureMatch]:
    """Feature 3 - Map features to code files using keyword heuristics and optional LLM summaries.

    Scores fall between 0 and 1 so higher numbers signal closer matches, and the results are
    capped at max_matches to keep the payload lightweight for the API/UI.
    """
    results: List[FeatureMatch] = []

    repo_files = list(repo_files)

    for feature in features:
        feature_name = feature.get("name", "Unnamed Feature")
        description = feature.get("description", "")
        feature_text = _feature_to_text(feature)
        keywords = _extract_keywords(feature_text, feature.get("tags", []))
        match_candidates: List[Dict[str, Any]] = []

        for scanned_file in repo_files:
            score = _score_feature_against_file(feature_text, keywords, scanned_file)
            if score <= 0:
                continue

            summary: Optional[str] = None
            if llm_client is not None:
                summary = llm_client.analyze_feature_with_llm(feature_name, scanned_file.snippet)

            match_candidates.append(
                {
                    "file_path": scanned_file.path,
                    "language": scanned_file.language,
                    "score": round(score, 3),
                    "snippet": scanned_file.snippet,
                    "llm_summary": summary,
                }
            )

        ordered_matches = sorted(match_candidates, key=lambda item: item["score"], reverse=True)[:max_matches]
        results.append(FeatureMatch(feature_name=feature_name, description=description, matches=ordered_matches))

    return results


def create_jira_tasks_from_features(features: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Placeholder for future Jira automation."""
    return [
        {
            "title": feature.get("name", "Unnamed Feature"),
            "description": feature.get("description", ""),
            "status": "todo",
        }
        for feature in features
    ]


def generate_code_summary_md(feature_matches: Iterable[FeatureMatch]) -> str:
    """Placeholder for generating markdown summaries of matches."""
    lines = ["# Feature to Code Summary"]
    for match in feature_matches:
        lines.append(f"\n## {match.feature_name}")
        if match.description:
            lines.append(match.description)
        if not match.matches:
            lines.append("- No related code detected yet.")
            continue
        for entry in match.matches:
            lines.append(f"- `{entry['file_path']}` (score: {entry['score']})")
    return "\n".join(lines)


def _feature_to_text(feature: Dict[str, Any]) -> str:
    parts = [feature.get("name", ""), feature.get("description", "")]
    tags = feature.get("tags") or []
    if isinstance(tags, list):
        parts.extend(str(tag) for tag in tags)
    return " ".join(filter(None, parts)).lower()


def _extract_keywords(feature_text: str, tags: Iterable[Any]) -> List[str]:
    tokens = set()
    for token in feature_text.split():
        if len(token) >= 4:
            tokens.add(token)
    for tag in tags:
        tag_str = str(tag).lower()
        if len(tag_str) >= 3:
            tokens.add(tag_str)
    return sorted(tokens)


def _score_feature_against_file(feature_text: str, keywords: List[str], scanned_file: ScannedFile) -> float:
    # Feature 3 story — Score snippets against features using keywords + similarity blend.
    text = scanned_file.snippet.lower()
    keyword_hits = sum(1 for keyword in keywords if keyword in text)
    keyword_score = keyword_hits / max(len(keywords), 1)

    similarity = SequenceMatcher(None, feature_text, text).ratio()

    return (keyword_score * 0.7) + (similarity * 0.3)
