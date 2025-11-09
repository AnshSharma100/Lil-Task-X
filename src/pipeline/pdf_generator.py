from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import matplotlib.pyplot as plt
from langchain_core.language_models import BaseLanguageModel
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

def _render_pie_chart(output_dir: Path, budget_report: Dict[str, Any]) -> Path:
    categories = budget_report.get("categories") or budget_report.get("breakdown") or {}
    if not categories and all(isinstance(v, (int, float)) for v in budget_report.values()):
        categories = budget_report
    if not categories:
        categories = {"Unspecified": budget_report.get("total", 1)}

    labels = list(categories.keys())
    values = [max(float(v), 0.01) for v in categories.values()]

    fig, ax = plt.subplots()
    ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=140)
    ax.axis("equal")
    pie_path = output_dir / "budget_pie.png"
    fig.savefig(pie_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return pie_path


def _render_bar_chart(output_dir: Path, tasks: List[Dict[str, Any]]) -> Path:
    allocation: Dict[str, float] = {}
    for task in tasks:
        owner = task.get("assignee") or task.get("owner") or "Unassigned"
        hours = task.get("estimated_hours") or task.get("hours") or task.get("time", 0)
        try:
            allocation[owner] = allocation.get(owner, 0.0) + float(hours)
        except (TypeError, ValueError):
            allocation[owner] = allocation.get(owner, 0.0)

    if not allocation:
        allocation = {"No Data": 1.0}

    owners = list(allocation.keys())
    hours_values = [allocation[o] for o in owners]

    fig, ax = plt.subplots(figsize=(8, 3))
    ax.bar(owners, hours_values, color="#4F6D7A")
    ax.set_ylabel("Estimated Hours")
    ax.set_title("Time Allocation by Team Member")
    ax.set_xticks(range(len(owners)))
    ax.set_xticklabels(owners, rotation=45, ha="right")
    bar_path = output_dir / "time_allocation.png"
    fig.savefig(bar_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return bar_path


def _generate_summary(llm: BaseLanguageModel, tasks: List[Dict[str, Any]], budget_report: Dict[str, Any], narrative_context: str) -> str:
    structured_overview = {
        "task_sample": tasks[:5],
        "budget": budget_report,
        "context": narrative_context,
    }
    prompt = (
        "You are a senior PM. Summarise the engineering plan based solely on the provided data.\n"
        "Ensure every claim references the task or budget entries explicitly.\n"
        "Highlight feasibility status, key risks, and next actions.\n"
        "Return 3 concise paragraphs plus a bullet list of recommendations.\n"
        f"DATA:\n{json.dumps(structured_overview, indent=2)}"
    )
    response = llm.invoke(prompt)
    if hasattr(response, "content") and isinstance(response.content, list):
        return "\n".join(part["text"] if isinstance(part, dict) else str(part) for part in response.content)
    if hasattr(response, "content") and isinstance(response.content, str):
        return response.content
    return str(response)


def _build_task_table(tasks: List[Dict[str, Any]]) -> Table:
    headers = ["Task", "Feature", "Assignee", "Hours", "Cost (USD)"]
    rows = [headers]
    for task in tasks[:15]:
        rows.append(
            [
                str(task.get("id") or task.get("task_id") or "N/A"),
                str(task.get("feature") or task.get("title") or ""),
                str(task.get("assignee") or task.get("owner") or "Unassigned"),
                f"{float(task.get('estimated_hours', task.get('hours', 0))):.1f}",
                f"{float(task.get('cost', task.get('salary_cost', 0))):.2f}",
            ]
        )
    table = Table(rows, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
            ]
        )
    )
    return table


def generate_budget_analysis_pdf(
    *,
    output_path: Path,
    tasks: List[Dict[str, Any]],
    budget_report: Dict[str, Any],
    llm: BaseLanguageModel,
    narrative_context: str,
) -> Path:
    """Create the phase 2 PDF containing charts, tables, and LLM-generated summary."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        pie_path = _render_pie_chart(tmp_path, budget_report)
        bar_path = _render_bar_chart(tmp_path, tasks)
        summary = _generate_summary(llm, tasks, budget_report, narrative_context)

        doc = SimpleDocTemplate(str(output_path), pagesize=LETTER)
        styles = getSampleStyleSheet()
        elements: List[Any] = []

        elements.append(Paragraph("Phase 2 Budget Analysis", styles["Title"]))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("Generated by the LangChain PM Agent (Gemini-2.5)", styles["Italic"]))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(summary.replace("\n", "<br/>"), styles["BodyText"]))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("Budget Allocation", styles["Heading2"]))
        elements.append(Image(str(pie_path), width=400, height=300))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("Time Allocation", styles["Heading2"]))
        elements.append(Image(str(bar_path), width=400, height=250))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("Priority Tasks", styles["Heading2"]))
        elements.append(_build_task_table(tasks))

        doc.build(elements)

    return output_path