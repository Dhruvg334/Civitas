"use client";

import { useState } from "react";

export type ReviewMode = "idle" | "edit" | "reroute" | "reject" | "evidence";

export function ReviewFields({ mode }: { mode: ReviewMode }) {
  if (mode === "edit") return <form className="reviewform"><label>Work-order summary<textarea defaultValue="Inspect and isolate the reported water leak." /></label><label>Required actions<textarea defaultValue="Secure affected road; isolate leak" /></label><div className="review-help">Only the fields exposed by the backend review schema can be edited here.</div></form>;
  if (mode === "reroute") return <form className="reviewform"><label>Primary department<input defaultValue="water" /></label><label>Secondary departments<input defaultValue="traffic" /></label><label>Grounded policy references<input defaultValue="PLAY-WATER-01" /></label><div className="review-help">Policy references are validated before the workflow resumes.</div></form>;
  if (mode === "reject") return <form className="reviewform"><label>Reason for rejection<textarea placeholder="Explain why this recommendation should not proceed." /></label></form>;
  if (mode === "evidence") return <form className="reviewform"><label>Evidence needed<textarea placeholder="What additional evidence would change this decision?" /></label></form>;
  return null;
}

export function ReviewPanel() {
  const [mode, setMode] = useState<ReviewMode>("idle");
  return <section className="human-review" aria-label="Human review"><div className="review-title"><span>HUMAN GATE</span><h2>Reviewer decision</h2><p>Operational action is paused here. Review the grounded route and work order before communication.</p></div><div className="policy-proof"><span>Grounding</span><b>PLAY-WATER-01</b><small>Water leakage response playbook</small></div><div className="review-actions"><button className="button">Approve recommendation</button><button className="outline" onClick={() => setMode("edit")}>Edit plan</button><button className="outline" onClick={() => setMode("reroute")}>Reroute</button><button className="text-button danger-text" onClick={() => setMode("evidence")}>More evidence</button><button className="text-button danger-text" onClick={() => setMode("reject")}>Reject</button></div><ReviewFields mode={mode} /></section>;
}
