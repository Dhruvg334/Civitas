"use client";

import { useState } from "react";

export function CitySignal() {
  return (
    <div className="city-signal" aria-label="Three reports converging into one civic incident and municipal action">
      <div className="city-grid" aria-hidden="true" />
      <div className="map-label label-school">SCHOOL</div>
      <div className="map-label label-road">WARD 12 · CROSSING</div>
      <svg viewBox="0 0 620 440" role="img" aria-label="Civic report flow map">
        <path className="street" d="M20 110 C150 75 190 150 320 118 S500 58 610 85" />
        <path className="street thin" d="M90 430 C135 300 180 235 310 210 S480 260 575 170" />
        <path className="street thin" d="M30 292 C165 285 250 350 400 338 S530 295 610 315" />
        <path className="signal-line line-a" d="M115 130 C210 155 260 200 328 232" />
        <path className="signal-line line-b" d="M160 328 C235 292 275 260 328 232" />
        <path className="signal-line line-c" d="M505 114 C420 152 376 192 328 232" />
        <path className="action-line" d="M348 235 C420 235 468 250 525 305" />
        <circle className="report-node n1" cx="115" cy="130" r="11" />
        <circle className="report-node n2" cx="160" cy="328" r="11" />
        <circle className="report-node n3" cx="505" cy="114" r="11" />
        <circle className="incident-ring" cx="328" cy="232" r="36" />
        <circle className="incident-node" cx="328" cy="232" r="16" />
        <rect className="action-node" x="507" y="287" width="42" height="42" rx="3" />
      </svg>
      <div className="signal-caption report-caption"><b>03 reports</b><span>same place, different evidence</span></div>
      <div className="signal-caption incident-caption"><b>01 incident</b><span>clustered + prioritized</span></div>
      <div className="signal-caption action-caption"><b>Action</b><span>routed for human review</span></div>
    </div>
  );
}

export function MiniMap() {
  const [activePin, setActivePin] = useState<string>("INC-0241");

  return (
    <div className="mini-map-container" aria-label="Ward 12 GIS Incident Map">
      <div className="mini-map">
        <iframe
          title="Ward 12 GIS Incident Map"
          loading="lazy"
          src="https://www.openstreetmap.org/export/embed.html?bbox=85.815%2C20.288%2C85.835%2C20.304&amp;layer=mapnik&amp;marker=20.2961%2C85.8245"
        />

        <div className="map-place school">CIVITAS SCHOOL</div>
        <div className="map-place ward">WARD 12 ZONE</div>

        {/* INCIDENT PINS */}
        <button
          onClick={() => setActivePin("INC-0241")}
          className={`map-pin main-pin ${activePin === "INC-0241" ? "selected" : ""}`}
          style={{ left: "50%", top: "45%" }}
          aria-label="INC-0241 Water Leak"
        >
          <span>3</span>
          <span className="pin-tooltip">INC-0241: Water Leakage (3 reports)</span>
        </button>

        <button
          onClick={() => setActivePin("INC-0240")}
          className={`map-pin secondary-pin ${activePin === "INC-0240" ? "selected" : ""}`}
          style={{ left: "28%", top: "62%" }}
          aria-label="INC-0240 Fallen Tree"
        >
          <span>2</span>
          <span className="pin-tooltip">INC-0240: Fallen Tree (2 reports)</span>
        </button>

        <button
          onClick={() => setActivePin("INC-0238")}
          className={`map-pin tertiary-pin ${activePin === "INC-0238" ? "selected" : ""}`}
          style={{ left: "72%", top: "32%" }}
          aria-label="INC-0238 Streetlight"
        >
          <span>1</span>
          <span className="pin-tooltip">INC-0238: Streetlight Outage</span>
        </button>

        {/* MAP LEGEND */}
        <div className="map-legend-bar">
          <div className="legend-item">
            <span className="dot selected-dot" />
            <span>Selected Incident (P1)</span>
          </div>
          <div className="legend-item">
            <span className="dot secondary-dot" />
            <span>Assigned (P2)</span>
          </div>
          <div className="legend-item">
            <span className="dot tertiary-dot" />
            <span>Clarification (P3)</span>
          </div>
        </div>
      </div>

      <style jsx>{`
        .mini-map-container {
          width: 100%;
          height: 100%;
          min-height: 420px;
          position: relative;
        }
        .mini-map {
          height: 100%;
          min-height: 420px;
          position: relative;
          background: #e5e3df;
          overflow: hidden;
        }
        .mini-map iframe {
          position: absolute;
          inset: 0;
          width: 100%;
          height: 100%;
          border: 0;
          filter: contrast(1.05) saturate(0.95);
        }
        .map-place {
          position: absolute;
          padding: 4px 8px;
          background: #172019;
          color: #fffdf7;
          font-size: 0.6rem;
          font-weight: 800;
          letter-spacing: 0.08em;
          border-radius: 4px;
          box-shadow: 2px 2px 0 rgba(0, 0, 0, 0.2);
          z-index: 10;
        }
        .map-place.school {
          right: 18%;
          top: 15%;
        }
        .map-place.ward {
          left: 10%;
          bottom: 15%;
        }
        .map-pin {
          position: absolute;
          width: 32px;
          height: 32px;
          border-radius: 50%;
          border: 2px solid #172019;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 800;
          font-size: 0.75rem;
          cursor: pointer;
          transform: translate(-50%, -50%);
          z-index: 12;
          transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .map-pin:hover {
          transform: translate(-50%, -50%) scale(1.15);
        }
        .map-pin.selected {
          transform: translate(-50%, -50%) scale(1.25);
          box-shadow: 0 0 14px rgba(232, 77, 122, 0.8);
          z-index: 15;
        }
        .main-pin {
          background: #e84d7a;
          color: #ffffff;
        }
        .secondary-pin {
          background: #0f5f4f;
          color: #ffffff;
        }
        .tertiary-pin {
          background: #e3b950;
          color: #172019;
        }
        .pin-tooltip {
          position: absolute;
          bottom: 125%;
          left: 50%;
          transform: translateX(-50%);
          background: #172019;
          color: #fffdf7;
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 0.65rem;
          white-space: nowrap;
          opacity: 0;
          pointer-events: none;
          transition: opacity 0.2s ease;
        }
        .map-pin:hover .pin-tooltip {
          opacity: 1;
        }
        .map-legend-bar {
          position: absolute;
          right: 12px;
          bottom: 12px;
          background: rgba(255, 253, 247, 0.95);
          border: 1px solid #172019;
          padding: 8px 12px;
          border-radius: 6px;
          display: flex;
          flex-direction: column;
          gap: 4px;
          font-size: 0.65rem;
          font-weight: 700;
          box-shadow: 3px 3px 0 #172019;
          z-index: 10;
        }
        .legend-item {
          display: flex;
          align-items: center;
          gap: 6px;
          color: #172019;
        }
        .dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }
        .selected-dot {
          background: #e84d7a;
        }
        .secondary-dot {
          background: #0f5f4f;
        }
        .tertiary-dot {
          background: #e3b950;
        }
      `}</style>
    </div>
  );
}
