from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict

from .config import PipelineConfig
from .data_loaders import dump_json
from .phase1 import PhaseOneProductStrategy
from .phase2_llm import PhaseTwoFeasibility


def orchestrate(base_dir: Path, outputs_dir: Path) -> Dict:
    config = PipelineConfig.from_env(base_dir=base_dir, outputs_dir=outputs_dir)

    phase1 = PhaseOneProductStrategy(config)
    phase1_result = phase1.run()

    phase2 = PhaseTwoFeasibility(config)
    phase2_result = phase2.run(phase1_result.prd_markdown, structured_spec=phase1_result.product_spec)

    final_payload = {
        "phase1": {
            "prd_path": str(phase1_result.prd_path),
            "raw_output": str(phase1_result.raw_output_path),
            "facts_path": str(phase1_result.facts_path),
            "structured_spec": phase1_result.product_spec,
        },
        "phase2": {
            "tasks_json": str(phase2_result.tasks_output_path),
            "plan_report_json": str(phase2_result.plan_report_path),
            "jira_payload_json": str(phase2_result.jira_output_path),
            "budget_pdf": str(phase2_result.budget_pdf_path),
            "features": phase2_result.features,
            "stories": [story.__dict__ for story in phase2_result.stories],
            "tasks": [task.__dict__ for task in phase2_result.tasks],
            "assignments": phase2_result.assignments,
            "budget_report": phase2_result.budget_report,
            "plan_overview": phase2_result.plan_overview,
            "delivery_report": phase2_result.delivery_report,
            "sign_off": phase2_result.sign_off,
            "decision_recommendations": phase2_result.decision_recommendations,
            "delivery_options": phase2_result.delivery_options,
            "jira_payload": phase2_result.jira_payload,
            "email_notifications": phase2_result.email_notifications,
            "repo_watchlist": phase2_result.repo_watchlist,
            "narrative_summary": phase2_result.narrative_summary,
            "raw_output": str(phase2_result.raw_output_path),
        },
    }

    final_output_path = config.outputs_dir / "final_output.json"
    dump_json(final_output_path, final_payload)
    return final_payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Agentic Product Management pipeline.")
    parser.add_argument("--base-dir", type=str, default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--outputs-dir", type=str, default=str(Path(__file__).resolve().parents[2] / "outputs"))
    args = parser.parse_args()

    base_dir = Path(args.base_dir).resolve()
    outputs_dir = Path(args.outputs_dir).resolve()
    payload = orchestrate(base_dir, outputs_dir)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
