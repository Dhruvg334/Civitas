"use client";

import { useState } from "react";
import Link from "next/link";
import { Footer, Nav, SectionLabel, Status } from "@/components/site";
import { MiniMap } from "@/components/civic-visuals";

interface IncidentItem {
  id: string;
  title: string;
  category: string;
  priority: "P1" | "P2" | "P3";
  status: string;
  tone: "neutral" | "good" | "warn" | "danger";
  reportsCount: number;
  ward: string;
  landmark: string;
  time: string;
  department: string;
}

const INITIAL_INCIDENTS: IncidentItem[] = [
  {
    id: "INC-0241",
    title: "School Crossing Water Main Leakage",
    category: "Water Supply & Drainage",
    priority: "P1",
    status: "WAITING_FOR_REVIEW",
    tone: "warn",
    reportsCount: 3,
    ward: "Ward 12 · Unit 8",
    landmark: "14m from DAV Public School Gate",
    time: "12m ago",
    department: "Water Supply & Drainage",
  },
  {
    id: "INC-0240",
    title: "Fallen Banyan Tree Branch Blocking Road",
    category: "Parks & Urban Forestry",
    priority: "P2",
    status: "ASSIGNED",
    tone: "good",
    reportsCount: 2,
    ward: "Ward 12 · Park Road",
    landmark: "Opposite Community Garden",
    time: "48m ago",
    department: "Parks & Forestry",
  },
  {
    id: "INC-0238",
    title: "Streetlight Cluster Power Failure",
    category: "Electrical & Public Lighting",
    priority: "P3",
    status: "WAITING_FOR_CLARIFICATION",
    tone: "neutral",
    reportsCount: 1,
    ward: "Ward 12 · East Gate",
    landmark: "Commercial Junction Poles #104-106",
    time: "2h ago",
    department: "Electrical Works",
  },
  {
    id: "INC-0235",
    title: "Severe Asphalt Pothole on Bus Route",
    category: "Road Infrastructure",
    priority: "P1",
    status: "RESOLVED",
    tone: "good",
    reportsCount: 4,
    ward: "Ward 12 · Hospital Flyover",
    landmark: "Near City Hospital Exit",
    time: "4h ago",
    department: "Road Maintenance",
  },
];

export default function Workspace() {
  const [selectedIncidentId, setSelectedIncidentId] = useState<string>("INC-0241");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [activeFilter, setActiveFilter] = useState<string>("ALL");

  const filteredIncidents = INITIAL_INCIDENTS.filter((item) => {
    const matchesSearch =
      item.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.ward.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.department.toLowerCase().includes(searchQuery.toLowerCase());

    if (!matchesSearch) return false;

    if (activeFilter === "ALL") return true;
    if (activeFilter === "P1") return item.priority === "P1";
    if (activeFilter === "P2") return item.priority === "P2";
    if (activeFilter === "P3") return item.priority === "P3";
    if (activeFilter === "REVIEW") return item.status === "WAITING_FOR_REVIEW";
    if (activeFilter === "RESOLVED") return item.status === "RESOLVED";

    return true;
  });

  return (
    <>
      <Nav />
      <main className="workspace-main-shell">
        {/* TOP COMMAND CENTER BANNER */}
        <section className="ops-banner">
          <div className="ops-banner-inner">
            <div>
              <SectionLabel index="01">MUNICIPAL COMMAND CENTER</SectionLabel>
              <h1 className="ops-heading">Ward 12 Operations Workspace</h1>
              <p className="ops-subtext">
                Live spatial incident queue with PostGIS clustering, multimodal ML triage, and human-in-the-loop work order verification.
              </p>
            </div>

            <div className="ops-stats-strip">
              <div className="stat-pill">
                <span>ACTIVE QUEUE</span>
                <b>{INITIAL_INCIDENTS.length} Incidents</b>
              </div>
              <div className="stat-pill">
                <span>GIS SYNC</span>
                <b className="gis-connected">● PostGIS 3.4 Live</b>
              </div>
              <div className="stat-pill">
                <span>SUPERVISOR GATES</span>
                <b className="p1-alert">1 Pending</b>
              </div>
            </div>
          </div>
        </section>

        {/* WORKSPACE GRID: LEFT QUEUE, RIGHT INTERACTIVE GIS MAP */}
        <div className="workspace-split-layout">
          {/* LEFT: SEARCHABLE INCIDENT QUEUE */}
          <div className="queue-column">
            {/* SEARCH & FILTER CONTROLS */}
            <div className="queue-controls-card">
              <div className="search-bar-wrap">
                <span className="search-icon">🔍</span>
                <input
                  type="text"
                  placeholder="Filter by ID, street, or department..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="queue-search-input"
                  aria-label="Filter incidents"
                />
                {searchQuery && (
                  <button className="clear-search-btn" onClick={() => setSearchQuery("")}>
                    ✕
                  </button>
                )}
              </div>

              <div className="filter-pills-row">
                {[
                  { id: "ALL", label: `All (${INITIAL_INCIDENTS.length})` },
                  { id: "P1", label: "P1 Critical" },
                  { id: "P2", label: "P2 Medium" },
                  { id: "P3", label: "P3 Low" },
                  { id: "REVIEW", label: "Needs Review" },
                  { id: "RESOLVED", label: "Resolved" },
                ].map((f) => (
                  <button
                    key={f.id}
                    className={`filter-btn ${activeFilter === f.id ? "active" : ""}`}
                    onClick={() => setActiveFilter(f.id)}
                  >
                    {f.label}
                  </button>
                ))}
              </div>
            </div>

            {/* INCIDENT LIST */}
            <div className="incident-cards-scrollable" role="list">
              {filteredIncidents.map((incident) => {
                const isSelected = incident.id === selectedIncidentId;

                return (
                  <article
                    key={incident.id}
                    className={`incident-queue-card ${isSelected ? "selected" : ""}`}
                    onClick={() => setSelectedIncidentId(incident.id)}
                    role="listitem"
                  >
                    <div className="card-top-row">
                      <div className="id-prio-group">
                        <span className={`priority-badge ${incident.priority.toLowerCase()}`}>
                          {incident.priority}
                        </span>
                        <span className="incident-id-tag">{incident.id}</span>
                      </div>
                      <div className="card-time-status">
                        <span className="time-tag">{incident.time}</span>
                        <Status tone={incident.tone}>{incident.status}</Status>
                      </div>
                    </div>

                    <h3 className="incident-title">{incident.title}</h3>
                    <p className="incident-landmark">📍 {incident.landmark}</p>

                    <div className="card-bottom-row">
                      <span className="cluster-tag">
                        👥 <b>{incident.reportsCount}</b> citizen reports clustered
                      </span>
                      <Link
                        href={`/incidents/${incident.id}`}
                        className="inspect-link"
                        onClick={(e) => e.stopPropagation()}
                      >
                        Inspect Dossier →
                      </Link>
                    </div>
                  </article>
                );
              })}

              {filteredIncidents.length === 0 && (
                <div className="empty-queue-message">
                  <span>No incidents match the selected filter query.</span>
                </div>
              )}
            </div>
          </div>

          {/* RIGHT: LEAFLET-POWERED GIS MAP */}
          <div className="map-column">
            <div className="map-wrapper-card">
              <MiniMap
                selectedIncidentId={selectedIncidentId}
                onSelectIncident={(id) => setSelectedIncidentId(id)}
                height="620px"
              />
            </div>
          </div>
        </div>
      </main>
      <Footer />

      <style jsx>{`
        .workspace-main-shell {
          width: min(calc(100% - 40px), 1280px);
          margin: 32px auto 80px;
        }
        .ops-banner {
          padding-bottom: 24px;
          border-bottom: 2px solid #172019;
          margin-bottom: 28px;
        }
        .ops-banner-inner {
          display: flex;
          justify-content: space-between;
          align-items: flex-end;
          gap: 24px;
          flex-wrap: wrap;
        }
        .ops-heading {
          font-size: clamp(2.2rem, 4vw, 3.2rem);
          font-family: Georgia, serif;
          margin: 6px 0 8px;
          color: #172019;
        }
        .ops-subtext {
          font-size: 0.95rem;
          color: #555e54;
          margin: 0;
          max-width: 620px;
          line-height: 1.55;
        }
        .ops-stats-strip {
          display: flex;
          gap: 12px;
          flex-wrap: wrap;
        }
        .stat-pill {
          padding: 8px 14px;
          border: 1px solid #172019;
          background: #ffffff;
          box-shadow: 2px 2px 0 #172019;
          border-radius: 4px;
        }
        .stat-pill span {
          display: block;
          font-size: 0.58rem;
          font-weight: 850;
          letter-spacing: 0.08em;
          color: #687067;
        }
        .stat-pill b {
          display: block;
          font-size: 0.85rem;
          color: #172019;
          margin-top: 2px;
        }
        .gis-connected {
          color: #0f5f4f !important;
        }
        .p1-alert {
          color: #e84d7a !important;
        }
        .workspace-split-layout {
          display: grid;
          grid-template-columns: 460px 1fr;
          gap: 28px;
          align-items: start;
        }
        .queue-column {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .queue-controls-card {
          border: 1px solid #172019;
          background: #ffffff;
          box-shadow: 3px 3px 0 #172019;
          padding: 16px;
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .search-bar-wrap {
          display: flex;
          align-items: center;
          gap: 8px;
          background: #fbf9f4;
          border: 1px solid #172019;
          padding: 8px 12px;
          border-radius: 4px;
        }
        .search-icon {
          font-size: 0.8rem;
        }
        .queue-search-input {
          border: 0;
          background: transparent;
          font-size: 0.82rem;
          width: 100%;
          outline: none;
          color: #172019;
        }
        .clear-search-btn {
          border: 0;
          background: transparent;
          font-size: 0.75rem;
          cursor: pointer;
          color: #687067;
        }
        .filter-pills-row {
          display: flex;
          gap: 6px;
          overflow-x: auto;
          padding-bottom: 2px;
        }
        .filter-btn {
          padding: 4px 8px;
          border: 1px solid #172019;
          background: #fbf9f4;
          font-size: 0.68rem;
          font-weight: 800;
          border-radius: 3px;
          cursor: pointer;
          white-space: nowrap;
          transition: all 0.15s ease;
        }
        .filter-btn.active {
          background: #172019;
          color: #ffffff;
        }
        .incident-cards-scrollable {
          display: flex;
          flex-direction: column;
          gap: 12px;
          max-height: 600px;
          overflow-y: auto;
          padding-right: 4px;
        }
        .incident-queue-card {
          border: 1px solid #172019;
          background: #ffffff;
          padding: 16px;
          cursor: pointer;
          transition: all 0.15s ease;
          position: relative;
        }
        .incident-queue-card:hover {
          background: #fbf9f4;
          box-shadow: 3px 3px 0 #172019;
        }
        .incident-queue-card.selected {
          border-left: 6px solid #e84d7a;
          background: #ffffff;
          box-shadow: 4px 4px 0 #172019;
        }
        .card-top-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }
        .id-prio-group {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .priority-badge {
          font-size: 0.6rem;
          font-weight: 900;
          padding: 2px 6px;
          border-radius: 3px;
        }
        .priority-badge.p1 {
          background: #e84d7a;
          color: #ffffff;
        }
        .priority-badge.p2 {
          background: #0f5f4f;
          color: #ffffff;
        }
        .priority-badge.p3 {
          background: #e3b950;
          color: #172019;
        }
        .incident-id-tag {
          font-size: 0.72rem;
          font-weight: 850;
          color: #687067;
        }
        .card-time-status {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .time-tag {
          font-size: 0.65rem;
          color: #687067;
        }
        .incident-title {
          font-size: 1rem;
          font-family: Georgia, serif;
          margin: 0 0 4px;
          color: #172019;
          line-height: 1.3;
        }
        .incident-landmark {
          font-size: 0.75rem;
          color: #0f5f4f;
          font-weight: 750;
          margin: 0 0 12px;
        }
        .card-bottom-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          border-top: 1px solid #e2ded4;
          padding-top: 10px;
          font-size: 0.72rem;
        }
        .cluster-tag {
          color: #555e54;
        }
        .inspect-link {
          font-weight: 800;
          color: #172019;
          text-decoration: none;
          transition: color 0.15s ease;
        }
        .inspect-link:hover {
          color: #e84d7a;
        }
        .empty-queue-message {
          padding: 30px;
          text-align: center;
          border: 1px dashed #172019;
          background: #fbf9f4;
          font-size: 0.85rem;
          color: #687067;
        }
        .map-column {
          position: sticky;
          top: 90px;
        }
        .map-wrapper-card {
          border: 2px solid #172019;
          background: #ffffff;
          box-shadow: 6px 6px 0 #172019;
          overflow: hidden;
        }
        @media (max-width: 1000px) {
          .workspace-split-layout {
            grid-template-columns: 1fr;
          }
          .map-column {
            position: static;
          }
        }
      `}</style>
    </>
  );
}
