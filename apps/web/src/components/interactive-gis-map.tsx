"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import Link from "next/link";
import type L from "leaflet";

export interface GisIncidentPin {
  id: string;
  title: string;
  category: string;
  priority: "P1" | "P2" | "P3";
  status: string;
  lat: number;
  lng: number;
  reportCount: number;
  landmarkProximity: string;
  department: string;
}

export const DEMO_INCIDENT_PINS: GisIncidentPin[] = [
  {
    id: "INC-0241",
    title: "School Crossing Water Main Leakage",
    category: "water_leakage",
    priority: "P1",
    status: "WAITING_FOR_REVIEW",
    lat: 20.29614,
    lng: 85.82451,
    reportCount: 3,
    landmarkProximity: "14m from DAV Public School Gate",
    department: "Water Supply & Drainage",
  },
  {
    id: "INC-0240",
    title: "Fallen Banyan Tree Branch Blocking Road",
    category: "fallen_tree",
    priority: "P2",
    status: "ASSIGNED",
    lat: 20.2918,
    lng: 85.8205,
    reportCount: 2,
    landmarkProximity: "Near Ward 12 Park Entrance",
    department: "Parks & Urban Forestry",
  },
  {
    id: "INC-0238",
    title: "Streetlight Cluster Power Failure",
    category: "streetlight",
    priority: "P3",
    status: "WAITING_FOR_CLARIFICATION",
    lat: 20.3012,
    lng: 85.8315,
    reportCount: 1,
    landmarkProximity: "East Gate Commercial Crossroad",
    department: "Electrical & Public Lighting",
  },
  {
    id: "INC-0235",
    title: "Severe Asphalt Pothole on Bus Route",
    category: "pothole",
    priority: "P1",
    status: "RESOLVED",
    lat: 20.2885,
    lng: 85.8268,
    reportCount: 4,
    landmarkProximity: "Near City Hospital Flyover",
    department: "Road Maintenance & Works",
  },
];

interface InteractiveGisMapProps {
  selectedIncidentId?: string;
  onSelectIncident?: (id: string) => void;
  height?: string;
  showControls?: boolean;
  interactive?: boolean;
}

export function InteractiveGisMap({
  selectedIncidentId = "INC-0241",
  onSelectIncident,
  height = "520px",
  showControls = true,
  interactive = true,
}: InteractiveGisMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const circleRef = useRef<L.Circle | null>(null);
  const leafletModuleRef = useRef<typeof L | null>(null);

  const [userSelectedPinId, setUserSelectedPinId] = useState<string | null>(null);
  const [isPopupClosed, setIsPopupClosed] = useState<boolean>(false);
  const [mapLayer, setMapLayer] = useState<"positron" | "osm" | "dark">("positron");
  const [showBuffer, setShowBuffer] = useState<boolean>(true);
  const bufferRadius = 500; // 500m school buffer
  const [dispatchMessage, setDispatchMessage] = useState<string>("");

  const activePinId = userSelectedPinId || selectedIncidentId;
  const activePopupPin =
    DEMO_INCIDENT_PINS.find((p) => p.id === activePinId) || DEMO_INCIDENT_PINS[0];

  const handleSelectPin = useCallback(
    (pin: GisIncidentPin) => {
      setUserSelectedPinId(pin.id);
      setIsPopupClosed(false);
      if (onSelectIncident) {
        onSelectIncident(pin.id);
      }
      if (mapInstanceRef.current) {
        mapInstanceRef.current.flyTo([pin.lat, pin.lng], 16, { duration: 0.8 });
      }
    },
    [onSelectIncident]
  );

  // Pan to incident when selected from external prop
  useEffect(() => {
    if (selectedIncidentId && mapInstanceRef.current) {
      const pin = DEMO_INCIDENT_PINS.find((p) => p.id === selectedIncidentId);
      if (pin) {
        mapInstanceRef.current.flyTo([pin.lat, pin.lng], 16, { duration: 1.0 });
      }
    }
  }, [selectedIncidentId]);

  useEffect(() => {
    let isMounted = true;

    async function initMap() {
      if (!mapContainerRef.current || mapInstanceRef.current) return;

      const LModule = (await import("leaflet")).default;
      if (!isMounted || !mapContainerRef.current) return;
      leafletModuleRef.current = LModule;

      // Import Leaflet CSS dynamically if not present
      if (!document.getElementById("leaflet-css")) {
        const link = document.createElement("link");
        link.id = "leaflet-css";
        link.rel = "stylesheet";
        link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
        document.head.appendChild(link);
      }

      // Initialize map centered on Ward 12, Bhubaneswar
      const map = LModule.map(mapContainerRef.current, {
        center: [20.29614, 85.82451],
        zoom: 15,
        zoomControl: false,
        attributionControl: false,
      });

      mapInstanceRef.current = map;

      // Initial CartoDB Voyager Tile Layer
      LModule.tileLayer(
        "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
        { maxZoom: 19, subdomains: "abcd" }
      ).addTo(map);

      // School Proximity Hazard Buffer Circle (500m)
      if (showBuffer) {
        const circle = LModule.circle([20.29614, 85.82451], {
          color: "#e84d7a",
          fillColor: "#e84d7a",
          fillOpacity: 0.12,
          weight: 1.5,
          dashArray: "6, 8",
          radius: bufferRadius,
        }).addTo(map);
        circleRef.current = circle;
      }

      // Landmark Markers (DAV Public School, Ward East Gate)
      const schoolIcon = LModule.divIcon({
        className: "landmark-poi-icon",
        html: `<div class="landmark-badge school-poi"><span class="poi-label">DAV Public School</span></div>`,
        iconSize: [140, 30],
        iconAnchor: [70, 15],
      });
      LModule.marker([20.2968, 85.8239], { icon: schoolIcon }).addTo(map);

      const eastGateIcon = LModule.divIcon({
        className: "landmark-poi-icon",
        html: `<div class="landmark-badge junction-poi"><span class="poi-label">East Gate Crossing</span></div>`,
        iconSize: [130, 30],
        iconAnchor: [65, 15],
      });
      LModule.marker([20.3015, 85.8312], { icon: eastGateIcon }).addTo(map);

      // Incident Markers
      DEMO_INCIDENT_PINS.forEach((pin) => {
        const isSelected = pin.id === activePinId;
        const colorClass =
          pin.priority === "P1" ? "p1-pin" : pin.priority === "P2" ? "p2-pin" : "p3-pin";

        const pinIcon = LModule.divIcon({
          className: "custom-incident-icon",
          html: `
            <div class="incident-marker-wrapper ${colorClass} ${isSelected ? "selected-marker" : ""}">
              ${pin.priority === "P1" ? '<div class="pulse-ring"></div>' : ""}
              <div class="marker-core">
                <span class="marker-cluster-count">${pin.reportCount}</span>
              </div>
              <div class="marker-mini-badge">${pin.id}</div>
            </div>
          `,
          iconSize: [40, 40],
          iconAnchor: [20, 20],
        });

        const marker = LModule.marker([pin.lat, pin.lng], { icon: pinIcon }).addTo(map);

        marker.on("click", () => {
          handleSelectPin(pin);
        });
      });

      setTimeout(() => {
        if (mapInstanceRef.current) mapInstanceRef.current.invalidateSize();
      }, 150);
      setTimeout(() => {
        if (mapInstanceRef.current) mapInstanceRef.current.invalidateSize();
      }, 450);
    }

    initMap();

    return () => {
      isMounted = false;
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [activePinId, bufferRadius, handleSelectPin, showBuffer]);

  // Synchronize map center when selectedIncidentId prop changes from parent
  useEffect(() => {
    if (!mapInstanceRef.current || !selectedIncidentId) return;
    const pin = DEMO_INCIDENT_PINS.find((p) => p.id === selectedIncidentId);
    if (pin) {
      mapInstanceRef.current.flyTo([pin.lat, pin.lng], 16, { duration: 0.8 });
    }
  }, [selectedIncidentId]);

  const handleLayerSwitch = (layer: "positron" | "osm" | "dark") => {
    setMapLayer(layer);
    const map = mapInstanceRef.current;
    const LModule = leafletModuleRef.current;
    if (!map || !LModule) return;

    map.eachLayer((l) => {
      if (l instanceof LModule.TileLayer) {
        map.removeLayer(l);
      }
    });

    const urls = {
      positron: "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
      osm: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
      dark: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    };

    LModule.tileLayer(urls[layer], { maxZoom: 19, subdomains: layer === "osm" ? "" : "abcd" }).addTo(map);

    setTimeout(() => {
      if (mapInstanceRef.current) mapInstanceRef.current.invalidateSize();
    }, 150);
  };

  const handleZoom = (delta: number) => {
    if (mapInstanceRef.current) {
      mapInstanceRef.current.setZoom(mapInstanceRef.current.getZoom() + delta);
    }
  };

  const handleJumpToLandmark = (lat: number, lng: number, zoom = 16) => {
    if (mapInstanceRef.current) {
      mapInstanceRef.current.flyTo([lat, lng], zoom, { duration: 1.0 });
    }
  };

  const handleDispatch = (pinId: string) => {
    setDispatchMessage(`✓ Field crew dispatched for ${pinId} to Water Supply & Drainage Dept.`);
    setTimeout(() => setDispatchMessage(""), 5000);
  };

  return (
    <div className="gis-map-root" style={{ height }}>
      {/* MAP CANVAS CONTAINER */}
      <div ref={mapContainerRef} className="leaflet-map-canvas" />

      {/* TOP FLOATING GIS CONTROL PANEL */}
      {showControls && (
        <div className="gis-top-bar">
          <div className="gis-status-badge">
            <span className="live-pulse" />
            <b>LIVE POSTGIS · WARD 12</b>
          </div>

          <div className="layer-switcher-buttons">
            <button
              className={`layer-btn ${mapLayer === "positron" ? "active" : ""}`}
              onClick={() => handleLayerSwitch("positron")}
            >
              Clean (Voyager)
            </button>
            <button
              className={`layer-btn ${mapLayer === "osm" ? "active" : ""}`}
              onClick={() => handleLayerSwitch("osm")}
            >
              Street (OSM)
            </button>
            <button
              className={`layer-btn ${mapLayer === "dark" ? "active" : ""}`}
              onClick={() => handleLayerSwitch("dark")}
            >
              Night (Dark)
            </button>
          </div>
        </div>
      )}

      {/* ZOOM & QUICK FOCUS CONTROLS */}
      {showControls && (
        <div className="gis-floating-tools">
          <div className="zoom-btn-group">
            <button className="tool-btn" onClick={() => handleZoom(1)} title="Zoom In">
              +
            </button>
            <button className="tool-btn" onClick={() => handleZoom(-1)} title="Zoom Out">
              −
            </button>
          </div>

          <div className="landmark-jumps">
            <button
              className="jump-pill"
              onClick={() => handleJumpToLandmark(20.29614, 85.82451, 16)}
              title="Focus DAV School Crossing"
            >
              School Zone
            </button>
            <button
              className="jump-pill"
              onClick={() => handleJumpToLandmark(20.3015, 85.8312, 16)}
              title="Focus East Gate Junction"
            >
              East Gate
            </button>
            <button
              className="jump-pill"
              onClick={() => handleJumpToLandmark(20.2918, 85.8205, 16)}
              title="Focus Park Road"
            >
              Park Road
            </button>
          </div>

          <div className="buffer-toggle-pill">
            <label>
              <input
                type="checkbox"
                checked={showBuffer}
                onChange={(e) => {
                  setShowBuffer(e.target.checked);
                  if (circleRef.current) {
                    if (e.target.checked) circleRef.current.setRadius(bufferRadius);
                    else circleRef.current.setRadius(0);
                  }
                }}
              />
              <span>500m School Buffer</span>
            </label>
          </div>
        </div>
      )}

      {/* ACTIVE INCIDENT POPUP CARD */}
      {activePopupPin && !isPopupClosed && interactive && (
        <div className="active-incident-popup-card">
          <div className="popup-header">
            <div className="popup-id-row">
              <span className={`priority-tag ${activePopupPin.priority.toLowerCase()}`}>
                {activePopupPin.priority} CRITICAL
              </span>
              <span className="popup-id">{activePopupPin.id}</span>
            </div>
            <button className="close-popup-btn" onClick={() => setIsPopupClosed(true)}>
              ✕
            </button>
          </div>

          <h4 className="popup-title">{activePopupPin.title}</h4>
          <p className="popup-landmark">📍 {activePopupPin.landmarkProximity}</p>

          <div className="popup-meta-row">
            <div className="meta-item">
              <span>Cluster Reports</span>
              <b>{activePopupPin.reportCount} Verified</b>
            </div>
            <div className="meta-item">
              <span>Department</span>
              <b>{activePopupPin.department}</b>
            </div>
          </div>

          {dispatchMessage ? (
            <div className="dispatch-alert">{dispatchMessage}</div>
          ) : (
            <div className="popup-actions-row">
              <Link href={`/incidents/${activePopupPin.id}`} className="button small popup-action-btn">
                Inspect Dossier →
              </Link>
              <button
                className="outline small dispatch-btn"
                onClick={() => handleDispatch(activePopupPin.id)}
              >
                Dispatch Crew
              </button>
            </div>
          )}
        </div>
      )}

      {/* MAP LEGEND FOOTER BAR */}
      <div className="gis-bottom-legend">
        <div className="legend-pills-row">
          <span className="legend-chip">
            <i className="chip-dot p1-dot" /> P1 Urgent (3+ Reports)
          </span>
          <span className="legend-chip">
            <i className="chip-dot p2-dot" /> P2 Moderate
          </span>
          <span className="legend-chip">
            <i className="chip-dot p3-dot" /> P3 Clarification
          </span>
          <span className="legend-chip buffer-chip">
            <i className="buffer-dash" /> 500m School Safety Buffer
          </span>
        </div>
        <div className="coord-readout">
          <span>LAT: 20.2961° N · LON: 85.8245° E · POSTGIS 3.4</span>
        </div>
      </div>

      <style jsx>{`
        .gis-map-root {
          width: 100%;
          position: relative;
          background: #e2dfd7;
          overflow: hidden;
          border: 1px solid #172019;
        }
        .leaflet-map-canvas {
          width: 100%;
          height: 100%;
          z-index: 1;
        }
        .gis-top-bar {
          position: absolute;
          top: 14px;
          left: 14px;
          right: 14px;
          display: flex;
          justify-content: space-between;
          align-items: center;
          z-index: 500;
          pointer-events: none;
        }
        .gis-status-badge {
          pointer-events: auto;
          display: flex;
          align-items: center;
          gap: 8px;
          background: rgba(23, 32, 25, 0.92);
          color: #ffffff;
          padding: 6px 12px;
          border-radius: 6px;
          font-size: 0.68rem;
          letter-spacing: 0.08em;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        .live-pulse {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #10b981;
          box-shadow: 0 0 8px #10b981;
          animation: pulse 1.8s infinite;
        }
        .layer-switcher-buttons {
          pointer-events: auto;
          display: flex;
          gap: 4px;
          background: #ffffff;
          border: 1px solid #172019;
          padding: 3px;
          border-radius: 6px;
          box-shadow: 3px 3px 0 #172019;
        }
        .layer-btn {
          border: 0;
          background: transparent;
          padding: 5px 10px;
          font-size: 0.72rem;
          font-weight: 750;
          border-radius: 4px;
          cursor: pointer;
          color: #172019;
          transition: all 0.15s ease;
        }
        .layer-btn.active {
          background: #172019;
          color: #ffffff;
        }
        .gis-floating-tools {
          position: absolute;
          left: 14px;
          top: 60px;
          display: flex;
          flex-direction: column;
          gap: 10px;
          z-index: 500;
        }
        .zoom-btn-group {
          display: flex;
          flex-direction: column;
          border: 1px solid #172019;
          background: #ffffff;
          box-shadow: 2px 2px 0 #172019;
          border-radius: 4px;
          overflow: hidden;
          width: 22px;
          max-width: 22px;
        }
        .tool-btn {
          width: 22px;
          height: 22px;
          padding: 0;
          border: 0;
          background: transparent;
          font-size: 0.85rem;
          font-weight: 800;
          cursor: pointer;
          display: grid;
          place-items: center;
          transition: background 0.15s ease;
          line-height: 1;
        }
        .tool-btn:first-child {
          border-bottom: 1px solid #e2ded4;
        }
        .tool-btn:hover {
          background: #fbf9f4;
        }
        :global(.leaflet-control-zoom) {
          border: 1px solid #172019 !important;
          box-shadow: 2px 2px 0 #172019 !important;
          border-radius: 4px !important;
          overflow: hidden !important;
        }
        :global(.leaflet-control-zoom a) {
          width: 22px !important;
          height: 22px !important;
          line-height: 22px !important;
          font-size: 0.85rem !important;
          border-bottom: 1px solid #e2ded4 !important;
        }
        .landmark-jumps {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .jump-pill {
          padding: 6px 10px;
          border: 1px solid #172019;
          background: #ffffff;
          font-size: 0.68rem;
          font-weight: 800;
          border-radius: 4px;
          box-shadow: 2px 2px 0 #172019;
          cursor: pointer;
          text-align: left;
          transition: all 0.15s ease;
        }
        .jump-pill:hover {
          background: #172019;
          color: #ffffff;
        }
        .buffer-toggle-pill {
          background: #ffffff;
          border: 1px solid #172019;
          padding: 4px 8px;
          border-radius: 4px;
          box-shadow: 2px 2px 0 #172019;
          font-size: 0.62rem;
          font-weight: 800;
        }
        .buffer-toggle-pill label {
          display: flex;
          align-items: center;
          gap: 4px;
          cursor: pointer;
        }
        .active-incident-popup-card {
          position: absolute;
          right: 14px;
          top: 60px;
          width: 320px;
          background: #ffffff;
          border: 2px solid #172019;
          box-shadow: 6px 6px 0 #172019;
          padding: 16px;
          border-radius: 8px;
          z-index: 500;
          animation: slideIn 0.2s ease-out;
        }
        .popup-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }
        .popup-id-row {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .priority-tag {
          font-size: 0.6rem;
          font-weight: 900;
          padding: 2px 6px;
          border-radius: 3px;
        }
        .priority-tag.p1 {
          background: #e84d7a;
          color: #ffffff;
        }
        .priority-tag.p2 {
          background: #0f5f4f;
          color: #ffffff;
        }
        .priority-tag.p3 {
          background: #e3b950;
          color: #172019;
        }
        .popup-id {
          font-size: 0.72rem;
          font-weight: 800;
          color: #687067;
        }
        .close-popup-btn {
          border: 0;
          background: transparent;
          font-size: 0.85rem;
          cursor: pointer;
          color: #687067;
        }
        .popup-title {
          font-size: 0.95rem;
          font-family: Georgia, serif;
          margin: 4px 0 6px;
          color: #172019;
          line-height: 1.3;
        }
        .popup-landmark {
          font-size: 0.75rem;
          color: #0f5f4f;
          font-weight: 750;
          margin: 0 0 12px;
        }
        .popup-meta-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 8px;
          padding: 8px 10px;
          background: #fbf9f4;
          border: 1px solid #e2ded4;
          margin-bottom: 14px;
        }
        .meta-item span {
          display: block;
          font-size: 0.58rem;
          font-weight: 850;
          color: #687067;
          text-transform: uppercase;
        }
        .meta-item b {
          display: block;
          font-size: 0.75rem;
          color: #172019;
          margin-top: 2px;
        }
        .popup-actions-row {
          display: flex;
          gap: 8px;
        }
        .popup-action-btn {
          flex: 1;
          justify-content: center;
          font-size: 0.75rem !important;
          padding: 8px 10px !important;
        }
        .dispatch-btn {
          font-size: 0.75rem !important;
          padding: 8px 10px !important;
          background: #fbf9f4;
        }
        .dispatch-alert {
          padding: 8px 10px;
          background: #dce8dd;
          border: 1px solid #0f5f4f;
          color: #0f5f4f;
          font-size: 0.75rem;
          font-weight: 800;
          border-radius: 4px;
        }
        .gis-bottom-legend {
          position: absolute;
          bottom: 12px;
          left: 14px;
          right: 14px;
          background: rgba(255, 253, 247, 0.95);
          border: 1px solid #172019;
          box-shadow: 3px 3px 0 #172019;
          padding: 8px 14px;
          border-radius: 6px;
          display: flex;
          justify-content: space-between;
          align-items: center;
          z-index: 500;
          font-size: 0.68rem;
          font-weight: 750;
        }
        .legend-pills-row {
          display: flex;
          align-items: center;
          gap: 14px;
          flex-wrap: wrap;
        }
        .legend-chip {
          display: flex;
          align-items: center;
          gap: 6px;
          color: #172019;
        }
        .chip-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          display: inline-block;
        }
        .p1-dot {
          background: #e84d7a;
        }
        .p2-dot {
          background: #0f5f4f;
        }
        .p3-dot {
          background: #e3b950;
        }
        .buffer-dash {
          width: 14px;
          height: 2px;
          border-top: 2px dashed #e84d7a;
          display: inline-block;
        }
        .coord-readout {
          color: #687067;
          font-size: 0.62rem;
          font-family: monospace;
        }
        @keyframes pulse {
          0%, 100% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.3); opacity: 0.6; }
        }
        @keyframes slideIn {
          from { opacity: 0; transform: translateY(-8px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @media (max-width: 768px) {
          .active-incident-popup-card {
            width: calc(100% - 28px);
            left: 14px;
            right: 14px;
            top: auto;
            bottom: 60px;
          }
          .gis-bottom-legend {
            flex-direction: column;
            gap: 6px;
            align-items: flex-start;
          }
        }
      `}</style>
      <style jsx global>{`
        .custom-incident-icon {
          background: transparent;
          border: none;
        }
        .incident-marker-wrapper {
          position: relative;
          width: 36px;
          height: 36px;
          border-radius: 50%;
          border: 2px solid #172019;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: transform 0.2s ease;
          box-shadow: 0 4px 8px rgba(0, 0, 0, 0.25);
        }
        .incident-marker-wrapper:hover {
          transform: scale(1.2);
          z-index: 1000 !important;
        }
        .incident-marker-wrapper.selected-marker {
          transform: scale(1.3);
          box-shadow: 0 0 16px rgba(232, 77, 122, 0.9);
          z-index: 1000 !important;
        }
        .p1-pin {
          background: #e84d7a;
          color: #ffffff;
        }
        .p2-pin {
          background: #0f5f4f;
          color: #ffffff;
        }
        .p3-pin {
          background: #e3b950;
          color: #172019;
        }
        .marker-cluster-count {
          font-size: 0.78rem;
          font-weight: 900;
        }
        .marker-mini-badge {
          position: absolute;
          bottom: -16px;
          background: #172019;
          color: #ffffff;
          font-size: 0.55rem;
          font-weight: 800;
          padding: 1px 4px;
          border-radius: 3px;
          white-space: nowrap;
        }
        .pulse-ring {
          position: absolute;
          inset: -8px;
          border-radius: 50%;
          border: 2px solid #e84d7a;
          animation: ringPulse 2s infinite ease-out;
        }
        @keyframes ringPulse {
          0% { transform: scale(0.8); opacity: 1; }
          100% { transform: scale(1.6); opacity: 0; }
        }
        .landmark-poi-icon {
          background: transparent;
        }
        .landmark-badge {
          display: flex;
          align-items: center;
          gap: 5px;
          background: #ffffff;
          border: 1px solid #172019;
          box-shadow: 2px 2px 0 #172019;
          padding: 3px 8px;
          border-radius: 4px;
          font-size: 0.65rem;
          font-weight: 800;
          color: #172019;
          white-space: nowrap;
        }
      `}</style>
    </div>
  );
}
