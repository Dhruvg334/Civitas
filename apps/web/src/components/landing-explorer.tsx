"use client";

import { useState } from "react";

const capabilities = [
  { key: "agents", eyebrow: "Agentic AI", title: "Reasoning with boundaries.", text: "Specialized agents structure evidence, retrieve policy, route an incident, plan operations and critique the recommendation. They pause when a person must decide.", facts: ["Evidence distinctions", "Policy reference checks", "Human review checkpoint"] },
  { key: "intelligence", eyebrow: "ML + geospatial", title: "Signals with real-world context.", text: "Vision, duplicate detection, severity, priority and spatial clustering remain deterministic tools—not black-box prompts. Nearby context can change urgency without changing facts.", facts: ["Duplicate candidates", "Severity ≠ priority", "Location-aware clustering"] },
  { key: "operations", eyebrow: "Municipal workflow", title: "From report to accountable action.", text: "The workflow produces a grounded routing and work-order recommendation, records review actions and communicates a cautious next step to the resident.", facts: ["Work-order readiness", "Traceable decisions", "Resident updates"] },
];

export function LandingExplorer() {
  const [active, setActive] = useState(0);
  const item = capabilities[active];
  return <section className="capability-section" aria-labelledby="capabilities-title"><div className="capability-intro"><p className="section-kicker">Three connected capabilities</p><h2 id="capabilities-title">One calm system for a messy civic moment.</h2><p>Explore the layers that make a recommendation reviewable instead of merely persuasive.</p></div><div className="capability-tabs" role="tablist" aria-label="Civitas capabilities">{capabilities.map((capability, index) => <button key={capability.key} role="tab" aria-selected={index === active} className={index === active ? "active" : ""} onClick={() => setActive(index)}><span>0{index + 1}</span>{capability.eyebrow}</button>)}</div><div className={`capability-stage ${item.key}`} role="tabpanel"><div><p className="section-kicker">{item.eyebrow}</p><h3>{item.title}</h3><p>{item.text}</p><ul>{item.facts.map((fact) => <li key={fact}>{fact}</li>)}</ul></div><div className="capability-visual" aria-hidden="true"><span className="visual-report">REPORT</span><span className="visual-node one" /><span className="visual-node two" /><span className="visual-node three" /><span className="visual-core">{active === 0 ? "REASON" : active === 1 ? "LOCATE" : "ACT"}</span><span className="visual-output">REVIEWABLE DECISION</span></div></div></section>;
}
