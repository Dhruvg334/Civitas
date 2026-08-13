"use client";

import { useState } from "react";

const capabilities = [
  {
    key: "agents",
    eyebrow: "Agentic AI Orchestration",
    title: "Reasoning with boundaries.",
    text: "Specialized agents structure observable evidence, retrieve verified policy, route incidents, plan field operations, and critique recommendations—pausing strictly when human authorization is required.",
    facts: ["Observable evidence distinctions", "Automated policy grounding", "Supervisor review checkpoint"],
    badge: "AGENTS",
    color: "#e84d7a",
  },
  {
    key: "intelligence",
    eyebrow: "ML & Geospatial Analysis",
    title: "Signals with real-world context.",
    text: "Vision analysis, duplicate candidate detection, severity scoring, and spatial clustering remain deterministic algorithms—not unpredictable LLM prompts. Spatial proximity raises urgency without inventing fake facts.",
    facts: ["DBSCAN spatial clustering", "CLIP visual zero-shot", "PostGIS proximity queries"],
    badge: "INTELLIGENCE",
    color: "#e3b950",
  },
  {
    key: "operations",
    eyebrow: "Municipal Operations Workflow",
    title: "From raw report to accountable action.",
    text: "The workflow converts multiple resident inputs into a work-order recommendation, logs every review action for auditability, and communicates cautious updates back to the resident.",
    facts: ["Work-order draft creation", "Full audit log tracing", "Automated resident feedback"],
    badge: "OPERATIONS",
    color: "#0f5f4f",
  },
];

export function LandingExplorer() {
  const [active, setActive] = useState(0);
  const item = capabilities[active];

  return (
    <section className="capability-section" aria-labelledby="capabilities-title">
      <div className="capability-intro">
        <p className="section-kicker">THREE CONNECTED CAPABILITIES</p>
        <h2 id="capabilities-title">One calm system for a messy civic moment.</h2>
        <p>
          Explore the architecture layers that make AI recommendations reviewable instead of merely persuasive.
        </p>
      </div>

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
            <span className="tab-title">{capability.eyebrow}</span>
          </button>
        ))}
      </div>

      <div className={`capability-stage ${item.key}`} role="tabpanel">
        <div className="stage-content">
          <p className="section-kicker">{item.eyebrow}</p>
          <h3>{item.title}</h3>
          <p className="stage-text">{item.text}</p>
          <ul className="fact-list">
            {item.facts.map((fact) => (
              <li key={fact} className="fact-pill">
                <span className="pill-dot" style={{ background: item.color }} />
                {fact}
              </li>
            ))}
          </ul>
        </div>

        <div className="capability-visual" aria-hidden="true">
          <div className="visual-card visual-card-left">
            <span className="visual-tag">INPUT REPORT</span>
            <small>Multimodal Resident Data</small>
          </div>

          <div className="visual-connector connector-left" />

          <div className="visual-core-node" style={{ borderColor: item.color }}>
            <span className="core-badge" style={{ background: item.color }}>{item.badge}</span>
            <b className="core-title">{active === 0 ? "REASON" : active === 1 ? "CLUSTER" : "ROUTE"}</b>
          </div>

          <div className="visual-connector connector-right" />

          <div className="visual-card visual-card-right">
            <span className="visual-tag">HUMAN GATE</span>
            <small>Reviewable Work Order</small>
          </div>
        </div>
      </div>

      <style jsx>{`
        .capability-section {
          padding: 85px 0 65px;
          border-top: 1px solid #172019;
        }
        .capability-intro {
          max-width: 780px;
          margin-bottom: 2.5rem;
        }
        .capability-intro h2 {
          font-size: clamp(2.4rem, 4.5vw, 4.2rem);
          line-height: 0.94;
          margin: 0.5rem 0 1rem;
          font-family: Georgia, serif;
        }
        .capability-intro p {
          color: #555e54;
          font-size: 1.05rem;
          line-height: 1.6;
        }
        .capability-tabs {
          display: flex;
          gap: 0;
          border-bottom: 1px solid #172019;
          background: #fbf9f4;
        }
        .tab-btn {
          flex: 1;
          padding: 16px 20px;
          background: transparent;
          border: 0;
          border-top: 1px solid #172019;
          border-right: 1px solid #172019;
          font-size: 0.82rem;
          font-weight: 800;
          text-align: left;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 12px;
          transition: background 0.15s ease, color 0.15s ease;
        }
        .tab-btn:last-child {
          border-right: 0;
        }
        .tab-btn.active {
          background: #172019;
          color: #ffffff;
        }
        .tab-num {
          color: #e84d7a;
          font-size: 0.72rem;
        }
        .capability-stage {
          display: grid;
          grid-template-columns: 1fr 1fr;
          min-height: 360px;
          border: 1px solid #172019;
          border-top: 0;
          background: #ffffff;
          box-shadow: 4px 4px 0 #172019;
        }
        .stage-content {
          padding: 44px;
        }
        .stage-content h3 {
          margin: 6px 0 16px;
          font-family: Georgia, serif;
          font-size: clamp(2rem, 3.5vw, 3.2rem);
          font-weight: 500;
          line-height: 0.96;
        }
        .stage-text {
          color: #495248;
          font-size: 0.95rem;
          line-height: 1.65;
          max-width: 520px;
        }
        .fact-list {
          display: flex;
          flex-wrap: wrap;
          gap: 10px;
          padding: 0;
          margin: 28px 0 0;
          list-style: none;
        }
        .fact-pill {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          border: 1px solid #172019;
          background: #fffdf7;
          font-size: 0.75rem;
          font-weight: 750;
        }
        .pill-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }
        .capability-visual {
          position: relative;
          display: flex;
          align-items: center;
          justify-content: space-around;
          padding: 30px;
          border-left: 1px solid #172019;
          background: linear-gradient(135deg, #e5efe3 0%, #c9d9cb 100%);
          overflow: hidden;
        }
        .visual-card {
          padding: 12px 14px;
          background: #ffffff;
          border: 1px solid #172019;
          box-shadow: 3px 3px 0 #172019;
          display: flex;
          flex-direction: column;
          gap: 4px;
          z-index: 2;
        }
        .visual-tag {
          font-size: 0.58rem;
          font-weight: 900;
          letter-spacing: 0.1em;
          color: #0f5f4f;
        }
        .visual-card small {
          font-size: 0.72rem;
          font-weight: 700;
          color: #172019;
        }
        .visual-core-node {
          padding: 16px 22px;
          background: #ffffff;
          border: 2px solid #172019;
          box-shadow: 4px 4px 0 #172019;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 6px;
          z-index: 2;
        }
        .core-badge {
          font-size: 0.55rem;
          font-weight: 900;
          color: #ffffff;
          padding: 2px 6px;
          border-radius: 3px;
        }
        .core-title {
          font-size: 0.95rem;
          font-family: Georgia, serif;
          color: #172019;
        }
        .visual-connector {
          position: absolute;
          top: 50%;
          width: 25%;
          height: 2px;
          border-top: 2px dashed #172019;
          z-index: 1;
        }
        .connector-left {
          left: 24%;
        }
        .connector-right {
          right: 24%;
        }
        @media (max-width: 800px) {
          .capability-stage {
            grid-template-columns: 1fr;
          }
          .capability-visual {
            min-height: 220px;
            border-left: 0;
            border-top: 1px solid #172019;
          }
        }
      `}</style>
    </section>
  );
}
