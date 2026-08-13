"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { MiniMap } from "@/components/civic-visuals";
import { Nav, Status, Footer } from "@/components/site";
import { fetchIncidents, IncidentRecord, SEEDED_INCIDENTS } from "@/lib/api";

export default function Workspace() {
  const [incidents, setIncidents] = useState<IncidentRecord[]>(SEEDED_INCIDENTS);
  const [filterCategory, setFilterCategory] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedId, setSelectedId] = useState<string>("INC-0241");
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      const data = await fetchIncidents();
      setIncidents(data);
      setLoading(false);
    }
    loadData();
  }, []);

  const filteredIncidents = incidents.filter((item) => {
    const matchesCategory =
      filterCategory === "ALL" || item.category.toLowerCase().includes(filterCategory.toLowerCase());
    const matchesSearch =
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.id.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const selectedIncident =
    incidents.find((item) => item.id === selectedId) || incidents[0] || SEEDED_INCIDENTS[0];

  return (
    <>
      <Nav />
      <main className="workspace-shell">
        <header className="workspace-header">
          <div>
            <span className="workspace-kicker">MUNICIPAL COMMAND CENTER / WARD 12</span>
            <h1>Incident Command Dashboard</h1>
            <p>Prioritized incidents, spatial context, and agent workflow state in one view.</p>
          </div>
          <div className="workspace-actions">
            <div className="search-box">
              <input
                type="text"
                placeholder="Search ticket ID or landmark..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="category-filter"
            >
              <option value="ALL">All Categories</option>
              <option value="Water">Water Leakage</option>
              <option value="Pothole">Pothole / Road</option>
              <option value="Garbage">Garbage</option>
              <option value="Streetlight">Streetlight</option>
              <option value="Tree">Fallen Tree</option>
            </select>
          </div>
        </header>

        <section className="ops-strip" aria-label="Queue summary">
          <div>
            <span>Open Incidents</span>
            <b>0{incidents.length}</b>
            <small>Active in queue</small>
          </div>
          <div>
            <span>Awaiting Review</span>
            <b>01</b>
            <small>Human review gate</small>
          </div>
          <div>
            <span>Clarification</span>
            <b>01</b>
            <small>Resident question sent</small>
          </div>
          <div>
            <span>Highest Priority</span>
            <b>P1 Critical</b>
            <small>School crossing leak</small>
          </div>
        </section>

        <div className="workspace-grid">
          <section className="queue-panel">
            <div className="panel-heading">
              <div>
                <span>INCIDENT QUEUE</span>
                <h2>Needs Attention ({filteredIncidents.length})</h2>
              </div>
              {loading && <span className="loading-badge">Refreshing...</span>}
            </div>

            <div className="queue-list">
              {filteredIncidents.map((row, index) => {
                const isSelected = row.id === selectedId;
                const tone =
                  row.status.includes("REVIEW")
                    ? "warn"
                    : row.status.includes("APPROVED")
                    ? "good"
                    : "neutral";

                return (
                  <div
                    key={row.id}
                    onClick={() => setSelectedId(row.id)}
                    className={`incident-row-wrapper ${isSelected ? "selected" : ""}`}
                  >
                    <Link href={`/incidents/${row.id}`} className="incident-row">
                      <span className="row-index">{String(index + 1).padStart(2, "0")}</span>
                      <div className="incident-main">
                        <span>
                          {row.id} · {row.category}
                        </span>
                        <b>{row.title}</b>
                        <small>
                          {row.primaryDepartment} · {row.reportsCount} report
                          {row.reportsCount > 1 ? "s" : ""}
                        </small>
                      </div>
                      <div className="incident-priority">
                        <span>Priority</span>
                        <b>{row.priority}</b>
                      </div>
                      <Status tone={tone}>{row.status}</Status>
                    </Link>
                  </div>
                );
              })}
            </div>
          </section>

          <section className="map-panel">
            <div className="panel-heading">
              <div>
                <span>SPATIAL CONTEXT & GIS</span>
                <h2>Ward 12 Map Overview</h2>
              </div>
              <span className="live-dot">Live PostGIS</span>
            </div>

            <MiniMap />

            <div className="map-context">
              <div>
                <span>Selected Incident</span>
                <b>{selectedIncident.id}</b>
              </div>
              <div>
                <span>Landmark Proximity</span>
                <b>{selectedIncident.location?.landmark || "Civitas School Gate"}</b>
              </div>
              <div>
                <span>Geospatial Proximity</span>
                <b>{selectedIncident.location?.latitude}, {selectedIncident.location?.longitude}</b>
              </div>
            </div>
          </section>
        </div>
      </main>
      <Footer />

      <style jsx>{`
        .search-box input {
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          color: #fff;
          padding: 0.5rem 0.875rem;
          border-radius: 8px;
          font-size: 0.875rem;
        }
        .category-filter {
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          color: #fff;
          padding: 0.5rem 0.875rem;
          border-radius: 8px;
          font-size: 0.875rem;
        }
        .incident-row-wrapper {
          border-radius: 8px;
          transition: background 0.15s ease;
        }
        .incident-row-wrapper.selected {
          background: rgba(99, 102, 241, 0.12);
          border-left: 3px solid #6366f1;
        }
        .loading-badge {
          font-size: 0.75rem;
          color: #818cf8;
        }
      `}</style>
    </>
  );
}
