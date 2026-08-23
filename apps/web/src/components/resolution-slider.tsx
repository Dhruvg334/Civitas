"use client";

import { useState, useRef } from "react";
import { FlatIcon } from "@/components/flat-icons";

interface Props {
  beforeLabel?: string;
  afterLabel?: string;
  classification?: string;
  remainingEvidence?: string[];
  resolvedEvidence?: string[];
}

export function ResolutionSlider({
  beforeLabel = "Before: Main Pipeline Rupture (INC-0241)",
  afterLabel = "After: Clamped Pipe & Backfilled Asphalt",
  classification = "RESOLVED",
  remainingEvidence = ["Minor surface moisture drying on road shoulder; zero standing puddles"],
  resolvedEvidence = [
    "Subsurface high-pressure water flow completely halted",
    "Ductile iron repair collar secured and pressure-tested",
    "Excavated trench backfilled and sealed with hot-mix asphalt",
    "Pedestrian crossing outside DAV Public School unobstructed",
  ],
}: Props) {
  const [sliderPosition, setSliderPosition] = useState(50);
  const [activeView, setActiveView] = useState<"slider" | "before" | "after">("slider");
  const isDragging = useRef(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleMove = (clientX: number) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = clientX - rect.left;
    let percentage = (x / rect.width) * 100;
    if (percentage < 0) percentage = 0;
    if (percentage > 100) percentage = 100;
    setSliderPosition(percentage);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (!isDragging.current) return;
    handleMove(e.touches[0].clientX);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging.current) return;
    handleMove(e.clientX);
  };

  return (
    <div className="resolution-verifier-card">
      {/* HEADER BAR */}
      <div className="verifier-header">
        <div className="verifier-title-col">
          <div className="verifier-kicker-row">
            <span className="verifier-kicker">AUTOMATED RESOLUTION CLASSIFIER</span>
            <span className="confidence-pill">ZERO-SHOT VISION: HIGH CONFIDENCE</span>
          </div>
          <h3 className="verifier-title">Before vs After Field Repair Verification</h3>
        </div>

        <div className="verifier-status-pill">
          <span className="status-indicator-dot" />
          <b>{classification.replace("_", " ").toUpperCase()}</b>
        </div>
      </div>

      {/* VIEW CONTROLS */}
      <div className="verifier-toggle-bar">
        <div className="toggle-group">
          <button
            type="button"
            className={`toggle-btn ${activeView === "slider" ? "active" : ""}`}
            onClick={() => {
              setActiveView("slider");
              setSliderPosition(50);
            }}
          >
            ⇄ Interactive Split Slider
          </button>
          <button
            type="button"
            className={`toggle-btn ${activeView === "before" ? "active" : ""}`}
            onClick={() => {
              setActiveView("before");
              setSliderPosition(100);
            }}
          >
            1. View Incident Photo
          </button>
          <button
            type="button"
            className={`toggle-btn ${activeView === "after" ? "active" : ""}`}
            onClick={() => {
              setActiveView("after");
              setSliderPosition(0);
            }}
          >
            2. View Repair Evidence
          </button>
        </div>

        <span className="drag-hint">
          {activeView === "slider" ? "Drag center handle to inspect before vs after" : "Full frame preview"}
        </span>
      </div>

      {/* COMPARATIVE VISUAL CANVAS (HEIGHT: 480px) */}
      <div
        ref={containerRef}
        className="slider-viewport"
        onMouseDown={() => (isDragging.current = true)}
        onMouseUp={() => (isDragging.current = false)}
        onMouseLeave={() => (isDragging.current = false)}
        onMouseMove={handleMouseMove}
        onTouchStart={() => (isDragging.current = true)}
        onTouchEnd={() => (isDragging.current = false)}
        onTouchMove={handleTouchMove}
      >
        {/* AFTER PANEL (Clean Paved Road) */}
        <div className="image-panel after-panel">
          <svg className="evidence-canvas-svg" viewBox="0 0 900 480" preserveAspectRatio="none">
            {/* Background Road Surface */}
            <rect width="900" height="480" fill="#242c26" />
            
            {/* Sidewalk Curb */}
            <rect x="0" y="0" width="900" height="100" fill="#dedad0" />
            <line x1="0" y1="100" x2="900" y2="100" stroke="#172019" strokeWidth="4" />
            <line x1="0" y1="104" x2="900" y2="104" stroke="#8a9489" strokeWidth="2" />
            
            {/* Sidewalk Tile Lines */}
            <line x1="150" y1="0" x2="150" y2="100" stroke="#c2bcb0" strokeWidth="1.5" />
            <line x1="300" y1="0" x2="300" y2="100" stroke="#c2bcb0" strokeWidth="1.5" />
            <line x1="450" y1="0" x2="450" y2="100" stroke="#c2bcb0" strokeWidth="1.5" />
            <line x1="600" y1="0" x2="600" y2="100" stroke="#c2bcb0" strokeWidth="1.5" />
            <line x1="750" y1="0" x2="750" y2="100" stroke="#c2bcb0" strokeWidth="1.5" />

            {/* School Crosswalk Stripes */}
            <rect x="60" y="20" width="40" height="60" fill="#ffffff" rx="2" />
            <rect x="130" y="20" width="40" height="60" fill="#ffffff" rx="2" />
            <rect x="200" y="20" width="40" height="60" fill="#ffffff" rx="2" />

            {/* Road Lane Markings */}
            <line x1="50" y1="290" x2="190" y2="290" stroke="#e8e4d8" strokeWidth="8" strokeDasharray="30 20" />
            <line x1="270" y1="290" x2="410" y2="290" stroke="#e8e4d8" strokeWidth="8" strokeDasharray="30 20" />
            <line x1="490" y1="290" x2="630" y2="290" stroke="#e8e4d8" strokeWidth="8" strokeDasharray="30 20" />
            <line x1="710" y1="290" x2="850" y2="290" stroke="#e8e4d8" strokeWidth="8" strokeDasharray="30 20" />

            {/* Repaired Trench & Hot-Mix Asphalt Patch */}
            <rect x="240" y="150" width="420" height="220" rx="12" fill="#181e19" stroke="#0f5f4f" strokeWidth="3" strokeDasharray="8 6" />
            <rect x="270" y="210" width="360" height="95" rx="8" fill="#0f1511" />
            
            {/* Status Badges on Canvas */}
            <g transform="translate(280, 175)">
              <rect width="210" height="30" rx="5" fill="#0f5f4f" />
              <text x="105" y="20" fill="#ffffff" fontSize="11" fontWeight="900" letterSpacing="0.08em" textAnchor="middle">
                ASPHALT SEALED & CURED
              </text>
            </g>

            {/* Clamped Pipe Cross-section */}
            <rect x="420" y="235" width="80" height="42" rx="6" fill="#475569" stroke="#94a3b8" strokeWidth="2.5" />
            <text x="460" y="261" fill="#ffffff" fontSize="11" fontWeight="bold" textAnchor="middle">
              COLLAR
            </text>

            <text x="450" y="340" fill="#dce8dd" fontSize="13" fontWeight="bold" textAnchor="middle">
              Water Main Pressure Normal (4.2 Bar) · Zero Surface Leakage
            </text>
          </svg>
          <span className="panel-badge after-badge">
            <FlatIcon name="check" size={14} color="#ffffff" />
            {afterLabel}
          </span>
        </div>

        {/* BEFORE PANEL (Ruptured Pipe & Water Flood) */}
        <div
          className="image-panel before-panel"
          style={{ clipPath: `polygon(0 0, ${sliderPosition}% 0, ${sliderPosition}% 100%, 0 100%)` }}
        >
          <svg className="evidence-canvas-svg" viewBox="0 0 900 480" preserveAspectRatio="none">
            {/* Damaged Road Base */}
            <rect width="900" height="480" fill="#302a24" />
            
            {/* Broken Sidewalk Curb */}
            <rect x="0" y="0" width="900" height="100" fill="#b0a797" />
            <line x1="0" y1="100" x2="900" y2="100" stroke="#172019" strokeWidth="4" />
            
            {/* Submerged / Damaged Lane Lines */}
            <line x1="50" y1="290" x2="190" y2="290" stroke="#786f5e" strokeWidth="8" strokeDasharray="30 20" />
            <line x1="710" y1="290" x2="850" y2="290" stroke="#786f5e" strokeWidth="8" strokeDasharray="30 20" />

            {/* Large Water Flood Surface */}
            <ellipse cx="440" cy="250" rx="270" ry="140" fill="#1e3a5f" opacity="0.92" />
            <ellipse cx="440" cy="250" rx="200" ry="95" fill="#2563eb" opacity="0.65" />
            
            {/* Water Plume Spray */}
            <path d="M 380 260 Q 430 110 450 100 Q 470 110 520 260" stroke="#93c5fd" strokeWidth="22" fill="none" opacity="0.8" />
            <path d="M 400 270 Q 440 130 450 120 Q 460 130 500 270" stroke="#ffffff" strokeWidth="8" fill="none" opacity="0.95" />

            {/* Water Ripple Rings */}
            <ellipse cx="440" cy="250" rx="120" ry="50" fill="none" stroke="#60a5fa" strokeWidth="3" strokeDasharray="10 8" />
            <ellipse cx="440" cy="250" rx="170" ry="75" fill="none" stroke="#93c5fd" strokeWidth="2" strokeDasharray="8 6" />

            {/* Hazard Alert Banner */}
            <g transform="translate(260, 165)">
              <rect width="360" height="38" rx="6" fill="#e84d7a" />
              <text x="180" y="25" fill="#ffffff" fontSize="13" fontWeight="900" letterSpacing="0.06em" textAnchor="middle">
                ACTIVE WATER MAIN BURST (INC-0241)
              </text>
            </g>

            <text x="440" y="360" fill="#fecdd3" fontSize="13" fontWeight="bold" textAnchor="middle">
              High-pressure plume flooded school crosswalk (3 Reports Clustered)
            </text>
          </svg>
          <span className="panel-badge before-badge">
            <FlatIcon name="alert" size={14} color="#ffffff" />
            {beforeLabel}
          </span>
        </div>

        {/* SLIDER DIVIDER */}
        {activeView === "slider" && (
          <div className="slider-divider-line" style={{ left: `${sliderPosition}%` }}>
            <div className="slider-pill-handle">
              <span>⇄</span>
            </div>
          </div>
        )}
      </div>

      {/* EVIDENCE SUMMARY CHECKLIST TILES */}
      <div className="verifier-checklist-grid">
        <div className="evidence-card resolved-card">
          <div className="card-top-row">
            <span className="card-tag resolved-tag">
              <FlatIcon name="check" size={14} color="#0f5f4f" />
              RESOLVED EVIDENCE ({resolvedEvidence.length})
            </span>
            <small className="card-meta">Zero-shot verified</small>
          </div>
          <ul className="evidence-list">
            {resolvedEvidence.map((item, idx) => (
              <li key={idx} className="evidence-item resolved-item">
                <FlatIcon name="check" size={14} color="#0f5f4f" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="evidence-card residual-card">
          <div className="card-top-row">
            <span className="card-tag residual-tag">
              <FlatIcon name="alert" size={14} color="#b45309" />
              RESIDUAL CONDITIONS ({remainingEvidence.length})
            </span>
            <small className="card-meta">Logged for 24h audit</small>
          </div>
          <ul className="evidence-list">
            {remainingEvidence.map((item, idx) => (
              <li key={idx} className="evidence-item residual-item">
                <span className="bullet-dash">▪</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <style jsx>{`
        .resolution-verifier-card {
          border: 2px solid #172019;
          background: #ffffff;
          box-shadow: 6px 6px 0 #172019;
          padding: 28px;
          border-radius: 8px;
        }
        .verifier-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 20px;
          padding-bottom: 18px;
          border-bottom: 1px solid #e2ded4;
          gap: 16px;
        }
        .verifier-kicker-row {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 4px;
        }
        .verifier-kicker {
          font-size: 0.64rem;
          font-weight: 900;
          letter-spacing: 0.12em;
          color: #0f5f4f;
        }
        .confidence-pill {
          font-size: 0.6rem;
          font-weight: 850;
          padding: 2px 6px;
          border: 1px solid #0f5f4f;
          background: #dce8dd;
          color: #0f5f4f;
          border-radius: 3px;
        }
        .verifier-title {
          font-size: 1.5rem;
          font-family: Georgia, serif;
          margin: 0;
          color: #172019;
        }
        .verifier-status-pill {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 6px 14px;
          border: 1px solid #0f5f4f;
          background: #dce8dd;
          color: #0f5f4f;
          border-radius: 4px;
          font-size: 0.74rem;
          font-weight: 850;
          letter-spacing: 0.08em;
          white-space: nowrap;
        }
        .status-indicator-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #0f5f4f;
        }
        .verifier-toggle-bar {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
          gap: 12px;
          flex-wrap: wrap;
        }
        .toggle-group {
          display: flex;
          gap: 6px;
        }
        .toggle-btn {
          padding: 7px 14px;
          border: 1px solid #172019;
          background: #fbf9f4;
          font-size: 0.76rem;
          font-weight: 800;
          border-radius: 4px;
          cursor: pointer;
          color: #495248;
          transition: all 0.15s ease;
        }
        .toggle-btn:hover {
          background: #ffffff;
        }
        .toggle-btn.active {
          background: #172019;
          color: #ffffff;
        }
        .drag-hint {
          font-size: 0.74rem;
          color: #687067;
          font-weight: 700;
        }
        .slider-viewport {
          position: relative;
          width: 100%;
          height: 480px;
          border: 2px solid #172019;
          border-radius: 6px;
          overflow: hidden;
          cursor: ew-resize;
          user-select: none;
          background: #1e241f;
        }
        .image-panel {
          position: absolute;
          inset: 0;
        }
        .evidence-canvas-svg {
          width: 100%;
          height: 100%;
          display: block;
        }
        .panel-badge {
          position: absolute;
          top: 14px;
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 6px 12px;
          font-size: 0.75rem;
          font-weight: 850;
          border-radius: 4px;
          border: 1px solid #172019;
          box-shadow: 2px 2px 0 #172019;
        }
        .before-badge {
          left: 14px;
          background: #e84d7a;
          color: #ffffff;
        }
        .after-badge {
          right: 14px;
          background: #0f5f4f;
          color: #ffffff;
        }
        .slider-divider-line {
          position: absolute;
          top: 0;
          bottom: 0;
          width: 4px;
          background: #ffffff;
          box-shadow: 0 0 14px rgba(0, 0, 0, 0.7);
          transform: translateX(-50%);
          pointer-events: none;
          z-index: 10;
        }
        .slider-pill-handle {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          width: 42px;
          height: 42px;
          border-radius: 50%;
          background: #ffffff;
          border: 2px solid #172019;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
          display: grid;
          place-items: center;
          font-size: 1.1rem;
          font-weight: 900;
          color: #172019;
        }
        .verifier-checklist-grid {
          display: grid;
          grid-template-columns: 1.4fr 1fr;
          gap: 20px;
          margin-top: 24px;
        }
        .evidence-card {
          border: 1px solid #172019;
          background: #ffffff;
          padding: 20px;
          border-radius: 6px;
        }
        .resolved-card {
          background: #f4f8f5;
          border-color: #0f5f4f;
        }
        .residual-card {
          background: #fbf9f4;
          border-color: #d97706;
        }
        .card-top-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
          padding-bottom: 8px;
          border-bottom: 1px solid #e2ded4;
        }
        .card-tag {
          font-size: 0.68rem;
          font-weight: 900;
          letter-spacing: 0.08em;
          display: inline-flex;
          align-items: center;
          gap: 6px;
        }
        .resolved-tag {
          color: #0f5f4f;
        }
        .residual-tag {
          color: #b45309;
        }
        .card-meta {
          font-size: 0.65rem;
          color: #687067;
          font-weight: 700;
        }
        .evidence-list {
          margin: 0;
          padding: 0;
          list-style: none;
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .evidence-item {
          display: flex;
          align-items: flex-start;
          gap: 8px;
          font-size: 0.82rem;
          line-height: 1.45;
        }
        .resolved-item span {
          color: #172019;
        }
        .residual-item span {
          color: #78350f;
        }
        .bullet-dash {
          color: #b45309;
          font-weight: 900;
        }
        @media (max-width: 860px) {
          .slider-viewport {
            height: 380px;
          }
          .verifier-checklist-grid {
            grid-template-columns: 1fr;
          }
        }
        @media (max-width: 540px) {
          .slider-viewport {
            height: 320px;
          }
        }
      `}</style>
    </div>
  );
}
