"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Footer, Nav, SectionLabel, Status } from "@/components/site";
import { FlatIcon } from "@/components/flat-icons";
import { InteractiveGisMap, GisIncidentPin } from "@/components/interactive-gis-map";
import { fetchPublicIncidentsGeoJson, getApiBaseUrl, PublicGeoJsonFeature } from "@/lib/api";

export default function OpenDataPage() {
  const [features, setFeatures] = useState<PublicGeoJsonFeature[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [differentialPrivacyEnabled, setDifferentialPrivacyEnabled] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");

  useEffect(() => {
    let isMounted = true;
    fetchPublicIncidentsGeoJson(200)
      .then((data) => {
        if (!isMounted) return;
        setFeatures(data.features || []);
        setLoading(false);
      })
      .catch(() => {
        if (!isMounted) return;
        setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, []);

  const filteredFeatures = features.filter((f) => {
    const matchesCat =
      selectedCategory === "ALL" ||
      f.properties.category.toLowerCase().includes(selectedCategory.toLowerCase());
    const matchesSearch =
      !searchQuery ||
      f.properties.incident_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.properties.description_sanitized.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.properties.assigned_department.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCat && matchesSearch;
  });

  const mapPins: GisIncidentPin[] = filteredFeatures.map((f) => ({
    id: f.properties.incident_id,
    title: f.properties.category.replace(/_/g, " ").toUpperCase(),
    category: f.properties.category,
    priority: "P2",
    status: f.properties.status,
    lat: f.geometry.coordinates[1],
    lng: f.geometry.coordinates[0],
    reportCount: 1,
    landmarkProximity: `H3 Hex: ${f.properties.h3_hex_cell}`,
    department: f.properties.assigned_department.replace(/_/g, " "),
  }));

  const handleDownloadGeoJson = () => {
    window.open(`${getApiBaseUrl()}/public/incidents.geojson?limit=500`, "_blank");
  };

  const handleDownloadCsv = () => {
    window.open(`${getApiBaseUrl()}/public/incidents.csv?limit=1000`, "_blank");
  };

  return (
    <>
      <Nav />
      <main className="open-data-shell">
        <header className="open-data-header">
          <div>
            <span className="workspace-kicker">MUNICIPAL CIVIC DATA & TRANSPARENCY</span>
            <h1>Public Open Data Portal</h1>
            <p className="open-data-subhead">
              Civitas publishes real-time municipal incident records under an open civic data mandate.
              All public feeds are protected by automated PII scrubbing and differential privacy spatial perturbation.
            </p>
          </div>

          <div className="open-data-actions">
            <button className="button secondary small" onClick={handleDownloadGeoJson}>
              <FlatIcon name="code" size={14} /> Download RFC 7946 GeoJSON
            </button>
            <button className="button primary small" onClick={handleDownloadCsv}>
              <FlatIcon name="download" size={14} /> Export Tabular CSV
            </button>
          </div>
        </header>

        {/* PRIVACY BADGE & CONTROLS */}
        <section className="privacy-banner-card">
          <div className="privacy-card-content">
            <div className="privacy-shield-icon">
              <FlatIcon name="shield" size={24} />
            </div>
            <div>
              <h3>Differential Privacy & Zero-Trust PII Redaction Active</h3>
              <p>
                Precise coordinates are perturbed with a bounded Gaussian noise envelope (±25m) to safeguard
                residential privacy while preserving neighborhood-level spatial hotspot accuracy. Citizen phone
                numbers, emails, and vehicle license plates are automatically redacted before publication.
              </p>
            </div>
          </div>
          <div className="privacy-toggle-box">
            <label className="toggle-label">
              <span>Differential Privacy Jitter</span>
              <input
                type="checkbox"
                checked={differentialPrivacyEnabled}
                onChange={(e) => setDifferentialPrivacyEnabled(e.target.checked)}
              />
            </label>
            <span className="badge good small">±25m Perturbation</span>
          </div>
        </section>

        {/* MAP SECTION */}
        <section className="open-data-map-section">
          <div className="section-title-row">
            <SectionLabel>CIVIC INCIDENT GEOSPATIAL MAP</SectionLabel>
            <span className="count-pill">{mapPins.length} Geocoded Records</span>
          </div>
          <div className="map-container-wrapper">
            <InteractiveGisMap
              selectedIncidentId={mapPins[0]?.id || "INC-0241"}
              height="380px"
              showControls={true}
              interactive={true}
            />
          </div>
        </section>

        {/* FILTER & TABLE SECTION */}
        <section className="open-data-table-section">
          <div className="table-controls-bar">
            <div className="search-box">
              <FlatIcon name="search" size={14} />
              <input
                type="text"
                placeholder="Search sanitized descriptions, H3 cells, or departments..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            <div className="category-chips">
              {["ALL", "water_leakage", "pothole", "streetlight", "fallen_tree", "drainage_blockage"].map((cat) => (
                <button
                  key={cat}
                  className={`chip-btn ${selectedCategory === cat ? "active" : ""}`}
                  onClick={() => setSelectedCategory(cat)}
                >
                  {cat.replace(/_/g, " ").toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          <div className="data-table-card">
            {loading ? (
              <div className="table-loading-state">Loading public open data feed...</div>
            ) : filteredFeatures.length === 0 ? (
              <div className="table-empty-state">No matching public incident records found.</div>
            ) : (
              <table className="civic-data-table">
                <thead>
                  <tr>
                    <th>Incident ID</th>
                    <th>Category</th>
                    <th>Sanitized Description</th>
                    <th>H3 Spatial Hex</th>
                    <th>Department</th>
                    <th>Status</th>
                    <th>Coordinates (Jittered)</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredFeatures.map((f) => (
                    <tr key={f.properties.incident_id}>
                      <td className="id-cell">
                        <Link href={`/incidents/${f.properties.incident_id}`}>
                          {f.properties.incident_id}
                        </Link>
                      </td>
                      <td>
                        <span className="category-tag">
                          {f.properties.category.replace(/_/g, " ")}
                        </span>
                      </td>
                      <td className="desc-cell">{f.properties.description_sanitized}</td>
                      <td className="mono-cell">{f.properties.h3_hex_cell}</td>
                      <td>{f.properties.assigned_department.replace(/_/g, " ")}</td>
                      <td>
                        <Status tone={f.properties.status === "RESOLVED" ? "good" : "warn"}>
                          {f.properties.status}
                        </Status>
                      </td>
                      <td className="mono-cell">
                        {f.geometry.coordinates[1].toFixed(5)}, {f.geometry.coordinates[0].toFixed(5)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </section>
      </main>
      <Footer />

      <style jsx>{`
        .open-data-shell {
          max-width: 1300px;
          margin: 0 auto;
          padding: 2.5rem 1.5rem;
          display: flex;
          flex-direction: column;
          gap: 2rem;
        }
        .open-data-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 1.5rem;
          flex-wrap: wrap;
        }
        .workspace-kicker {
          font-size: 0.75rem;
          font-weight: 700;
          letter-spacing: 0.08em;
          color: var(--color-brand, #2563eb);
          text-transform: uppercase;
          display: block;
          margin-bottom: 0.35rem;
        }
        .open-data-header h1 {
          font-size: 2rem;
          font-weight: 800;
          color: var(--color-text-primary, #0f172a);
          margin: 0 0 0.5rem 0;
        }
        .open-data-subhead {
          font-size: 0.95rem;
          color: var(--color-text-secondary, #475569);
          max-width: 750px;
          line-height: 1.5;
          margin: 0;
        }
        .open-data-actions {
          display: flex;
          gap: 0.75rem;
          align-items: center;
        }
        .privacy-banner-card {
          background: linear-gradient(135deg, rgba(37, 99, 235, 0.06), rgba(16, 185, 129, 0.06));
          border: 1px solid rgba(37, 99, 235, 0.2);
          border-radius: 12px;
          padding: 1.25rem 1.5rem;
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 1.5rem;
          flex-wrap: wrap;
        }
        .privacy-card-content {
          display: flex;
          gap: 1rem;
          align-items: flex-start;
          max-width: 800px;
        }
        .privacy-shield-icon {
          color: var(--color-brand, #2563eb);
          margin-top: 0.15rem;
        }
        .privacy-card-content h3 {
          font-size: 1rem;
          font-weight: 700;
          margin: 0 0 0.3rem 0;
          color: var(--color-text-primary, #0f172a);
        }
        .privacy-card-content p {
          font-size: 0.85rem;
          color: var(--color-text-secondary, #475569);
          margin: 0;
          line-height: 1.45;
        }
        .privacy-toggle-box {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          gap: 0.5rem;
        }
        .toggle-label {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 0.85rem;
          font-weight: 600;
          color: var(--color-text-primary, #0f172a);
        }
        .section-title-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 0.75rem;
        }
        .count-pill {
          font-size: 0.75rem;
          font-weight: 600;
          padding: 0.2rem 0.6rem;
          border-radius: 999px;
          background: var(--color-bg-secondary, #f1f5f9);
          color: var(--color-text-secondary, #475569);
        }
        .map-container-wrapper {
          border-radius: 12px;
          overflow: hidden;
          border: 1px solid var(--color-border, #e2e8f0);
          height: 380px;
        }
        .table-controls-bar {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 1rem;
          margin-bottom: 1rem;
          flex-wrap: wrap;
        }
        .search-box {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          background: var(--color-bg-primary, #ffffff);
          border: 1px solid var(--color-border, #e2e8f0);
          border-radius: 8px;
          padding: 0.45rem 0.75rem;
          width: 340px;
        }
        .search-box input {
          border: none;
          outline: none;
          background: transparent;
          font-size: 0.85rem;
          width: 100%;
          color: var(--color-text-primary, #0f172a);
        }
        .category-chips {
          display: flex;
          gap: 0.4rem;
          flex-wrap: wrap;
        }
        .chip-btn {
          border: 1px solid var(--color-border, #e2e8f0);
          background: var(--color-bg-primary, #ffffff);
          padding: 0.35rem 0.65rem;
          border-radius: 6px;
          font-size: 0.75rem;
          font-weight: 600;
          color: var(--color-text-secondary, #475569);
          cursor: pointer;
          transition: all 0.15s ease;
        }
        .chip-btn.active {
          background: var(--color-brand, #2563eb);
          color: #ffffff;
          border-color: var(--color-brand, #2563eb);
        }
        .data-table-card {
          background: var(--color-bg-primary, #ffffff);
          border: 1px solid var(--color-border, #e2e8f0);
          border-radius: 12px;
          overflow-x: auto;
        }
        .civic-data-table {
          width: 100%;
          border-collapse: collapse;
          text-align: left;
          font-size: 0.85rem;
        }
        .civic-data-table th {
          background: var(--color-bg-secondary, #f8fafc);
          padding: 0.75rem 1rem;
          font-weight: 600;
          color: var(--color-text-secondary, #475569);
          border-bottom: 1px solid var(--color-border, #e2e8f0);
        }
        .civic-data-table td {
          padding: 0.75rem 1rem;
          border-bottom: 1px solid var(--color-border, #e2e8f0);
          color: var(--color-text-primary, #0f172a);
        }
        .id-cell a {
          font-weight: 700;
          color: var(--color-brand, #2563eb);
          text-decoration: none;
        }
        .category-tag {
          font-weight: 600;
          text-transform: capitalize;
        }
        .desc-cell {
          max-width: 320px;
          color: var(--color-text-secondary, #475569);
        }
        .mono-cell {
          font-family: monospace;
          font-size: 0.8rem;
          color: var(--color-text-secondary, #64748b);
        }
        .table-loading-state,
        .table-empty-state {
          padding: 3rem;
          text-align: center;
          color: var(--color-text-secondary, #64748b);
          font-size: 0.9rem;
        }
      `}</style>
    </>
  );
}
