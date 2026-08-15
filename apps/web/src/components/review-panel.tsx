"use client";

import { useState } from "react";
import { approveWorkOrder } from "@/lib/api";

export type ReviewMode = "idle" | "edit" | "reroute" | "reject" | "evidence";

export function ReviewFields({
  mode,
  onSubmit,
}: {
  mode: ReviewMode;
  onSubmit: (details: string) => void;
}) {
  const [value, setValue] = useState("");

  if (mode === "edit") {
    return (
      <form
        className="reviewform"
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit(value || "Modified work order actions.");
        }}
      >
        <label>
          Work-order summary
          <textarea
            defaultValue="Inspect and isolate the reported water leak."
            onChange={(e) => setValue(e.target.value)}
          />
        </label>
        <label>
          Required actions
          <textarea defaultValue="Secure affected road; isolate leak; manage traffic." />
        </label>
        <div className="review-help">
          Only the fields exposed by the backend review schema can be edited here.
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
          onSubmit(value || "Rerouted department assignment.");
        }}
      >
        <label>
          Primary department
          <input defaultValue="water_supply" onChange={(e) => setValue(e.target.value)} />
        </label>
        <label>
          Secondary departments
          <input defaultValue="traffic_coordination" />
        </label>
        <label>
          Grounded policy references
          <input defaultValue="PLAY-WATER-01, ROUTE-WATER-02" />
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
          onSubmit(value || "Rejected by supervisor.");
        }}
      >
        <label>
          Reason for rejection
          <textarea
            required
            placeholder="Explain why this recommendation should not proceed."
            onChange={(e) => setValue(e.target.value)}
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
          onSubmit(value || "Requested additional clarification evidence.");
        }}
      >
        <label>
          Evidence needed
          <textarea
            required
            placeholder="What additional evidence would change this decision?"
            onChange={(e) => setValue(e.target.value)}
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

export function ReviewPanel() {
  const [mode, setMode] = useState<ReviewMode>("idle");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ status: string; message: string } | null>(null);

  const handleAction = async (action: "approve" | "edit" | "reroute" | "reject", details?: string) => {
    setLoading(true);
    try {
      const res = await approveWorkOrder("WO-0241-A", action, details);
      setResult({
        status: res.status,
        message:
          action === "approve"
            ? "Work order approved! Workflow thread resumed and citizen update dispatched."
            : action === "reject"
            ? "Incident recommendation rejected and archived."
            : `Action '${action}' submitted: ${res.status}`,
      });
      setMode("idle");
    } catch (err) {
      setResult({
        status: "ERROR",
        message: err instanceof Error ? err.message : "Failed to record review action.",
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
              onClick={() => handleAction("approve")}
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
            onSubmit={(details) =>
              handleAction(mode === "evidence" ? "reject" : (mode as "approve" | "edit" | "reroute" | "reject"), details)
            }
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
        .review-result-banner.approved {
          background: rgba(16, 185, 129, 0.15);
          border: 1px solid rgba(16, 185, 129, 0.4);
          color: #34d399;
        }
        .review-result-banner.rejected {
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
