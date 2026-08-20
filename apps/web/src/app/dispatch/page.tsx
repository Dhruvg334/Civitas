"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Footer, Nav, SectionLabel, Status } from "@/components/site";
import { FlatIcon } from "@/components/flat-icons";
import {
  fetchWorkOrderBatches,
  calculateBoqEstimate,
  WorkOrderDispatchBundle,
  BOQEstimateResponse,
} from "@/lib/api";

export default function DispatchPage() {
  const [bundles, setBundles] = useState<WorkOrderDispatchBundle[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedBundleId, setSelectedBundleId] = useState<string | null>(null);

  // BOQ Calculator State
  const [boqCategory, setBoqCategory] = useState<string>("pothole_road_damage");
  const [defectAreaCm2, setDefectAreaCm2] = useState<number>(1500);
  const [defectDepthMm, setDefectDepthMm] = useState<number>(60);
  const [isEmergency, setIsEmergency] = useState<boolean>(false);
  const [boqResult, setBoqResult] = useState<BOQEstimateResponse | null>(null);
  const [calculatingBoq, setCalculatingBoq] = useState<boolean>(false);

  useEffect(() => {
    let isMounted = true;
    fetchWorkOrderBatches()
      .then((data) => {
        if (!isMounted) return;
        setBundles(data.bundles || []);
        if (data.bundles && data.bundles.length > 0) {
          setSelectedBundleId(data.bundles[0].bundle_id);
        }
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

  const handleCalculateBoq = () => {
    setCalculatingBoq(true);
    calculateBoqEstimate(boqCategory, defectAreaCm2, defectDepthMm, isEmergency)
      .then((res) => {
        setBoqResult(res);
        setCalculatingBoq(false);
      })
      .catch(() => {
        setCalculatingBoq(false);
      });
  };

  useEffect(() => {
    handleCalculateBoq();
  }, [boqCategory, defectAreaCm2, defectDepthMm, isEmergency]);

  const selectedBundle = bundles.find((b) => b.bundle_id === selectedBundleId) || bundles[0];

  return (
    <>
      <Nav />
      <main className="dispatch-shell">
        <header className="dispatch-header">
          <div>
            <span className="workspace-kicker">FLEET ROUTING & WORK ORDER OPTIMIZATION</span>
            <h1>Spatial Crew Dispatch & Route Planner</h1>
            <p className="dispatch-subhead">
              Civitas clusters open municipal work orders by crew specialty and spatial H3 hexagonal
              neighborhoods, minimizing truck rolls, mobilization overhead, and transit emissions.
            </p>
          </div>
        </header>

        <div className="dispatch-layout-grid">
          {/* LEFT: DISPATCH BUNDLES LIST & WAYPOINTS */}
          <div className="dispatch-left-col">
            <div className="section-title-row">
              <SectionLabel>H3 HEXAGONAL DISPATCH BUNDLES</SectionLabel>
              <span className="count-pill">{bundles.length} Bundles Ready</span>
            </div>

            {loading ? (
              <div className="loading-card">Loading dispatch bundles...</div>
            ) : (
              <div className="bundles-list">
                {bundles.map((bundle) => {
                  const isSelected = bundle.bundle_id === selectedBundleId;
                  return (
                    <div
                      key={bundle.bundle_id}
                      className={`bundle-card ${isSelected ? "selected" : ""}`}
                      onClick={() => setSelectedBundleId(bundle.bundle_id)}
                    >
                      <div className="bundle-header">
                        <div>
                          <span className="bundle-id">{bundle.bundle_id}</span>
                          <h3 className="crew-title">{bundle.crew_type}</h3>
                        </div>
                        <span className="hex-badge">H3: {bundle.target_hex_cell}</span>
                      </div>

                      <div className="bundle-meta-row">
                        <span>
                          <FlatIcon name="clock" size={13} /> {bundle.total_duration_hours} hrs est.
                        </span>
                        <span>
                          <FlatIcon name="code" size={13} /> {bundle.work_order_ids.length} Work Orders
                        </span>
                        <span>
                          <strong>₹{bundle.total_cost_inr.toLocaleString()}</strong> (${bundle.total_cost_usd})
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {selectedBundle && (
              <div className="waypoints-card">
                <div className="waypoints-header">
                  <h3>
                    <FlatIcon name="map-pin" size={16} /> Optimized Multi-Stop Waypoints ({selectedBundle.bundle_id})
                  </h3>
                  <span className="badge neutral small">{selectedBundle.waypoints.length} Stops</span>
                </div>

                <div className="waypoints-timeline">
                  {selectedBundle.waypoints.map((wp, idx) => (
                    <div key={wp.work_order_id} className="waypoint-item">
                      <div className="waypoint-marker">{idx + 1}</div>
                      <div className="waypoint-content">
                        <div className="wp-title-row">
                          <Link href={`/incidents/${wp.incident_id}`} className="wp-id">
                            {wp.work_order_id} ({wp.incident_id})
                          </Link>
                          <span className="wp-hours">{wp.estimated_hours} hrs</span>
                        </div>
                        <p className="wp-category">{wp.category.replace(/_/g, " ").toUpperCase()}</p>
                        <span className="wp-coords">
                          GPS: {wp.latitude.toFixed(5)}, {wp.longitude.toFixed(5)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* RIGHT: INTERACTIVE BOQ ESTIMATOR */}
          <div className="dispatch-right-col">
            <div className="section-title-row">
              <SectionLabel>SCHEDULE OF RATES (SOR) BOQ ESTIMATOR</SectionLabel>
              <span className="badge good small">Live Pricing Engine</span>
            </div>

            <div className="boq-calculator-card">
              <div className="boq-form-grid">
                <div className="form-group">
                  <label>Defect Category</label>
                  <select
                    value={boqCategory}
                    onChange={(e) => setBoqCategory(e.target.value)}
                    className="select-input"
                  >
                    <option value="pothole_road_damage">Road Pothole & Asphalt Distress</option>
                    <option value="water_leakage">Potable Water Main Leakage / Rupture</option>
                    <option value="broken_streetlight">High-Voltage Streetlight / Luminaire Fault</option>
                    <option value="general_hazard">General Hazard / Obstruction</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Defect Surface Area: <strong>{defectAreaCm2} cm²</strong> ({(defectAreaCm2 / 10000).toFixed(2)} m²)</label>
                  <input
                    type="range"
                    min={100}
                    max={10000}
                    step={100}
                    value={defectAreaCm2}
                    onChange={(e) => setDefectAreaCm2(Number(e.target.value))}
                  />
                </div>

                <div className="form-group">
                  <label>Defect Depth: <strong>{defectDepthMm} mm</strong> ({(defectDepthMm / 10).toFixed(1)} cm)</label>
                  <input
                    type="range"
                    min={10}
                    max={300}
                    step={10}
                    value={defectDepthMm}
                    onChange={(e) => setDefectDepthMm(Number(e.target.value))}
                  />
                </div>

                <div className="form-group checkbox-group">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={isEmergency}
                      onChange={(e) => setIsEmergency(e.target.checked)}
                    />
                    <span>Emergency Priority Contingency (+15%)</span>
                  </label>
                </div>
              </div>

              {boqResult && (
                <div className="boq-results-box">
                  <div className="boq-total-banner">
                    <div>
                      <span className="boq-total-label">Total Estimated Repair Cost</span>
                      <div className="boq-price-row">
                        <span className="boq-inr">₹{boqResult.total_estimated_cost_inr.toLocaleString()}</span>
                        <span className="boq-usd">(${boqResult.total_estimated_cost_usd} USD)</span>
                      </div>
                    </div>
                    <div className="boq-duration-pill">
                      <FlatIcon name="clock" size={14} /> Est. {boqResult.estimated_duration_hours} hrs
                    </div>
                  </div>

                  <div className="boq-line-items-table-wrapper">
                    <table className="boq-table">
                      <thead>
                        <tr>
                          <th>Item Code</th>
                          <th>Description</th>
                          <th>Qty</th>
                          <th>Rate</th>
                          <th>Total</th>
                        </tr>
                      </thead>
                      <tbody>
                        {boqResult.line_items.map((item) => (
                          <tr key={item.item_code}>
                            <td className="mono-cell">{item.item_code}</td>
                            <td>{item.description}</td>
                            <td className="mono-cell">{item.quantity} {item.unit}</td>
                            <td className="mono-cell">₹{item.unit_rate_inr}</td>
                            <td className="mono-cell font-bold">₹{item.total_cost_inr.toLocaleString()}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
      <Footer />

      <style jsx>{`
        .dispatch-shell {
          max-width: 1300px;
          margin: 0 auto;
          padding: 2.5rem 1.5rem;
          display: flex;
          flex-direction: column;
          gap: 2rem;
        }
        .dispatch-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 1.5rem;
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
        .dispatch-header h1 {
          font-size: 2rem;
          font-weight: 800;
          color: var(--color-text-primary, #0f172a);
          margin: 0 0 0.5rem 0;
        }
        .dispatch-subhead {
          font-size: 0.95rem;
          color: var(--color-text-secondary, #475569);
          max-width: 750px;
          line-height: 1.5;
          margin: 0;
        }
        .dispatch-layout-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 2rem;
          align-items: flex-start;
        }
        @media (max-width: 960px) {
          .dispatch-layout-grid {
            grid-template-columns: 1fr;
          }
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
        .bundles-list {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
          margin-bottom: 1.5rem;
        }
        .bundle-card {
          background: var(--color-bg-primary, #ffffff);
          border: 1px solid var(--color-border, #e2e8f0);
          border-radius: 12px;
          padding: 1.25rem;
          cursor: pointer;
          transition: all 0.15s ease;
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }
        .bundle-card:hover {
          border-color: var(--color-brand, #2563eb);
        }
        .bundle-card.selected {
          border-color: var(--color-brand, #2563eb);
          background: rgba(37, 99, 235, 0.02);
          box-shadow: 0 0 0 1px var(--color-brand, #2563eb);
        }
        .bundle-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 1rem;
        }
        .bundle-id {
          font-size: 0.75rem;
          font-family: monospace;
          color: var(--color-text-secondary, #64748b);
          display: block;
        }
        .crew-title {
          font-size: 1.05rem;
          font-weight: 700;
          color: var(--color-text-primary, #0f172a);
          margin: 0.15rem 0 0 0;
        }
        .hex-badge {
          font-size: 0.7rem;
          font-family: monospace;
          background: var(--color-bg-secondary, #f1f5f9);
          padding: 0.2rem 0.5rem;
          border-radius: 4px;
          color: var(--color-text-secondary, #475569);
        }
        .bundle-meta-row {
          display: flex;
          gap: 1rem;
          font-size: 0.8rem;
          color: var(--color-text-secondary, #475569);
        }
        .waypoints-card {
          background: var(--color-bg-primary, #ffffff);
          border: 1px solid var(--color-border, #e2e8f0);
          border-radius: 12px;
          padding: 1.25rem;
        }
        .waypoints-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1rem;
        }
        .waypoints-header h3 {
          font-size: 0.95rem;
          font-weight: 700;
          margin: 0;
          display: flex;
          align-items: center;
          gap: 0.4rem;
        }
        .waypoints-timeline {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }
        .waypoint-item {
          display: flex;
          gap: 1rem;
          align-items: flex-start;
        }
        .waypoint-marker {
          width: 24px;
          height: 24px;
          border-radius: 50%;
          background: var(--color-brand, #2563eb);
          color: #ffffff;
          font-size: 0.75rem;
          font-weight: 700;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }
        .waypoint-content {
          flex: 1;
        }
        .wp-title-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .wp-id {
          font-weight: 700;
          font-size: 0.85rem;
          color: var(--color-brand, #2563eb);
          text-decoration: none;
        }
        .wp-hours {
          font-size: 0.75rem;
          font-weight: 600;
          color: var(--color-text-secondary, #64748b);
        }
        .wp-category {
          font-size: 0.8rem;
          font-weight: 600;
          color: var(--color-text-primary, #0f172a);
          margin: 0.2rem 0;
        }
        .wp-coords {
          font-size: 0.75rem;
          font-family: monospace;
          color: var(--color-text-secondary, #64748b);
        }
        .boq-calculator-card {
          background: var(--color-bg-primary, #ffffff);
          border: 1px solid var(--color-border, #e2e8f0);
          border-radius: 12px;
          padding: 1.5rem;
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }
        .boq-form-grid {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }
        .form-group {
          display: flex;
          flex-direction: column;
          gap: 0.4rem;
        }
        .form-group label {
          font-size: 0.8rem;
          font-weight: 600;
          color: var(--color-text-primary, #0f172a);
        }
        .select-input {
          padding: 0.5rem;
          border: 1px solid var(--color-border, #e2e8f0);
          border-radius: 6px;
          font-size: 0.85rem;
          background: var(--color-bg-primary, #ffffff);
          color: var(--color-text-primary, #0f172a);
        }
        .checkbox-group {
          margin-top: 0.25rem;
        }
        .checkbox-label {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          cursor: pointer;
        }
        .boq-total-banner {
          background: linear-gradient(135deg, rgba(37, 99, 235, 0.08), rgba(16, 185, 129, 0.08));
          border: 1px solid rgba(37, 99, 235, 0.2);
          border-radius: 8px;
          padding: 1rem 1.25rem;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .boq-total-label {
          font-size: 0.75rem;
          font-weight: 600;
          color: var(--color-text-secondary, #475569);
          display: block;
        }
        .boq-price-row {
          display: flex;
          align-items: baseline;
          gap: 0.5rem;
        }
        .boq-inr {
          font-size: 1.6rem;
          font-weight: 800;
          color: var(--color-text-primary, #0f172a);
        }
        .boq-usd {
          font-size: 0.9rem;
          color: var(--color-text-secondary, #64748b);
        }
        .boq-duration-pill {
          background: #ffffff;
          border: 1px solid var(--color-border, #e2e8f0);
          border-radius: 999px;
          padding: 0.35rem 0.75rem;
          font-size: 0.8rem;
          font-weight: 700;
          display: flex;
          align-items: center;
          gap: 0.4rem;
          color: var(--color-brand, #2563eb);
        }
        .boq-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 0.8rem;
          margin-top: 1rem;
        }
        .boq-table th {
          background: var(--color-bg-secondary, #f8fafc);
          padding: 0.5rem 0.75rem;
          text-align: left;
          color: var(--color-text-secondary, #475569);
          border-bottom: 1px solid var(--color-border, #e2e8f0);
        }
        .boq-table td {
          padding: 0.5rem 0.75rem;
          border-bottom: 1px solid var(--color-border, #f1f5f9);
        }
        .mono-cell {
          font-family: monospace;
        }
        .font-bold {
          font-weight: 700;
        }
        .loading-card {
          padding: 3rem;
          text-align: center;
          color: var(--color-text-secondary, #64748b);
        }
      `}</style>
    </>
  );
}
