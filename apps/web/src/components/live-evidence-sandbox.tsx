"use client";

import { useState } from "react";
import { FlatIcon } from "@/components/flat-icons";

interface Preset {
  id: string;
  label: string;
  icon: string;
  text: string;
  category: string;
  landmark: string;
  observedFacts: string[];
  reportedClaims: string[];
  retrievedPolicy: string;
  severity: number;
  priority: "P1" | "P2" | "P3";
  department: string;
}

const PRESETS: Preset[] = [
  {
    id: "water",
    label: "Water Main Leak",
    icon: "water",
    text: "Heavy water bursting from underground pipeline near DAV School gate. Kids are crossing into flooded street.",
    category: "water_leakage",
    landmark: "14m from DAV Public School Gate (Hazard Buffer active)",
    observedFacts: ["High-volume liquid surface pooling", "Roadway obstruction", "Sub-surface main fissure"],
    reportedClaims: ["Pipeline burst approximately 40 minutes ago", "Water entering school compound"],
    retrievedPolicy: "PLAY-WATER-01 (Municipal Main Line Rupture Protocol) · Ward 12",
    severity: 78,
    priority: "P1",
    department: "Water Supply & Drainage (Primary) + Traffic Control (Support)",
  },
  {
    id: "tree",
    label: "Fallen Tree",
    icon: "tree",
    text: "Large banyan branch snapped in heavy wind and completely blocking the inbound lane on Park Road.",
    category: "fallen_tree",
    landmark: "Park Road, opposite Ward Community Center",
    observedFacts: ["Overhead timber debris on asphalt", "1 lane completely impassable"],
    reportedClaims: ["Branch snapped during morning thunderstorm", "No injuries reported"],
    retrievedPolicy: "PLAY-FORESTRY-03 (Obstruction Clearing & Heavy Timber Removal)",
    severity: 54,
    priority: "P2",
    department: "Parks & Urban Forestry",
  },
  {
    id: "light",
    label: "Streetlight Outage",
    icon: "streetlight",
    text: "Three streetlights in a row are flickering and dark along the East Gate crossing at night.",
    category: "streetlight",
    landmark: "East Gate Commercial Crossroad, Poles #104-106",
    observedFacts: ["Zero luminaire output detected on 3 poles", "Underground feeder continuity fault"],
    reportedClaims: ["Dark for 3 consecutive nights", "Pedestrians struggling to cross"],
    retrievedPolicy: "PLAY-LIGHT-02 (Feeder Circuit Diagnostic & Luminaire Repair)",
    severity: 38,
    priority: "P3",
    department: "Electrical & Public Lighting",
  },
];

export function LiveEvidenceSandbox() {
  const [activePreset, setActivePreset] = useState<Preset>(PRESETS[0]);
  const [customText, setCustomText] = useState<string>(PRESETS[0].text);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);

  const handleSelectPreset = (preset: Preset) => {
    setActivePreset(preset);
    setCustomText(preset.text);
    setIsProcessing(true);
    setTimeout(() => setIsProcessing(false), 350);
  };

  return (
    <div className="sandbox-card-root">
      <div className="sandbox-top-header">
        <div>
          <span className="sandbox-kicker">LIVE INTERACTIVE DEMO</span>
          <h3 className="sandbox-heading">Real-Time Evidence & Intelligence Sandbox</h3>
          <p className="sandbox-subtext">
            Test how Civitas separates raw citizen claims from observable media evidence, retrieved policy playbooks, and deterministic risk scores.
          </p>
        </div>

        <div className="preset-selector-chips">
          {PRESETS.map((p) => (
            <button
              key={p.id}
              className={`preset-chip ${activePreset.id === p.id ? "active" : ""}`}
              onClick={() => handleSelectPreset(p)}
            >
              <FlatIcon name={p.icon} size={14} />
              <span>{p.label}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="sandbox-body-grid">
        {/* INPUT COLUMN */}
        <div className="sandbox-input-col">
          <div className="col-header">
            <span className="step-num">01</span>
            <b>Raw Citizen Intake</b>
          </div>
          <div className="textarea-container">
            <textarea
              className="sandbox-textarea"
              value={customText}
              onChange={(e) => setCustomText(e.target.value)}
              rows={4}
              aria-label="Citizen report text"
            />
            <div className="input-meta-bar">
              <span>📍 WGS84: 20.29614° N, 85.82451° E</span>
              <span>📸 1 Attached Image</span>
            </div>
          </div>

          <div className="evidence-badge-box">
            <span className="badge-title">BOUNDARY INTEGRITY CHECK</span>
            <p>
              Civitas <b>never hallucinates</b> response timelines. Every action must be grounded in an existing municipal playbook.
            </p>
          </div>
        </div>

        {/* OUTPUT COLUMN */}
        <div className="sandbox-output-col">
          <div className="col-header">
            <span className="step-num">02</span>
            <b>Structured Evidence & Risk Breakdown</b>
            {isProcessing && <span className="processing-pill">Reasoning...</span>}
          </div>

          <div className="output-cards-stack">
            {/* OBSERVED VS REPORTED */}
            <div className="evidence-split-card">
              <div className="split-half observed">
                <div className="split-label">
                  <span className="dot dot-obs" /> OBSERVED FACTS (MEDIA)
                </div>
                <ul>
                  {activePreset.observedFacts.map((fact) => (
                    <li key={fact}>{fact}</li>
                  ))}
                </ul>
              </div>

              <div className="split-half reported">
                <div className="split-label">
                  <span className="dot dot-rep" /> REPORTED CLAIMS (CITIZEN)
                </div>
                <ul>
                  {activePreset.reportedClaims.map((claim) => (
                    <li key={claim}>{claim}</li>
                  ))}
                </ul>
              </div>
            </div>

            {/* POLICY GROUNDING & RISK */}
            <div className="grounding-risk-row">
              <div className="grounding-box">
                <span className="row-kicker">RETRIEVED MUNICIPAL PLAYBOOK</span>
                <b className="policy-code">{activePreset.retrievedPolicy}</b>
                <span className="landmark-tag">📍 {activePreset.landmark}</span>
              </div>

              <div className="risk-score-box">
                <div className="score-item">
                  <span>SEVERITY</span>
                  <b className="score-val">{activePreset.severity}/100</b>
                </div>
                <div className="score-item">
                  <span>PRIORITY</span>
                  <b className={`prio-pill ${activePreset.priority.toLowerCase()}`}>
                    {activePreset.priority}
                  </b>
                </div>
              </div>
            </div>

            {/* ROUTING & HUMAN GATE */}
            <div className="routing-gate-bar">
              <div className="dept-info">
                <span>ASSIGNED JURISDICTION</span>
                <b>{activePreset.department}</b>
              </div>
              <div className="human-gate-pill">
                <span className="gate-icon">🛡️</span>
                <span>PAUSED AT SUPERVISOR CHECKPOINT</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        .sandbox-card-root {
          border: 2px solid #172019;
          background: #ffffff;
          box-shadow: 6px 6px 0 #172019;
          padding: 32px;
          margin: 40px 0;
        }
        .sandbox-top-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 20px;
          padding-bottom: 24px;
          border-bottom: 1px solid #172019;
          margin-bottom: 28px;
          flex-wrap: wrap;
        }
        .sandbox-kicker {
          font-size: 0.65rem;
          font-weight: 900;
          letter-spacing: 0.12em;
          color: #0f5f4f;
          display: block;
          margin-bottom: 4px;
        }
        .sandbox-heading {
          font-size: 1.6rem;
          font-family: Georgia, serif;
          margin: 0 0 6px;
          color: #172019;
        }
        .sandbox-subtext {
          font-size: 0.9rem;
          color: #555e54;
          margin: 0;
          max-width: 650px;
          line-height: 1.5;
        }
        .preset-selector-chips {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
        }
        .preset-chip {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 8px 14px;
          border: 1px solid #172019;
          background: #fbf9f4;
          font-size: 0.78rem;
          font-weight: 800;
          border-radius: 4px;
          cursor: pointer;
          transition: all 0.15s ease;
        }
        .preset-chip:hover {
          background: #172019;
          color: #ffffff;
        }
        .preset-chip.active {
          background: #172019;
          color: #ffffff;
          box-shadow: 3px 3px 0 #e84d7a;
        }
        .sandbox-body-grid {
          display: grid;
          grid-template-columns: 1fr 1.3fr;
          gap: 32px;
        }
        .col-header {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 14px;
        }
        .step-num {
          font-size: 0.72rem;
          font-weight: 900;
          color: #0f5f4f;
          background: #dce8dd;
          padding: 2px 6px;
          border: 1px solid #0f5f4f;
          border-radius: 3px;
        }
        .col-header b {
          font-size: 0.9rem;
          color: #172019;
        }
        .processing-pill {
          margin-left: auto;
          font-size: 0.65rem;
          font-weight: 800;
          background: #e3b950;
          padding: 2px 8px;
          border-radius: 4px;
        }
        .textarea-container {
          border: 1px solid #172019;
          background: #fbf9f4;
          border-radius: 4px;
          overflow: hidden;
        }
        .sandbox-textarea {
          width: 100%;
          border: 0;
          background: transparent;
          padding: 14px;
          font-size: 0.88rem;
          line-height: 1.55;
          font-family: inherit;
          resize: none;
          outline: none;
          color: #172019;
        }
        .input-meta-bar {
          display: flex;
          justify-content: space-between;
          padding: 8px 14px;
          background: #ede9df;
          font-size: 0.68rem;
          font-weight: 750;
          color: #555e54;
          border-top: 1px solid #e2ded4;
        }
        .evidence-badge-box {
          margin-top: 20px;
          padding: 14px;
          border: 1px dashed #0f5f4f;
          background: #f4f8f5;
          border-radius: 4px;
        }
        .badge-title {
          font-size: 0.62rem;
          font-weight: 900;
          letter-spacing: 0.1em;
          color: #0f5f4f;
          display: block;
          margin-bottom: 4px;
        }
        .evidence-badge-box p {
          font-size: 0.8rem;
          color: #495248;
          margin: 0;
          line-height: 1.45;
        }
        .output-cards-stack {
          display: flex;
          flex-direction: column;
          gap: 14px;
        }
        .evidence-split-card {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 12px;
          border: 1px solid #172019;
          background: #fbf9f4;
          padding: 14px;
        }
        .split-label {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 0.62rem;
          font-weight: 900;
          letter-spacing: 0.08em;
          margin-bottom: 8px;
        }
        .dot {
          width: 7px;
          height: 7px;
          border-radius: 50%;
        }
        .dot-obs {
          background: #0f5f4f;
        }
        .dot-rep {
          background: #e84d7a;
        }
        .split-half ul {
          margin: 0;
          padding-left: 16px;
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .split-half li {
          font-size: 0.78rem;
          color: #495248;
          line-height: 1.35;
        }
        .grounding-risk-row {
          display: grid;
          grid-template-columns: 1.8fr 1fr;
          gap: 12px;
          border: 1px solid #172019;
          background: #ffffff;
          padding: 14px;
        }
        .row-kicker {
          font-size: 0.58rem;
          font-weight: 900;
          letter-spacing: 0.1em;
          color: #687067;
          display: block;
          margin-bottom: 4px;
        }
        .policy-code {
          font-size: 0.85rem;
          color: #172019;
          display: block;
          margin-bottom: 6px;
        }
        .landmark-tag {
          font-size: 0.72rem;
          font-weight: 750;
          color: #0f5f4f;
        }
        .risk-score-box {
          display: flex;
          gap: 12px;
          border-left: 1px solid #e2ded4;
          padding-left: 14px;
          align-items: center;
        }
        .score-item span {
          display: block;
          font-size: 0.58rem;
          font-weight: 900;
          color: #687067;
        }
        .score-val {
          font-size: 1.15rem;
          font-family: monospace;
          color: #e84d7a;
        }
        .prio-pill {
          display: inline-block;
          font-size: 0.75rem;
          font-weight: 900;
          padding: 2px 8px;
          border-radius: 3px;
          margin-top: 2px;
        }
        .prio-pill.p1 {
          background: #e84d7a;
          color: #ffffff;
        }
        .prio-pill.p2 {
          background: #0f5f4f;
          color: #ffffff;
        }
        .prio-pill.p3 {
          background: #e3b950;
          color: #172019;
        }
        .routing-gate-bar {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 16px;
          border: 1px solid #172019;
          background: #172019;
          color: #ffffff;
          border-radius: 4px;
          flex-wrap: wrap;
          gap: 10px;
        }
        .dept-info span {
          display: block;
          font-size: 0.58rem;
          font-weight: 850;
          letter-spacing: 0.08em;
          color: #9da99e;
        }
        .dept-info b {
          font-size: 0.82rem;
          color: #ffffff;
        }
        .human-gate-pill {
          display: flex;
          align-items: center;
          gap: 6px;
          background: #2b382d;
          padding: 4px 10px;
          border-radius: 4px;
          font-size: 0.68rem;
          font-weight: 850;
          letter-spacing: 0.06em;
          color: #dce8dd;
        }
        @media (max-width: 900px) {
          .sandbox-body-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
}
