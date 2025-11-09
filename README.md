# Lil-Task-X — LangChain PM Agent

## Architecture Overview

Lil-Task-X is now a fully agentic Product Management pipeline powered by **Gemini 2.5 Flash** and **LangChain**. The system runs in two deterministic phases:

- **Phase 1 – Product Strategy**: a ReAct agent ingests the product brief, performs live competitor research, and returns a market-ready PRD in Markdown plus structured JSON.
- **Phase 2 – Delivery Plan**: the same agent family converts the PRD into features, stories, tasks, staffing assignments, delivery scenarios (on-track / need-more / reduce-scope), email drafts, and repo watchlist reminders alongside budget projections. A Gemini-backed PDF generator produces visual artefacts.

All reasoning happens through LangChain’s `initialize_agent` API with `AgentType.ZERO_SHOT_REACT_DESCRIPTION`. Every LLM call uses `temperature=0` and `top_p=0.1` to minimise hallucinations. Competitive claims are grounded by an automatic web-search tool (SerpAPI or Exa).

## Gemini + LangChain Agent Flow

1. **LLM**: `ChatGoogleGenerativeAI` (Gemini 2.5 Flash by default, Pro tiers optional when enabled).
2. **Tools** (`src/agents/pm_agent.py`):
   - `competitor_report`: SerpAPI/Exa-powered search that returns structured competitor data.
   - `load_csv`: exposes repo CSVs (employees, budgets, stakeholders) as JSON.
   - `budget_calculator`: aggregates numeric spend categories for validation.
   - `task_splitter`: supplies baseline lifecycle tasks per feature.
   - `jira_uploader`: mock integration that confirms export readiness.
   - `pdf_generator`: bridges to the Matplotlib + ReportLab PDF renderer.
3. **Agent**: ReAct loop plans tool usage, reasons through evidence, then emits the final JSON payloads consumed by each phase.
4. **Decision Support**: Phase 2 applies budget and capacity checks, surfaces three human-readable delivery options, drafts Jira issues/emails, and flags repo areas to monitor for shareholder alignment.

## Prerequisites & Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
```

Fill in the `.env` file with your credentials:

- `GOOGLE_API_KEY` – required for Gemini APIs (defaults target `gemini-2.5-flash`).
- `SERPAPI_KEY` – optional, enables Google web search (preferred).
- `EXA_API_KEY` – optional, enables Exa search (used if present).
- `GEMINI_MODEL` – optional override for the primary Gemini model (defaults to `gemini-2.5-flash`).
- `GEMINI_FAST_MODEL` – optional override for lightweight requests; defaults to the same value.
- `GEMINI_PRD_MODEL` – optional override for the phase-one PRD synthesis call (defaults to `gemini-1.5-pro-latest`).

> If both SERPAPI and EXA keys are absent the agent warns that competitor data is unavailable, but the run will continue with local knowledge only.

## Running the Pipeline

```bash
python -m src.pipeline.main --base-dir "$(pwd)" --outputs-dir "$(pwd)/outputs"
```

After a successful run you will find three canonical artefacts inside `outputs/`:

1. `phase1_product_spec.md` – the polished PRD with market sizing, personas, feature roadmap, risks, and KPIs.
2. `phase2_tasks.json` – structured data containing features, stories, Jira-ready tasks, staffing assignments, budget reconciliation, delivery options, email drafts, and repo watchlist guidance.
3. `phase2_budget_analysis.pdf` – charts, tables, and Gemini-generated narrative summarising budget usage and scheduling insights.

`final_output.json` aggregates the key paths plus structured outputs for downstream automation.

## Testing Each Phase Individually

- **Phase 1**: run `PhaseOneProductStrategy(config).run()` from a Python shell after initialising `PipelineConfig`. Inspect the saved prompt (`phase1_prompt.txt`), raw agent trace (`phase1_raw.json`), and PRD Markdown.
- **Phase 2**: feed the Phase 1 PRD into `PhaseTwoFeasibility(config).run(prd_markdown)`. Examine `phase2_raw.json` for all intermediate ReAct steps, and open `phase2_budget_analysis.pdf` to verify charts.

For automated regression, stub `ChatGoogleGenerativeAI.invoke` with canned responses. The agent tools accept JSON strings, so you can simulate tool outputs during tests without hitting external services.

## Adding or Updating CSV Sources

- Place new CSVs under `data/` and reference them via relative paths when invoking the `load_csv` tool (e.g., `data/new_employees.csv`).
- Ensure column headers are descriptive; they will be preserved in JSON for the agent to interpret.
- Budget files should expose numeric values in a single column. Non-numeric entries are coerced to `0.0` by the `budget_calculator` tool.

## Budget & Task Calculations

- Hourly costs derive from the employee roster CSV (`Hourly_Rate_USD`). The agent keeps individuals under 160 hours across the 12-week plan.
- The `budget_calculator` tool aggregates CSV rows so the agent can cross-check totals before returning `budget_report`.
- The PDF generator plots two charts: budget allocation (pie) and engineer/tester workload (bar). A Gemini summary validates that every claim aligns with the JSON payload.

## Optional Jira Uploading

`jira_uploader` currently mocks the API call and returns a confirmation string. To enable a real integration:

1. Replace the tool implementation in `src/agents/pm_agent.py` with a call to your Jira Cloud/Server REST endpoint.
2. Inject authentication (OAuth or PAT) and handle error responses.
3. Continue returning a concise status message so the agent’s reasoning remains traceable.

## Troubleshooting & Zero-Hallucination Guardrails

- All Gemini calls fix `temperature=0` and `top_p=0.1` to eliminate creative drift.
- Prompts instruct the agent to cite sources for competitor statements and budget maths. Check `phase*_raw.json` to review the reasoning chain.
- If competitor scraping fails (missing API key, rate limit), rerun after setting the relevant env var. The agent degrades gracefully but flags the absence of live intel.

## Contributing

- Keep new tools deterministic and JSON-oriented so the ReAct agent can parse outputs reliably.
- When adding files under `data/`, document them in this README and ensure relative paths work on macOS/Linux.
- Pull requests should regenerate `final_output.json` to validate that all three deliverables compile successfully.