"use client";

import { useState, useRef, ReactNode } from "react";

interface Props {
  beforeLabel?: string;
  afterLabel?: string;
  classification?: string;
  remainingEvidence?: string[];
  resolvedEvidence?: string[];
}

export function ResolutionSlider({
  beforeLabel = "INITIAL REPORT EVIDENCE",
  afterLabel = "FIELD RESOLUTION EVIDENCE",
  classification = "partially_resolved",
  remainingEvidence = ["Visible standing water remains near footpath"],
  resolvedEvidence = ["Active pipe water flow is no longer visible"],
}: Props) {
  const [sliderPosition, setSliderPosition] = useState(50);
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
    <div className="resolution-card">
      <div className="resolution-header">
        <div>
          <span className="kicker">BEFORE / AFTER VERIFICATION</span>
          <h3>Resolution Evidence Classifier</h3>
        </div>
        <span className={`badge ${classification}`}>
          {classification.replace("_", " ").toUpperCase()}
        </span>
      </div>

      <div
        ref={containerRef}
        className="slider-container"
        onMouseDown={() => (isDragging.current = true)}
        onMouseUp={() => (isDragging.current = false)}
        onMouseLeave={() => (isDragging.current = false)}
        onMouseMove={handleMouseMove}
        onTouchStart={() => (isDragging.current = true)}
        onTouchEnd={() => (isDragging.current = false)}
        onTouchMove={handleTouchMove}
      >
        {/* AFTER IMAGE (Background) */}
        <div className="image-panel after-panel">
          <svg className="mock-evidence-svg" viewBox="0 0 800 400" preserveAspectRatio="none">
            <defs>
              <linearGradient id="afterGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#0f172a" />
                <stop offset="50%" stopColor="#1e293b" />
                <stop offset="100%" stopColor="#0f766e" />
              </linearGradient>
            </defs>
            <rect width="800" height="400" fill="url(#afterGrad)" />
            {/* Road lines */}
            <path d="M 0 260 Q 400 240 800 260" stroke="#475569" strokeWidth="6" fill="none" />
            <path d="M 0 320 Q 400 300 800 320" stroke="#334155" strokeWidth="4" fill="none" />
            {/* Repaired road patch */}
            <rect x="250" y="180" width="300" height="100" rx="8" fill="#1e293b" stroke="#0d9488" strokeWidth="2" strokeDasharray="6 4" />
            <text x="400" y="235" textAnchor="middle" fill="#2dd4bf" fontSize="16" fontWeight="bold">REPAIRED ROAD SURFACE</text>
            {/* Small standing puddle */}
            <ellipse cx="280" cy="250" rx="40" ry="12" fill="rgba(56, 189, 248, 0.4)" stroke="#38bdf8" strokeWidth="1.5" />
            <text x="280" y="278" textAnchor="middle" fill="#93c5fd" fontSize="12">Standing water remaining</text>
          </svg>
          <span className="panel-label after-label">{afterLabel}</span>
        </div>

        {/* BEFORE IMAGE (Clipped Foreground) */}
        <div
          className="image-panel before-panel"
          style={{ clipPath: `polygon(0 0, ${sliderPosition}% 0, ${sliderPosition}% 100%, 0 100%)` }}
        >
          <svg className="mock-evidence-svg" viewBox="0 0 800 400" preserveAspectRatio="none">
            <defs>
              <linearGradient id="beforeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#1e1b4b" />
                <stop offset="50%" stopColor="#311b92" />
                <stop offset="100%" stopColor="#450a0a" />
              </linearGradient>
            </defs>
            <rect width="800" height="400" fill="url(#beforeGrad)" />
            {/* Active water leakage flow */}
            <path d="M 150 120 Q 300 220 500 200 T 800 300" stroke="#38bdf8" strokeWidth="24" fill="none" opacity="0.8" />
            <path d="M 180 140 Q 320 240 520 210 T 800 310" stroke="#e0f2fe" strokeWidth="8" fill="none" opacity="0.9" />
            <text x="400" y="160" textAnchor="middle" fill="#f87171" fontSize="18" fontWeight="bold">ACTIVE LEAKAGE & FLUID DISCHARGE</text>
            {/* Hazard alert symbol */}
            <circle cx="400" cy="220" r="28" fill="#ef4444" opacity="0.9" />
            <text x="400" y="227" textAnchor="middle" fill="#ffffff" fontSize="22" fontWeight="bold">!</text>
          </svg>
          <span className="panel-label before-label">{beforeLabel}</span>
        </div>

        {/* SLIDER DIVIDER LINE & HANDLE */}
        <div className="slider-divider" style={{ left: `${sliderPosition}%` }}>
          <div className="slider-handle">
            <span>⇄</span>
          </div>
        </div>
      </div>

      <div className="verification-details">
        <div className="evidence-column resolved">
          <h4>Resolved Evidence</h4>
          <ul>
            {resolvedEvidence.map((item, idx) => (
              <li key={idx}>✓ {item}</li>
            ))}
          </ul>
        </div>
        <div className="evidence-column remaining">
          <h4>Remaining Evidence / Follow-up Needed</h4>
          <ul>
            {remainingEvidence.map((item, idx) => (
              <li key={idx}>⚠️ {item}</li>
            ))}
          </ul>
        </div>
      </div>

      <style jsx>{`
        .resolution-card {
          background: rgba(15, 23, 42, 0.85);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 14px;
          padding: 1.25rem;
          margin: 1.5rem 0;
          backdrop-filter: blur(12px);
        }
        .resolution-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1rem;
        }
        .kicker {
          font-size: 0.75rem;
          font-weight: 700;
          letter-spacing: 0.08em;
          color: #2dd4bf;
          display: block;
          margin-bottom: 0.25rem;
        }
        .resolution-header h3 {
          margin: 0;
          font-size: 1.125rem;
          color: #f8fafc;
          font-family: "Outfit", sans-serif;
        }
        .badge {
          padding: 0.35rem 0.75rem;
          border-radius: 20px;
          font-size: 0.75rem;
          font-weight: 700;
          letter-spacing: 0.05em;
        }
        .badge.partially_resolved {
          background: rgba(245, 158, 11, 0.2);
          color: #fbbf24;
          border: 1px solid rgba(245, 158, 11, 0.4);
        }
        .badge.resolved {
          background: rgba(16, 185, 129, 0.2);
          color: #34d399;
          border: 1px solid rgba(16, 185, 129, 0.4);
        }
        .slider-container {
          position: relative;
          width: 100%;
          height: 260px;
          border-radius: 10px;
          overflow: hidden;
          cursor: ew-resize;
          user-select: none;
          border: 1px solid rgba(255, 255, 255, 0.15);
        }
        .image-panel {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
        }
        .mock-evidence-svg {
          width: 100%;
          height: 100%;
          display: block;
        }
        .panel-label {
          position: absolute;
          top: 12px;
          padding: 4px 10px;
          border-radius: 4px;
          font-size: 0.7rem;
          font-weight: 700;
          letter-spacing: 0.05em;
        }
        .before-label {
          left: 12px;
          background: rgba(220, 38, 38, 0.85);
          color: #ffffff;
        }
        .after-label {
          right: 12px;
          background: rgba(13, 148, 136, 0.85);
          color: #ffffff;
        }
        .slider-divider {
          position: absolute;
          top: 0;
          bottom: 0;
          width: 2px;
          background: #ffffff;
          box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
          transform: translateX(-50%);
          pointer-events: none;
        }
        .slider-handle {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          width: 36px;
          height: 36px;
          border-radius: 50%;
          background: #ffffff;
          color: #0f172a;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: bold;
          font-size: 14px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
        }
        .verification-details {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 1rem;
          margin-top: 1rem;
        }
        .evidence-column {
          background: rgba(255, 255, 255, 0.03);
          padding: 0.875rem;
          border-radius: 8px;
        }
        .evidence-column h4 {
          margin: 0 0 0.5rem;
          font-size: 0.8125rem;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }
        .resolved h4 {
          color: #34d399;
        }
        .remaining h4 {
          color: #fbbf24;
        }
        .evidence-column ul {
          margin: 0;
          padding: 0;
          list-style: none;
        }
        .evidence-column li {
          font-size: 0.8125rem;
          color: #cbd5e1;
          margin-bottom: 0.25rem;
        }
        @media (max-width: 640px) {
          .verification-details {
            grid-template-columns: 1fr;
          }
          .slider-container {
            height: 200px;
          }
        }
      `}</style>
    </div>
  );
}
