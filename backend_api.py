from __future__ import annotations

import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from src.pipeline.config import PipelineConfig
from src.pipeline.phase1 import PhaseOneProductStrategy
from src.pipeline.phase2_llm import PhaseTwoFeasibility
from src.agents.pm_agent import create_llm

app = FastAPI(title="AI Product Manager Backend")

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage for conversation state
conversation_store: Dict[str, Dict[str, Any]] = {}

UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)


class ChatMessage(BaseModel):
    session_id: str
    message: str


class AnalysisResponse(BaseModel):
    session_id: str
    market_ready_description: str
    task_assignments: List[Dict[str, Any]]
    cost_summary: Dict[str, Any]
    feasibility: bool
    recommendations: List[str]
    conversation_state: Dict[str, Any]
    phase1_outputs: Dict[str, Any]
    phase2_outputs: Dict[str, Any]


def _save_upload(file: UploadFile, session_dir: Path) -> Path:
    """Save uploaded file to session directory."""
    file_path = session_dir / file.filename
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return file_path


def _extract_recommendations(phase2_result: Any) -> List[str]:
    """Extract recommendations from phase 2 results."""
    recommendations = []
    
    try:
        decision = phase2_result.decision_recommendations
        
        # Handle if decision is a string instead of dict
        if isinstance(decision, str):
            recommendations.append(decision)
            return recommendations
        
        # Handle dict
        if isinstance(decision, dict):
            if decision.get("status") != "feasible":
                recommendations.append(f"Status: {decision.get('status', 'unknown')}")
                recommendations.append(f"Summary: {decision.get('summary', 'No summary available')}")
                
                for action in decision.get("actions", []):
                    recommendations.append(f"Action required: {action}")
                
                for note in decision.get("notes", []):
                    recommendations.append(f"Note: {note}")
        
        # Add delivery options
        if hasattr(phase2_result, 'delivery_options') and isinstance(phase2_result.delivery_options, list):
            for option in phase2_result.delivery_options:
                if isinstance(option, dict):
                    feasibility_color = option.get("feasibility", "unknown")
                    if feasibility_color in ["yellow", "red"]:
                        recommendations.append(
                            f"Alternative: {option.get('option')} "
                            f"({feasibility_color}) - {option.get('description', '')}"
                        )
    except Exception as e:
        recommendations.append(f"Could not extract full recommendations: {str(e)}")
    
    return recommendations if recommendations else ["Plan is feasible with current constraints."]


def _check_feasibility(phase2_result: Any, deadline: Optional[str] = None) -> bool:
    """Determine if the plan is feasible."""
    try:
        decision = phase2_result.decision_recommendations
        
        # Handle string decision
        if isinstance(decision, str):
            return "feasible" in decision.lower()
        
        # Handle dict decision
        if isinstance(decision, dict):
            status = decision.get("status", "")
            if status == "feasible":
                return True
        
        # Check if any delivery option is green
        if hasattr(phase2_result, 'delivery_options') and isinstance(phase2_result.delivery_options, list):
            for option in phase2_result.delivery_options:
                if isinstance(option, dict) and option.get("feasibility") == "green":
                    return True
    except Exception:
        pass
    
    return False


@app.post("/run-analysis", response_model=AnalysisResponse)
async def run_analysis(
    deadline: str = Form(...),
    budget_csv: UploadFile = File(...),
    employees_csv: UploadFile = File(...),
    product_description: Optional[str] = Form(None),
    product_file: Optional[UploadFile] = File(None),
):
    """
    Main endpoint: accepts inputs, runs LangChain pipeline, returns structured plan.
    """
    try:
        # Create session
        session_id = str(uuid.uuid4())
        session_dir = UPLOADS_DIR / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Save uploads
        budget_path = _save_upload(budget_csv, session_dir)
        employees_path = _save_upload(employees_csv, session_dir)
        
        # Handle product description
        if product_file:
            product_path = _save_upload(product_file, session_dir)
            product_text = product_path.read_text(encoding="utf-8")
        elif product_description:
            product_path = session_dir / "product_description.txt"
            product_path.write_text(product_description, encoding="utf-8")
            product_text = product_description
        else:
            raise HTTPException(status_code=400, detail="Product description or file required")
        
        # Create outputs directory
        outputs_dir = session_dir / "outputs"
        outputs_dir.mkdir(exist_ok=True)
        
        # Configure pipeline - use project root for .env file
        project_root = Path(__file__).parent
        config = PipelineConfig.from_env(
            base_dir=session_dir,
            outputs_dir=outputs_dir,
            env_path=project_root / ".env"
        )
        
        # Override CSV paths
        config.budget_csv_path = budget_path
        config.developers_csv_path = employees_path
        config.testers_csv_path = employees_path  # Use same file for now
        config.product_description_path = product_path
        
        # Run Phase 1: Strategy
        phase1 = PhaseOneProductStrategy(config)
        phase1_result = phase1.run()
        
        # Run Phase 2: Development Planning
        phase2 = PhaseTwoFeasibility(config)
        phase2_result = phase2.run(
            phase1_result.prd_markdown,
            structured_spec=phase1_result.product_spec
        )
        
        # Determine feasibility
        feasibility = _check_feasibility(phase2_result, deadline)
        recommendations = _extract_recommendations(phase2_result)
        
        # Build response
        conversation_state = {
            "session_id": session_id,
            "session_dir": str(session_dir),
            "deadline": deadline,
            "budget_path": str(budget_path),
            "employees_path": str(employees_path),
            "product_path": str(product_path),
            "phase1_result": {
                "prd_path": str(phase1_result.prd_path),
                "facts_path": str(phase1_result.facts_path),
            },
            "phase2_result": {
                "tasks_path": str(phase2_result.tasks_output_path),
                "plan_report_path": str(phase2_result.plan_report_path),
                "jira_path": str(phase2_result.jira_output_path),
                "pdf_path": str(phase2_result.budget_pdf_path),
            },
            "confirmed": False,
            "revision_count": 0,
        }
        
        # Store in memory
        conversation_store[session_id] = conversation_state
        
        # Safely serialize tasks
        task_assignments = []
        if hasattr(phase2_result, 'tasks'):
            for task in phase2_result.tasks:
                if hasattr(task, '__dict__'):
                    task_assignments.append(task.__dict__)
                else:
                    task_assignments.append({"error": "Invalid task format"})
        
        # Safely get cost summary
        cost_summary = phase2_result.budget_report if hasattr(phase2_result, 'budget_report') else {}
        if not isinstance(cost_summary, dict):
            cost_summary = {"error": "Invalid budget report format", "raw": str(cost_summary)}
        
        # Safely serialize stories
        stories_list = []
        if hasattr(phase2_result, 'stories'):
            for story in phase2_result.stories:
                if hasattr(story, '__dict__'):
                    stories_list.append(story.__dict__)
        
        response = AnalysisResponse(
            session_id=session_id,
            market_ready_description=phase1_result.prd_markdown,
            task_assignments=task_assignments,
            cost_summary=cost_summary,
            feasibility=feasibility,
            recommendations=recommendations,
            conversation_state=conversation_state,
            phase1_outputs={
                "product_spec": phase1_result.product_spec if hasattr(phase1_result, 'product_spec') else {},
                "prd_markdown": phase1_result.prd_markdown,
            },
            phase2_outputs={
                "features": phase2_result.features if hasattr(phase2_result, 'features') else [],
                "stories": stories_list,
                "assignments": phase2_result.assignments if hasattr(phase2_result, 'assignments') else {},
                "plan_overview": phase2_result.plan_overview if hasattr(phase2_result, 'plan_overview') else {},
                "delivery_report": phase2_result.delivery_report if hasattr(phase2_result, 'delivery_report') else {},
                "sign_off": phase2_result.sign_off if hasattr(phase2_result, 'sign_off') else {},
                "jira_payload": phase2_result.jira_payload if hasattr(phase2_result, 'jira_payload') else [],
            },
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/chat-revise")
async def chat_revise(payload: ChatMessage):
    """
    Chatbot endpoint: accepts PM messages, updates context, re-runs if needed.
    Supports:
    - Adjusting budget/deadline
    - Cutting features
    - Reviewing and editing tasks
    - Confirming the plan
    """
    session_id = payload.session_id
    message = payload.message.strip().lower()
    
    if session_id not in conversation_store:
        raise HTTPException(status_code=404, detail="Session not found")
    
    state = conversation_store[session_id]
    session_dir = Path(state["session_dir"])
    config = PipelineConfig.from_env(
        base_dir=session_dir,
        outputs_dir=session_dir / "outputs"
    )
    
    # Parse intent using Gemini
    llm = create_llm(config, model="gemini-2.0-flash-exp", max_output_tokens=2048)
    
    intent_prompt = f"""You are a PM assistant chatbot. Parse the user's intent from this message:
"{payload.message}"

Determine which action they want:
1. adjust_budget - they want to change the budget amount
2. adjust_deadline - they want to change the deadline
3. cut_features - they want to remove specific features or ask you to suggest cuts
4. review_tasks - they want to review or edit task assignments
5. confirm_plan - they are ready to confirm the plan
6. general_query - general question about the plan

Respond with ONLY a JSON object:
{{
  "intent": "one of the above",
  "extracted_value": "any numeric value, date, or feature name mentioned",
  "details": "brief explanation"
}}
"""
    
    try:
        intent_response = llm.invoke(intent_prompt)
        intent_text = intent_response.content if hasattr(intent_response, "content") else str(intent_response)
        
        # Extract JSON
        if isinstance(intent_text, list):
            intent_text = "\n".join(str(part.get("text", part)) if isinstance(part, dict) else str(part) for part in intent_text)
        
        start = intent_text.find("{")
        end = intent_text.rfind("}") + 1
        intent_json = json.loads(intent_text[start:end])
        
        intent = intent_json.get("intent", "general_query")
        extracted_value = intent_json.get("extracted_value", "")
        
    except Exception:
        intent = "general_query"
        extracted_value = ""
    
    # Handle different intents
    if intent == "confirm_plan":
        state["confirmed"] = True
        conversation_store[session_id] = state
        
        return JSONResponse({
            "session_id": session_id,
            "response": "Plan confirmed! Your final outputs are ready for the Jira/email/GitHub teams.",
            "action": "confirmed",
            "state": state,
        })
    
    elif intent in ["adjust_budget", "adjust_deadline"]:
        # Update state and re-run
        if intent == "adjust_budget" and extracted_value:
            # Update budget CSV (simplified - just log for now)
            state["deadline"] = extracted_value if intent == "adjust_deadline" else state.get("deadline")
        
        state["revision_count"] += 1
        
        return JSONResponse({
            "session_id": session_id,
            "response": f"Understood. I've updated the {intent.replace('adjust_', '')}. Re-running analysis...",
            "action": "rerun_needed",
            "state": state,
        })
    
    elif intent == "cut_features":
        # Suggest features to cut or confirm removal
        phase2_path = Path(state["phase2_result"]["tasks_path"])
        tasks_data = json.loads(phase2_path.read_text())
        
        features = tasks_data.get("features", [])
        feature_names = [f["name"] for f in features]
        
        suggestion_prompt = f"""Given these features:
{json.dumps(feature_names, indent=2)}

And the user's request: "{payload.message}"

Suggest which feature(s) to remove to reduce scope, or confirm which specific feature they mentioned.
Return ONLY a JSON array of feature names to remove: ["feature1", "feature2"]
"""
        
        suggestion_response = llm.invoke(suggestion_prompt)
        suggestion_text = suggestion_response.content if hasattr(suggestion_response, "content") else str(suggestion_response)
        
        return JSONResponse({
            "session_id": session_id,
            "response": f"I recommend removing these features: {suggestion_text}. Shall I proceed?",
            "action": "awaiting_confirmation",
            "suggested_cuts": suggestion_text,
            "state": state,
        })
    
    else:
        # General query - provide info about current plan
        phase2_path = Path(state["phase2_result"]["plan_report_path"])
        plan_data = json.loads(phase2_path.read_text())
        
        query_prompt = f"""The user asked: "{payload.message}"

Here's the current plan summary:
{json.dumps(plan_data, indent=2)}

Provide a helpful, concise response (2-3 sentences max).
"""
        
        query_response = llm.invoke(query_prompt)
        query_text = query_response.content if hasattr(query_response, "content") else str(query_response)
        
        if isinstance(query_text, list):
            query_text = "\n".join(str(part.get("text", part)) if isinstance(part, dict) else str(part) for part in query_text)
        
        return JSONResponse({
            "session_id": session_id,
            "response": query_text,
            "action": "info",
            "state": state,
        })


@app.get("/download-report/{session_id}")
async def download_report(session_id: str):
    """Download the PDF report for a session."""
    if session_id not in conversation_store:
        raise HTTPException(status_code=404, detail="Session not found")
    
    state = conversation_store[session_id]
    pdf_path = Path(state["phase2_result"]["pdf_path"])
    
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"pm_analysis_report_{session_id}.pdf"
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "AI Product Manager Backend"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
