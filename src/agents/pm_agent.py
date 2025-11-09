from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from langchain.agents import AgentExecutor, AgentType, initialize_agent
from langchain.tools import tool
from langchain_community.utilities import SerpAPIWrapper
from langchain_google_genai import ChatGoogleGenerativeAI

try:
    from exa_py import Exa  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    Exa = None  # type: ignore

from ..pipeline.config import PipelineConfig
from ..pipeline.pdf_generator import generate_budget_analysis_pdf


def create_llm(config: PipelineConfig, *, model: Optional[str] = None, max_output_tokens: int = 4096) -> ChatGoogleGenerativeAI:
    """Instantiate a Gemini chat model with deterministic settings."""

    if not config.google_api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set. Populate it in your environment or .env file.")
    chosen_model = model or config.resolved_gemini_model
    return ChatGoogleGenerativeAI(
        model=chosen_model,
        google_api_key=config.google_api_key,
        temperature=0,
        top_p=0.1,
        max_output_tokens=max_output_tokens,
    )


def _build_competitor_payload(results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    payload: List[Dict[str, str]] = []
    for item in results:
        title = item.get("title") or item.get("name") or "Unknown"
        url = item.get("link") or item.get("url") or item.get("source_url") or ""
        snippet = item.get("snippet") or item.get("description") or item.get("summary") or ""
        payload.append(
            {
                "title": str(title),
                "summary": str(snippet),
                "url": str(url),
            }
        )
    return payload


def build_tools(config: PipelineConfig, llm: ChatGoogleGenerativeAI) -> List[Any]:
    """Create LangChain tools wired to local data sources and utilities."""

    base_dir = Path(config.product_description_path).parents[1]

    serp_wrapper: Optional[SerpAPIWrapper] = None
    if config.serpapi_api_key:
        serp_wrapper = SerpAPIWrapper(serpapi_api_key=config.serpapi_api_key)

    exa_wrapper: Optional[Any] = None
    exa_key = config.exa_api_key
    if exa_key and exa_key.lower() != "optional_exa_api_key" and Exa is not None:
        try:
            exa_wrapper = Exa(api_key=exa_key)
        except Exception:
            exa_wrapper = None

    @tool("competitor_report")
    def competitor_report(query: str) -> str:
        """Searches the web for competitor products and extracts structured insights."""

        parsed_query = query
        if isinstance(query, str) and query.strip().startswith("{"):
            try:
                payload = json.loads(query)
                parsed_query = payload.get("query", "") or query
            except json.JSONDecodeError:
                parsed_query = query
        if not isinstance(parsed_query, str):
            parsed_query = str(parsed_query)

        if exa_wrapper is not None:
            try:
                response = exa_wrapper.search(parsed_query, num_results=5)
            except Exception:
                response = None
            if hasattr(response, "results"):
                results = [
                    {
                        "title": getattr(item, "title", ""),
                        "summary": getattr(item, "summary", "") or getattr(item, "text", ""),
                        "url": getattr(item, "url", ""),
                    }
                    for item in getattr(response, "results", [])
                ]
            elif isinstance(response, dict):
                results = response.get("results", [])
            else:
                results = []
        elif serp_wrapper is not None:
            try:
                response = serp_wrapper.results(parsed_query)
            except Exception:
                response = {}
            results = response.get("organic_results", []) if isinstance(response, dict) else []
        else:
            return json.dumps(
                {
                    "warning": "No web search key configured. Provide SERPAPI_KEY or EXA_API_KEY.",
                    "items": [],
                }
            )
        payload = _build_competitor_payload(results)
        bulletins = [item["summary"] for item in payload if item.get("summary")]
        overview = " ".join(bulletins)[:1200]
        return json.dumps({"query": parsed_query, "items": payload, "overview": overview}, ensure_ascii=False)

    @tool("load_csv")
    def load_csv(relative_path: str) -> str:
        """Loads a CSV file relative to the repository root and returns JSON rows."""
        
        # Handle cases where the input might be a JSON string with a relative_path key
        if isinstance(relative_path, str) and relative_path.strip().startswith('{'):
            try:
                parsed = json.loads(relative_path)
                if isinstance(parsed, dict) and 'relative_path' in parsed:
                    relative_path = parsed['relative_path']
            except json.JSONDecodeError:
                pass
        
        path = base_dir / relative_path
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {relative_path}")
        df = pd.read_csv(path)
        return df.to_json(orient="records")

    @tool("budget_calculator")
    def budget_calculator(budget_json: str) -> str:
        """Aggregates budget entries and returns totals by category and overall spend."""

        # Parse input - handle both string and already-parsed data
        try:
            data = json.loads(budget_json) if isinstance(budget_json, str) else budget_json
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON input", "total": 0.0, "categories": {}})
        
        # Handle nested structure with 'entries' key
        if isinstance(data, dict):
            if 'entries' in data:
                data = data['entries']
            else:
                # If it's a dict without 'entries', try to extract values
                return json.dumps({"error": "Expected list of budget entries or dict with 'entries' key", "total": 0.0, "categories": {}})
        
        # Ensure data is now a list
        if not isinstance(data, list):
            return json.dumps({"error": "Expected list of budget entries", "total": 0.0, "categories": {}})
        
        total = 0.0
        categories: Dict[str, float] = {}
        
        for entry in data:
            # Skip if entry is not a dict
            if not isinstance(entry, dict):
                continue
                
            # Extract category with multiple fallbacks
            category = str(entry.get("category") or entry.get("Category") or entry.get("type") or entry.get("resource") or "uncategorised")
            
            # Extract amount with multiple fallbacks
            amount_str = entry.get("amount") or entry.get("Amount") or entry.get("value") or entry.get("Budget") or entry.get("cost")
            try:
                amount = float(amount_str)
            except (TypeError, ValueError):
                amount = 0.0
            
            total += amount
            categories[category] = categories.get(category, 0.0) + amount
        
        payload = {"total": round(total, 2), "categories": {k: round(v, 2) for k, v in categories.items()}}
        return json.dumps(payload)

    @tool("task_splitter")
    def task_splitter(features_json: str) -> str:
        """Splits feature descriptions into default lifecycle tasks (analysis, build, QA, launch)."""

        try:
            features = json.loads(features_json)
        except json.JSONDecodeError:
            features = [item.strip() for item in features_json.split("\n") if item.strip()]
        tasks: List[Dict[str, Any]] = []
        for index, feature in enumerate(features, start=1):
            feature_name = feature.get("name") if isinstance(feature, dict) else feature
            for suffix, description in [
                ("analysis", "requirements review and scope confirmation"),
                ("implementation", "core development work and code review"),
                ("qa", "test planning, execution, and bug triage"),
                ("launch", "release readiness, docs, and enablement"),
            ]:
                tasks.append(
                    {
                        "id": f"TASK-{index:02d}-{suffix}",
                        "feature": str(feature_name),
                        "workstream": suffix,
                        "description": description,
                    }
                )
        return json.dumps({"tasks": tasks})

    @tool("jira_uploader")
    def jira_uploader(payload: str) -> str:
        """Mocks uploading tasks to Jira and returns a confirmation message."""

        try:
            data = json.loads(payload)
            items = len(data.get("tasks", []))
        except json.JSONDecodeError:
            items = 0
        return f"Mock Jira upload complete. {items} tasks queued for import."

    @tool("pdf_generator")
    def pdf_generator(payload: str) -> str:
        """Generates a budget analysis PDF from JSON payload and returns the file path."""

        data = json.loads(payload)
        output_path = Path(data.get("output_path", base_dir / "outputs" / "phase2_budget_analysis.pdf"))
        tasks = data.get("tasks", [])
        budget_report = data.get("budget_report", {})
        narrative_context = data.get("narrative", "")
        path = generate_budget_analysis_pdf(output_path=output_path, tasks=tasks, budget_report=budget_report, llm=llm, narrative_context=narrative_context)
        return str(path)

    tools: List[Any] = [
        competitor_report,
        load_csv,
        budget_calculator,
        task_splitter,
        jira_uploader,
        pdf_generator,
    ]
    return tools


def create_pm_agent(
    config: PipelineConfig,
    *,
    llm: Optional[ChatGoogleGenerativeAI] = None,
    additional_tools: Optional[List[Any]] = None,
    verbose: bool = True,
) -> AgentExecutor:
    """Initialise the ReAct PM agent with common tools."""

    llm_instance = llm or create_llm(config)
    tools = build_tools(config, llm_instance)
    if additional_tools:
        tools.extend(additional_tools)
    agent = initialize_agent(
        tools,
        llm_instance,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=verbose,
        handle_parsing_errors=True,
        max_iterations=5,  # Reduced from 20 for speed
        early_stopping_method="force",
        return_intermediate_steps=True,
    )
    return agent