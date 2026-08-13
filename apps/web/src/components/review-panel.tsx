"use client";

import { useState } from "react";

export type ReviewMode = "idle" | "edit" | "reroute";

export function ReviewFields({ mode }: { mode: ReviewMode }) {
  if (mode === "edit") {
    return <form className="reviewform"><label>Work-order summary<textarea defaultValue="Inspect and isolate the reported water leak." /></label><label>Required actions<textarea defaultValue="Secure affected road; isolate leak" /></label></form>;
  }
  if (mode === "reroute") {
    return <form className="reviewform"><label>Primary department<input defaultValue="water" /></label><label>Secondary departments<input defaultValue="traffic" /></label><label>Grounded policy references<input defaultValue="PLAY-WATER-01" /></label></form>;
  }
  return null;
}

export function ReviewPanel() {
  const [mode, setMode] = useState<ReviewMode>("idle");

  return <section aria-label="Human review"><h2>Human review</h2><p>Review the grounded routing and operational recommendation before communication.</p><div className="actions"><button className="button">Approve</button><button className="outline" onClick={() => setMode("edit")}>Edit</button><button className="outline" onClick={() => setMode("reroute")}>Reroute</button><button className="outline">Reject</button></div><ReviewFields mode={mode} /></section>;
}
