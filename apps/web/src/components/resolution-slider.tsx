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
            <span className="confidence-pill">CLIP CV CONFIDENCE: 98.4%</span>
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
            className={`toggle-btn ${activeView === "slider" ? "active" : ""}`}
            onClick={() => {
              setActiveView("slider");
              setSliderPosition(50);
            }}
          >
            ⇄ Interactive Split Slider
          </button>
          <button
            className={`toggle-btn ${activeView === "before" ? "active" : ""}`}
            onClick={() => {
              setActiveView("before");
              setSliderPosition(100);
            }}
          >
            1. View Incident Photo
          </button>
          <button
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
          {activeView === "slider" ? "Drag divider left/right to compare" : "Full frame preview"}
        </span>
      </div>

      {/* COMPARATIVE VISUAL CANVAS */}
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
        {/* AFTER PANEL (Background - Clean Paved Road) */}
        <div className="image-panel after-panel">
          <svg className="evidence-canvas-svg" viewBox="0 0 900 420" preserveAspectRatio="none">
            {/* Background Road Surface */}
            <rect width="900" height="420" fill="#2c332d" />
            <rect x="0" y="0" width="900" height="90" fill="#dedad0" />
            {/* Sidewalk Curb */}
            <line x1="0" y1="90" x2="900" y2="90" stroke="#172019" strokeWidth="4" />
            <line x1="0" y1="94" x2="900" y2="94" stroke="#8a9489" strokeWidth="2" />
            
            {/* Road Lane Markings */}
            <line x1="50" y1="250" x2="180" y2="250" stroke="#e8e4d8" strokeWidth="6" strokeDasharray="20 15" />
            <line x1="260" y1="250" x2="390" y2="250" stroke="#e8e4d8" strokeWidth="6" strokeDasharray="20 15" />
            <line x1="470" y1="250" x2="600" y2="250" stroke="#e8e4d8" strokeWidth="6" strokeDasharray="20 15" />
            <line x1="680" y1="250" x2="810" y2="250" stroke="#e8e4d8" strokeWidth="6" strokeDasharray="20 15" />

            {/* Fresh Asphalt Patch & Clamped Pipeline Area */}
            <rect x="260" y="140" width="380" height="170" rx="10" fill="#1e241f" stroke="#0f5f4f" strokeWidth="3" strokeDasharray="6 4" />
            <rect x="290" y="195" width="320" height="60" rx="6" fill="#121813" />
            
            {/* Subsurface Repair Badge */}
            <g transform="translate(300, 160)">
              <rect width="190" height="26" rx="4" fill="#0f5f4f" />
              <text x="95" y="17" fill="#ffffff" fontSize="11" fontWeight="bold" textAnchor="middle">
                ASPHALT SEALED & CURED
              </text>
            </g>

            {/* Verified Pipe Collar */}
            <rect x="420" y="210" width="60" height="30" rx="4" fill="#64748b" stroke="#94a3b8" strokeWidth="2" />
            <text x="450" y="230" fill="#ffffff" fontSize="10" fontWeight="bold" textAnchor="middle">
              CLAMP
            </text>

            <text x="450" y="280" fill="#dce8dd" fontSize="12" fontWeight="bold" textAnchor="middle">
              ✓ Water Main Pressure Normal (4.2 Bar) · No Active Leakage
            </text>
          </svg>
          <span className="panel-badge after-badge">
            <FlatIcon name="check" size={12} color="#ffffff" />
            {afterLabel}
          </span>
        </div>

        {/* BEFORE PANEL (Foreground - Ruptured pipe & water puddle) */}
        <div
          className="image-panel before-panel"
          style={{ clipPath: `polygon(0 0, ${sliderPosition}% 0, ${sliderPosition}% 100%, 0 100%)` }}
        >
          <svg className="evidence-canvas-svg" viewBox="0 0 900 420" preserveAspectRatio="none">
            {/* Background Damaged Road */}
            <rect width="900" height="420" fill="#38332c" />
            <rect x="0" y="0" width="900" height="90" fill="#b8b0a0" />
            <line x1="0" y1="90" x2="900" y2="90" stroke="#172019" strokeWidth="4" />

            {/* Road Markings Damaged */}
            <line x1="50" y1="250" x2="180" y2="250" stroke="#8c8270" strokeWidth="6" strokeDasharray="20 15" />
            <line x1="680" y1="250" x2="810" y2="250" stroke="#8c8270" strokeWidth="6" strokeDasharray="20 15" />

            {/* Large Water Puddle & Cavity */}
            <ellipse cx="440" cy="220" rx="220" ry="110" fill="#1e3a5f" opacity="0.9" />
            <ellipse cx="440" cy="220" rx="170" ry="80" fill="#2563eb" opacity="0.6" />
            
            {/* Burst Spray Graphic */}
            <path d="M 380 230 Q 420 120 450 110 Q 480 120 520 230" stroke="#93c5fd" strokeWidth="16" fill="none" opacity="0.85" />
            <path d="M 400 240 Q 440 140 450 130 Q 460 140 500 240" stroke="#ffffff" strokeWidth="6" fill="none" opacity="0.95" />

            {/* Hazard Alert Banner */}
            <g transform="translate(290, 150)">
              <rect width="320" height="34" rx="4" fill="#e84d7a" />
              <text x="160" y="22" fill="#ffffff" fontSize="13" fontWeight="bold" textAnchor="middle">
                ⚠️ ACTIVE WATER MAIN BURST (INC-0241)
              </text>
            </g>

            <text x="450" y="310" fill="#fecdd3" fontSize="12" fontWeight="bold" textAnchor="middle">
              High-pressure flow flooded school crosswalk (3 Reports Clustered)
            </text>
          </svg>
          <span className="panel-badge before-badge">
            <FlatIcon name="alert" size={12} color="#ffffff" />
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
          padding: 24px;
          border-radius: 8px;
        }
        .verifier-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 18px;
          padding-bottom: 16px;
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
          font-size: 1.35rem;
          font-family: Georgia, serif;
          margin: 0;
          color: #172019;
        }
        .verifier-status-pill {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 6px 12px;
          border: 1px solid #0f5f4f;
          background: #dce8dd;
          color: #0f5f4f;
          border-radius: 4px;
          font-size: 0.72rem;
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
          margin-bottom: 12px;
          gap: 12px;
          flex-wrap: wrap;
        }
        .toggle-group {
          display: flex;
          gap: 6px;
        }
        .toggle-btn {
          padding: 6px 12px;
          border: 1px solid #172019;
          background: #fbf9f4;
          font-size: 0.74rem;
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
          font-size: 0.72rem;
          color: #687067;
          font-weight: 700;
        }
        .slider-viewport {
          position: relative;
          width: 100%;
          height: 320px;
          border: 1px solid #172019;
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
          top: 12px;
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 5px 10px;
          font-size: 0.72rem;
          font-weight: 850;
          border-radius: 4px;
          border: 1px solid #172019;
          box-shadow: 2px 2px 0 #172019;
        }
        .before-badge {
          left: 12px;
          background: #e84d7a;
          color: #ffffff;
        }
        .after-badge {
          right: 12px;
          background: #0f5f4f;
          color: #ffffff;
        }
        .slider-divider-line {
          position: absolute;
          top: 0;
          bottom: 0;
          width: 3px;
          background: #ffffff;
          box-shadow: 0 0 12px rgba(0, 0, 0, 0.6);
          transform: translateX(-50%);
          pointer-events: none;
          z-index: 10;
        }
        .slider-pill-handle {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          width: 38px;
          height: 38px;
          border-radius: 50%;
          background: #ffffff;
          border: 2px solid #172019;
          box-shadow: 0 4px 10px rgba(0, 0, 0, 0.35);
          display: grid;
          place-items: center;
          font-size: 1rem;
          font-weight: 900;
          color: #172019;
        }
        .verifier-checklist-grid {
          display: grid;
          grid-template-columns: 1.2fr 1fr;
          gap: 16px;
          margin-top: 18px;
        }
        .evidence-card {
          border: 1px solid #172019;
          padding: 16px;
          border-radius: 6px;
          background: #fbf9f4;
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
          display: inline-flex;
          align-items: center;
          gap: 6px;
          font-size: 0.68rem;
          font-weight: 900;
          letter-spacing: 0.08em;
        }
        .resolved-tag {
          color: #0f5f4f;
        }
        .residual-tag {
          color: #b45309;
        }
        .card-meta {
          font-size: 0.68rem;
          color: #687067;
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
          font-size: 0.8rem;
          line-height: 1.45;
          color: #172019;
        }
        .bullet-dash {
          color: #b45309;
          font-size: 0.9rem;
        }
        @media (max-width: 800px) {
          .verifier-checklist-grid {
            grid-template-columns: 1fr;
          }
          .slider-viewport {
            height: 250px;
          }
        }
      `}</style>
    </div>
  );
}
