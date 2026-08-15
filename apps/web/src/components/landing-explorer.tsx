"use client";

import { useState } from "react";
import { FlatIcon } from "@/components/flat-icons";

const capabilities = [
  {
    key: "agents",
    eyebrow: "Agentic AI Orchestration",
    title: "Reasoning with strict governance boundaries.",
    text: "Specialized LangGraph agents structure observable evidence, retrieve verified city policy, compute deterministic severity scores, and synthesize draft work orders—pausing execution strictly when human supervisor authorization is required.",
    facts: [
      "Explicit evidence vs claim separation",
      "Grounded municipal playbook retrieval",
      "Mandatory supervisor review gate",
      "Full audit trace recorded in PostgreSQL",
    ],
    badge: "LANGGRAPH AGENTS",
    color: "#e84d7a",
    icon: "workflow",
  },
  {
    key: "intelligence",
    eyebrow: "ML & Geospatial Analysis",
    title: "Deterministic signals with real-world spatial context.",
    text: "Vision analysis, duplicate candidate detection, and spatial clustering remain deterministic algorithms—not unpredictable LLM prompts. Spatial proximity to schools or hospitals raises priority without inventing ungrounded facts.",
    facts: [
      "PostGIS 3.4 geo-proximity queries",
      "DBSCAN spatial incident clustering",
      "CLIP zero-shot visual verification",
      "Before/After repair verification score",
    ],
    badge: "POSTGIS + CV",
    color: "#0f5f4f",
    icon: "map",
  },
  {
    key: "operations",
    eyebrow: "Municipal Operations Workflow",
    title: "From raw citizen report to accountable field dispatch.",
    text: "The platform aggregates multiple resident reports into a single consolidated incident dossier, dispatches field crews with verified tool checklists, and delivers transparent status checkpoints back to citizens.",
    facts: [
      "1-Click Crew Dispatch & routing",
      "Standardized work-order envelopes",
      "Bi-directional citizen clarification",
      "Fraud-resistant resolution sign-off",
    ],
    badge: "MUNICIPAL OPS",
    color: "#172019",
    icon: "shield",
  },
];

export function LandingExplorer() {
  const [active, setActive] = useState(0);
  const item = capabilities[active];

  return (
    <section className="capability-section" aria-labelledby="capabilities-title">
      <div className="capability-container">
        <div className="capability-intro">
          <div className="section-tag-row">
            <span className="tag-index">02</span>
            <span className="section-kicker">THREE CONNECTED CAPABILITIES</span>
          </div>
          <h2 id="capabilities-title" className="capability-main-title">
            One calm system for a messy civic moment.
          </h2>
          <p className="capability-subtitle">
            Explore the architecture layers that make AI recommendations reviewable instead of merely persuasive.
          </p>
        </div>

        {/* INTERACTIVE TABS */}
        <div className="capability-tabs" role="tablist" aria-label="Civitas capabilities">
          {capabilities.map((capability, index) => (
            <button
              key={capability.key}
              role="tab"
              aria-selected={index === active}
              className={`tab-btn ${index === active ? "active" : ""}`}
              onClick={() => setActive(index)}
            >
              <span className="tab-num">0{index + 1}</span>
              <FlatIcon name={capability.icon} size={16} />
              <span className="tab-title">{capability.eyebrow}</span>
            </button>
          ))}
        </div>

        {/* TAB CONTENT STAGE */}
        <div className={`capability-stage ${item.key}`} role="tabpanel">
          <div className="stage-content">
            <span className="stage-eyebrow" style={{ color: item.color }}>
              LAYER 0{active + 1} · {item.eyebrow.toUpperCase()}
            </span>
            <h3 className="stage-heading">{item.title}</h3>
            <p className="stage-text">{item.text}</p>

            <ul className="fact-list">
              {item.facts.map((fact) => (
                <li key={fact} className="fact-pill">
                  <FlatIcon name="check" size={14} color="#0f5f4f" />
                  <span>{fact}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="capability-visual" aria-hidden="true">
            <div className="visual-pipeline">
              <div className="visual-card">
                <span className="visual-tag">INPUT DATA</span>
                <b>Citizen Reports</b>
                <small>Text & Geotagged Media</small>
              </div>

              <div className="pipeline-arrow">→</div>

              <div className="visual-core-node" style={{ borderColor: item.color }}>
                <span className="core-badge" style={{ background: item.color }}>
                  {item.badge}
                </span>
                <b className="core-title">
                  {active === 0 ? "Orchestrate" : active === 1 ? "Cluster & Score" : "Dispatch & Audit"}
                </b>
                <small className="core-sub">Deterministic Guardrails</small>
              </div>

              <div className="pipeline-arrow">→</div>

              <div className="visual-card">
                <span className="visual-tag gate-tag">SUPERVISOR GATE</span>
                <b>Reviewable Order</b>
                <small>Human Approval Gate</small>
              </div>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        .capability-section {
          padding: 60px 0 40px;
          border-top: 1px solid #172019;
          background: #faf8f3;
        }
        .capability-container {
          width: min(calc(100% - 40px), 1180px);
          margin: 0 auto;
        }
        .capability-intro {
          margin-bottom: 2rem;
        }
        .section-tag-row {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
        }
        .tag-index {
          font-size: 0.65rem;
          font-weight: 900;
          padding: 2px 6px;
          border: 1px solid #172019;
          background: #172019;
          color: #ffffff;
          border-radius: 3px;
        }
        .section-kicker {
          font-size: 0.68rem;
          font-weight: 900;
          letter-spacing: 0.12em;
          color: #0f5f4f;
        }
        .capability-main-title {
          font-size: clamp(2rem, 3.8vw, 3.2rem);
          line-height: 1.05;
          margin: 6px 0 10px;
          font-family: Georgia, serif;
          color: #172019;
        }
        .capability-subtitle {
          color: #555e54;
          font-size: 1rem;
          line-height: 1.6;
          max-width: 720px;
          margin: 0;
        }
        .capability-tabs {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 8px;
          margin-bottom: 12px;
        }
        .tab-btn {
          padding: 14px 18px;
          background: #ffffff;
          border: 1px solid #172019;
          border-radius: 6px;
          font-size: 0.82rem;
          font-weight: 800;
          text-align: left;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 10px;
          color: #495248;
          box-shadow: 2px 2px 0 #172019;
          transition: all 0.15s ease;
        }
        .tab-btn:hover {
          background: #f4f8f5;
          color: #172019;
        }
        .tab-btn.active {
          background: #172019;
          color: #ffffff;
          box-shadow: 3px 3px 0 #e84d7a;
        }
        .tab-num {
          color: #e84d7a;
          font-size: 0.72rem;
          font-weight: 900;
        }
        .capability-stage {
          display: grid;
          grid-template-columns: 1.2fr 1fr;
          border: 2px solid #172019;
          background: #ffffff;
          box-shadow: 5px 5px 0 #172019;
          border-radius: 8px;
          overflow: hidden;
        }
        .stage-content {
          padding: 36px;
        }
        .stage-eyebrow {
          font-size: 0.65rem;
          font-weight: 900;
          letter-spacing: 0.1em;
          display: block;
          margin-bottom: 8px;
        }
        .stage-heading {
          margin: 0 0 14px;
          font-family: Georgia, serif;
          font-size: clamp(1.6rem, 2.6vw, 2.2rem);
          line-height: 1.15;
          color: #172019;
        }
        .stage-text {
          color: #495248;
          font-size: 0.92rem;
          line-height: 1.6;
          margin: 0 0 24px;
        }
        .fact-list {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 10px;
          padding: 0;
          margin: 0;
          list-style: none;
        }
        .fact-pill {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          border: 1px solid #e2ded4;
          background: #fbf9f4;
          font-size: 0.75rem;
          font-weight: 750;
          color: #172019;
          border-radius: 4px;
        }
        .capability-visual {
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 30px 24px;
          border-left: 1px solid #172019;
          background: #f4f8f5;
        }
        .visual-pipeline {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 12px;
          width: 100%;
          max-width: 320px;
        }
        .visual-card {
          width: 100%;
          padding: 12px 14px;
          background: #ffffff;
          border: 1px solid #172019;
          box-shadow: 2px 2px 0 #172019;
          border-radius: 6px;
          display: flex;
          flex-direction: column;
          gap: 2px;
          text-align: center;
        }
        .visual-tag {
          font-size: 0.58rem;
          font-weight: 900;
          letter-spacing: 0.1em;
          color: #0f5f4f;
        }
        .gate-tag {
          color: #e84d7a;
        }
        .visual-card b {
          font-size: 0.85rem;
          color: #172019;
        }
        .visual-card small {
          font-size: 0.68rem;
          color: #687067;
        }
        .pipeline-arrow {
          font-size: 1.1rem;
          font-weight: 900;
          color: #0f5f4f;
          transform: rotate(90deg);
        }
        .visual-core-node {
          width: 100%;
          padding: 14px 16px;
          background: #ffffff;
          border: 2px solid #172019;
          box-shadow: 3px 3px 0 #172019;
          border-radius: 6px;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 4px;
        }
        .core-badge {
          font-size: 0.55rem;
          font-weight: 900;
          color: #ffffff;
          padding: 2px 6px;
          border-radius: 3px;
          letter-spacing: 0.06em;
        }
        .core-title {
          font-size: 0.95rem;
          font-family: Georgia, serif;
          color: #172019;
        }
        .core-sub {
          font-size: 0.65rem;
          color: #687067;
          font-weight: 750;
        }
        @media (max-width: 900px) {
          .capability-tabs {
            grid-template-columns: 1fr;
          }
          .capability-stage {
            grid-template-columns: 1fr;
          }
          .capability-visual {
            border-left: 0;
            border-top: 1px solid #172019;
          }
          .fact-list {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </section>
  );
}
