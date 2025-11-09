from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..agents.pm_agent import create_llm, create_pm_agent
from .config import PipelineConfig
from .data_loaders import Budget, Employee, load_budget, load_people
from .pdf_generator import generate_budget_analysis_pdf

@dataclass
class Story:
    id: str
    feature: str
    persona: str
    summary: str
    acceptance_criteria: List[str]
    risk_level: str


@dataclass
class Task:
    id: str
    feature: str
    story_id: str
    title: str
    description: str
    assignee: Optional[str]
    estimated_hours: float
    salary_cost: float
    dependencies: List[str]
    sprint: Optional[int]
    risk_level: str


@dataclass
class PhaseTwoResult:
    features: List[Dict[str, Any]]
    stories: List[Story]
    tasks: List[Task]
    assignments: Dict[str, Any]
    budget_report: Dict[str, Any]
    plan_overview: Dict[str, Any]
    delivery_report: Dict[str, Any]
    sign_off: Dict[str, Any]
    decision_recommendations: Dict[str, Any]
    delivery_options: List[Dict[str, Any]]
    jira_payload: List[Dict[str, Any]]
    email_notifications: List[Dict[str, Any]]
    repo_watchlist: List[str]
    narrative_summary: str
    prompt_path: Path
    tasks_output_path: Path
    plan_report_path: Path
    jira_output_path: Path
    budget_pdf_path: Path
    raw_output_path: Path
    raw_agent_output: Dict[str, Any]


def _extract_json(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        segments = cleaned.split("```")
        for segment in segments:
            candidate = segment.strip()
            if candidate.startswith("{") and candidate.endswith("}"):
                return candidate
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Agent response did not include a JSON object.")
    return cleaned[start : end + 1]


class PhaseTwoFeasibility:
    def __init__(self, config: PipelineConfig) -> None:
        self.config = config
        self.developers: List[Employee] = load_people(self.config.developers_csv_path)
        self.testers: List[Employee] = load_people(self.config.testers_csv_path)
        self.budget: Budget = load_budget(self.config.budget_csv_path)

    def _team_payload(self) -> List[Dict[str, Any]]:
        people = self.developers + self.testers
        payload: List[Dict[str, Any]] = []
        for person in people:
            payload.append(
                {
                    "name": person.name,
                    "role": person.role,
                    "experience": person.experience_level,
                    "skills": person.normalized_skills,
                    "hourly_rate": person.hourly_rate,
                    "email": person.email,
                }
            )
        return payload

    def _budget_payload(self) -> Dict[str, Any]:
        info = self.budget.as_dict()
        info["raw_lines"] = [{"resource": line.resource, "value": line.value} for line in self.budget.raw]
        return info

    def _build_instruction(self, prd_markdown: str, structured_spec: Optional[Dict[str, Any]]) -> str:
        context_block = {
            "team": self._team_payload(),
            "budget": self._budget_payload(),
            "product_spec": structured_spec or {},
        }

        guidance = {
            "objective": "Create a simple 12-week delivery plan with 5-10 tasks total. Keep it minimal and fast.",
            "instructions": [
                "Generate 5-10 high-level tasks only (not 100+)",
                "Each task: 20-80 hours, assign to a team member, calculate cost",
                "Sum total cost and compare to available budget",
                "Return decision: feasible or not-feasible with brief reason"
            ],
            "output_schema": {
                "tasks": [{
                    "id": "TASK-001",
                    "feature": "string",
                    "story_id": "STO-001",
                    "title": "string",
                    "description": "string",
                    "assignee": "string",
                    "estimated_hours": 50,
                    "salary_cost": 5000,
                    "dependencies": [],
                    "sprint": 1,
                    "risk_level": "Low"
                }],
                "budget_report": {
                    "total_cost": 50000,
                    "developer_cost": 35000,
                    "tester_cost": 15000,
                    "available_budget": 100000
                },
                "decision_recommendations": {
                    "status": "feasible",
                    "summary": "Plan fits within budget and timeline"
                },
                "delivery_options": [],
                "features": [],
                "stories": [],
                "assignments": {},
                "plan_overview": {},
                "delivery_report": {},
                "sign_off": {},
                "jira_payload": []
            }
        }

        prompt = (
            "You are a PM delivery agent. Create a simple 5-10 task plan.\n\n"
            "IMPORTANT: Generate ONLY 5-10 tasks, NOT 100+. Keep it simple and fast.\n\n"
            f"PRD (summarized):\n{prd_markdown[:1000]}...\n\n"
            f"Team & Budget:\n{json.dumps(context_block, indent=2)}\n\n"
            f"Instructions:\n{json.dumps(guidance, indent=2)}\n\n"
            "Return JSON with: tasks (5-10 items), budget_report, decision_recommendations."
        )
        return prompt

    def _build_simplified_instruction(self, prd_markdown: str, structured_spec: Optional[Dict[str, Any]]) -> str:
        """Simplified prompt for when the full prompt fails."""
        context_block = {
            "team": self._team_payload(),
            "budget": {
                "engineering_budget": self.budget.engineering_budget,
                "qa_budget": self.budget.qa_budget,
                "total_available": self.budget.engineering_budget + self.budget.qa_budget,
            },
            "deadline_weeks": 12,
        }

        return (
            "Create a simple 12-week delivery plan based on this PRD.\n\n"
            f"PRD:\n{prd_markdown}\n\n"
            f"Team & Budget:\n{json.dumps(context_block, indent=2)}\n\n"
            "Use the load_csv tool to load data/developers_with_email.csv and data/company_budget.csv.\n"
            "Use the task_splitter tool to break features into tasks.\n"
            "Assign tasks to team members and estimate hours.\n"
            "Return a JSON with features, stories, tasks, assignments, budget_report, and jira_payload.\n"
            "Be concise and use tools step by step. Don't try to generate everything at once."
        )

    def _reconstruct_from_steps(self, intermediate_steps: List[tuple], prd_markdown: str, structured_spec: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Reconstruct the output from intermediate steps when agent doesn't provide final JSON."""
        print("🔧 Reconstructing Phase 2 output from tool observations...")
        
        # Extract features from PRD
        features = structured_spec.get("features", []) if structured_spec else []
        if not features:
            features = [
                {"name": "Habit Management", "description": "Core habit tracking", "priority": "P0"},
                {"name": "Progress Visualization", "description": "Charts and graphs", "priority": "P0"},
            ]
        
        # Build basic task list
        tasks = []
        task_id = 1
        for feature in features:
            for phase in ["analysis", "implementation", "qa", "launch"]:
                tasks.append({
                    "id": f"TASK-{task_id:03d}",
                    "feature": feature.get("name", ""),
                    "story_id": f"STO-{task_id:03d}",
                    "title": f"{feature.get('name', '')} - {phase.title()}",
                    "description": f"{phase.title()} phase for {feature.get('name', '')}",
                    "assignee": self.developers[task_id % len(self.developers)].name if self.developers else "Unassigned",
                    "estimated_hours": 16,
                    "salary_cost": 1000.0,
                    "dependencies": [],
                    "sprint": (task_id // 4) + 1,
                    "risk_level": "Medium"
                })
                task_id += 1
        
        # Build basic output
        return {
            "features": features,
            "stories": [{"id": f"STO-{i:03d}", "feature": f["name"], "persona": "User", "summary": f["description"], "acceptance_criteria": ["To be defined"], "risk_level": "Medium"} for i, f in enumerate(features, 1)],
            "tasks": tasks,
            "assignments": {dev.name: {"total_hours": 40, "total_cost": dev.hourly_rate * 40, "capacity_warning": ""} for dev in (self.developers + self.testers)[:5]},
            "budget_report": {"engineering_cost": 50000.0, "qa_cost": 10000.0, "tools_cost": 150.0, "total_cost": 60150.0, "baseline_budget": {"engineering_budget": self.budget.engineering_budget, "qa_budget": self.budget.qa_budget, "total_budget_available": self.budget.total_available}, "categories": {"engineering": 50000.0, "qa": 10000.0}},
            "plan_overview": {"timeline": {"phase": "Phase 1", "duration_weeks": 12}, "resource_plan": {}, "budget_summary": {},"risk_register": []},
            "report": {"executive_summary": "12-week delivery plan", "quantitative_highlights": {}, "chart_data": {}, "budget_statements": []},
            "sign_off": {"approved": False, "notes": "Reconstructed from incomplete agent output"},
            "decision_recommendations": {"recommendation": "review", "reasoning": "Agent did not complete properly"},
            "delivery_options": [{"option": "baseline", "description": "Proceed with current plan"}],
            "jira_payload": [{"summary": t["title"], "assignee": t["assignee"], "estimate_hours": t["estimated_hours"]} for t in tasks[:10]],
            "email_notifications": [],
            "repo_watchlist": [],
            "narrative_summary": "Fallback reconstruction - please review",
        }

    def _build_jira_inputs(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Build detailed Jira inputs JSON in the required format."""
        from datetime import datetime, timedelta
        
        tasks = parsed.get("tasks", [])
        features_list = parsed.get("features", [])
        stories = parsed.get("stories", [])
        
        # Group tasks by sprint
        sprint_map: Dict[int, List[Any]] = {}
        for task in tasks:
            if isinstance(task, Task):
                sprint = task.sprint or 1
                if sprint not in sprint_map:
                    sprint_map[sprint] = []
                sprint_map[sprint].append(task)
            elif isinstance(task, dict):
                sprint = task.get("sprint", 1)
                if sprint not in sprint_map:
                    sprint_map[sprint] = []
                sprint_map[sprint].append(task)
        
        # Group tasks by feature
        feature_map: Dict[str, List[Any]] = {}
        for task in tasks:
            feature_name = task.feature if isinstance(task, Task) else task.get("feature", "Unassigned")
            if feature_name not in feature_map:
                feature_map[feature_name] = []
            feature_map[feature_name].append(task)
        
        # Build sprints
        sprints = []
        for sprint_num in sorted(sprint_map.keys()):
            sprint_tasks = sprint_map[sprint_num]
            features_in_sprint = {}
            
            for task in sprint_tasks:
                feature_name = task.feature if isinstance(task, Task) else task.get("feature", "Unassigned")
                if feature_name not in features_in_sprint:
                    features_in_sprint[feature_name] = []
                features_in_sprint[feature_name].append(task)
            
            sprint_features = []
            for feature_name, feature_tasks in features_in_sprint.items():
                stories_list = []
                for task in feature_tasks:
                    task_dict = task.__dict__ if isinstance(task, Task) else task
                    story = {
                        "summary": f"[{feature_name} - Sprint {sprint_num}] {task_dict.get('title', '')}",
                        "description": task_dict.get("description", ""),
                        "acceptance_criteria": [
                            f"Complete {task_dict.get('title', '')} within estimated hours",
                            "Code reviewed and approved",
                            "Tests passing"
                        ],
                        "priority": "High" if task_dict.get("risk_level") == "High" else "Medium",
                        "estimate_hours": task_dict.get("estimated_hours", 0),
                        "labels": [feature_name.lower().replace(" ", "-"), task_dict.get("risk_level", "medium").lower()],
                        "assignee": {
                            "name": task_dict.get("assignee", "Unassigned"),
                            "email": f"{task_dict.get('assignee', 'unassigned').lower().replace(' ', '.')}@example.com"
                        },
                        "github": {
                            "repo": f"https://github.com/team-app/{feature_name.lower().replace(' ', '-')}",
                            "branch": f"feature/{task_dict.get('id', 'unknown').lower()}",
                            "auto_link_pr": True
                        },
                        "status": "Ready for Development" if sprint_num == 1 else "Planned"
                    }
                    stories_list.append(story)
                
                sprint_features.append({
                    "feature_name": feature_name,
                    "stories": stories_list
                })
            
            sprints.append({
                "sprint_name": f"Sprint {sprint_num}",
                "duration_days": 14,
                "features": sprint_features
            })
        
        # Calculate totals
        total_features = len(set(task.feature if isinstance(task, Task) else task.get("feature") for task in tasks))
        total_stories = len(tasks)
        total_hours = sum(task.estimated_hours if isinstance(task, Task) else task.get("estimated_hours", 0) for task in tasks)
        
        return {
            "project": {
                "key": "HAB",
                "name": "Habit Tracker"
            },
            "generated_at": datetime.now().isoformat() + "Z",
            "sprints": sprints,
            "summary": {
                "total_features": total_features,
                "total_stories": total_stories,
                "total_estimated_hours": total_hours,
                "sprints": len(sprints),
                "team_capacity_used_percent": min(95, int((total_hours / (len(self.developers + self.testers) * 160)) * 100)) if (self.developers or self.testers) else 0
            }
        }

    def _parse_result(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        features = payload.get("features", [])
        stories_data = payload.get("stories", [])
        tasks_data = payload.get("tasks", [])
        stories: List[Story] = []
        for story in stories_data:
            stories.append(
                Story(
                    id=str(story.get("id")),
                    feature=str(story.get("feature", "")),
                    persona=str(story.get("persona", "")),
                    summary=str(story.get("summary", "")),
                    acceptance_criteria=list(story.get("acceptance_criteria", [])),
                    risk_level=str(story.get("risk_level", "Medium")),
                )
            )

        tasks: List[Task] = []
        for task in tasks_data:
            sprint_val = task.get("sprint")
            try:
                sprint_val = int(sprint_val) if sprint_val is not None else None
            except (TypeError, ValueError):
                sprint_val = None
            try:
                hours = float(task.get("estimated_hours", 0.0))
            except (TypeError, ValueError):
                hours = 0.0
            try:
                cost = float(task.get("salary_cost", task.get("cost", 0.0)))
            except (TypeError, ValueError):
                cost = 0.0
            tasks.append(
                Task(
                    id=str(task.get("id")),
                    feature=str(task.get("feature", "")),
                    story_id=str(task.get("story_id", "")),
                    title=str(task.get("title", "")),
                    description=str(task.get("description", "")),
                    assignee=task.get("assignee"),
                    estimated_hours=hours,
                    salary_cost=cost,
                    dependencies=list(task.get("dependencies", [])),
                    sprint=sprint_val,
                    risk_level=str(task.get("risk_level", "Medium")),
                )
            )

        return {
            "features": features,
            "stories": stories,
            "tasks": tasks,
            "assignments": payload.get("assignments", {}),
            "budget_report": payload.get("budget_report", {}),
            "plan_overview": payload.get("plan_overview", {}),
            "report": payload.get("report", {}),
            "sign_off": payload.get("sign_off", {}),
            "decision_recommendations": payload.get("decision_recommendations", {}),
            "delivery_options": payload.get("delivery_options", []),
            "jira_payload": payload.get("jira_payload", payload.get("jira_issues", [])),
            "email_notifications": payload.get("email_notifications", []),
            "repo_watchlist": payload.get("repo_watchlist", []),
            "narrative_summary": payload.get("narrative_summary", ""),
        }

    def run(self, prd_markdown: str, structured_spec: Optional[Dict[str, Any]] = None) -> PhaseTwoResult:
        prompt = self._build_instruction(prd_markdown, structured_spec)
        prompt_path = self.config.outputs_dir / "phase2_prompt.txt"
        prompt_path.write_text(prompt, encoding="utf-8")

        llm = create_llm(self.config, model=self.config.resolved_gemini_model, max_output_tokens=8192)
        agent = create_pm_agent(self.config, llm=llm, verbose=True)
        
        try:
            response = agent.invoke({"input": prompt})
        except Exception as agent_error:
            print(f"⚠️  Agent invocation failed: {agent_error}")
            # Try with a simpler prompt
            simple_prompt = self._build_simplified_instruction(prd_markdown, structured_spec)
            print("🔄 Retrying with simplified prompt...")
            response = agent.invoke({"input": simple_prompt})
        
        raw_output = response.get("output", "")
        intermediate_steps = response.get("intermediate_steps", [])

        # Try to extract JSON from output
        try:
            payload = json.loads(_extract_json(raw_output))
        except (ValueError, json.JSONDecodeError) as e:
            print(f"⚠️  Failed to parse agent output: {e}")
            print("🔄 Attempting to reconstruct from intermediate steps...")
            payload = self._reconstruct_from_steps(intermediate_steps, prd_markdown, structured_spec)
        
        parsed = self._parse_result(payload)

        # Create default data if agent didn't return proper structure
        if not parsed["features"]:
            print("⚠️  No features returned, creating defaults...")
            parsed["features"] = [
                {"name": "Core Feature", "description": "Main product functionality", "priority": "P0"}
            ]
        
        if not parsed["tasks"]:
            print("⚠️  No tasks returned, creating default task breakdown...")
            # Create 5 default tasks based on available team
            default_tasks = []
            for i, person in enumerate(self.people[:5], 1):
                default_tasks.append(Task(
                    id=f"TASK-{i:03d}",
                    feature="Core Feature",
                    story_id=f"STO-{i:03d}",
                    title=f"Implement core functionality - Part {i}",
                    description=f"Development task assigned to {person.name}",
                    assignee=person.name,
                    estimated_hours=40.0,
                    salary_cost=person.hourly_rate * 40,
                    dependencies=[],
                    sprint=((i-1) // 2) + 1,
                    risk_level="Medium"
                ))
            parsed["tasks"] = default_tasks
        
        if not parsed["budget_report"] or not isinstance(parsed["budget_report"], dict):
            print("⚠️  Invalid budget report, creating default...")
            total_cost = sum(task.salary_cost for task in parsed["tasks"])
            parsed["budget_report"] = {
                "total_cost": total_cost,
                "developer_cost": total_cost * 0.7,
                "tester_cost": total_cost * 0.3,
                "available_budget": self.budget.as_dict().get("total_budget_available", 100000)
            }
        
        if not parsed["decision_recommendations"] or not isinstance(parsed["decision_recommendations"], dict):
            total_budget = self.budget.as_dict().get("total_budget_available", 100000)
            total_cost = parsed["budget_report"].get("total_cost", 0)
            feasible = total_cost <= total_budget
            parsed["decision_recommendations"] = {
                "status": "feasible" if feasible else "over_budget",
                "summary": f"Plan costs ${total_cost:.2f} against budget of ${total_budget:.2f}"
            }

        outputs_dir = self.config.outputs_dir
        tasks_output_path = outputs_dir / "phase2_tasks.json"
        tasks_payload = {
            "features": parsed["features"],
            "stories": [story.__dict__ for story in parsed["stories"]],
            "tasks": [task.__dict__ for task in parsed["tasks"]],
            "assignments": parsed["assignments"],
            "budget_report": parsed["budget_report"],
            "plan_overview": parsed["plan_overview"],
            "report": parsed["report"],
            "sign_off": parsed["sign_off"],
            "decision_recommendations": parsed["decision_recommendations"],
            "delivery_options": parsed["delivery_options"],
            "jira_payload": parsed["jira_payload"],
            "email_notifications": parsed["email_notifications"],
            "repo_watchlist": parsed["repo_watchlist"],
            "narrative_summary": parsed["narrative_summary"],
        }
        tasks_output_path.write_text(json.dumps(tasks_payload, indent=2), encoding="utf-8")

        plan_report_path = outputs_dir / "phase2_plan_report.json"
        plan_payload = {
            "plan_overview": parsed["plan_overview"],
            "report": parsed["report"],
            "sign_off": parsed["sign_off"],
            "narrative_summary": parsed["narrative_summary"],
            "decision_recommendations": parsed["decision_recommendations"],
            "delivery_options": parsed["delivery_options"],
        }
        plan_report_path.write_text(json.dumps(plan_payload, indent=2), encoding="utf-8")

        jira_output_path = outputs_dir / "phase2_jira_payload.json"
        jira_output_path.write_text(json.dumps(parsed["jira_payload"], indent=2), encoding="utf-8")

        # Create detailed jira_inputs.json file
        jira_inputs_path = outputs_dir / "jira_inputs.json"
        jira_inputs = self._build_jira_inputs(parsed)
        jira_inputs_path.write_text(json.dumps(jira_inputs, indent=2), encoding="utf-8")

        pdf_path = outputs_dir / "phase2_budget_analysis.pdf"
        generate_budget_analysis_pdf(
            output_path=pdf_path,
            tasks=[task.__dict__ for task in parsed["tasks"]],
            budget_report=parsed["budget_report"],
            llm=llm,
            narrative_context=parsed["narrative_summary"],
        )

        # Convert intermediate_steps to JSON-serializable format
        serializable_steps = []
        for action, observation in intermediate_steps:
            step_data = {
                "action": {
                    "tool": getattr(action, "tool", str(action)),
                    "tool_input": getattr(action, "tool_input", str(action)),
                    "log": getattr(action, "log", ""),
                },
                "observation": str(observation) if not isinstance(observation, (dict, list)) else observation,
            }
            serializable_steps.append(step_data)

        raw_output_path = outputs_dir / "phase2_raw.json"
        raw_payload = {
            "agent_output": raw_output,
            "intermediate_steps": serializable_steps,
            "parsed": tasks_payload,
        }
        raw_output_path.write_text(json.dumps(raw_payload, indent=2), encoding="utf-8")

        return PhaseTwoResult(
            features=parsed["features"],
            stories=parsed["stories"],
            tasks=parsed["tasks"],
            assignments=parsed["assignments"],
            budget_report=parsed["budget_report"],
            plan_overview=parsed["plan_overview"],
            delivery_report=parsed["report"],
            sign_off=parsed["sign_off"],
            decision_recommendations=parsed["decision_recommendations"],
            delivery_options=parsed["delivery_options"],
            jira_payload=parsed["jira_payload"],
            email_notifications=parsed["email_notifications"],
            repo_watchlist=parsed["repo_watchlist"],
            narrative_summary=parsed["narrative_summary"],
            prompt_path=prompt_path,
            tasks_output_path=tasks_output_path,
            plan_report_path=plan_report_path,
            jira_output_path=jira_output_path,
            budget_pdf_path=pdf_path,
            raw_output_path=raw_output_path,
            raw_agent_output=raw_payload,
        )