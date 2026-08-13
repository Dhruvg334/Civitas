"""Application owner for one compiled Civitas LangGraph workflow."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from civitas_workflow.workflow_contracts import HumanReviewDecision
from langgraph.types import Command

from civitas_api.operations import reports as reports_ops
from civitas_api.operations import workflow_runs


@dataclass
class WorkflowRuntimeService:
    workflow: object

    def start(self, report_id: str) -> dict[str, object]:
        if reports_ops.get_incident(report_id) is None:
            raise LookupError(f"report {report_id} not found")
        active = workflow_runs.find_active(report_id)
        if active:
            return self._summary(active)
        workflow_id = f"wf-{uuid4().hex}"
        trace_id = f"trc-{uuid4().hex}"
        row = workflow_runs.create(workflow_id, workflow_id, report_id, trace_id)
        self.workflow.graph.invoke(
            {"trace_id": trace_id, "report_id": report_id}, self._config(row)
        )
        return self._refresh(row)

    def get(self, workflow_id: str) -> dict[str, object]:
        row = workflow_runs.get(workflow_id)
        if row is None:
            raise LookupError(f"workflow {workflow_id} not found")
        return self._refresh(row)

    def clarification(self, workflow_id: str, answers: dict[str, str]) -> dict[str, object]:
        row = self._require_waiting(workflow_id, "WAITING_FOR_CLARIFICATION")
        self.workflow.graph.invoke(Command(resume=answers), self._config(row))
        return self._refresh(row)

    def review(self, workflow_id: str, decision: dict[str, object]) -> dict[str, object]:
        row = self._require_waiting(workflow_id, "WAITING_FOR_REVIEW")
        snapshot = self.workflow.graph.get_state(self._config(row))
        values = snapshot.values
        if decision.get("operational_plan") and values.get("operational_plan"):
            current = values["operational_plan"].model_dump(mode="json")
            decision["operational_plan"] = {**current, **decision["operational_plan"]}
        if decision.get("routing") and values.get("routing"):
            current = values["routing"].model_dump(mode="json")
            decision["routing"] = {**current, **decision["routing"]}
        validated = HumanReviewDecision.model_validate(decision)
        self.workflow.graph.invoke(
            Command(resume=validated.model_dump(mode="json", exclude_none=True)), self._config(row)
        )
        return self._refresh(row)

    @staticmethod
    def _config(row: dict[str, object]) -> dict[str, object]:
        return {"configurable": {"thread_id": row["thread_id"]}}

    def _refresh(self, row: dict[str, object]) -> dict[str, object]:
        snapshot = self.workflow.graph.get_state(self._config(row))
        values = snapshot.values
        interrupts = snapshot.tasks[-1].interrupts if snapshot.tasks else ()
        interrupt_type = str(interrupts[0].value.get("kind")) if interrupts else None
        status = "RUNNING"
        if interrupt_type == "clarification":
            status = "WAITING_FOR_CLARIFICATION"
        elif interrupt_type == "human_review":
            status = "WAITING_FOR_REVIEW"
        elif values.get("status") is not None:
            raw = values["status"]
            status = (
                "COMPLETED"
                if str(raw).endswith("APPROVED")
                else (
                    "REJECTED"
                    if str(raw).endswith("REJECTED")
                    else "FAILED"
                    if str(raw).endswith("FAILED")
                    else "COMPLETED"
                )
            )
        workflow_runs.update(str(row["workflow_id"]), status, interrupt_type)
        current = workflow_runs.get(str(row["workflow_id"])) or row
        return self._summary(current, values)

    def _require_waiting(self, workflow_id: str, expected: str) -> dict[str, object]:
        row = workflow_runs.get(workflow_id)
        if row is None:
            raise LookupError(f"workflow {workflow_id} not found")
        if row["status"] != expected:
            raise ValueError(f"workflow is not waiting for {expected.lower()}")
        return row

    @staticmethod
    def _summary(
        row: dict[str, object], values: dict[str, object] | None = None
    ) -> dict[str, object]:
        return {
            "workflow_id": row["workflow_id"],
            "report_id": row["report_id"],
            "incident_id": row.get("incident_id"),
            "trace_id": row["trace_id"],
            "status": row["status"],
            "interrupt_type": row.get("interrupt_type"),
            "state": {
                "work_order_id": (values or {}).get("work_order_id"),
                "warnings": (values or {}).get("warnings", []),
            },
        }
