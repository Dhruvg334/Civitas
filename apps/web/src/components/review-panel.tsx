"use client";

import { useState } from "react";
import { submitWorkflowReview, WorkflowReviewRequest, WorkflowSummary } from "@/lib/api";

export type ReviewMode = "idle" | "edit" | "reroute" | "reject" | "evidence";

export function ReviewFields({
  mode,
  onSubmit,
}: {
  mode: ReviewMode;
  onSubmit: (payload: Partial<WorkflowReviewRequest>) => void;
}) {
  const [summary, setSummary] = useState("Inspect and isolate the reported water leak.");
  const [actions, setActions] = useState("Secure affected road; isolate leak; manage traffic.");
  const [primaryDept, setPrimaryDept] = useState("water_supply");
  const [secondaryDepts, setSecondaryDepts] = useState("traffic_coordination");
  const [policies, setPolicies] = useState("PLAY-WATER-01, ROUTE-WATER-02");
  const [notes, setNotes] = useState("");

  if (mode === "edit") {
    return (
      <form
        className="reviewform"
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit({
            action: "edit",
            operational_plan: {
              summary,
              required_actions: actions.split(";").map((s) => s.trim()).filter(Boolean),
            },
          });
        }}
      >
        <label>
          Work-order summary
          <textarea
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            required
          />
        </label>
        <label>
          Required actions (semicolon separated)
          <textarea
            value={actions}
            onChange={(e) => setActions(e.target.value)}
          />
        </label>
        <div className="review-help">
          Only the narrow fields exposed by EditableWorkOrder schema can be modified here.
        </div>
        <button className="button small-button" type="submit">
          Save & Submit Edit
        </button>
      </form>
    );
  }

  if (mode === "reroute") {
    return (
      <form
        className="reviewform"
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit({
            action: "reroute",
            routing: {
              primary_department: primaryDept,
              secondary_departments: secondaryDepts.split(",").map((s) => s.trim()).filter(Boolean),
              policy_references: policies.split(",").map((s) => s.trim()).filter(Boolean),
            },
          });
        }}
      >
        <label>
          Primary department
          <input
            value={primaryDept}
            onChange={(e) => setPrimaryDept(e.target.value)}
            required
          />
        </label>
        <label>
          Secondary departments (comma separated)
          <input
            value={secondaryDepts}
            onChange={(e) => setSecondaryDepts(e.target.value)}
          />
        </label>
        <label>
          Grounded policy references
          <input
            value={policies}
            onChange={(e) => setPolicies(e.target.value)}
          />
        </label>
        <div className="review-help">
          Policy references are validated before the workflow resumes.
        </div>
        <button className="button small-button" type="submit">
          Submit Reroute
        </button>
      </form>
    );
  }

  if (mode === "reject") {
    return (
      <form
        className="reviewform"
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit({
            action: "reject",
            notes: notes || "Recommendation rejected by municipal reviewer.",
          });
        }}
      >
        <label>
          Reason for rejection
          <textarea
            required
            value={notes}
            placeholder="Explain why this recommendation should not proceed."
            onChange={(e) => setNotes(e.target.value)}
          />
        </label>
        <button className="button danger-button small-button" type="submit">
          Confirm Rejection
        </button>
      </form>
    );
  }

  if (mode === "evidence") {
    return (
      <form
        className="reviewform"
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit({
            action: "request_more_evidence",
            notes: notes || "Additional photographic evidence or specific dimensions requested.",
          });
        }}
      >
        <label>
          Evidence needed
          <textarea
            required
            value={notes}
            placeholder="What additional evidence would change this decision?"
            onChange={(e) => setNotes(e.target.value)}
          />
        </label>
        <button className="button small-button" type="submit">
          Request Clarification
        </button>
      </form>
    );
  }

  return null;
}

export function ReviewPanel({
  workflowId,
  onReviewComplete,
}: {
  workflowId: string;
  onReviewComplete?: (summary: WorkflowSummary) => void;
}) {
  const [mode, setMode] = useState<ReviewMode>("idle");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ status: string; message: string } | null>(null);

  const handleReviewAction = async (payload: Partial<WorkflowReviewRequest>) => {
    setLoading(true);
    try {
      const fullRequest: WorkflowReviewRequest = {
        action: payload.action || "approve",
        notes: payload.notes,
        routing: payload.routing,
        operational_plan: payload.operational_plan,
      };
      const summary = await submitWorkflowReview(workflowId, fullRequest);
      setResult({
        status: summary.status,
        message:
          fullRequest.action === "approve"
            ? "Work order approved! Field crew dispatched and status update published."
            : fullRequest.action === "reject"
            ? "Incident recommendation rejected and work order archived."
            : `Workflow decision '${fullRequest.action}' recorded: status is now ${summary.status}.`,
      });
      setMode("idle");
      if (onReviewComplete) {
        onReviewComplete(summary);
      }
    } catch (err) {
      setResult({
        status: "ERROR",
        message: err instanceof Error ? err.message : "Failed to record review decision.",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="human-review" aria-label="Human review">
      <div className="review-title">
        <span>HUMAN GATE</span>
        <h2>Reviewer decision</h2>
        <p>
          Operational action is paused here. Review the grounded route and work order before
          communication.
        </p>
      </div>

      <div className="policy-proof">
        <span>Grounding</span>
        <b>PLAY-WATER-01</b>
        <small>Water leakage response playbook</small>
      </div>

      {result ? (
        <div className={`review-result-banner ${result.status.toLowerCase()}`}>
          <b>Review Decision Recorded</b>
          <p>{result.message}</p>
          <button className="text-button" onClick={() => setResult(null)}>
            Change decision
          </button>
        </div>
      ) : (
        <>
          <div className="review-actions">
            <button
              className="button"
              disabled={loading}
              onClick={() => handleReviewAction({ action: "approve", notes: "Approved by supervisor." })}
            >
              {loading ? "Recording..." : "Approve recommendation"}
            </button>
            <button className="outline" onClick={() => setMode("edit")}>
              Edit plan
            </button>
            <button className="outline" onClick={() => setMode("reroute")}>
              Reroute
            </button>
            <button className="text-button danger-text" onClick={() => setMode("evidence")}>
              More evidence
            </button>
            <button className="text-button danger-text" onClick={() => setMode("reject")}>
              Reject
            </button>
          </div>

          <ReviewFields
            mode={mode}
            onSubmit={(payload) => handleReviewAction(payload)}
          />
        </>
      )}

      <style jsx>{`
        .review-result-banner {
          padding: 1rem;
          border-radius: 8px;
          margin-top: 1rem;
          font-size: 0.875rem;
        }
        .review-result-banner.completed,
        .review-result-banner.approved {
          background: rgba(16, 185, 129, 0.15);
          border: 1px solid rgba(16, 185, 129, 0.4);
          color: #34d399;
        }
        .review-result-banner.rejected,
        .review-result-banner.error {
          background: rgba(239, 68, 68, 0.15);
          border: 1px solid rgba(239, 68, 68, 0.4);
          color: #f87171;
        }
        .review-result-banner b {
          display: block;
          margin-bottom: 0.25rem;
        }
        .review-result-banner p {
          margin: 0 0 0.5rem;
          color: #e2e8f0;
        }
      `}</style>
    </section>
  );
}
