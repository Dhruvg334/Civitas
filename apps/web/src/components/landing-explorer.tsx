"use client";

import { useState } from "react";
import { FlatIcon } from "@/components/flat-icons";

interface WorkflowStep {
  id: string;
  name: string;
  type: "intake" | "model" | "policy" | "eval" | "gate" | "spatial";
  input: string;
  output: string;
  details: string;
}

interface Capability {
  key: string;
  eyebrow: string;
  title: string;
  text: string;
  badge: string;
  color: string;
  icon: string;
  nodes: WorkflowStep[];
  facts: string[];
}

const capabilities: Capability[] = [
  {
    key: "agents",
    eyebrow: "Agentic AI Orchestration",
    title: "LangGraph State Machine with Strict Governance",
    text: "Specialized LangGraph agents structure observable evidence, retrieve verified city policy, compute deterministic severity scores, and synthesize draft work orders—pausing execution strictly when human supervisor authorization is required.",
    badge: "LANGGRAPH AGENT GRAPH",
    color: "#e84d7a",
    icon: "workflow",
    nodes: [
      {
        id: "node-1",
        name: "Intake Context Normalizer",
        type: "intake",
        input: "Raw Citizen Audio / Photo / Description",
        output: "Structured Evidence vs Claim Triad",
        details: "Normalizes citizen descriptions without overwriting subjective claims or discarding contradictory details.",
      },
      {
        id: "node-2",
        name: "Policy Grounding Agent",
        type: "policy",
        input: "Evidence Envelope + Category",
        output: "Citations: PLAY-WATER-01 (Ward 12)",
        details: "Queries PostgreSQL knowledge base for municipal playbooks, preventing arbitrary LLM delivery promises.",
      },
      {
        id: "node-3",
        name: "Critic & Compliance Loop",
        type: "eval",
        input: "Draft Work Order + Policy Playbook",
        output: "Policy Compliance: Verified (Passed)",
        details: "Critic node audits draft work order against city operating standards before advancing state.",
      },
      {
        id: "node-4",
        name: "Human Supervisor Gate",
        type: "gate",
        input: "Validated Work Order Packet",
        output: "1-Click Crew Authorization",
        details: "Execution strictly halts until a certified municipal supervisor clicks to approve or request clarification.",
      },
    ],
    facts: [
      "Explicit separation of observable facts vs citizen claims",
      "Grounded municipal playbook citations (e.g. PLAY-WATER-01)",
      "Mandatory human review gate before work order issuance",
      "Complete state trace persisted in PostgreSQL for auditability",
    ],
  },
  {
    key: "intelligence",
    eyebrow: "ML & Geospatial Analysis",
    title: "PostGIS 3.4 Spatial Clustering & Multimodal Vision",
    text: "Vision analysis, duplicate candidate detection, and spatial clustering remain deterministic algorithms—not unpredictable LLM prompts. Spatial proximity to schools or hospitals raises priority without inventing ungrounded facts.",
    badge: "POSTGIS 3.4 + ZERO-SHOT CLIP",
    color: "#0f5f4f",
    icon: "map",
    nodes: [
      {
        id: "node-1",
        name: "WGS84 Coordinates Stream",
        type: "spatial",
        input: "GPS Latitude: 20.29614, Longitude: 85.82451",
        output: "Point Geometry (SRID 4326)",
        details: "Converts citizen device geotags into spatial points for PostGIS spatial index evaluation.",
      },
      {
        id: "node-2",
        name: "500m Hazard Proximity Buffer",
        type: "spatial",
        input: "ST_DWithin(geom, landmark_geom, 500)",
        output: "Trigger: 14m from DAV Public School",
        details: "Proximity to high-density pedestrian corridors immediately escalates risk factor deterministically.",
      },
      {
        id: "node-3",
        name: "DBSCAN Cluster Aggregator",
        type: "model",
        input: "Candidate Reports (100m radius)",
        output: "Consolidated Incident INC-0241",
        details: "Fuses duplicate reports across text and photos into 1 high-confidence operational incident dossier.",
      },
      {
        id: "node-4",
        name: "CLIP Zero-Shot Vision Match",
        type: "model",
        input: "Submitted Photo Evidence",
        output: "Defect: Water Main Rupture (High Confidence)",
        details: "Zero-shot visual model identifies defect type and verifies asphalt pooling severity without hallucinations.",
      },
    ],
    facts: [
      "PostGIS 3.4 geo-proximity queries (ST_DWithin, ST_Buffer)",
      "DBSCAN spatial clustering merges duplicate reports into 1 incident",
      "CLIP zero-shot visual defect verification",
      "Deterministic priority score calculated via landmark weightings",
    ],
  },
  {
    key: "operations",
    eyebrow: "Municipal Operations Workflow",
    title: "From Triage to Verified Field Repair Closure",
    text: "The platform aggregates multiple resident reports into a single consolidated incident dossier, dispatches field crews with verified tool checklists, and delivers transparent status checkpoints back to citizens.",
    badge: "MUNICIPAL OPERATIONS ENVELOPE",
    color: "#172019",
    icon: "shield",
    nodes: [
      {
        id: "node-1",
        name: "Work Order Packet Generation",
        type: "gate",
        input: "Authorized Incident Dossier",
        output: "Work Order WO-2026-0881",
        details: "Generates bill of materials (ductile iron sleeve, hot-mix asphalt) and required crew qualifications.",
      },
      {
        id: "node-2",
        name: "Field Crew Dispatch & Routing",
        type: "spatial",
        input: "Ward 12 Water & Drainage Unit",
        output: "ETA: 24 mins · Crew Lead: Marcus",
        details: "Directs nearest certified municipal field unit to site with exact GPS waypoints and hazard buffer notes.",
      },
      {
        id: "node-3",
        name: "Citizen Push Checkpoint",
        type: "intake",
        input: "Field Status Update",
        output: "SMS / App Alert: Crew on site",
        details: "Keeps reporting residents updated at every step without burdening dispatch staff with manual emails.",
      },
      {
        id: "node-4",
        name: "Before/After Repair Verification",
        type: "eval",
        input: "Field Completion Photo",
        output: "Status: VERIFIED_RESOLVED",
        details: "Automated vision audit verifies ductile collar clamp and fresh asphalt seal before closing ticket.",
      },
    ],
    facts: [
      "1-Click Crew Dispatch with standardized equipment checklists",
      "Bi-directional resident clarification dialog for field questions",
      "Automated SMS/app status checkpoints across the resolution lifecycle",
      "Fraud-resistant Before/After photo resolution sign-off",
    ],
  },
];

export function LandingExplorer() {
  const [activeTab, setActiveTab] = useState<number>(0);
  const [selectedNode, setSelectedNode] = useState<number>(0);
  const currentCapability = capabilities[activeTab];
  const currentNode = currentCapability.nodes[selectedNode] || currentCapability.nodes[0];

  const handleTabChange = (index: number) => {
    setActiveTab(index);
    setSelectedNode(0);
  };

  return (
    <section className="capability-section" aria-labelledby="capabilities-title">
      <div className="capability-container">
        {/* HEADER */}
        <div className="capability-intro">
          <div className="section-tag-row">
            <span className="tag-index">02</span>
            <span className="section-kicker">THREE CONNECTED WORKFLOWS</span>
          </div>
          <h2 id="capabilities-title" className="capability-main-title">
            Engineered for Reviewable Civic Decision-Making
          </h2>
          <p className="capability-subtitle">
            Explore how agentic LangGraph orchestration, deterministic PostGIS spatial algorithms, and municipal operations work together seamlessly.
          </p>
        </div>

        {/* WORKFLOW SELECTOR TABS */}
        <div className="capability-tabs" role="tablist" aria-label="Civitas capabilities">
          {capabilities.map((cap, index) => {
            const isActive = index === activeTab;
            return (
              <button
                key={cap.key}
                type="button"
                role="tab"
                aria-selected={isActive}
                className={`tab-btn ${isActive ? "active" : ""}`}
                onClick={() => handleTabChange(index)}
              >
                <div className="tab-top-row">
                  <span className="tab-num">WORKFLOW 0{index + 1}</span>
                  <FlatIcon name={cap.icon} size={16} color={isActive ? "#e84d7a" : "#0f5f4f"} />
                </div>
                <b className="tab-title">{cap.eyebrow}</b>
              </button>
            );
          })}
        </div>

        {/* WORKFLOW STAGE & FLOW GRAPH */}
        <div className="workflow-stage-card">
          <div className="stage-top-meta">
            <div className="stage-badge-pill" style={{ borderColor: currentCapability.color }}>
              <span className="dot-indicator" style={{ background: currentCapability.color }} />
              <b>{currentCapability.badge}</b>
            </div>
            <h3 className="stage-heading">{currentCapability.title}</h3>
            <p className="stage-description">{currentCapability.text}</p>
          </div>

          {/* INTERACTIVE NODE GRAPH (REACT FLOW STYLE) */}
          <div className="node-flow-canvas">
            <div className="canvas-header">
              <span>INTERACTIVE PIPELINE GRAPH (Click node to inspect)</span>
              <span className="step-counter">
                Node {selectedNode + 1} of {currentCapability.nodes.length}
              </span>
            </div>

            <div className="nodes-track">
              {currentCapability.nodes.map((node, nIdx) => {
                const isNodeActive = nIdx === selectedNode;
                return (
                  <div key={node.id} className="node-wrapper">
                    <button
                      type="button"
                      className={`flow-node-box ${isNodeActive ? "selected" : ""}`}
                      onClick={() => setSelectedNode(nIdx)}
                    >
                      <div className="node-box-header">
                        <span className="node-step-tag">STEP 0{nIdx + 1}</span>
                        <span className={`node-type-pill ${node.type}`}>
                          {node.type.toUpperCase()}
                        </span>
                      </div>
                      <b className="node-box-title">{node.name}</b>
                      <div className="node-preview-arrow">
                        <small className="node-out-preview">→ {node.output.slice(0, 24)}...</small>
                      </div>
                    </button>

                    {nIdx < currentCapability.nodes.length - 1 && (
                      <div className="flow-connector-edge">
                        <span className="connector-line" />
                        <span className="connector-arrow">▶</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* SELECTED NODE INSPECTOR PANEL */}
            <div className="node-inspector-panel">
              <div className="inspector-badge-row">
                <span className="inspector-step-num">STEP 0{selectedNode + 1} INSPECTION</span>
                <h4>{currentNode.name}</h4>
              </div>

              <p className="inspector-desc">{currentNode.details}</p>

              <div className="inspector-io-grid">
                <div className="io-card input-io">
                  <span className="io-tag">INPUT DATA CONTRACT</span>
                  <code>{currentNode.input}</code>
                </div>

                <div className="io-card output-io">
                  <span className="io-tag">OUTPUT ARTIFACT</span>
                  <code>{currentNode.output}</code>
                </div>
              </div>
            </div>
          </div>

          {/* KEY CAPABILITY FACTS */}
          <div className="facts-footer-row">
            <span className="facts-kicker">ENGINEERING GUARANTEES:</span>
            <ul className="facts-pills-list">
              {currentCapability.facts.map((fact) => (
                <li key={fact} className="fact-pill-item">
                  <FlatIcon name="check" size={13} color="#0f5f4f" />
                  <span>{fact}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      <style jsx>{`
        .capability-section {
          padding: 85px 0;
          border-top: 1px solid #172019;
          background: #fbf9f4;
        }
        .capability-container {
          width: min(calc(100% - 40px), 1180px);
          margin: 0 auto;
        }
        .capability-intro {
          margin-bottom: 36px;
        }
        .section-tag-row {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 12px;
        }
        .tag-index {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          height: 22px;
          padding: 0 7px;
          font-size: 0.68rem;
          font-weight: 900;
          line-height: 1;
          background: #172019;
          color: #ffffff;
          border-radius: 4px;
        }
        .section-kicker {
          font-size: 0.72rem;
          font-weight: 900;
          letter-spacing: 0.12em;
          color: #0f5f4f;
          line-height: 1;
          text-transform: uppercase;
        }
        .capability-main-title {
          font-size: clamp(2.2rem, 4vw, 3.4rem);
          font-family: Georgia, serif;
          margin: 0 0 10px;
          color: #172019;
          line-height: 1.05;
        }
        .capability-subtitle {
          font-size: 1rem;
          color: #555e54;
          max-width: 720px;
          line-height: 1.55;
          margin: 0;
        }
        .capability-tabs {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 12px;
          margin-bottom: 24px;
        }
        .tab-btn {
          border: 2px solid #172019;
          background: #ffffff;
          padding: 16px 18px;
          border-radius: 6px;
          text-align: left;
          cursor: pointer;
          transition: all 0.15s ease;
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .tab-btn:hover {
          background: #ffffff;
          box-shadow: 4px 4px 0 #172019;
        }
        .tab-btn.active {
          background: #172019;
          color: #ffffff;
          box-shadow: 5px 5px 0 #e84d7a;
        }
        .tab-top-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .tab-num {
          font-size: 0.65rem;
          font-weight: 900;
          letter-spacing: 0.1em;
          color: #687067;
        }
        .tab-btn.active .tab-num {
          color: #e84d7a;
        }
        .tab-title {
          font-size: 0.95rem;
          line-height: 1.3;
        }
        .workflow-stage-card {
          border: 2px solid #172019;
          background: #ffffff;
          box-shadow: 6px 6px 0 #172019;
          padding: 32px;
          border-radius: 8px;
        }
        .stage-top-meta {
          margin-bottom: 28px;
        }
        .stage-badge-pill {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 4px 10px;
          border: 1px solid #172019;
          background: #fbf9f4;
          border-radius: 4px;
          font-size: 0.68rem;
          font-weight: 900;
          letter-spacing: 0.08em;
          margin-bottom: 10px;
        }
        .dot-indicator {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }
        .stage-heading {
          font-size: 1.8rem;
          font-family: Georgia, serif;
          margin: 0 0 8px;
          color: #172019;
        }
        .stage-description {
          font-size: 0.95rem;
          color: #555e54;
          line-height: 1.55;
          max-width: 850px;
          margin: 0;
        }
        .node-flow-canvas {
          border: 1px solid #172019;
          background: #fbf9f4;
          border-radius: 6px;
          padding: 20px;
          margin-bottom: 28px;
        }
        .canvas-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          font-size: 0.65rem;
          font-weight: 900;
          letter-spacing: 0.1em;
          color: #687067;
          margin-bottom: 16px;
        }
        .step-counter {
          color: #0f5f4f;
        }
        .nodes-track {
          display: flex;
          align-items: center;
          gap: 8px;
          overflow-x: auto;
          padding-bottom: 14px;
          margin-bottom: 18px;
        }
        .node-wrapper {
          display: flex;
          align-items: center;
          gap: 8px;
          flex-shrink: 0;
        }
        .flow-node-box {
          border: 2px solid #172019;
          background: #ffffff;
          padding: 14px;
          border-radius: 6px;
          width: 210px;
          text-align: left;
          cursor: pointer;
          transition: all 0.15s ease;
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .flow-node-box:hover {
          box-shadow: 3px 3px 0 #172019;
          transform: translateY(-2px);
        }
        .flow-node-box.selected {
          background: #172019;
          color: #ffffff;
          box-shadow: 4px 4px 0 #e84d7a;
          border-color: #172019;
        }
        .node-box-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .node-step-tag {
          font-size: 0.6rem;
          font-weight: 900;
          color: #687067;
        }
        .flow-node-box.selected .node-step-tag {
          color: #e84d7a;
        }
        .node-type-pill {
          font-size: 0.55rem;
          font-weight: 900;
          padding: 2px 5px;
          border-radius: 3px;
          border: 1px solid #172019;
        }
        .node-type-pill.intake {
          background: #fbf9f4;
          color: #172019;
        }
        .node-type-pill.model {
          background: #dce8dd;
          color: #0f5f4f;
        }
        .node-type-pill.policy {
          background: #fef3c7;
          color: #92400e;
        }
        .node-type-pill.eval {
          background: #fce7f3;
          color: #be185d;
        }
        .node-type-pill.gate {
          background: #fee2e2;
          color: #991b1b;
        }
        .node-type-pill.spatial {
          background: #e0e7ff;
          color: #3730a3;
        }
        .node-box-title {
          font-size: 0.82rem;
          line-height: 1.3;
        }
        .node-preview-arrow {
          margin-top: 2px;
        }
        .node-out-preview {
          font-size: 0.65rem;
          color: #687067;
        }
        .flow-node-box.selected .node-out-preview {
          color: #dce8dd;
        }
        .flow-connector-edge {
          display: flex;
          align-items: center;
          gap: 2px;
        }
        .connector-line {
          width: 18px;
          height: 2px;
          background: #172019;
        }
        .connector-arrow {
          font-size: 0.65rem;
          color: #0f5f4f;
        }
        .node-inspector-panel {
          border: 1px solid #172019;
          background: #ffffff;
          padding: 18px;
          border-radius: 6px;
        }
        .inspector-badge-row {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 6px;
        }
        .inspector-step-num {
          font-size: 0.62rem;
          font-weight: 900;
          letter-spacing: 0.1em;
          color: #e84d7a;
          background: #fdf2f8;
          padding: 3px 6px;
          border: 1px solid #e84d7a;
          border-radius: 3px;
        }
        .inspector-badge-row h4 {
          font-size: 1.15rem;
          font-family: Georgia, serif;
          margin: 0;
          color: #172019;
        }
        .inspector-desc {
          font-size: 0.85rem;
          color: #555e54;
          line-height: 1.5;
          margin: 0 0 16px;
        }
        .inspector-io-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 12px;
        }
        .io-card {
          padding: 12px 14px;
          border-radius: 4px;
          border: 1px solid #e2ded4;
        }
        .input-io {
          background: #fbf9f4;
        }
        .output-io {
          background: #f4f8f5;
          border-color: #0f5f4f;
        }
        .io-tag {
          display: block;
          font-size: 0.58rem;
          font-weight: 900;
          letter-spacing: 0.1em;
          color: #687067;
          margin-bottom: 4px;
        }
        .io-card code {
          font-size: 0.78rem;
          font-weight: 700;
          color: #172019;
          word-break: break-word;
        }
        .facts-footer-row {
          display: flex;
          align-items: center;
          gap: 16px;
          flex-wrap: wrap;
          padding-top: 18px;
          border-top: 1px solid #e2ded4;
        }
        .facts-kicker {
          font-size: 0.65rem;
          font-weight: 900;
          letter-spacing: 0.1em;
          color: #0f5f4f;
        }
        .facts-pills-list {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          margin: 0;
          padding: 0;
          list-style: none;
        }
        .fact-pill-item {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 4px 9px;
          border: 1px solid #e2ded4;
          background: #fbf9f4;
          font-size: 0.74rem;
          font-weight: 750;
          color: #172019;
          border-radius: 4px;
        }
        @media (max-width: 900px) {
          .capability-tabs {
            grid-template-columns: 1fr;
          }
          .inspector-io-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </section>
  );
}
