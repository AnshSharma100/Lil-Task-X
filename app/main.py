"""FastAPI entry point for Lil Task X."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl

from .feature_mapper import FeatureMatch, map_features_to_code
from .llm_connector import NemotronClient
from .repo_scanner import clone_repository, scan_repository
from .utils import get_github_token, read_features

app = FastAPI(title="Lil Task X", version="0.1.0")
logger = logging.getLogger(__name__)

# Ensure environment variables are loaded once at startup.
get_github_token()


class AnalyzeRepoRequest(BaseModel):
    repo_url: HttpUrl
    use_llm: Optional[bool] = None  # retained for backward compatibility but ignored


class MatchDetail(BaseModel):
    file_path: str
    language: str
    score: float
    snippet: str
    llm_summary: Optional[str] = None


class FeatureMatchModel(BaseModel):
    feature_name: str
    description: str
    matches: List[MatchDetail]


class AnalyzeRepoResponse(BaseModel):
    repo_url: HttpUrl
    branch: Optional[str]
    files_scanned: int
    feature_matches: List[FeatureMatchModel]


class FeatureMatchesResponse(BaseModel):
    feature_matches: List[FeatureMatchModel]


# Feature 1 cache: hold the most recent AnalyzeRepoResponse for /features_map.
_analysis_state: Dict[str, Any] = {"latest": None}


@app.post("/analyze_repo", response_model=AnalyzeRepoResponse)
async def analyze_repo(payload: AnalyzeRepoRequest) -> AnalyzeRepoResponse:
    """Feature 1 - FastAPI Analysis API: clone the repo, scan code, and map features."""
    # Feature 1 story — Build analyze_repo endpoint for on-demand scans.
    repo_url_str = str(payload.repo_url)
    try:
        repo_path = clone_repository(repo_url_str)
        scanned_files = scan_repository(repo_path)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Unexpected error while cloning or scanning %s", repo_url_str)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to prepare repository for analysis: {exc}",
        ) from exc

    features = read_features()

    llm_client = NemotronClient()

    try:
        feature_matches = map_features_to_code(features, scanned_files, llm_client=llm_client)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Feature mapping failed for %s", repo_url_str)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to map features to repository: {exc}",
        ) from exc

    response = AnalyzeRepoResponse(
        repo_url=payload.repo_url,
        branch=None,
        files_scanned=len(scanned_files),
        feature_matches=[_feature_match_to_model(match) for match in feature_matches],
    )

    _analysis_state["latest"] = response
    return response


@app.get("/features_map", response_model=FeatureMatchesResponse)
async def get_features_map() -> FeatureMatchesResponse:
    """Return the most recent feature-to-code mapping."""
    # Feature 1 story — Serve cached mappings via features_map endpoint.
    latest: AnalyzeRepoResponse | None = _analysis_state.get("latest")
    if latest is None:
        raise HTTPException(status_code=404, detail="No analysis has been performed yet")
    return FeatureMatchesResponse(feature_matches=latest.feature_matches)


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "ok"}


def _feature_match_to_model(feature_match: FeatureMatch) -> FeatureMatchModel:
    return FeatureMatchModel(
        feature_name=feature_match.feature_name,
        description=feature_match.description,
        matches=[MatchDetail(**entry) for entry in feature_match.matches],
    )
