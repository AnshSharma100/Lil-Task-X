"""Streamlit client for Lil Task X."""
from __future__ import annotations

import json
import os
from typing import Any, Dict

import requests
import streamlit as st

API_BASE_URL = os.getenv("LIL_TASK_API", "http://localhost:5000")

st.set_page_config(page_title="Lil Task X", layout="wide")
st.title("Lil Task X")
sidebar_panel = st.sidebar.container()

def render_sidebar(matches: Any) -> None:
    # Feature 4 story — Add feature coverage sidebar with ✅/❌ indicators.
    sidebar_panel.empty()
    box = sidebar_panel.container()
    box.subheader("Feature Coverage")
    if not matches:
        box.info("Run an analysis to populate coverage.")
        return
    for feature in matches:
        name = feature.get("feature_name", "Unnamed Feature")
        description = feature.get("description", "")
        detected = bool(feature.get("matches"))
        icon = "✅" if detected else "❌"
        if description:
            box.markdown(f"{icon} **{name}** — {description}")
        else:
            box.markdown(f"{icon} **{name}**")

st.write("Paste a GitHub repository URL to analyze features against the codebase.")
render_sidebar(None)
st.write("Paste a GitHub repository URL to analyze features against the codebase.")

repo_url = st.text_input("GitHub Repository URL", placeholder="https://github.com/owner/repo")
branch = st.text_input("Branch (optional)", placeholder="main")
use_llm = st.checkbox("Use Nemotron summaries", value=False)

analyze_triggered = st.button("Analyze 🔍")
latest_feature_matches = None

if analyze_triggered:
    if not repo_url:
        st.warning("Please provide a repository URL before analyzing.")
    else:
        payload: Dict[str, Any] = {"repo_url": repo_url, "use_llm": use_llm}
        if branch:
            payload["branch"] = branch

        with st.spinner("Analyzing repository..."):
            try:
                response = requests.post(f"{API_BASE_URL}/analyze_repo", json=payload, timeout=120)
                response.raise_for_status()
                data = response.json()
            except requests.HTTPError as exc:
                detail = None
                if exc.response is not None:
                    try:
                        detail = exc.response.json().get("detail")
                    except Exception:  # pragma: no cover - defensive
                        detail = exc.response.text
                message = detail or str(exc)
                st.error(f"Failed to analyze repository: {message}")
                data = None
            except requests.RequestException as exc:
                st.error(f"Failed to analyze repository: {exc}")
                data = None

        if data:
            # Feature 4 story — Build repository analysis UI with summaries and downloads.
            st.success("Repository analyzed successfully.")
            feature_matches = data.get("feature_matches", [])
            latest_feature_matches = feature_matches
            render_sidebar(feature_matches)

            if not feature_matches:
                st.info("No features detected or no matching code snippets found.")
            else:
                for feature in feature_matches:
                    with st.expander(feature.get("feature_name", "Unnamed Feature"), expanded=False):
                        st.caption(f"Detected {len(feature.get('matches', []))} related files.")
                        for match in feature.get("matches", []):
                            st.markdown(f"**File:** `{match.get('file_path')}`")
                            st.markdown(f"Score: {match.get('score')}")
                            snippet = match.get("snippet", "")
                            if snippet:
                                st.code(snippet, language=match.get("language", "text"))
                            llm_summary = match.get("llm_summary")
                            if llm_summary:
                                st.markdown("**LLM Summary:**")
                                st.write(llm_summary)

                download_payload = json.dumps(feature_matches, indent=2)
                st.download_button(
                    label="Download Mapping (JSON)",
                    data=download_payload,
                    file_name="feature_mapping.json",
                    mime="application/json",
                )

if latest_feature_matches is None:
    try:
        response = requests.get(f"{API_BASE_URL}/features_map", timeout=10)
        if response.ok:
            cached = response.json().get("feature_matches")
            if cached:
                render_sidebar(cached)
    except requests.RequestException:
        sidebar_panel.info("Backend API not reachable yet. Start it via uvicorn or docker-compose.")
