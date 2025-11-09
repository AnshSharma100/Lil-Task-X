"""Feature-to-code mapping utilities."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

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
    llm_client: Any,
    max_matches: int = 5,
) -> List[FeatureMatch]:
    """Feature 3 - Map features to code files using heuristics followed by mandatory LLM verification."""
    if llm_client is None:  # pragma: no cover - defensive guard
        raise ValueError("llm_client must be provided; the mapper always verifies with the model now.")

    results: List[FeatureMatch] = []

    repo_files = list(repo_files)

    for feature in features:
        feature_name = feature.get("name", "Unnamed Feature")
        description = feature.get("description", "")
        feature_text = _feature_to_text(feature)
        keywords = _extract_keywords(feature_text, feature.get("tags", []))
        heuristic_candidates: List[Tuple[ScannedFile, float]] = []

        for scanned_file in repo_files:
            score = _score_feature_against_file(feature_text, keywords, scanned_file)
            heuristic_candidates.append((scanned_file, max(score, 0.0)))

        if not heuristic_candidates:
            results.append(FeatureMatch(feature_name=feature_name, description=description, matches=[]))
            continue

        heuristic_candidates.sort(key=lambda pair: pair[1], reverse=True)

        processed_matches: List[Dict[str, Any]] = []
        candidate_slice: Sequence[Tuple[ScannedFile, float]] = heuristic_candidates[: max_matches * 4]
        positive_matches: List[Dict[str, Any]] = []

        for scanned_file, base_score in candidate_slice:
            evaluation = llm_client.evaluate_feature_match(
                feature,
                file_path=scanned_file.path,
                code_snippet=scanned_file.snippet,
            )

            evaluated_score = evaluation.score if evaluation.score is not None else base_score
            final_score = round(evaluated_score, 3)
            llm_summary: Optional[str] = evaluation.summary

            entry = {
                "file_path": scanned_file.path,
                "language": scanned_file.language,
                "score": final_score,
                "snippet": scanned_file.snippet,
                "llm_summary": llm_summary,
            }

            processed_matches.append(entry)

            if evaluation.score is not None and evaluation.score >= 0.55:
                positive_matches.append(entry)
                if len(positive_matches) >= max_matches:
                    break

        if positive_matches:
            ordered_matches = sorted(positive_matches, key=lambda item: item["score"], reverse=True)[:max_matches]
        else:
            ordered_matches = sorted(processed_matches, key=lambda item: item["score"], reverse=True)[:max_matches]

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
