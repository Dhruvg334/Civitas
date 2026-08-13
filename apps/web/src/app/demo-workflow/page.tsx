"use client";

import { useState } from "react";
import Link from "next/link";
import { Footer, Nav, Status } from "@/components/site";
import { AgentTraceVisualizer } from "@/components/agent-trace-visualizer";

const stages = [
  {
    id: "intake",
    label: "Intake",
    title: "Three reports enter one evidence queue.",
    summary:
      "Each report keeps its original category, citizen wording, media type, and approximate proximity. Nothing is merged prematurely just because it looks similar.",
    output: "3 report contexts loaded",
    facts: [
      "REPORT-A · Photo uploaded · Water on road near school",
      "REPORT-B · Text only · Bikes slipping by the gate",
      "REPORT-C · Video uploaded · Citizen category: pothole",
    ],
  },
  {
    id: "evidence",
    label: "Evidence",
    title: "Evidence is structured without flattening its source.",
    summary:
      "The evidence agent separates what media supports from what citizens say, retains contradictions, and leaves the root cause of the water unknown until verified.",
    output: "Structured evidence validated",
    facts: [
      "OBSERVED · Standing water across carriageway",
      "REPORTED · Slippery conditions near school gate",
      "INFERRED · Category likely water leakage, cause unconfirmed",
    ],
  },
  {
    id: "intelligence",
    label: "ML + geo",
    title: "Deterministic signals find the operational incident.",
    summary:
      "Duplicate candidate detection, severity scoring, and priority tools contribute their own typed results. School and traffic context increases urgency without altering physical facts.",
    output: "INC-0241 candidate created",
    facts: [
      "Duplicate candidate · Three reports in candidate window",
      "Severity · Elevated (2.4m affected width)",
      "Priority · High (School crossing + morning peak traffic)",
    ],
  },
  {
    id: "grounding",
    label: "Grounding",
    title: "The recommendation has a policy trail.",
    summary:
      "Civitas retrieves only policy and playbook material relevant to water leakage, traffic coordination, escalation, and work-order readiness.",
    output: "SUPPORTED knowledge result",
    facts: [
      "PLAY-WATER-01 · Water leakage response playbook",
      "ROUTE-WATER-02 · Jurisdiction & traffic coordination",
      "SAFETY-WATER-01 · Secure affected crossing zone",
    ],
  },
  {
    id: "decision",
    label: "Decision",
    title: "Routing and planning become reviewable output.",
    summary:
      "The routing agent recommends the primary and secondary department while the planning agent proposes an operational package. The critic checks unsupported claims and reference validity.",
    output: "Critic: PASS",
    facts: [
      "Primary · Water Department",
      "Secondary · Traffic Coordination",
      "Work order · Inspect, isolate leak, secure crossing",
    ],
  },
  {
    id: "review",
    label: "Human review",
    title: "A real pause before operational commitment.",
    summary:
      "The graph reaches its persisted human-review checkpoint. Supervisor approval resumes the workflow thread, after which a safe resident update is generated.",
    output: "WAITING_FOR_REVIEW",
    facts: [
      "Workflow · WF-DEMO-0241",
      "Thread · report-demo-water",
      "Review actions · Approve, Edit, Reroute, Reject",
    ],
  },
];

export default function Demo() {
  const [active, setActive] = useState(0);
  const [showTrace, setShowTrace] = useState(false);
  const stage = stages[active];

  return (
    <>
      <Nav />
      <main className="demo-shell rich-demo">
        <header className="demo-header-banner">
          <div>
            <span className="workspace-kicker">GOLDEN RUNTIME SLICE / BHUBANESWAR DEMO</span>
            <h1>Water near a school is not three separate tickets.</h1>
            <p>
              Follow the seeded water-leak incident through real workflow steps: intake context,
              evidence boundaries, deterministic ML, policy grounding, routing, planning, critic checks,
              and supervisor authorization.
            </p>
          </div>
          <div className="demo-header-actions">
            <Status tone="good">OFFLINE DEMO RUNTIME</Status>
            <button
              onClick={() => setShowTrace(!showTrace)}
              className="outline small-trace-btn"
            >
              {showTrace ? "Hide Agent Trace" : "View Agent Trace (LangGraph)"}
            </button>
          </div>
        </header>

        {showTrace && (
          <section className="trace-drawer">
            <AgentTraceVisualizer
              incidentId="INC-0241"
              workflowId="WF-DEMO-0241"
              currentStep={stage.id}
            />
          </section>
        )}

        <section className="demo-casebar">
          <div>
            <span>INCIDENT ID</span>
            <b>INC-0241 · School crossing water leak</b>
          </div>
          <div>
            <span>INPUT REPORTS</span>
            <b>03 related citizen reports</b>
          </div>
          <div>
            <span>GIS LOCATION</span>
            <b>20.2961 N, 85.8245 E (Ward 12)</b>
          </div>
          <div>
            <span>WORKFLOW STATE</span>
            <Status tone="warn">WAITING_FOR_REVIEW</Status>
          </div>
        </section>

        <div className="demo-grid">
          <aside className="demo-stepper" aria-label="Demo stages">
            {stages.map((item, index) => (
              <button
                onClick={() => setActive(index)}
                className={`step-btn ${active === index ? "active" : active > index ? "passed" : ""}`}
                key={item.id}
              >
                <span className="step-badge-num">{String(index + 1).padStart(2, "0")}</span>
                <div>
                  <b>{item.label}</b>
                  <small>
                    {index < active ? "✓ Complete" : index === active ? "Active Step" : "Queued"}
                  </small>
                </div>
              </button>
            ))}
          </aside>

          <section className="demo-stage">
            <div className="demo-stage-index">
              <span>{String(active + 1).padStart(2, "0")}</span>
              <p>{stage.label.toUpperCase()} STEP</p>
            </div>
            <h2>{stage.title}</h2>
            <p className="stage-lede">{stage.summary}</p>

            <div className="demo-output">
              <div className="demo-output-header">
                <span>STAGE AGENT OUTPUT</span>
                <Status tone={active === 5 ? "warn" : "good"}>{stage.output}</Status>
              </div>
              <div className="demo-facts">
                {stage.facts.map((fact) => (
                  <article key={fact}>
                    <span className="fact-bullet">•</span>
                    <p>{fact}</p>
                  </article>
                ))}
              </div>
            </div>

            {/* STAGE-SPECIFIC INTERACTIVE CARDS */}
            {active === 0 && (
              <div className="report-evidence-grid">
                <article className="report-card">
                  <span className="card-tag">REPORT-A</span>
                  <b>“Water on road near school.”</b>
                  <small>Photo uploaded · Category uncertain</small>
                </article>
                <article className="report-card">
                  <span className="card-tag">REPORT-B</span>
                  <b>“Bikes are slipping by the gate.”</b>
                  <small>Text only · Landmark context retained</small>
                </article>
                <article className="report-card">
                  <span className="card-tag">REPORT-C</span>
                  <b>Selected: Pothole</b>
                  <small>Video uploaded · Category remains citizen-reported</small>
                </article>
              </div>
            )}

            {active === 2 && (
              <div className="signal-board-grid">
                <article className="signal-card">
                  <span className="signal-tag">SPATIAL DUPLICATE</span>
                  <b>3 Related Reports</b>
                  <small>Proximity candidate window: 45m radius</small>
                </article>
                <article className="signal-card">
                  <span className="signal-tag">VISION SEVERITY</span>
                  <b>Elevated (2.4m)</b>
                  <small>Retained strictly as ML vision inference</small>
                </article>
                <article className="signal-card">
                  <span className="signal-tag">PRIORITY CALCULATOR</span>
                  <b>P1 - High Urgency</b>
                  <small>School crossing + morning peak traffic</small>
                </article>
              </div>
            )}

            {active === 3 && (
              <div className="knowledge-evidence-grid">
                <div className="know-card">
                  <span className="know-tag">RETRIEVED PLAYBOOK</span>
                  <b>PLAY-WATER-01</b>
                  <p>Municipal water leakage response procedure.</p>
                </div>
                <div className="know-card">
                  <span className="know-tag">POLICY STATUS</span>
                  <b>GROUNDED</b>
                  <p>Operational evidence matches required criteria.</p>
                </div>
                <div className="know-card">
                  <span className="know-tag">CRITIC SANITY CHECK</span>
                  <b>Passed Validations</b>
                  <p>No fabricated policy IDs or phantom laws.</p>
                </div>
              </div>
            )}

            {active === 5 && (
              <div className="review-demo-box">
                <div className="review-info">
                  <span className="review-tag">HUMAN APPROVAL REQUIRED</span>
                  <b>Primary: Water Department · Secondary: Traffic Control</b>
                  <p>
                    Inspect and isolate active leak; secure school crossing during field inspection.
                    No guaranteed resolution timeframe provided to resident.
                  </p>
                </div>
                <div className="review-actions-row">
                  <button className="button small">Approve Work Order</button>
                  <button className="outline small">Edit Operational Plan</button>
                  <button className="outline small">Reroute Department</button>
                </div>
              </div>
            )}

            <footer className="stage-footer-bar">
              <div className="trace-info">
                <span>WORKFLOW TRACE ID:</span>
                <code>trace-demo-water · {stage.id} node</code>
              </div>
              <div className="nav-buttons">
                <button
                  disabled={active === 0}
                  onClick={() => setActive((v) => v - 1)}
                  className="prev-btn"
                >
                  ← Previous Step
                </button>
                <button
                  disabled={active === stages.length - 1}
                  onClick={() => setActive((v) => v + 1)}
                  className="next-btn"
                >
                  Next Step →
                </button>
              </div>
            </footer>
          </section>
        </div>
      </main>
      <Footer />

      <style jsx>{`
        .demo-shell {
          width: min(calc(100% - 40px), 1180px);
          margin: 40px auto 90px;
        }
        .demo-header-banner {
          display: flex;
          justify-content: space-between;
          align-items: flex-end;
          gap: 30px;
          padding-bottom: 28px;
          border-bottom: 2px solid #172019;
        }
        .demo-header-banner h1 {
          font-size: clamp(2.5rem, 4.5vw, 4.2rem);
          line-height: 0.92;
          margin: 8px 0;
          font-family: Georgia, serif;
        }
        .demo-header-banner p {
          max-width: 680px;
          color: #495248;
          font-size: 0.95rem;
          line-height: 1.6;
          margin: 0;
        }
        .demo-header-actions {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          gap: 12px;
        }
        .small-trace-btn {
          font-size: 0.72rem !important;
          padding: 8px 12px !important;
        }
        .trace-drawer {
          margin: 20px 0;
          border: 1px solid #172019;
          box-shadow: 4px 4px 0 #172019;
        }
        .demo-casebar {
          display: grid;
          grid-template-columns: 1.4fr 1fr 1.2fr 1fr;
          margin: 24px 0;
          border: 1px solid #172019;
          background: #ffffff;
          box-shadow: 3px 3px 0 #172019;
        }
        .demo-casebar > div {
          padding: 14px 18px;
          border-right: 1px solid #e2ded4;
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .demo-casebar > div:last-child {
          border-right: 0;
        }
        .demo-casebar span {
          font-size: 0.58rem;
          font-weight: 850;
          letter-spacing: 0.1em;
          color: #687067;
        }
        .demo-casebar b {
          font-size: 0.78rem;
          color: #172019;
        }
        .demo-grid {
          display: grid;
          grid-template-columns: 240px minmax(0, 1fr);
          border: 1px solid #172019;
          box-shadow: 4px 4px 0 #172019;
          background: #ffffff;
          min-height: 580px;
        }
        .demo-stepper {
          border-right: 1px solid #172019;
          background: #fbf9f4;
        }
        .step-btn {
          width: 100%;
          border: 0;
          border-bottom: 1px solid #e2ded4;
          background: transparent;
          padding: 16px 18px;
          text-align: left;
          display: grid;
          grid-template-columns: 28px 1fr;
          gap: 10px;
          align-items: center;
          cursor: pointer;
          transition: background 0.15s ease;
        }
        .step-btn:hover,
        .step-btn.active {
          background: #ffffff;
        }
        .step-btn.active {
          box-shadow: inset 4px 0 0 #e84d7a;
        }
        .step-btn.passed .step-badge-num {
          color: #0f5f4f;
        }
        .step-badge-num {
          font-size: 0.7rem;
          font-weight: 900;
          color: #687067;
        }
        .step-btn b {
          display: block;
          font-size: 0.78rem;
          color: #172019;
        }
        .step-btn small {
          display: block;
          font-size: 0.62rem;
          color: #687067;
          margin-top: 2px;
        }
        .demo-stage {
          padding: 38px;
          display: flex;
          flex-direction: column;
        }
        .demo-stage-index {
          display: flex;
          align-items: center;
          gap: 10px;
        }
        .demo-stage-index span {
          display: grid;
          place-items: center;
          width: 32px;
          height: 32px;
          border: 1px solid #172019;
          font-size: 0.7rem;
          font-weight: 900;
          background: #fbf9f4;
        }
        .demo-stage-index p {
          font-size: 0.62rem;
          font-weight: 900;
          letter-spacing: 0.12em;
          color: #0f5f4f;
          margin: 0;
        }
        .demo-stage h2 {
          font-size: clamp(2.2rem, 4vw, 3.6rem);
          line-height: 0.96;
          margin: 18px 0 14px;
          font-family: Georgia, serif;
        }
        .stage-lede {
          font-size: 0.95rem;
          line-height: 1.6;
          color: #495248;
          max-width: 720px;
        }
        .demo-output {
          margin: 22px 0;
          border: 1px solid #172019;
          background: #ffffff;
        }
        .demo-output-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 10px 14px;
          border-bottom: 1px solid #e2ded4;
          background: #fbf9f4;
          font-size: 0.62rem;
          font-weight: 850;
          letter-spacing: 0.1em;
          color: #687067;
        }
        .demo-facts {
          display: grid;
        }
        .demo-facts article {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 12px 14px;
          border-bottom: 1px solid #e2ded4;
        }
        .demo-facts article:last-child {
          border-bottom: 0;
        }
        .fact-bullet {
          color: #e84d7a;
          font-size: 1.2rem;
        }
        .demo-facts p {
          margin: 0;
          font-size: 0.82rem;
          color: #172019;
          font-weight: 650;
        }
        .report-evidence-grid,
        .signal-board-grid,
        .knowledge-evidence-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 12px;
          margin-top: 18px;
        }
        .report-card,
        .signal-card,
        .know-card {
          padding: 16px;
          border: 1px solid #172019;
          background: #fbf9f4;
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .card-tag,
        .signal-tag,
        .know-tag {
          font-size: 0.58rem;
          font-weight: 900;
          letter-spacing: 0.1em;
          color: #0f5f4f;
        }
        .report-card b,
        .signal-card b,
        .know-card b {
          font-size: 0.85rem;
          color: #172019;
        }
        .report-card small,
        .signal-card small,
        .know-card p {
          font-size: 0.72rem;
          color: #687067;
          margin: 0;
        }
        .review-demo-box {
          margin-top: 20px;
          padding: 22px;
          border: 1px solid #172019;
          background: #fff8dc;
          box-shadow: 4px 4px 0 #172019;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .review-tag {
          font-size: 0.6rem;
          font-weight: 900;
          letter-spacing: 0.1em;
          color: #e84d7a;
        }
        .review-info b {
          display: block;
          font-size: 1.05rem;
          font-family: Georgia, serif;
          margin: 6px 0;
        }
        .review-info p {
          font-size: 0.82rem;
          color: #384237;
          margin: 0;
          line-height: 1.5;
        }
        .review-actions-row {
          display: flex;
          gap: 10px;
        }
        .stage-footer-bar {
          margin-top: auto;
          padding-top: 24px;
          border-top: 1px solid #e2ded4;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .trace-info span {
          font-size: 0.58rem;
          font-weight: 850;
          letter-spacing: 0.1em;
          color: #687067;
          margin-right: 6px;
        }
        .trace-info code {
          font-size: 0.72rem;
          background: #fbf9f4;
          padding: 3px 6px;
          border: 1px solid #e2ded4;
        }
        .nav-buttons {
          display: flex;
          gap: 10px;
        }
        .prev-btn,
        .next-btn {
          padding: 8px 14px;
          border: 1px solid #172019;
          background: #ffffff;
          font-size: 0.75rem;
          font-weight: 750;
          cursor: pointer;
        }
        .prev-btn:disabled,
        .next-btn:disabled {
          opacity: 0.35;
          cursor: not-allowed;
        }
        @media (max-width: 850px) {
          .demo-grid {
            grid-template-columns: 1fr;
          }
          .demo-stepper {
            display: flex;
            overflow-x: auto;
            border-right: 0;
            border-bottom: 1px solid #172019;
          }
          .step-btn {
            min-width: 140px;
            grid-template-columns: 1fr;
          }
          .report-evidence-grid,
          .signal-board-grid,
          .knowledge-evidence-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </>
  );
}
