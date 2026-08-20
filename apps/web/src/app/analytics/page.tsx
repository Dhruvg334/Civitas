"use client";

import { useEffect, useState } from "react";
import { Footer, Nav, SectionLabel } from "@/components/site";
import { fetchContractorScorecards, ContractorScorecard } from "@/lib/api";

export default function AnalyticsPage() {
  const [scorecards, setScorecards] = useState<ContractorScorecard[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedDept, setSelectedDept] = useState<string>("ALL");

  useEffect(() => {
    let isMounted = true;
    fetchContractorScorecards()
      .then((data) => {
        if (!isMounted) return;
        setScorecards(data.scorecards || []);
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

  const filteredScorecards = scorecards.filter((sc) => {
    if (selectedDept === "ALL") return true;
    return sc.department.toLowerCase() === selectedDept.toLowerCase();
  });

  const avgSla =
    scorecards.length > 0
      ? (scorecards.reduce((acc, s) => acc + s.sla_compliance_rate_pct, 0) / scorecards.length).toFixed(1)
      : "0";

  const avgMttr =
    scorecards.length > 0
      ? (scorecards.reduce((acc, s) => acc + s.mean_time_to_resolution_hours, 0) / scorecards.length).toFixed(1)
      : "0";

  const totalJobs = scorecards.reduce((acc, s) => acc + s.completed_jobs, 0);
  const totalDisputes = scorecards.reduce((acc, s) => acc + s.dispute_count, 0);

  return (
    <>
      <Nav />
      <main className="analytics-shell">
        <header className="analytics-header">
          <div>
            <span className="workspace-kicker">OPERATIONAL INTELLIGENCE & VENDOR ACCOUNTABILITY</span>
            <h1>Municipal Contractor & SLA Analytics</h1>
            <p className="analytics-subhead">
              Continuous monitoring of statutory SLA compliance, Mean Time to Resolution (MTTR),
              and citizen dispute rates across municipal repair vendors.
            </p>
          </div>
        </header>

        {/* SUMMARY KPI CARDS */}
        <section className="kpi-grid">
          <div className="kpi-card">
            <span className="kpi-label">Avg Statutory SLA Compliance</span>
            <div className="kpi-value-row">
              <span className="kpi-number">{avgSla}%</span>
              <span className="badge good small">Target: ≥85%</span>
            </div>
            <p className="kpi-subtext">Across all active municipal service contracts</p>
          </div>

          <div className="kpi-card">
            <span className="kpi-label">Mean Time to Resolution (MTTR)</span>
            <div className="kpi-value-row">
              <span className="kpi-number">{avgMttr} hrs</span>
              <span className="badge neutral small">Baseline: 24h</span>
            </div>
            <p className="kpi-subtext">From work order dispatch to verified field closure</p>
          </div>

          <div className="kpi-card">
            <span className="kpi-label">Total Completed Work Orders</span>
            <div className="kpi-value-row">
              <span className="kpi-number">{totalJobs}</span>
              <span className="badge good small">Verified</span>
            </div>
            <p className="kpi-subtext">Photogrammetrically verified repairs</p>
          </div>

          <div className="kpi-card">
            <span className="kpi-label">Citizen Dispute Frequency</span>
            <div className="kpi-value-row">
              <span className="kpi-number">{totalDisputes}</span>
              <span className="badge warn small">{((totalDisputes / Math.max(1, totalJobs)) * 100).toFixed(1)}% Rate</span>
            </div>
            <p className="kpi-subtext">Disputes filed within 72h review window</p>
          </div>
        </section>

        {/* CONTRACTOR SCORECARDS SECTION */}
        <section className="contractors-section">
          <div className="section-title-row">
            <SectionLabel>VENDOR PERFORMANCE SCORECARDS</SectionLabel>
            <div className="dept-filter-chips">
              {["ALL", "water_supply", "road_maintenance", "electrical_engineering", "public_works"].map((dept) => (
                <button
                  key={dept}
                  className={`chip-btn ${selectedDept === dept ? "active" : ""}`}
                  onClick={() => setSelectedDept(dept)}
                >
                  {dept.replace(/_/g, " ").toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          {loading ? (
            <div className="loading-card">Loading contractor performance scorecards...</div>
          ) : (
            <div className="scorecards-grid">
              {filteredScorecards.map((sc) => (
                <div key={sc.contractor_id} className="scorecard-card">
                  <div className="scorecard-header">
                    <div>
                      <span className="contractor-id">{sc.contractor_id}</span>
                      <h3 className="contractor-name">{sc.contractor_name}</h3>
                      <span className="contractor-dept">{sc.department.replace(/_/g, " ").toUpperCase()}</span>
                    </div>
                    <div className="score-badge-box">
                      <span className="score-num">{sc.composite_performance_score}</span>
                      <span className="score-max">/100</span>
                      <span
                        className={`tier-tag ${
                          sc.performance_tier === "TIER_1_EXCELLENT"
                            ? "tier-1"
                            : sc.performance_tier === "TIER_2_GOOD"
                            ? "tier-2"
                            : "tier-3"
                        }`}
                      >
                        {sc.performance_tier.replace(/_/g, " ")}
                      </span>
                    </div>
                  </div>

                  <div className="metrics-bars-box">
                    <div className="metric-row">
                      <div className="metric-header-row">
                        <span>Statutory SLA Compliance</span>
                        <strong>{sc.sla_compliance_rate_pct}%</strong>
                      </div>
                      <div className="progress-bar-bg">
                        <div
                          className="progress-bar-fill good"
                          style={{ width: `${Math.min(100, sc.sla_compliance_rate_pct)}%` }}
                        />
                      </div>
                    </div>

                    <div className="metric-row">
                      <div className="metric-header-row">
                        <span>Mean Time to Resolution (MTTR)</span>
                        <strong>{sc.mean_time_to_resolution_hours} hrs</strong>
                      </div>
                      <div className="progress-bar-bg">
                        <div
                          className="progress-bar-fill neutral"
                          style={{ width: `${Math.min(100, (sc.mean_time_to_resolution_hours / 36) * 100)}%` }}
                        />
                      </div>
                    </div>

                    <div className="metric-row">
                      <div className="metric-header-row">
                        <span>Citizen Dispute Rate</span>
                        <strong className={sc.dispute_rate_pct > 10 ? "text-warn" : ""}>
                          {sc.dispute_rate_pct}% ({sc.dispute_count} cases)
                        </strong>
                      </div>
                      <div className="progress-bar-bg">
                        <div
                          className={`progress-bar-fill ${sc.dispute_rate_pct > 10 ? "danger" : "good"}`}
                          style={{ width: `${Math.min(100, sc.dispute_rate_pct * 5)}%` }}
                        />
                      </div>
                    </div>
                  </div>

                  <div className="scorecard-footer">
                    <span>
                      Total Completed Jobs: <strong>{sc.completed_jobs} / {sc.total_assigned_jobs}</strong>
                    </span>
                    <span>
                      SLA Compliant: <strong>{sc.sla_compliant_jobs}</strong>
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
      <Footer />

      <style jsx>{`
        .analytics-shell {
          max-width: 1300px;
          margin: 0 auto;
          padding: 2.5rem 1.5rem;
          display: flex;
          flex-direction: column;
          gap: 2rem;
        }
        .analytics-header {
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
        .analytics-header h1 {
          font-size: 2rem;
          font-weight: 800;
          color: var(--color-text-primary, #0f172a);
          margin: 0 0 0.5rem 0;
        }
        .analytics-subhead {
          font-size: 0.95rem;
          color: var(--color-text-secondary, #475569);
          max-width: 750px;
          line-height: 1.5;
          margin: 0;
        }
        .kpi-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
          gap: 1.25rem;
        }
        .kpi-card {
          background: var(--color-bg-primary, #ffffff);
          border: 1px solid var(--color-border, #e2e8f0);
          border-radius: 12px;
          padding: 1.25rem 1.5rem;
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }
        .kpi-label {
          font-size: 0.8rem;
          font-weight: 600;
          color: var(--color-text-secondary, #64748b);
          text-transform: uppercase;
          letter-spacing: 0.04em;
        }
        .kpi-value-row {
          display: flex;
          align-items: baseline;
          justify-content: space-between;
          gap: 0.75rem;
        }
        .kpi-number {
          font-size: 1.85rem;
          font-weight: 800;
          color: var(--color-text-primary, #0f172a);
        }
        .kpi-subtext {
          font-size: 0.75rem;
          color: var(--color-text-secondary, #64748b);
          margin: 0;
        }
        .contractors-section {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }
        .section-title-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 1rem;
          flex-wrap: wrap;
        }
        .dept-filter-chips {
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
        .scorecards-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
          gap: 1.25rem;
        }
        .scorecard-card {
          background: var(--color-bg-primary, #ffffff);
          border: 1px solid var(--color-border, #e2e8f0);
          border-radius: 12px;
          padding: 1.5rem;
          display: flex;
          flex-direction: column;
          gap: 1.25rem;
        }
        .scorecard-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 1rem;
        }
        .contractor-id {
          font-size: 0.75rem;
          font-family: monospace;
          color: var(--color-text-secondary, #64748b);
          display: block;
          margin-bottom: 0.2rem;
        }
        .contractor-name {
          font-size: 1.15rem;
          font-weight: 700;
          color: var(--color-text-primary, #0f172a);
          margin: 0 0 0.25rem 0;
        }
        .contractor-dept {
          font-size: 0.75rem;
          font-weight: 700;
          color: var(--color-brand, #2563eb);
        }
        .score-badge-box {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          gap: 0.25rem;
        }
        .score-num {
          font-size: 1.85rem;
          font-weight: 800;
          color: var(--color-text-primary, #0f172a);
        }
        .score-max {
          font-size: 0.8rem;
          color: var(--color-text-secondary, #64748b);
          margin-top: -0.4rem;
        }
        .tier-tag {
          font-size: 0.65rem;
          font-weight: 700;
          padding: 0.2rem 0.5rem;
          border-radius: 4px;
          text-transform: uppercase;
        }
        .tier-1 {
          background: rgba(16, 185, 129, 0.15);
          color: #059669;
        }
        .tier-2 {
          background: rgba(37, 99, 235, 0.15);
          color: #2563eb;
        }
        .tier-3 {
          background: rgba(239, 68, 68, 0.15);
          color: #dc2626;
        }
        .metrics-bars-box {
          display: flex;
          flex-direction: column;
          gap: 0.85rem;
        }
        .metric-row {
          display: flex;
          flex-direction: column;
          gap: 0.3rem;
        }
        .metric-header-row {
          display: flex;
          justify-content: space-between;
          font-size: 0.8rem;
          color: var(--color-text-secondary, #475569);
        }
        .progress-bar-bg {
          height: 6px;
          background: var(--color-bg-secondary, #f1f5f9);
          border-radius: 999px;
          overflow: hidden;
        }
        .progress-bar-fill {
          height: 100%;
          border-radius: 999px;
        }
        .progress-bar-fill.good {
          background: #10b981;
        }
        .progress-bar-fill.neutral {
          background: #3b82f6;
        }
        .progress-bar-fill.danger {
          background: #ef4444;
        }
        .scorecard-footer {
          border-top: 1px solid var(--color-border, #f1f5f9);
          padding-top: 0.75rem;
          display: flex;
          justify-content: space-between;
          font-size: 0.8rem;
          color: var(--color-text-secondary, #64748b);
        }
        .loading-card {
          padding: 3rem;
          text-align: center;
          background: var(--color-bg-primary, #ffffff);
          border: 1px solid var(--color-border, #e2e8f0);
          border-radius: 12px;
          color: var(--color-text-secondary, #64748b);
        }
        .text-warn {
          color: #dc2626;
        }
      `}</style>
    </>
  );
}
