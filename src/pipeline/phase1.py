from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..agents.pm_agent import create_llm, create_pm_agent
from .config import PipelineConfig
from .data_loaders import load_product_description


@dataclass
class PhaseOneResult:
    product_spec: Dict[str, Any]
    prd_markdown: str
    raw_agent_output: Dict[str, Any]
    prompt_path: Path
    facts_path: Path
    prd_path: Path
    raw_output_path: Path


def _normalize_json_text(text: str) -> str:
    """Strip common wrappers like Final Answer prefixes or markdown fences."""
    cleaned = text.strip()
    if cleaned.lower().startswith("final answer:"):
        cleaned = cleaned.split(":", 1)[1].strip()
    if cleaned.startswith("```"):
        segments = cleaned.split("```")
        for segment in segments:
            candidate = segment.strip()
            if not candidate:
                continue
            if candidate.lower().startswith("json"):
                candidate = candidate[4:].strip()
            if candidate:
                cleaned = candidate
                break
    return cleaned.strip()


def _extract_json(text: str) -> str:
    """Extract the first JSON object from a model response."""
    cleaned = _normalize_json_text(text)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Agent response did not include a JSON object.")
    candidate = cleaned[start : end + 1]
    return candidate


class PhaseOneProductStrategy:
    def __init__(self, config: PipelineConfig) -> None:
        self.config = config

    @staticmethod
    def _coerce_content_to_text(content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: List[str] = []
            for part in content:
                if isinstance(part, dict) and "text" in part:
                    parts.append(str(part["text"]))
                else:
                    parts.append(str(part))
            return "\n".join(parts)
        return str(content)

    def _build_fact_instruction(self, product_text: str) -> str:
        available_csvs: list[str] = []
        shareholders_path = self.config.product_description_path.parent / "shareholders.csv"
        if shareholders_path.exists():
            available_csvs.append("data/shareholders.csv")
        available_csvs.append("data/developers_with_email.csv")
        available_csvs.append("data/testers_with_email.csv")

        guidance = {
            "objective": "Collect concise factual evidence to inform the downstream PRD writer.",
            "data_sources": {
                "product_description": "data/product_description.txt",
                "available_csvs": available_csvs,
            },
            "tools": ["competitor_report", "load_csv"],
            "output_schema": {
                "facts": {
                    "competitors": [
                        {
                            "name": "string",
                            "summary": "string",
                            "differentiators": ["string"],
                            "gaps": ["string"],
                            "sources": ["url"],
                        }
                    ],
                    "user_needs": ["string"],
                    "market_ranges": {
                        "tam_range": "string",
                        "sam_range": "string",
                        "som_range": "string",
                    },
                    "extracted_insights": ["string"],
                    "evidence_refs": ["string"],
                },
                "status": "complete|insufficient_data",
            },
            "constraints": [
                "Use competitor_report to validate every competitive claim.",
                "Limit yourself to at most 4 tool invocations; stop once required data is captured.",
                "Never invent competitor names; rely on returned data only.",
                "Surface only short bullet-style facts (keep strings under 240 characters).",
                "Temperature must remain 0; do not speculate beyond provided sources.",
                "Return minimal JSON (no markdown, no explanations).",
                "Return only valid JSON; no commentary or prose outside the JSON object.",
                "When ready to finish, do not emit another Thought; respond with 'Final Answer: ' immediately followed by the JSON object.",
                "Limit competitors to at most five entries and insights to six bullets.",
            ],
            "final_response": "Return a JSON object with keys 'facts' and 'status'.",
        }

        prompt = (
            "You are a senior product analyst agent operating with ReAct instructions.\n"
            "Your job is to collect verified evidence for a later writer.\n"
            "Follow these steps:\n"
            "- Read the product description to understand context.\n"
            "- Call competitor_report for Habitica, Todoist, Notion, and similar habit apps.\n"
            "- Optionally inspect CSVs if stakeholder info is critical (only if needed).\n"
            "- Output concise JSON facts only. Do not draft any narrative PRD sections.\n"
            "- Stop early once you have enough data to populate the schema.\n\n"
            f"Product Description:\n{product_text}\n\n"
            f"Directive JSON:\n{json.dumps(guidance, indent=2)}\n\n"
            "When you finish your reasoning steps, respond with Final Answer: {JSON}. No markdown fences, no extra narration outside the JSON object."
        )
        return prompt

    def _collect_tool_outputs(self, intermediate_steps: List[Any]) -> Dict[str, Any]:
        evidence: Dict[str, Any] = {
            "competitor_items": [],
            "competitor_overviews": [],
            "csv_rows": {},
            "raw_steps": [],
        }
        for action, observation in intermediate_steps:
            tool_name = getattr(action, "tool", "")
            tool_input = getattr(action, "tool_input", "")
            if isinstance(tool_input, dict):
                tool_input_str = json.dumps(tool_input)
            else:
                tool_input_str = str(tool_input)
            if isinstance(observation, bytes):
                observation_str: Any = observation.decode("utf-8", errors="replace")
            else:
                observation_str = observation
            evidence["raw_steps"].append(
                {
                    "tool": tool_name,
                    "input": tool_input_str,
                    "observation": observation_str,
                }
            )
            if tool_name == "competitor_report":
                try:
                    parsed = json.loads(observation_str)
                    overview = parsed.get("overview")
                    if overview:
                        evidence["competitor_overviews"].append(str(overview)[:800])
                    items = parsed.get("items") or []
                    if isinstance(items, list):
                        for item in items:
                            evidence["competitor_items"].append({
                                "source_query": tool_input_str,
                                "title": item.get("title"),
                                "summary": item.get("summary"),
                                "url": item.get("url"),
                            })
                except json.JSONDecodeError:
                    evidence["competitor_items"].append(
                        {
                            "source_query": tool_input_str,
                            "raw_observation": str(observation_str),
                        }
                    )
            elif tool_name == "load_csv":
                try:
                    parsed_rows = json.loads(observation_str)
                except json.JSONDecodeError:
                    parsed_rows = observation_str
                evidence["csv_rows"][tool_input_str] = parsed_rows
        # Limit evidence size to avoid overly long prompts
        evidence["competitor_items"] = evidence["competitor_items"][:20]
        evidence["competitor_overviews"] = evidence["competitor_overviews"][:10]
        evidence["raw_steps"] = evidence["raw_steps"][:20]
        return evidence

    def _fallback_synthesize_facts(
        self,
        llm: Any,
        product_text: str,
        raw_output: str,
        evidence: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        if not evidence["competitor_items"] and not evidence["csv_rows"] and not evidence.get("raw_steps"):
            return None
        fallback_instruction = {
            "objective": "Repair the fact payload when the agent response is malformed.",
            "expected_schema": {
                "facts": {
                    "competitors": "Array with up to five competitor entries including name, summary, differentiators, gaps, sources.",
                    "user_needs": "Top six succinct needs.",
                    "market_ranges": "Object with tam_range, sam_range, som_range (strings, use empty string if unknown).",
                    "extracted_insights": "Up to six bullet insights.",
                    "evidence_refs": "Flat list of distinct source URLs.",
                },
                "status": "complete|insufficient_data",
            },
            "rules": [
                "Use only information provided in evidence; do not fabricate sources.",
                "Keep each string under 240 characters.",
                "If a range is unknown, return an empty string rather than null.",
                "Always set status to 'complete' when at least three competitors and four user needs are present; otherwise 'insufficient_data'.",
            ],
        }

        payload = {
            "product_description": product_text,
            "raw_agent_output": raw_output,
            "competitor_items": evidence["competitor_items"],
            "competitor_overviews": evidence["competitor_overviews"],
            "csv_rows": evidence["csv_rows"],
            "raw_steps": evidence.get("raw_steps", []),
        }

        prompt = (
            "The fact-gathering agent failed to return valid JSON. You must repair the payload using its evidence.\n"
            "Respect the schema and constraints below. Respond with clean JSON only.\n\n"
            f"Directive JSON:\n{json.dumps(fallback_instruction, indent=2)}\n\n"
            f"Evidence JSON:\n{json.dumps(payload, indent=2)}\n\n"
            "Return ONLY valid JSON with keys facts and status. No markdown fences, no commentary."
        )

        fallback_response = llm.invoke(prompt)
        fallback_text = self._coerce_content_to_text(getattr(fallback_response, "content", fallback_response))
        parsers: List[Any] = [
            lambda text: json.loads(text),
            lambda text: json.loads(_extract_json(text)),
        ]
        for parser in parsers:
            try:
                payload = parser(fallback_text)
                if isinstance(payload, dict):
                    payload.setdefault("status", "insufficient_data")
                    return payload
            except Exception:
                continue
        evidence.setdefault("fallback_text", fallback_text)
        deterministic = self._deterministic_fact_recovery(product_text, evidence)
        if deterministic:
            evidence.setdefault("deterministic_fallback", deterministic)
            return deterministic
        return None

    def _deterministic_fact_recovery(
        self,
        product_text: str,
        evidence: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        competitor_items = evidence.get("competitor_items", [])
        if not competitor_items:
            return None

        competitors: List[Dict[str, Any]] = []
        seen_names: set[str] = set()
        for item in competitor_items:
            title = str(item.get("title") or item.get("source_query") or "Unknown").strip()
            name = title.split(" - ")[0].split(":")[0].strip() or "Unknown"
            if name.lower() in seen_names:
                continue
            seen_names.add(name.lower())
            summary = str(item.get("summary") or item.get("raw_observation") or "")[:240]
            url = item.get("url") or item.get("raw_observation") or ""
            differentiators = []
            gaps = []
            if summary:
                sentences = [s.strip() for s in summary.replace("...", ". ").split(".") if s.strip()]
                if sentences:
                    differentiators.append(sentences[0][:160])
                if len(sentences) > 1:
                    gaps.append(sentences[1][:160])
            competitors.append(
                {
                    "name": name[:80],
                    "summary": summary or "Competitor summary unavailable",
                    "differentiators": differentiators or ["Differentiator not captured"],
                    "gaps": gaps or ["Gap not captured"],
                    "sources": [str(url)] if url else [],
                }
            )
            if len(competitors) >= 5:
                break

        text_lines = [line.strip().strip("\"") for line in product_text.replace("\\n", "\n").splitlines() if line.strip()]
        user_needs: List[str] = []
        for line in text_lines:
            cleaned = line
            if cleaned.lower().startswith("we want"):
                cleaned = cleaned[7:].strip()
            cleaned = cleaned.strip(".")
            if cleaned:
                user_needs.append(cleaned[:240] + ("." if not cleaned.endswith(".") else ""))
        user_needs = user_needs[:6] or ["Need details unavailable"]

        insights: List[str] = []
        overview_notes = evidence.get("competitor_overviews", [])
        if overview_notes:
            overview_text = " ".join(str(note) for note in overview_notes)
            for sentence in overview_text.split("."):
                snippet = sentence.strip()
                if snippet:
                    insights.append(snippet[:200] + ("." if not snippet.endswith(".") else ""))
                    if len(insights) >= 6:
                        break
        if len(insights) < 3:
            insights.extend([
                "Market crowded with gamified trackers; simplicity is a differentiator.",
                "Progress visualization and reminders are the most repeated needs.",
                "Mobile-first experience expected with optional web dashboard.",
            ][: 3 - len(insights)])

        evidence_refs = []
        for item in competitor_items:
            url = item.get("url")
            if url and url not in evidence_refs:
                evidence_refs.append(url)
            if len(evidence_refs) >= 12:
                break

        status = "complete" if len(competitors) >= 3 and len(user_needs) >= 4 else "insufficient_data"
        return {
            "facts": {
                "competitors": competitors,
                "user_needs": user_needs,
                "market_ranges": {
                    "tam_range": "",
                    "sam_range": "",
                    "som_range": "",
                },
                "extracted_insights": insights[:6],
                "evidence_refs": evidence_refs,
            },
            "status": status,
        }

    def _build_prd_instruction(
        self,
        product_text: str,
        facts_payload: Dict[str, Any],
    ) -> str:
        builder = {
            "objective": "Transform the verified fact payload into an executive-ready PRD and structured specification.",
            "inputs": {
                "product_description": product_text,
                "collected_facts": facts_payload,
            },
            "schema": {
                "prd_markdown_lines": "Array of single-line markdown strings representing the PRD sections (no line should exceed 180 characters).",
                "structured_spec": {
                    "summary": "Concise overview paragraph (<= 280 chars).",
                    "personas": "List of persona objects (name, goals, frustrations).",
                    "journey": "Key user journey stages with success metrics.",
                    "features": "Core features with priority, description, acceptance criteria, effort estimate (S/M/L), and linked evidence refs.",
                    "rollout": "Roadmap phases with timing assumptions.",
                    "risks": "Top risks with mitigations and owners.",
                    "kpis": "Measurable KPIs with target metrics and measurement cadence.",
                    "open_questions": "Any unresolved assumptions requiring follow-up.",
                    "evidence_refs": "Deduplicated list of evidence references leveraged in synthesis.",
                },
            },
            "requirements": [
                "Use only facts provided in collected_facts; if a detail is missing, call it out in open_questions.",
                "Cite evidence_refs inside features and risks using inline references like [ref_1].",
                "PRD sections must include: Overview, Problem, Goals, Personas, Solution, Roadmap, Success Metrics, Risks.",
                "Ensure roadmap aligns with stated market timing and team capacity assumptions from facts.",
                "Return ONLY valid JSON matching the schema. No extra narrative or markdown fences.",
            ],
        }

        prompt = (
            "You are a principal product manager tasked with authoring a full PRD based strictly on provided evidence.\n"
            "Facts have been pre-validated; you must synthesize them into a crisp, actionable document.\n"
            "Maintain deterministic reasoning (temperature 0).\n\n"
            f"Product Description:\n{product_text}\n\n"
            f"Collected Facts Payload:\n{json.dumps(facts_payload, indent=2)}\n\n"
            f"Directive JSON:\n{json.dumps(builder, indent=2)}\n\n"
            "Return ONLY valid JSON with keys prd_markdown_lines and structured_spec. No markdown fences or additional commentary."
        )
        return prompt

    def run(self) -> PhaseOneResult:
        product_text = load_product_description(self.config.product_description_path)
        prompt = self._build_fact_instruction(product_text)

        prompt_path = self.config.outputs_dir / "phase1_prompt.txt"
        prompt_path.write_text(prompt, encoding="utf-8")

        fact_llm = create_llm(
            self.config,
            model=self.config.resolved_gemini_model,
            max_output_tokens=2048,
        )
        try:  # Lazy import to avoid static analysis issues when LangChain isn't installed
            from langchain_core.exceptions import OutputParserException  # type: ignore
        except ImportError:  # pragma: no cover - fallback when module missing
            OutputParserException = Exception  # type: ignore
        agent = create_pm_agent(self.config, llm=fact_llm, verbose=True)
        try:
            response = agent.invoke({"input": prompt})
            raw_output = response.get("output", "")
            intermediate_steps = response.get("intermediate_steps", [])
        except OutputParserException as exc:
            raw_output = str(exc)
            marker = "Could not parse LLM output:"
            if marker in raw_output:
                raw_output = raw_output.split(marker, 1)[1].strip()
            intermediate_steps = []
        evidence = self._collect_tool_outputs(intermediate_steps)
        fallback_used = False

        try:
            facts_payload = json.loads(_extract_json(raw_output))
        except Exception:
            facts_payload = self._fallback_synthesize_facts(fact_llm, product_text, raw_output, evidence)
            if facts_payload is None:
                debug_path = self.config.outputs_dir / "phase1_fact_parse_error.txt"
                debug_payload = {
                    "raw_output": raw_output,
                    "evidence": evidence,
                }
                debug_path.write_text(json.dumps(debug_payload, indent=2), encoding="utf-8")
                raise RuntimeError(
                    "Phase 1 fact-gathering agent did not return valid JSON."
                )
            fallback_used = True

        status = facts_payload.get("status")
        if status not in {"complete", "COMPLETE"}:
            raise RuntimeError(f"Phase 1 fact-gathering agent returned status '{status}'.")

        facts = facts_payload.get("facts")
        if not facts:
            raise RuntimeError("Phase 1 fact-gathering agent returned empty facts payload.")

        facts_path = self.config.outputs_dir / "phase1_facts.json"
        facts_path.write_text(json.dumps(facts_payload, indent=2), encoding="utf-8")

        synthesis_prompt = self._build_prd_instruction(product_text, facts_payload)
        synthesis_llm = create_llm(
            self.config,
            model=self.config.resolved_prd_gemini_model,
            max_output_tokens=4096,
        )
        synthesis_response = synthesis_llm.invoke(synthesis_prompt)
        final_text = (
            synthesis_response.content
            if hasattr(synthesis_response, "content")
            else str(synthesis_response)
        )

        try:
            final_payload = json.loads(_extract_json(final_text))
        except Exception as exc:
            debug_path = self.config.outputs_dir / "phase1_prd_parse_error.txt"
            debug_path.write_text(final_text, encoding="utf-8")
            raise RuntimeError("Phase 1 synthesis model did not return valid PRD JSON.") from exc

        prd_lines = final_payload.get("prd_markdown_lines", [])
        if isinstance(prd_lines, str):
            prd_lines = [prd_lines]
        if not prd_lines:
            raise RuntimeError("Phase 1 synthesis model did not return PRD markdown lines.")

        prd_markdown = "\n".join(prd_lines)
        product_spec = final_payload.get("structured_spec", {})
        if not product_spec:
            raise RuntimeError("Phase 1 synthesis model did not return a structured specification.")

        outputs_dir = self.config.outputs_dir
        prd_path = outputs_dir / "phase1_product_spec.md"
        prd_path.write_text(prd_markdown, encoding="utf-8")

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

        raw_output_path = outputs_dir / "phase1_raw.json"
        raw_payload = {
            "fact_agent_output": raw_output,
            "fact_agent_steps": serializable_steps,
            "facts_payload": facts_payload,
            "fact_evidence": evidence,
            "fact_fallback_used": fallback_used,
            "synthesis_prompt": synthesis_prompt,
            "synthesis_raw_output": final_text,
            "final_payload": final_payload,
        }
        raw_output_path.write_text(json.dumps(raw_payload, indent=2), encoding="utf-8")

        return PhaseOneResult(
            product_spec=product_spec,
            prd_markdown=prd_markdown,
            raw_agent_output=raw_payload,
            prompt_path=prompt_path,
            facts_path=facts_path,
            prd_path=prd_path,
            raw_output_path=raw_output_path,
        )
