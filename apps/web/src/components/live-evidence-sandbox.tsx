"use client";

import { useState } from "react";
import { FlatIcon } from "@/components/flat-icons";

interface Preset {
  id: string;
  label: string;
  icon: string;
  text: string;
  category: string;
  mediaType: string;
  mediaLabel: string;
  gps: string;
  landmark: string;
  observedFacts: string[];
  reportedClaims: string[];
  retrievedPolicy: string;
  policyTitle: string;
  severity: number;
  priority: "P1" | "P2" | "P3";
  department: string;
  workOrderDraft: string;
}

const PRESETS: Preset[] = [
  {
    id: "water",
    label: "Water Main Rupture",
    icon: "water",
    text: "Heavy water bursting from underground pipeline near DAV School gate. Road is flooded and water is entering compounds.",
    category: "water_leakage",
    mediaType: "Live Camera Geotag",
    mediaLabel: "Sub-surface Pipe Fracture (High Pressure)",
    gps: "20.29614° N, 85.82451° E · Ward 12",
    landmark: "14m from DAV Public School Gate (500m Safety Buffer Active)",
    observedFacts: [
      "High-pressure liquid pooling and asphalt surface fissure",
      "Sub-surface municipal main line failure",
      "Roadway pedestrian crossing obstructed",
    ],
    reportedClaims: [
      "Water bursting for approximately 45 minutes",
      "Liquid entering residential compounds",
    ],
    retrievedPolicy: "PLAY-WATER-01",
    policyTitle: "Municipal Distribution Rupture & Emergency Isolation Protocol",
    severity: 78,
    priority: "P1",
    department: "Public Health Engineering / Water Works",
    workOrderDraft: "Dispatch ductile collar repair sleeve (8-inch) + excavation crew to Ward 12.",
  },
  {
    id: "tree",
    label: "Fallen Banyan Branch",
    icon: "tree",
    text: "Large banyan tree branch snapped during morning rain, completely blocking the southbound lane on Park Road.",
    category: "fallen_tree",
    mediaType: "Street View Sensor",
    mediaLabel: "Overhead Timber Obstruction across Roadway",
    gps: "20.29420° N, 85.82110° E · Ward 11",
    landmark: "Park Road, opposite Community Center",
    observedFacts: [
      "Heavy timber obstruction resting across roadway",
      "Southbound vehicular lane 100% blocked",
      "No structural impact on overhead power lines detected",
    ],
    reportedClaims: [
      "Branch snapped during squall",
      "Traffic building up rapidly",
    ],
    retrievedPolicy: "PLAY-FORESTRY-03",
    policyTitle: "Roadway Timber Removal & Rapid Arborist Clearance",
    severity: 54,
    priority: "P2",
    department: "Parks & Urban Forestry Department",
    workOrderDraft: "Deploy 2 arborist chainsaws and hydraulic crane to clear Park Road.",
  },
  {
    id: "light",
    label: "Streetlight Circuit Outage",
    icon: "streetlight",
    text: "Three consecutive streetlights are dark along East Gate commercial crossroad. Dark stretch at night.",
    category: "streetlight",
    mediaType: "Infrared Optical Sensor",
    mediaLabel: "Zero Luminaire Output on Poles #104-106",
    gps: "20.29880° N, 85.83100° E · Ward 10",
    landmark: "East Gate Commercial Crossroad",
    observedFacts: [
      "Zero luminaire output verified on poles #104, #105, #106",
      "Underground feeder cable ground fault suspected",
    ],
    reportedClaims: [
      "Dark for 3 consecutive nights",
      "Difficult crossing for pedestrians",
    ],
    retrievedPolicy: "PLAY-LIGHT-02",
    policyTitle: "Feeder Circuit Diagnostic & Municipal Luminaire Replacement",
    severity: 38,
    priority: "P3",
    department: "Electrical Division / Public Lighting",
    workOrderDraft: "Dispatch electrical maintenance van to inspect circuit breaker #04.",
  },
];

export function LiveEvidenceSandbox() {
  const [activePreset, setActivePreset] = useState<Preset>(PRESETS[0]);
  const [customText, setCustomText] = useState<string>(PRESETS[0].text);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [supervisorStatus, setSupervisorStatus] = useState<"pending" | "approved" | "clarification">("pending");
  const [actionNotice, setActionNotice] = useState<string>("");

  const handleSelectPreset = (preset: Preset) => {
    setActivePreset(preset);
    setCustomText(preset.text);
    setSupervisorStatus("pending");
    setActionNotice("");
    setIsProcessing(true);
    setTimeout(() => setIsProcessing(false), 300);
  };

  const handleRunIntake = () => {
    setIsProcessing(true);
    setActionNotice("");
    setSupervisorStatus("pending");
    setTimeout(() => {
      setIsProcessing(false);
      setActionNotice("✓ Multimodal evidence extracted and policy playbooks retrieved successfully.");
    }, 450);
  };

  const handleApprove = () => {
    setSupervisorStatus("approved");
    setActionNotice("✓ Work order WO-2026-0881 authorized by Supervisor Marcus Vance.");
  };

  const handleClarify = () => {
    setSupervisorStatus("clarification");
    setActionNotice("✓ Single-question photo request dispatched to citizen via WhatsApp.");
  };

  return (
    <div className="sandbox-panel-root">
      {/* TOP CONTROLS & PRESET BAR */}
      <div className="sandbox-control-strip">
        <div className="strip-left-status">
          <span className="live-pulse-dot" />
          <b className="strip-title">LIVE INTAKE & REASONING ENGINE</b>
        </div>

        <div className="preset-selector-row" role="tablist">
          {PRESETS.map((p) => {
            const isSelected = activePreset.id === p.id;
            return (
              <button
                key={p.id}
                type="button"
                role="tab"
                aria-selected={isSelected}
                className={`preset-tab-btn ${isSelected ? "active" : ""}`}
                onClick={() => handleSelectPreset(p)}
              >
                <FlatIcon name={p.icon} size={14} />
                <span>{p.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* 2-COLUMN SANDBOX WORKSPACE */}
      <div className="sandbox-columns-grid">
        {/* LEFT: RAW MULTIMODAL INTAKE */}
        <div className="sandbox-intake-col">
          <div className="pane-header">
            <span className="pane-step-badge">01</span>
            <div>
              <b className="pane-heading">Citizen Multimodal Intake</b>
              <p className="pane-sub">Raw citizen statement & attached observable media</p>
            </div>
          </div>

          <div className="intake-form-box">
            <label className="intake-label" htmlFor="sandbox-text-input">
              Citizen Description (Editable)
            </label>
            <textarea
              id="sandbox-text-input"
              className="sandbox-textarea"
              value={customText}
              onChange={(e) => setCustomText(e.target.value)}
              rows={3}
            />

            {/* ATTACHED MEDIA TELEMETRY CARD */}
            <div className="media-telemetry-tile">
              <div className="media-tile-top">
                <div className="media-badge">
                  <FlatIcon name="camera" size={13} color="#0f5f4f" />
                  <span>{activePreset.mediaType}</span>
                </div>
                <span className="gps-tag">
                  <FlatIcon name="pin" size={12} color="#687067" />
                  <span>{activePreset.gps}</span>
                </span>
              </div>
              <b className="media-tag-title">{activePreset.mediaLabel}</b>
              <div className="landmark-text">
                <FlatIcon name="landmark" size={12} color="#495248" />
                <span>Landmark: {activePreset.landmark}</span>
              </div>
            </div>

            <button
              type="button"
              className="button run-reasoning-btn"
              onClick={handleRunIntake}
              disabled={isProcessing}
            >
              {isProcessing ? (
                "Analyzing Incident Evidence..."
              ) : (
                <span className="btn-label-with-icon">
                  <FlatIcon name="workflow" size={14} />
                  <span>Run Multimodal Extraction</span>
                </span>
              )}
            </button>
          </div>

          <div className="boundary-guarantee-note">
            <FlatIcon name="shield" size={18} color="#0f5f4f" />
            <div>
              <b>Boundary Integrity Rule</b>
              <p>
                Civitas never allows LLMs to hallucinate SLA commitments or silently overwrite citizen assertions.
              </p>
            </div>
          </div>
        </div>

        {/* RIGHT: STRUCTURED EVIDENCE & POLICY GROUNDING */}
        <div className="sandbox-reasoning-col">
          <div className="pane-header">
            <span className="pane-step-badge">02</span>
            <div>
              <b className="pane-heading">Structured Evidence & Policy Grounding</b>
              <p className="pane-sub">Observable facts, playbook matching & human checkpoint</p>
            </div>
          </div>

          <div className="reasoning-cards-stack">
            {/* EVIDENCE SPLIT: OBSERVED VS REPORTED */}
            <div className="evidence-split-card">
              <div className="split-column observed">
                <div className="split-title-row">
                  <span className="dot dot-obs" />
                  <b>OBSERVED FACTS (MEDIA)</b>
                </div>
                <ul className="evidence-list">
                  {activePreset.observedFacts.map((fact) => (
                    <li key={fact}>{fact}</li>
                  ))}
                </ul>
              </div>

              <div className="split-column reported">
                <div className="split-title-row">
                  <span className="dot dot-rep" />
                  <b>REPORTED CLAIMS (CITIZEN)</b>
                </div>
                <ul className="evidence-list">
                  {activePreset.reportedClaims.map((claim) => (
                    <li key={claim}>{claim}</li>
                  ))}
                </ul>
              </div>
            </div>

            {/* RETRIEVED POLICY PLAYBOOK & RISK SCORES */}
            <div className="policy-risk-card">
              <div className="policy-details">
                <span className="policy-kicker">RETRIEVED MUNICIPAL PLAYBOOK</span>
                <b className="policy-code-badge">{activePreset.retrievedPolicy}</b>
                <p className="policy-title-text">{activePreset.policyTitle}</p>
                <small className="dept-text">Assigned: {activePreset.department}</small>
              </div>

              <div className="risk-meters-group">
                <div className="meter-box">
                  <span>SEVERITY</span>
                  <b className="severity-val">{activePreset.severity}/100</b>
                </div>
                <div className="meter-box">
                  <span>PRIORITY</span>
                  <b className={`prio-badge prio-${activePreset.priority.toLowerCase()}`}>
                    {activePreset.priority} CRITICAL
                  </b>
                </div>
              </div>
            </div>

            {/* SUPERVISOR HUMAN-IN-THE-LOOP CHECKPOINT */}
            <div className="supervisor-action-card">
              <div className="supervisor-header">
                <div>
                  <span className="supervisor-kicker">HUMAN SUPERVISOR CHECKPOINT</span>
                  <b className="draft-order-title">Draft Work Order: {activePreset.workOrderDraft}</b>
                </div>
                <span className={`status-pill status-${supervisorStatus}`}>
                  {supervisorStatus === "approved"
                    ? "DISPATCH AUTHORIZED"
                    : supervisorStatus === "clarification"
                    ? "WAITING CITIZEN PHOTO"
                    : "AWAITING SUPERVISOR"}
                </span>
              </div>

              {supervisorStatus === "pending" && (
                <div className="supervisor-btn-row">
                  <button type="button" className="button small authorize-btn" onClick={handleApprove}>
                    Authorize Work Order Dispatch →
                  </button>
                  <button type="button" className="outline small clarify-btn" onClick={handleClarify}>
                    Request 1 Photo Clarification
                  </button>
                </div>
              )}

              {actionNotice && (
                <div className="action-feedback-toast" role="status">
                  <span>{actionNotice}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        .sandbox-panel-root {
          border: 2px solid #172019;
          background: #ffffff;
          box-shadow: 6px 6px 0 #172019;
          border-radius: 8px;
          overflow: hidden;
        }
        .sandbox-control-strip {
          display: flex;
          justify-content: space-between;
          align-items: center;
          background: #172019;
          color: #ffffff;
          padding: 12px 24px;
          gap: 16px;
          flex-wrap: wrap;
        }
        .strip-left-status {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .live-pulse-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #10b981;
          animation: pulse 1.6s infinite;
        }
        @keyframes pulse {
          0%, 100% {
            opacity: 1;
            transform: scale(1);
          }
          50% {
            opacity: 0.4;
            transform: scale(0.85);
          }
        }
        .strip-title {
          font-size: 0.68rem;
          letter-spacing: 0.12em;
          color: #dce8dd;
        }
        .preset-selector-row {
          display: flex;
          gap: 6px;
          flex-wrap: wrap;
        }
        .preset-tab-btn {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 6px 12px;
          background: #232d25;
          color: #fbf9f4;
          border: 1px solid #334035;
          border-radius: 4px;
          font-size: 0.74rem;
          font-weight: 750;
          cursor: pointer;
          transition: all 0.15s ease;
        }
        .preset-tab-btn:hover {
          background: #334035;
        }
        .preset-tab-btn.active {
          background: #0f5f4f;
          border-color: #0f5f4f;
          color: #ffffff;
          box-shadow: 0 0 8px rgba(15, 95, 79, 0.5);
        }
        .sandbox-columns-grid {
          display: grid;
          grid-template-columns: 1fr 1.25fr;
          gap: 28px;
          padding: 28px 32px;
          background: #fbf9f4;
        }
        .pane-header {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 14px;
        }
        .pane-step-badge {
          width: 28px;
          height: 28px;
          background: #172019;
          color: #ffffff;
          font-size: 0.75rem;
          font-weight: 900;
          border-radius: 4px;
          display: grid;
          place-items: center;
          flex-shrink: 0;
        }
        .pane-heading {
          display: block;
          font-size: 0.95rem;
          color: #172019;
        }
        .pane-sub {
          font-size: 0.72rem;
          color: #687067;
          margin: 0;
        }
        .intake-form-box {
          display: flex;
          flex-direction: column;
          gap: 12px;
          background: #ffffff;
          border: 1px solid #172019;
          border-radius: 6px;
          padding: 16px;
        }
        .intake-label {
          font-size: 0.72rem;
          font-weight: 800;
          color: #172019;
        }
        .sandbox-textarea {
          width: 100%;
          border: 1px solid #172019;
          background: #fbf9f4;
          padding: 10px 12px;
          font-size: 0.85rem;
          line-height: 1.45;
          border-radius: 4px;
          outline: none;
          font-family: inherit;
          resize: vertical;
        }
        .sandbox-textarea:focus {
          background: #ffffff;
          border-color: #0f5f4f;
        }
        .media-telemetry-tile {
          border: 1px solid #e2ded4;
          background: #f4f8f5;
          padding: 10px 12px;
          border-radius: 4px;
          display: flex;
          flex-direction: column;
          gap: 3px;
        }
        .media-tile-top {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .media-badge {
          display: inline-flex;
          align-items: center;
          gap: 5px;
          font-size: 0.64rem;
          font-weight: 850;
          color: #0f5f4f;
        }
        .gps-tag {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          font-size: 0.62rem;
          font-weight: 700;
          color: #687067;
        }
        .media-tag-title {
          font-size: 0.8rem;
          color: #172019;
        }
        .landmark-text {
          display: inline-flex;
          align-items: center;
          gap: 5px;
          font-size: 0.68rem;
          color: #495248;
        }
        .run-reasoning-btn {
          width: 100%;
          padding: 10px;
        }
        .btn-label-with-icon {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 7px;
        }
        .boundary-guarantee-note {
          display: flex;
          gap: 10px;
          padding: 12px;
          border: 1px solid #0f5f4f;
          background: #dce8dd;
          border-radius: 6px;
          margin-top: 14px;
        }
        .shield-icon {
          font-size: 1.1rem;
        }
        .boundary-guarantee-note b {
          display: block;
          font-size: 0.76rem;
          color: #0f5f4f;
          margin-bottom: 2px;
        }
        .boundary-guarantee-note p {
          font-size: 0.7rem;
          color: #172019;
          margin: 0;
          line-height: 1.35;
        }
        .reasoning-cards-stack {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .evidence-split-card {
          display: grid;
          grid-template-columns: 1fr 1fr;
          border: 1px solid #172019;
          background: #ffffff;
          border-radius: 6px;
          overflow: hidden;
        }
        .split-column {
          padding: 14px;
        }
        .split-column.observed {
          background: #f4f8f5;
          border-right: 1px solid #e2ded4;
        }
        .split-title-row {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 0.66rem;
          font-weight: 900;
          letter-spacing: 0.08em;
          margin-bottom: 8px;
        }
        .split-column.observed .split-title-row {
          color: #0f5f4f;
        }
        .split-column.reported .split-title-row {
          color: #991b1b;
        }
        .dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
        }
        .dot-obs {
          background: #0f5f4f;
        }
        .dot-rep {
          background: #e84d7a;
        }
        .evidence-list {
          list-style: none;
          padding: 0;
          margin: 0;
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .evidence-list li {
          font-size: 0.74rem;
          color: #334035;
          line-height: 1.35;
        }
        .evidence-list li::before {
          content: "• ";
          color: #687067;
        }
        .policy-risk-card {
          display: flex;
          justify-content: space-between;
          align-items: center;
          border: 1px solid #172019;
          background: #ffffff;
          border-radius: 6px;
          padding: 14px 16px;
          gap: 16px;
        }
        .policy-kicker {
          font-size: 0.58rem;
          font-weight: 900;
          letter-spacing: 0.1em;
          color: #687067;
          display: block;
        }
        .policy-code-badge {
          font-size: 0.86rem;
          color: #0f5f4f;
          display: block;
          margin: 2px 0;
        }
        .policy-title-text {
          font-size: 0.74rem;
          color: #172019;
          margin: 0 0 3px;
        }
        .dept-text {
          font-size: 0.66rem;
          color: #687067;
          display: block;
        }
        .risk-meters-group {
          display: flex;
          gap: 12px;
        }
        .meter-box {
          display: flex;
          flex-direction: column;
          gap: 2px;
          text-align: right;
        }
        .meter-box span {
          font-size: 0.56rem;
          font-weight: 850;
          color: #687067;
        }
        .severity-val {
          font-size: 1.1rem;
          color: #e84d7a;
          font-family: Georgia, serif;
        }
        .prio-badge {
          font-size: 0.62rem;
          font-weight: 900;
          padding: 3px 6px;
          border-radius: 3px;
          background: #fee2e2;
          color: #991b1b;
          border: 1px solid #991b1b;
        }
        .supervisor-action-card {
          border: 1px solid #172019;
          background: #ffffff;
          border-radius: 6px;
          padding: 14px 16px;
          display: flex;
          flex-direction: column;
          gap: 10px;
        }
        .supervisor-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 12px;
        }
        .supervisor-kicker {
          font-size: 0.58rem;
          font-weight: 900;
          letter-spacing: 0.1em;
          color: #0f5f4f;
          display: block;
        }
        .draft-order-title {
          font-size: 0.78rem;
          color: #172019;
          display: block;
          margin-top: 2px;
        }
        .status-pill {
          font-size: 0.6rem;
          font-weight: 850;
          padding: 3px 8px;
          border-radius: 4px;
          white-space: nowrap;
        }
        .status-pending {
          background: #fef08a;
          color: #854d0e;
          border: 1px solid #854d0e;
        }
        .status-approved {
          background: #dce8dd;
          color: #0f5f4f;
          border: 1px solid #0f5f4f;
        }
        .status-clarification {
          background: #fce7f3;
          color: #be185d;
          border: 1px solid #be185d;
        }
        .supervisor-btn-row {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
        }
        .action-feedback-toast {
          padding: 6px 10px;
          background: #f4f8f5;
          border: 1px solid #0f5f4f;
          color: #0f5f4f;
          font-size: 0.72rem;
          font-weight: 750;
          border-radius: 4px;
        }
        @media (max-width: 900px) {
          .sandbox-columns-grid {
            grid-template-columns: 1fr;
          }
          .evidence-split-card {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
}
