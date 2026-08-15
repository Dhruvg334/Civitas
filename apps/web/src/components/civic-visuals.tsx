"use client";

import dynamic from "next/dynamic";

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

const DynamicGisMap = dynamic(
  () => import("@/components/interactive-gis-map").then((mod) => mod.InteractiveGisMap),
  {
    ssr: false,
    loading: () => (
      <div className="gis-loading-placeholder">
        <div className="loading-spinner" />
        <span>Initializing PostGIS Layer & Leaflet Engine...</span>
      </div>
    ),
  }
);

export function MiniMap({
  selectedIncidentId = "INC-0241",
  onSelectIncident,
  height = "520px",
}: {
  selectedIncidentId?: string;
  onSelectIncident?: (id: string) => void;
  height?: string;
}) {
  return (
    <div className="mini-map-container" aria-label="Ward 12 Interactive GIS Incident Map">
      <DynamicGisMap
        selectedIncidentId={selectedIncidentId}
        onSelectIncident={onSelectIncident}
        height={height}
      />
      <style jsx>{`
        .mini-map-container {
          width: 100%;
          height: 100%;
          min-height: 480px;
          position: relative;
        }
        .gis-loading-placeholder {
          width: 100%;
          height: 480px;
          background: #fbf9f4;
          border: 1px solid #172019;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 12px;
          color: #555e54;
          font-size: 0.8rem;
          font-weight: 700;
        }
        .loading-spinner {
          width: 32px;
          height: 32px;
          border: 3px solid #e2ded4;
          border-top-color: #0f5f4f;
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
