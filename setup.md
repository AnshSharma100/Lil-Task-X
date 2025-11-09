# GitHub Copilot — Full Project Setup Prompt for Lil Task X

# 🎯 Goal:
# Build the initial Lil Task X prototype.
# It should let me paste a GitHub repo link, scan that repo for code relevant to features in features.json,
# and prepare AI-generated story-to-code mappings or Jira-ready summaries.
# The backend will later use NVIDIA’s Nemotron-Nano-9B-v2 (served locally with vLLM).

# -------------------------------------------------------------
# 1️⃣ Project Structure
# -------------------------------------------------------------
# Create a project layout like this:
# ├── .env                     # holds GITHUB_TOKEN (not committed)
# ├── .gitignore               # add .env, __pycache__, /models
# ├── requirements.txt
# ├── app/
# │   ├── __init__.py
# │   ├── main.py              # FastAPI app entry point
# │   ├── repo_scanner.py      # clones and inspects GitHub repos
# │   ├── feature_mapper.py    # matches features.json to code
# │   ├── llm_connector.py     # connects to local Nemotron vLLM endpoint
# │   └── utils.py             # helper functions
# ├── features.json            # (I’ll upload this file manually)
# ├── docker-compose.yml
# ├── client/
# │   └── frontend.py          # lightweight Streamlit UI for now
# └── README.md

# -------------------------------------------------------------
# 2️⃣ Environment + Secrets
# -------------------------------------------------------------
# - Add python-dotenv to requirements.txt
# - Load GITHUB_TOKEN from .env
# - Never print or expose the token.
# - Confirm token presence with: print("✅ GitHub token loaded")

# -------------------------------------------------------------
# 3️⃣ Backend Logic (FastAPI)
# -------------------------------------------------------------
# In app/main.py:
#   - Expose two endpoints:
#     POST /analyze_repo → takes {"repo_url": "https://github.com/..."} and triggers repo scan
#     GET /features_map → returns mapping of feature names to detected code files
#
# In app/repo_scanner.py:
#   - Use GitPython or PyGitHub to clone the repo into /tmp
#   - Read all .py/.js/.java files (depending on repo)
#   - Return structured list of file paths + short content snippets
#
# In app/feature_mapper.py:
#   - Load features.json
#   - For each story/feature, use fuzzy keyword matching or embeddings
#     to link it to related code snippets (e.g., "validation", "pipeline", "forecast").
#   - Produce a mapping like:
#     {
#       "Feature 1 - Data Ingestion": ["src/data_loader.py", "schemas/validation.py"],
#       "Feature 2 - CLI": ["cli.py", "run_pipeline.py"]
#     }
#
# In app/llm_connector.py:
#   - Connect to Nemotron-Nano-9B-v2 via vLLM REST API (http://localhost:8000/v1)
#   - Create helper function `analyze_feature_with_llm(feature, code_snippet)`
#     that sends `/think Analyze how this code supports feature X` to the model.

# -------------------------------------------------------------
# 4️⃣ Frontend (client/frontend.py)
# -------------------------------------------------------------
# - Use Streamlit
# - UI should have:
#   1. Text input for GitHub repo URL
#   2. “Analyze” button → calls backend
#   3. Display of features from features.json
#   4. For each feature, list matched code files and summaries
#   5. Optional export to JSON/Markdown
#
# Example:
#   [ Textbox: paste repo URL ]
#   [ Analyze 🔍 ]
#   Feature → Code Mapping Table

# -------------------------------------------------------------
# 5️⃣ Model Integration (Nemotron)
# -------------------------------------------------------------
# In docker-compose.yml:
#   version: "3"
#   services:
#     nemotron:
#       image: vllm/vllm-openai:v0.10.1
#       command: >
#         vllm serve nvidia/NVIDIA-Nemotron-Nano-9B-v2
#         --trust-remote-code
#         --mamba_ssm_cache_dtype float32
#         --enable-auto-tool-choice
#         --tool-parser-plugin "NVIDIA-Nemotron-Nano-9B-v2/nemotron_toolcall_parser_no_streaming.py"
#         --tool-call-parser "nemotron_json"
#       ports:
#         - "8000:8000"
#       volumes:
#         - ./NVIDIA-Nemotron-Nano-9B-v2:/model
#
#     api:
#       build: .
#       command: uvicorn app.main:app --reload --host 0.0.0.0 --port 5000
#       ports:
#         - "5000:5000"
#       volumes:
#         - .:/code
#       env_file:
#         - .env
#       depends_on:
#         - nemotron
#
# -------------------------------------------------------------
# 6️⃣ Commit Rules
# -------------------------------------------------------------
# - Commit everything except `.env` and the cloned model directory.
# - Ensure `README.md` includes setup + usage steps.

# -------------------------------------------------------------
# 7️⃣ Stretch Goal (for Copilot)
# -------------------------------------------------------------
# Add placeholder functions for future automation:
#   def create_jira_tasks_from_features()
#   def generate_code_summary_md()
#
# These can later connect to Jira or GitHub Issues APIs.
