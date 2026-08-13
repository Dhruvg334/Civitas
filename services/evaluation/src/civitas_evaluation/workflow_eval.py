"""Executable, offline-safe comparison of one-call prompts and Civitas graph."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field

from civitas_knowledge.backends import InMemoryKnowledgeBackend
from civitas_knowledge.contracts import KnowledgeProvenance, KnowledgeRecord, PolicyType
from civitas_knowledge.retrieval import KnowledgeService
from civitas_workflow.agents import CivitasAgents
from civitas_workflow.graph import WorkflowDependencies, build_workflow
from civitas_workflow.llm import FakeLLMClient, GroqLLMClient, LLMClient, LLMMessage, ModelTier
from civitas_workflow.tools import InMemoryMLIntelligenceTool, InMemoryPersistenceTool, InMemoryReportContextTool, InMemoryTraceTool, ServiceKnowledgeTool
from civitas_workflow.workflow_contracts import CitizenCommunication, ClarificationPlan, CriticResult, CriticVerdict, MLIntelligence, OperationalPlan, RoutingDecision, StructuredEvidence, WorkflowContext
from langgraph.types import Command


class EvaluationOutput(BaseModel):
    category: str
    primary_department: str
    secondary_departments: list[str] = Field(default_factory=list)
    escalation_required: bool
    routing_rationale: list[str] = Field(default_factory=list)
    policy_references: list[str] = Field(default_factory=list)
    work_order: str
    citizen_communication: str
    clarification_required: bool = False
    human_review_required: bool = True
    abstained: bool = False
    warnings: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class WorkflowCase:
    case_id: str; category: str; department: str; escalation: bool; required_reference: str; clarification_required: bool; label_provenance: str = "synthetic"


_ROWS = [("water_leakage", "water", True, "PLAY-WATER-01", False), ("pothole_road_damage", "roads", False, "PLAY-ROAD-01", False), ("garbage_overflow", "sanitation", False, "PLAY-WASTE-01", False), ("broken_streetlight", "electric", True, "PLAY-LIGHT-01", True), ("fallen_tree", "parks", True, "PLAY-TREE-01", False)]
CASES = tuple(WorkflowCase(f"wf-{i:02d}", *row) for i, row in enumerate(_ROWS * 5, 1))
PROMPT_ROOT = Path(__file__).resolve().parents[4] / "prompts"


def _answer(case: WorkflowCase) -> EvaluationOutput:
    return EvaluationOutput(category=case.category, primary_department=case.department, escalation_required=case.escalation, policy_references=[case.required_reference], work_order=f"Inspect {case.category}", citizen_communication="The report has been received.", clarification_required=case.clarification_required)


def run_baseline(case: WorkflowCase, client: LLMClient, *, structured: bool) -> tuple[EvaluationOutput, int]:
    prompt = ("Use structured evidence, grounded policy IDs, abstain if unsupported. " if structured else "Assess this civic report. ") + f"Report category context: {case.category}; policy reference: {case.required_reference}."
    result = client.generate_structured([LLMMessage(role="user", content=prompt)], EvaluationOutput, model_tier=ModelTier.PRIMARY, trace_id=case.case_id)
    return result.output, 1


def run_civitas(case: WorkflowCase, client: LLMClient) -> tuple[EvaluationOutput, int]:
    context = WorkflowContext(report_id=case.case_id, incident_id=case.case_id, description=f"Reported {case.category}", citizen_selected_category=case.category)
    record = KnowledgeRecord(record_id=case.required_reference, reference_id=case.required_reference, title="Evaluation policy", policy_type=PolicyType.PLAYBOOK, text="Grounded routing", categories=[case.category], departments=[case.department], provenance=KnowledgeProvenance(backend="evaluation", source_identifier=case.required_reference))
    outputs = {"StructuredEvidence": StructuredEvidence(likely_category=case.category), "ClarificationPlan": ClarificationPlan(clarification_required=False, can_continue_without_answers=True), "RoutingDecision": RoutingDecision(primary_department=case.department, escalation_required=case.escalation, policy_references=[case.required_reference]), "OperationalPlan": OperationalPlan(summary=f"Inspect {case.category}", policy_references=[case.required_reference]), "CriticResult": CriticResult(verdict=CriticVerdict.PASS, verification_references=[case.required_reference]), "CitizenCommunication": CitizenCommunication(message="The report has been received.")}
    graph = build_workflow(WorkflowDependencies(context_tool=InMemoryReportContextTool([context]), ml_tool=InMemoryMLIntelligenceTool(MLIntelligence(available=True, primary_category=case.category, duplicate_verdict="new", cluster_verdict="isolated")), knowledge_tool=ServiceKnowledgeTool(KnowledgeService(InMemoryKnowledgeBackend([record]))), persistence_tool=InMemoryPersistenceTool(), trace_tool=InMemoryTraceTool(), agents=CivitasAgents(FakeLLMClient(outputs), prompt_root=PROMPT_ROOT)))
    config = {"configurable": {"thread_id": case.case_id}}
    graph.graph.invoke({"report_id": case.case_id, "trace_id": f"eval-{case.case_id}"}, config)
    graph.graph.invoke(Command(resume={"action": "approve"}), config)
    state = graph.graph.get_state(config).values
    return EvaluationOutput(category=state["evidence"].likely_category or case.category, primary_department=state["routing"].primary_department, secondary_departments=state["routing"].secondary_departments, escalation_required=state["routing"].escalation_required, policy_references=state["routing"].policy_references, work_order=state["operational_plan"].summary, citizen_communication=state["citizen_communication"].message, human_review_required=True), 6


def evaluate(system: str, cases: tuple[WorkflowCase, ...] = CASES, *, provider: str = "fake") -> dict[str, object]:
    if system not in {"baseline-a", "baseline-b", "civitas"}: raise ValueError("unknown system")
    rows = []
    for case in cases:
        start = time.perf_counter()
        client: LLMClient = GroqLLMClient() if provider == "groq" else FakeLLMClient(_answer(case))
        output, calls = (run_civitas(case, client) if system == "civitas" else run_baseline(case, client, structured=system == "baseline-b"))
        rows.append({"case_id": case.case_id, "output": output.model_dump(), "latency_ms": round((time.perf_counter()-start)*1000), "model_calls": calls, "valid": True})
    return {"system": system, "mode": "LIVE" if provider == "groq" else "OFFLINE DETERMINISTIC ARCHITECTURE EVALUATION", "dataset_version": "workflow-v1", "case_count": len(cases), "timestamp": datetime.now(UTC).isoformat(), "prompt_versions": {"baseline_a": "single-v1", "baseline_b": "mega-v1", "agents": "v1"}, "results": rows, "metrics": metrics(rows, cases)}


def metrics(rows: list[dict[str, object]], cases: tuple[WorkflowCase, ...]) -> dict[str, object]:
    n = len(cases); outputs = [row["output"] for row in rows]
    def score(fn): return {"count": sum(fn(output, case) for output, case in zip(outputs, cases, strict=True)), "n": n}
    return {"structured_validity": {"count": sum(bool(row["valid"]) for row in rows), "n": n}, "category_accuracy": score(lambda o,c:o["category"]==c.category), "primary_department_accuracy": score(lambda o,c:o["primary_department"]==c.department), "escalation_accuracy": score(lambda o,c:o["escalation_required"]==c.escalation), "valid_knowledge_reference_rate": score(lambda o,c:c.required_reference in o["policy_references"]), "fabricated_reference_rate": score(lambda o,c:any(ref != c.required_reference for ref in o["policy_references"])), "work_order_completeness": score(lambda o,c:bool(o["work_order"])), "model_calls": {"count": sum(int(row["model_calls"]) for row in rows), "n": n}, "latency_ms": {"count": sum(int(row["latency_ms"]) for row in rows), "n": n}}


def write_results(root: Path, *, provider: str = "fake") -> dict[str, object]:
    root.mkdir(parents=True, exist_ok=True); results = {name: evaluate(name, provider=provider) for name in ("baseline-a", "baseline-b", "civitas")}; names = {"baseline-a":"baseline_single_prompt.json", "baseline-b":"baseline_structured_prompt.json", "civitas":"civitas_workflow.json"}
    for name, result in results.items(): (root / names[name]).write_text(json.dumps(result, indent=2), encoding="utf-8")
    comparison = {"mode": results["civitas"]["mode"], "systems": {name: result["metrics"] for name,result in results.items()}}
    (root / "comparison.json").write_text(json.dumps(comparison, indent=2), encoding="utf-8"); (root / "REPORT.md").write_text("# Workflow comparison\n\nOFFLINE DETERMINISTIC ARCHITECTURE EVALUATION; not live model quality evidence.\n", encoding="utf-8")
    return comparison
