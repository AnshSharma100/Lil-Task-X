# 🚀 AI Product Manager System - Complete Setup & Usage Guide

## Quick Start (5 minutes)

### 1. Install Dependencies

```bash
# Run the quickstart script
./quickstart.sh

# OR manually:
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add:
# - GOOGLE_API_KEY (get from https://ai.google.dev/)
# - SERPAPI_KEY (get from https://serpapi.com/) OR EXA_API_KEY
nano .env
```

### 3. Start the Backend

```bash
python backend_api.py
```

Backend runs at `http://localhost:8000`

### 4. Start the Frontend (Optional)

```bash
cd frontend
npm install  # First time only
npm start
```

Frontend runs at `http://localhost:3000`

---

## System Architecture

### Three Ways to Use This System

#### 1. **Web Interface** (Recommended)
- Full-featured React frontend
- File uploads, chat interface, PDF downloads
- Real-time analysis feedback

#### 2. **API Only**
- Direct HTTP calls to FastAPI endpoints
- Integrate into existing tools
- Automate workflows

#### 3. **CLI Mode**
- Command-line pipeline execution
- No frontend/backend needed
- Batch processing

---

## Usage Examples

### Example 1: Web Interface Workflow

1. **Open** `http://localhost:3000` in browser

2. **Fill Form**:
   - **Deadline**: `2025-03-30`
   - **Budget CSV**: Upload `data/company_budget.csv`
   - **Employees CSV**: Upload `data/developers_with_email.csv`
   - **Product Description**: Paste or upload product brief

3. **Submit** → Wait for analysis (30-60 seconds)

4. **Review Results**:
   - ✓ Feasibility status
   - Budget breakdown
   - Task assignments
   - Recommendations

5. **Chat with Agent**:
   ```
   User: "Can we finish by March 15 instead?"
   Agent: "That's 2 weeks earlier. I recommend removing the analytics module..."
   
   User: "Remove analytics and social features"
   Agent: "Updated. New feasibility: GREEN. Cost reduced by $15,000..."
   
   User: "Confirm plan"
   Agent: "Plan confirmed! Generating final outputs..."
   ```

6. **Download** PDF report

---

### Example 2: Direct API Usage

#### Run Initial Analysis

```bash
curl -X POST http://localhost:8000/run-analysis \
  -F "deadline=2025-03-30" \
  -F "budget_csv=@data/company_budget.csv" \
  -F "employees_csv=@data/developers_with_email.csv" \
  -F "product_description=We want to build a habit tracking app..."
```

**Response**:
```json
{
  "session_id": "abc123...",
  "market_ready_description": "...",
  "task_assignments": [...],
  "cost_summary": {...},
  "feasibility": true,
  "recommendations": [...]
}
```

#### Chat Revision

```bash
curl -X POST http://localhost:8000/chat-revise \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "abc123...",
    "message": "Increase budget to $150,000"
  }'
```

#### Download Report

```bash
curl -O http://localhost:8000/download-report/abc123...
```

---

### Example 3: CLI Mode

```bash
python -m src.pipeline.main \
  --base-dir "$(pwd)" \
  --outputs-dir "$(pwd)/outputs"
```

**Outputs** (in `outputs/` directory):
- `phase1_facts.json` - Competitor research results
- `phase1_product_spec.md` - Generated PRD
- `phase2_tasks.json` - Full task breakdown
- `phase2_plan_report.json` - Executive summary
- `phase2_jira_payload.json` - Jira-ready issues
- `phase2_budget_analysis.pdf` - Visual report
- `final_output.json` - Combined results

---

## Understanding the Outputs

### Phase 1: Strategy Outputs

**`phase1_facts.json`** - Structured market research:
```json
{
  "facts": {
    "competitors": [
      {
        "name": "Habitica",
        "summary": "Gamified habit tracker...",
        "differentiators": ["RPG elements", "Character building"],
        "gaps": ["Complex interface"],
        "sources": ["https://habitica.com"]
      }
    ],
    "user_needs": [
      "Simple habit tracking",
      "Progress visualization",
      "Reminders"
    ],
    "extracted_insights": [
      "Market wants simplicity over features",
      "Mobile-first approach critical"
    ],
    "evidence_refs": ["https://..."]
  },
  "status": "complete"
}
```

**`phase1_product_spec.md`** - Market-ready PRD:
```markdown
# Product Requirements Document

## Overview
A simple, mobile-first habit tracking app...

## Problem Statement
Users frustrated with complex apps like Habitica...

## Solution
Clean interface with...

## Features
1. Habit Creation
2. Daily Check-ins
3. Streak Tracking
...
```

---

### Phase 2: Development Outputs

**`phase2_tasks.json`** - Full execution plan:
```json
{
  "features": [
    {"name": "Habit Tracking", "priority": "P0"}
  ],
  "tasks": [
    {
      "id": "TASK-001",
      "feature": "Habit Tracking",
      "title": "Design habit data schema",
      "assignee": "ava@example.com",
      "estimated_hours": 8,
      "salary_cost": 680,
      "sprint": 1,
      "risk_level": "Low"
    }
  ],
  "budget_report": {
    "engineering_cost": 85000,
    "qa_cost": 15000,
    "total_cost": 120000,
    "baseline_budget": 150000
  },
  "decision_recommendations": {
    "status": "feasible",
    "summary": "Project can be delivered on time and under budget"
  }
}
```

**`phase2_jira_payload.json`** - Ready for Jira import:
```json
[
  {
    "issue_type": "Epic",
    "epic": "MVP-CORE",
    "title": "Core Habit Tracking",
    "story": "As a user, I want to track my daily habits",
    "description": "Implement habit CRUD, streak tracking, reminders",
    "assignee": "ava@example.com",
    "labels": ["mvp", "frontend", "backend"],
    "estimate": 40,
    "due_date": "2025-02-15"
  }
]
```

**`phase2_budget_analysis.pdf`** - Visual report with:
- Executive summary (LLM-generated)
- Budget pie chart
- Resource allocation bar chart
- Task breakdown table

---

## Chatbot Commands Reference

### Budget & Timeline Adjustments

```
"Increase budget to $150,000"
"Extend deadline to April 30"
"We have $200k available"
"Move the deadline 2 weeks later"
```

### Feature Management

```
"Remove the social features"
"Cut the analytics dashboard"
"Which features should I remove to save $20k?"
"Suggest features to cut"
```

### Task Review

```
"Show me tasks for Sprint 1"
"Reassign TASK-005 to Daniel"
"What's assigned to Ava?"
"Add a task for API documentation"
```

### Confirmation

```
"Confirm plan"
"I approve this plan"
"Lock it in"
```

### General Queries

```
"What's our total cost?"
"How many hours for QA?"
"When will feature X be done?"
"Are we under budget?"
```

---

## Advanced Configuration

### Custom Models

Edit `src/pipeline/config.py` or set environment variables:

```python
# Use Gemini 1.5 Pro for everything
GEMINI_MODEL=gemini-1.5-pro-latest

# Use different models for different phases
GEMINI_MODEL=gemini-2.0-flash-exp           # Phase 1 & 2 agents
GEMINI_PRD_MODEL=gemini-1.5-pro-latest      # PRD synthesis only
```

### Adding Custom Tools

Edit `src/agents/pm_agent.py`:

```python
@tool("my_custom_tool")
def my_custom_tool(input_data: str) -> str:
    """
    Tool description for the agent.
    
    Args:
        input_data: What the agent should pass in
        
    Returns:
        JSON string or plain text result
    """
    # Your logic here
    result = do_something(input_data)
    return json.dumps(result)

# Register in build_tools()
def build_tools(config, llm):
    tools = [
        competitor_report,
        load_csv,
        my_custom_tool,  # Add here
        # ...
    ]
    return tools
```

### Modifying Agent Behavior

**Change Phase 1 prompts** (`src/pipeline/phase1.py`):
```python
def _build_fact_instruction(self, product_text: str) -> str:
    guidance = {
        "objective": "Your custom objective",
        "constraints": [
            "Your custom constraint 1",
            "Your custom constraint 2"
        ]
    }
    # ...
```

**Change Phase 2 prompts** (`src/pipeline/phase2_llm.py`):
```python
def _build_instruction(self, prd_markdown: str, structured_spec) -> str:
    guidance = {
        "objective": "Your custom planning objective",
        # ...
    }
```

---

## Troubleshooting

### "Module not found" errors

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Agent returns incomplete JSON

**Check**:
1. `outputs/phase1_fact_parse_error.txt` - Shows raw agent output
2. Web search API key is set (SERPAPI_KEY or EXA_API_KEY)
3. GOOGLE_API_KEY is valid

**The agent has automatic fallback** - it will extract facts from tool outputs even if the model truncates mid-response.

### Backend won't start

```bash
# Install FastAPI dependencies
pip install fastapi uvicorn python-multipart pydantic

# Check port 8000 is free
lsof -i :8000
```

### Frontend can't connect

1. Ensure backend is running on `http://localhost:8000`
2. Check browser console for CORS errors
3. Try clearing browser cache

### PDF generation fails

```bash
# Install chart libraries
pip install matplotlib reportlab

# Check outputs directory permissions
ls -la outputs/
```

### Out of Gemini quota

**Error**: `429 Too Many Requests`

**Solutions**:
- Wait for quota reset
- Upgrade Gemini API tier
- Reduce `max_output_tokens` in config
- Use caching (Phase 1 outputs can be reused)

---

## Performance Optimization

### Speed Up Analysis

1. **Use cached Phase 1 outputs**:
   ```python
   # In backend_api.py, load existing facts instead of re-running
   facts = json.loads(Path("outputs/phase1_facts.json").read_text())
   ```

2. **Reduce tool calls**:
   ```python
   # In phase1.py, lower max iterations
   agent = create_pm_agent(config, max_iterations=6)  # Instead of 10
   ```

3. **Use faster model**:
   ```bash
   GEMINI_MODEL=gemini-1.5-flash-latest  # Faster than 2.0
   ```

### Reduce Costs

1. **Shorter prompts**: Remove verbose instructions
2. **Lower output tokens**: Set `max_output_tokens=1024` for Phase 1
3. **Cache competitor data**: Store results, don't re-search every run
4. **Use SerpAPI free tier**: 100 searches/month

---

## Production Deployment

### Backend (FastAPI)

```bash
# Install production server
pip install gunicorn

# Run with Gunicorn
gunicorn backend_api:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# OR with Docker
docker build -t pm-backend .
docker run -p 8000:8000 pm-backend
```

### Frontend (React)

```bash
cd frontend
npm run build

# Serve with nginx/Apache
# Or deploy to Vercel/Netlify
```

### Environment

- Use **Redis** for session storage (replace in-memory dict)
- Add **database** for persistence (PostgreSQL/MongoDB)
- Enable **authentication** (JWT tokens)
- Add **rate limiting** (slowapi)
- Use **env-specific configs** (production.env)

---

## Integration Examples

### Jira Automation (For Teammates)

```python
import requests
import json

# Load Jira payload
jira_data = json.load(open("outputs/phase2_jira_payload.json"))

# Push to Jira
for issue in jira_data:
    response = requests.post(
        "https://your-domain.atlassian.net/rest/api/3/issue",
        auth=("email", "api_token"),
        json={
            "fields": {
                "project": {"key": "PROJ"},
                "summary": issue["title"],
                "description": issue["description"],
                "issuetype": {"name": issue["issue_type"]},
                "assignee": {"emailAddress": issue["assignee"]},
                # ...
            }
        }
    )
```

### Email Notifications (For Teammates)

```python
import smtplib
from email.mime.text import MIMEText

# Load email data
tasks = json.load(open("outputs/phase2_tasks.json"))
emails = tasks["email_notifications"]

for email in emails:
    msg = MIMEText(email["body"])
    msg["Subject"] = email["subject"]
    msg["To"] = email["to"]
    
    # Send via SMTP
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login("your_email", "app_password")
        server.send_message(msg)
```

---

## FAQ

**Q: Can I use this without a web search API?**
A: Yes, but competitor research will be limited. The agent will use only local knowledge.

**Q: Does this actually create Jira issues?**
A: No - this module only generates the JSON payload. Your teammates' module handles the actual Jira API integration.

**Q: Can I run this offline?**
A: No - it requires internet for Gemini API and web search.

**Q: How long does a typical analysis take?**
A: 30-90 seconds for Phase 1, 20-60 seconds for Phase 2 (depends on complexity).

**Q: Can I use OpenAI instead of Gemini?**
A: Yes - replace `ChatGoogleGenerativeAI` with `ChatOpenAI` in `pm_agent.py` and update imports.

**Q: Is my data stored anywhere?**
A: Only locally in `uploads/{session_id}/`. Nothing sent to external services except API calls.

---

## Support & Contributions

**Found a bug?** Open an issue on GitHub
**Want to contribute?** Submit a pull request
**Need help?** Check `outputs/*_error.txt` files for debug info

---

## Roadmap

- [ ] Multi-session management UI
- [ ] Real-time collaboration (WebSockets)
- [ ] Template library (different project types)
- [ ] Cost estimation improvements (cloud resources)
- [ ] Integration marketplace (Slack, Trello, etc.)
- [ ] Mobile app companion

---

**Happy Planning! 🚀**
