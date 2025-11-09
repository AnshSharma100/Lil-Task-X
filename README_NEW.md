# AI Product Manager System

An advanced AI-powered Product Management pipeline using **Gemini 2.0 Flash**, LangChain agents, and FastAPI. This system analyzes product descriptions, researches competitors, generates market-ready PRDs, creates feasibility plans with budget analysis, and provides an interactive chatbot for PM revision workflows.

---

## 🎯 System Overview

This is the **PM Input + Analysis Pipeline** portion of a 4-part system:
- ✅ **This Module**: Backend analysis pipeline + minimal frontend
- 🔗 **Other Modules** (handled by teammates): Jira automation, email sending, GitHub repo matching

### What It Does

1. **Strategy Phase (Phase 1)**:
   - Researches competitors using web search (SerpAPI/Exa)
   - Extracts market insights and user needs
   - Generates a polished, market-ready Product Requirements Document (PRD)

2. **Development Phase (Phase 2)**:
   - Creates staffed task assignments with cost estimates
   - Generates budget breakdown with pie charts and resource allocation
   - Checks feasibility against deadline and budget constraints
   - Provides delivery options and recommendations

3. **Chatbot Revision Loop**:
   - Adjust budget or deadline interactively
   - Cut features or ask for suggestions
   - Review and edit task assignments conversationally
   - Confirm plan to generate final outputs

4. **PDF Report Generation**:
   - Market insights and competitor overview
   - Budget breakdown with charts (matplotlib)
   - Feasibility summary and recommendations
   - Agent reasoning and decision paths

---

## 🧱 Tech Stack

### Backend
- **Python 3.12+**
- **FastAPI** - REST API with `/run-analysis` and `/chat-revise` endpoints
- **LangChain** - Agent orchestration with ReAct pattern
- **Gemini 2.0 Flash** - Primary model for analysis (via `langchain-google-genai`)
- **ReportLab + Matplotlib** - PDF generation with charts
- **Pandas** - CSV processing

### Frontend
- **React 18** - Minimal SPA with form inputs and chat panel
- **Axios** - HTTP client for API calls

---

## 📦 Installation

### Prerequisites
- Python 3.12+
- Node.js 18+ (for frontend)
- API Keys:
  - `GOOGLE_API_KEY` (Gemini)
  - `SERPAPI_KEY` or `EXA_API_KEY` (competitor research)

### Backend Setup

```bash
# Clone the repo
git clone <repo-url>
cd Lil-Task-X-1

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your API keys:
# GOOGLE_API_KEY=your_gemini_key
# SERPAPI_KEY=your_serpapi_key  # OR
# EXA_API_KEY=your_exa_key
```

### Frontend Setup

```bash
cd frontend
npm install
```

---

## 🚀 Running the System

### Start Backend (FastAPI)

```bash
# From project root
python backend_api.py
```

Backend runs on `http://localhost:8000`

**Endpoints**:
- `POST /run-analysis` - Submit inputs, get feasibility analysis
- `POST /chat-revise` - Chatbot revision loop
- `GET /download-report/{session_id}` - Download PDF report
- `GET /health` - Health check

### Start Frontend (React)

```bash
cd frontend
npm start
```

Frontend runs on `http://localhost:3000`

---

## 📋 Usage Guide

### Input Format

#### 1. Deadline
Date input (e.g., `2025-03-30`)

#### 2. Budget & Resources CSV
Schema:
```csv
Resource,Value
Engineering Budget (USD),120000
QA Budget (USD),40000
Cloud Services Budget (USD),30000
Licensing & Tools Budget (USD),15000
Gemini API Available,False
Gemini API Monthly Cost (USD),100
Firebase Auth Monthly Cost (USD),50
Security/Compliance Budget (USD),10000
Training & Upskilling Budget (USD),5000
Emergency Contingency Reserve (USD),8000
```

#### 3. Employee Directory CSV
Schema:
```csv
Name,Role,Experience_Level,Skills,Hourly_Rate_USD,Email
Ava Chen,Senior Frontend Engineer,Senior,"frontend,react,typescript,uiux,css",85,ava@example.com
Daniel Lee,Mid Backend Engineer,Mid,"backend,nodejs,python,api,databases",60,daniel@example.com
Isha Patel,Junior Fullstack Engineer,Junior,"react,javascript,html,css,basic-backend",35,isha@example.com
```

#### 4. Product Description
Text or file upload (.txt, .pdf) describing:
- What the product does
- Target users
- Key features
- Competitors (optional - agent will research)
- Timeline goals

### Frontend Workflow

1. **Fill Form**: Enter deadline, upload CSVs, provide product description
2. **Submit**: Click "Run Analysis"
3. **Review Results**:
   - Feasibility status (green/red)
   - Recommendations (if not feasible)
   - Cost summary
   - Task assignments preview
4. **Chat with Agent**:
   - "Increase budget to $150,000"
   - "Extend deadline to April 15"
   - "Remove the analytics dashboard feature"
   - "Which features should I cut?"
   - "Reassign task TASK-001 to Daniel"
5. **Confirm Plan**: Type "confirm" in chat when satisfied
6. **Download Report**: Get PDF with full analysis

---

## 🧠 How It Works

### Phase 1: Strategy & PRD Generation

1. **Agent Setup**:
   - Model: `gemini-2.0-flash-exp`
   - Temperature: 0 (deterministic)
   - Tools: `competitor_report`, `load_csv`

2. **Competitor Research**:
   - Agent calls web search for each competitor
   - Extracts differentiators, gaps, and sources
   - Limits to 4 tool calls max

3. **Fact Synthesis**:
   - Collects: competitors, user needs, market ranges, insights
   - Outputs: `phase1_facts.json`

4. **PRD Generation**:
   - Model: `gemini-1.5-pro-latest` (configurable)
   - Inputs: facts + product description
   - Outputs: `phase1_product_spec.md` (markdown PRD)

5. **Error Handling**:
   - If JSON parsing fails, deterministic fallback extracts facts from tool evidence
   - Captures intermediate steps for debugging

### Phase 2: Development Planning & Feasibility

1. **Input Processing**:
   - Loads PRD, employee directory, budget CSV
   - Calculates team capacity (160 hrs/person max)

2. **Task Generation**:
   - Agent uses `task_splitter` tool
   - Assigns owners based on skills
   - Estimates hours and costs

3. **Budget Analysis**:
   - Sums engineering, QA, tools, contingency
   - Compares against baseline budget
   - Flags over-budget scenarios

4. **Feasibility Check**:
   ```python
   if total_cost > budget or timeline > deadline:
       status = "over_budget" | "over_capacity"
       recommendations = ["increase_budget", "extend_timeline", "reduce_scope"]
   else:
       status = "feasible"
   ```

5. **Delivery Options**:
   - **Green**: On track
   - **Yellow**: Needs adjustment
   - **Red**: Requires major changes

6. **Outputs**:
   - `phase2_tasks.json` - Full task breakdown
   - `phase2_plan_report.json` - Executive summary
   - `phase2_jira_payload.json` - Ready for Jira import (teammates' module)
   - `phase2_budget_analysis.pdf` - Charts + narrative

### Chatbot Revision Loop

1. **Intent Parsing**:
   - Uses Gemini to classify user message:
     - `adjust_budget` / `adjust_deadline`
     - `cut_features`
     - `review_tasks`
     - `confirm_plan`
     - `general_query`

2. **Action Handling**:
   - **Adjust**: Updates state, triggers re-analysis
   - **Cut Features**: Suggests lowest-impact removals
   - **Review**: Allows conversational edits
   - **Confirm**: Locks plan, outputs final JSON

3. **Session Management**:
   - Each session stored in `/uploads/{session_id}/`
   - State persisted in memory (extend to Redis for production)

---

## 📂 Project Structure

```
Lil-Task-X-1/
├── backend_api.py              # FastAPI endpoints
├── requirements.txt            # Python dependencies
├── .env                        # API keys (not committed)
├── data/                       # Sample CSVs
│   ├── company_budget.csv
│   ├── developers_with_email.csv
│   └── product_description.txt
├── src/
│   ├── agents/
│   │   └── pm_agent.py         # LangChain agent + tools
│   └── pipeline/
│       ├── config.py           # Pipeline configuration
│       ├── data_loaders.py     # CSV parsers
│       ├── phase1.py           # Strategy phase
│       ├── phase2_llm.py       # Development phase
│       ├── pdf_generator.py    # Chart + PDF generation
│       └── main.py             # CLI orchestrator
├── frontend/
│   ├── package.json
│   ├── public/
│   │   └── index.html
│   └── src/
│       ├── App.js              # Main React component
│       ├── App.css             # Styling
│       └── index.js            # Entry point
└── uploads/                    # Session storage (auto-created)
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Required
GOOGLE_API_KEY=<your_gemini_api_key>

# Search (choose one)
SERPAPI_KEY=<your_serpapi_key>
EXA_API_KEY=<your_exa_api_key>

# Optional Model Overrides
GEMINI_MODEL=gemini-2.0-flash-exp          # Default: 2.0 Flash
GEMINI_PRD_MODEL=gemini-1.5-pro-latest     # For PRD synthesis
```

### Model Configuration

Default models:
- **Phase 1 Agent**: `gemini-2.0-flash-exp` (tool calling, competitor research)
- **PRD Synthesis**: `gemini-1.5-pro-latest` (longer context for PRD generation)
- **Phase 2 Agent**: `gemini-2.0-flash-exp` (task planning, budget analysis)
- **Chatbot**: `gemini-2.0-flash-exp` (intent parsing, feature suggestions)

Override in `src/pipeline/config.py` or via environment variables.

---

## 🚫 What This Does NOT Do

- ❌ Create Jira issues (handled by teammates' module)
- ❌ Send emails (handled by teammates' module)
- ❌ Analyze GitHub repos (handled by teammates' module)

**This module** focuses solely on:
- ✅ PM input collection
- ✅ LangChain analysis pipeline
- ✅ Chatbot revision workflow
- ✅ PDF report generation

---

## 🐛 Troubleshooting

### Phase 1 Agent Returns Incomplete JSON

**Symptom**: `RuntimeError: Phase 1 fact-gathering agent did not return valid JSON`

**Solution**:
1. Check `outputs/phase1_fact_parse_error.txt` for raw output
2. Verify `SERPAPI_KEY` or `EXA_API_KEY` is set (needed for competitor research)
3. Agent now has deterministic fallback - rerun should succeed

### Backend Fails to Start

**Symptom**: `ImportError: No module named 'fastapi'`

**Solution**:
```bash
pip install -r requirements.txt
```

### Frontend Can't Connect to Backend

**Symptom**: CORS error or network failure

**Solution**:
1. Ensure backend is running on `http://localhost:8000`
2. Check CORS middleware in `backend_api.py` (should allow all origins in dev)
3. Update `API_BASE` in `frontend/src/App.js` if backend port changed

### PDF Generation Fails

**Symptom**: Missing charts in PDF

**Solution**:
```bash
pip install matplotlib reportlab
```

---

## 📊 Sample Output

### Phase 1 (`outputs/phase1_facts.json`)
```json
{
  "facts": {
    "competitors": [
      {
        "name": "Habitica",
        "summary": "Gamified habit tracker using RPG elements",
        "differentiators": ["Gamification", "Character building"],
        "gaps": ["May not be simple enough"],
        "sources": ["https://habitica.com/"]
      }
    ],
    "user_needs": [
      "Plan and track daily habits",
      "Simple, clean interface",
      "Progress visualization"
    ],
    "market_ranges": {
      "tam_range": "",
      "sam_range": "",
      "som_range": ""
    },
    "extracted_insights": [
      "Gamification is common but adds complexity",
      "Users want simplicity over features"
    ],
    "evidence_refs": ["https://habitica.com/", "..."]
  },
  "status": "complete"
}
```

### Phase 2 (`outputs/phase2_jira_payload.json`)
```json
[
  {
    "issue_type": "Epic",
    "epic": "MVP-CORE",
    "title": "Core Habit Tracking",
    "story": "As a user, I want to track daily habits",
    "description": "Implement habit creation, logging, and streak tracking",
    "assignee": "ava@example.com",
    "labels": ["mvp", "frontend"],
    "estimate": 40,
    "due_date": "2025-02-15"
  }
]
```

---

## 🎓 Advanced Usage

### CLI Mode (No Frontend)

```bash
python -m src.pipeline.main \
  --base-dir "$(pwd)" \
  --outputs-dir "$(pwd)/outputs"
```

Outputs saved to `outputs/final_output.json`

### Custom Tools

Add tools in `src/agents/pm_agent.py`:

```python
@tool("my_custom_tool")
def my_tool(input: str) -> str:
    """Description for the agent."""
    # Your logic here
    return "result"
```

Register in `build_tools()` function.

### Adjusting Agent Behavior

Edit prompts in:
- `src/pipeline/phase1.py` → `_build_fact_instruction()`
- `src/pipeline/phase2_llm.py` → `_build_instruction()`

---

## 📝 License

MIT License

---

## 👥 Credits

Built with:
- [LangChain](https://langchain.com/)
- [Google Gemini](https://ai.google.dev/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)

---

## 🔗 Integration Points

### For Jira Automation Team
- Consume: `outputs/phase2_jira_payload.json`
- Schema: `{issue_type, epic, title, story, description, assignee, labels, estimate, due_date}`

### For Email Team
- Consume: `outputs/phase2_tasks.json` → `email_notifications` array
- Schema: `{to, subject, body}`

### For GitHub Repo Team
- Consume: `outputs/phase2_tasks.json` → `repo_watchlist` array
- List of feature flags / specs to monitor

---

**Need help?** Check `/outputs` directory for debug files after each run:
- `phase1_raw.json` - Full agent trace
- `phase2_raw.json` - Full planning trace
- `*_error.txt` - Error details if something fails
