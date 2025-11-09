# Lil Task X

Lil Task X is a prototype for scanning GitHub repositories, cross-referencing them with feature definitions, and producing AI-assisted mappings ready for product or Jira workflows. The backend is powered by FastAPI and integrates with NVIDIA's Nemotron model when available. A lightweight Streamlit client offers an interactive view over the generated mappings.

## Prerequisites
- Python 3.11+
- Git
- Optional: Docker & Docker Compose for containerised runs
- A GitHub token stored in `.env` for private repository access

## Local Setup
1. Clone this repository and switch into the project directory.
2. Create a virtual environment and install dependencies:
	```powershell
	python -m venv .venv
	.\.venv\Scripts\Activate
	pip install -r requirements.txt
	```
3. Open `.env` and add your token value:
	```powershell
	notepad .env
	# set GITHUB_TOKEN=ghp_your_token
	```
	When the API starts successfully it prints `✅ GitHub token loaded` once without revealing the secret.
4. Launch the API:
	```powershell
	uvicorn app.main:app --reload --host 0.0.0.0 --port 5000
	```
5. (Optional) Start the Streamlit client in another shell:
	```powershell
	streamlit run client\frontend.py
	```

## Using Docker Compose
The provided `docker-compose.yml` spins up both the vLLM Nemotron service and the FastAPI backend.

1. Download or mount the `NVIDIA-Nemotron-Nano-9B-v2` model inside `./NVIDIA-Nemotron-Nano-9B-v2`.
2. Ensure `.env` exists with `GITHUB_TOKEN`.
3. Start the stack:
	```powershell
	docker compose up --build
	```
4. Access the API at `http://localhost:5000` and the vLLM endpoint at `http://localhost:8000/v1`.

## Workflow Overview
1. Paste a GitHub repository URL via the Streamlit UI or POST `/analyze_repo` with `{ "repo_url": "..." }`.
2. The backend clones the repository into a temporary directory, scans supported source files, and extracts representative snippets.
3. Feature descriptions from `features.json` are matched to code files using heuristic scoring; optional Nemotron summaries enrich each match.
4. Retrieve the latest mapping by calling `GET /features_map` or exporting from the UI.

## Endpoints
- `POST /analyze_repo`: Trigger a repository scan and feature mapping.
  ```json
  {
	 "repo_url": "https://github.com/owner/repo",
	 "branch": "main",
	 "use_llm": true
  }
  ```
- `GET /features_map`: Fetch the cached feature-to-code mapping from the most recent analysis.
- `GET /health`: Basic health probe.

## Frontend
`client/frontend.py` hosts a Streamlit UI with:
- Repository URL input and optional branch override
- Toggle for Nemotron summaries
- Expandable sections per feature with code snippets
- JSON download of the generated mapping

## Development Notes
- Temporary repositories are stored under your OS temp directory (`%TEMP%/lil_task_x/repos`).
- `features.json` is expected at the repository root; structure is normalised regardless of list or dict formats.
- Placeholder functions exist for future Jira automation and markdown export within `app/feature_mapper.py`.

## Testing the API Quickly
With the server running you can use the provided curl example:
```powershell
curl -X POST http://localhost:5000/analyze_repo `
  -H "Content-Type: application/json" `
  -d '{"repo_url": "https://github.com/tiangolo/fastapi"}'
```

## Roadmap
- Integrate Nemotron responses into persistent storage
- Connect placeholder automation hooks to Jira / GitHub Issues
- Add unit tests covering repository scanning heuristics