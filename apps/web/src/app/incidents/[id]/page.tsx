"use client";

import { use, useState } from "react";
import { ReviewPanel } from "@/components/review-panel";
import { ResolutionSlider } from "@/components/resolution-slider";
import { AgentTraceVisualizer } from "@/components/agent-trace-visualizer";
import { ErrorBoundary } from "@/components/error-boundary";
import { Nav, Status, Footer } from "@/components/site";
import { MiniMap } from "@/components/civic-visuals";

interface IncidentData {
  title: string;
  priority: "P1" | "P2" | "P3";
  ward: string;
  department: string;
  category: string;
  landmark: string;
  playbook: string;
  reportsCount: number;
  observedText: string;
  reportedText: string;
  inferredText: string;
  workOrderDesc: string;
}

const INCIDENT_CATALOG: Record<string, IncidentData> = {
  "INC-0241": {
    title: "School Crossing Water Main Leakage",
    priority: "P1",
    ward: "WARD 12 · UNIT 8",
    department: "Water Supply & Drainage + Traffic Control",
    category: "water_leakage",
    landmark: "14m from DAV Public School Gate (Active School Buffer)",
    playbook: "PLAY-WATER-01 (Municipal Main Line Rupture Protocol)",
    reportsCount: 3,
    observedText: "Standing water crossing active school corridor and high-pressure subsurface fissure.",
    reportedText: "Bicycles slipping near school gate during morning arrival; road flooded.",
    inferredText: "Likely 150mm ductile distribution line rupture requiring collar clamping.",
    workOrderDesc: "Isolate sub-zone isolation valve V-12, deploy mechanical backhoe for excavation, install ductile iron repair sleeve, and backfill with asphalt cold patch.",
  },
  "INC-0240": {
    title: "Park Road Snapped Banyan Tree Branch",
    priority: "P2",
    ward: "WARD 12 · PARK SECTOR",
    department: "Parks & Urban Forestry",
    category: "fallen_tree",
    landmark: "Park Road, opposite Ward Community Center",
    playbook: "PLAY-FORESTRY-03 (Obstruction Clearing & Heavy Timber Removal)",
    reportsCount: 2,
    observedText: "Overhead timber debris across outbound lane; asphalt surface scratched.",
    reportedText: "Branch snapped in storm; blocking school vans.",
    inferredText: "Heavy banyan branch under mechanical tension; chainsaw crew required.",
    workOrderDesc: "Deploy boom crane truck and 2 chainsaw operators to section timber into 1m logs, clear road lane, and chip residue.",
  },
  "INC-0238": {
    title: "East Gate Luminaire & Dark Corridor Fault",
    priority: "P3",
    ward: "WARD 12 · EAST GATE JUNCTION",
    department: "Electrical & Public Lighting",
    category: "streetlight",
    landmark: "East Gate Commercial Crossroad, Poles #104-106",
    playbook: "PLAY-LIGHT-02 (Feeder Circuit Diagnostic & Luminaire Repair)",
    reportsCount: 1,
    observedText: "Zero luminaire output across 3 consecutive poles during night cycle.",
    reportedText: "Dark for 3 consecutive nights; pedestrians cannot see pavement.",
    inferredText: "Underground feeder cable short or burnt ballast relay.",
    workOrderDesc: "Test continuity of feeder circuit FC-08, replace blown 250W LED driver modules on Poles 104-106, and verify photocell timer.",
  },
  "INC-0235": {
    title: "Hospital Axis Stormwater Drain Blockage",
    priority: "P1",
    ward: "WARD 08 · HOSPITAL SECTOR",
    department: "Drainage & Sewerage Board",
    category: "drainage_blockage",
    landmark: "Ambulance Access Bay, Capital Hospital Entrance",
    playbook: "PLAY-DRAIN-04 (Emergency Stormwater Desilting)",
    reportsCount: 4,
    observedText: "Storm drain inlet completely submerged by refuse; backflow onto ambulance ramp.",
    reportedText: "Water entering emergency bay; vehicles slowing down.",
    inferredText: "Sediment and plastic obstruction inside 600mm reinforced concrete pipe.",
    workOrderDesc: "Deploy high-pressure water jetting vacuum truck VJ-04 to flush obstruction, clear inlet grate, and install sediment trap.",
  },
};

export default function Incident({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const incidentId = (id || "INC-0241").toUpperCase();
  const incident: IncidentData = INCIDENT_CATALOG[incidentId] || {
    title: `Civic Incident ${incidentId}`,
    priority: "P2",
    ward: "WARD 12 · MUNICIPAL ZONE",
    department: "Public Works & Infrastructure",
    category: "general_hazard",
    landmark: "Ward 12 Municipal Corridor (PostGIS Georeferenced)",
    playbook: "PLAY-GEN-01 (Standard Civic Hazard Resolution)",
    reportsCount: 2,
    observedText: "Visual anomaly detected on municipal infrastructure asset.",
    reportedText: "Citizen report logged with evidence attachment.",
    inferredText: "Standard field inspection protocol recommended.",
    workOrderDesc: "Deploy district inspection crew to assess site and implement corrective action.",
  };
  const [activeTab, setActiveTab] = useState<string>("evidence");

  return (
    <>
      <Nav />
      <main className="incident-shell">
        {/* INCIDENT DOSSIER TOP BANNER */}
        <header className="incident-top-header">
          <div className="incident-title-block">
            <div className="incident-tag-row">
              <span className={`prio-tag ${incident.priority.toLowerCase()}`}>
                {incident.priority} {incident.priority === "P1" ? "CRITICAL" : incident.priority === "P2" ? "MODERATE" : "INSPECTION"}
              </span>
              <span className="incident-id-badge">{incidentId}</span>
              <span className="ward-tag">{incident.ward}</span>
            </div>
            <h1 className="incident-main-heading">{incident.title}</h1>
            <p className="incident-sub-desc">
              {incident.reportsCount} related resident reports (photo, text, video) consolidated via PostGIS spatial clustering and CLIP zero-shot vision classification.
            </p>
          </div>

          <div className="incident-state-card">
            <span className="state-label">WORKFLOW STATE</span>
            <Status tone={incident.priority === "P1" ? "warn" : "good"}>WAITING_FOR_REVIEW</Status>
            <div className="trace-id-box">
              <span>TRACE: CIV-TR-{incidentId.slice(-4)}</span>
              <span>THREAD: th-{incident.category}-{incidentId.slice(-4)}</span>
            </div>
          </div>
        </header>

        {/* SECTION NAVIGATION TABS */}
        <nav className="incident-subnav-tabs" aria-label="Incident sections">
          {[
            { id: "evidence", label: "01 Multimodal Evidence" },
            { id: "gis", label: "02 GIS Map & Proximity" },
            { id: "assessment", label: "03 Risk & Severity" },
            { id: "routing", label: "04 Work Order Plan" },
            { id: "resolution", label: "05 Resolution Check" },
            { id: "trace", label: "06 Agent Trace" },
          ].map((tab) => (
            <a
              key={tab.id}
              href={`#${tab.id}`}
              className={`tab-anchor ${activeTab === tab.id ? "active" : ""}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </a>
          ))}
        </nav>

        <div className="incident-two-column-layout">
          {/* LEFT: INCIDENT DOSSIER SECTIONS */}
          <div className="incident-dossier-col">
            {/* SECTION 01: EVIDENCE */}
            <section id="evidence" className="dossier-card">
              <div className="dossier-card-header">
                <span className="section-pill">01</span>
                <div>
                  <h2>Multimodal Evidence & Claims Breakdown</h2>
                  <p>Observed visual evidence is strictly separated from citizen reported assertions.</p>
                </div>
              </div>

              <div className="evidence-grid-triad">
                <article className="evidence-triad-card obs">
                  <span className="triad-kicker obs">OBSERVED EVIDENCE (MEDIA)</span>
                  <b>Standing water crossing active school corridor</b>
                  <p>Computer vision verified liquid surface pooling and pedestrian hazard across road (frame-002).</p>
                </article>

                <article className="evidence-triad-card rep">
                  <span className="triad-kicker rep">CITIZEN REPORTED</span>
                  <b>Bicycles slipping near school gate during arrival</b>
                  <p>Citizen text claim preserved verbatim as safety landmark context.</p>
                </article>

                <article className="evidence-triad-card inf">
                  <span className="triad-kicker inf">INFERRED ATTRIBUTION</span>
                  <b>Likely underground distribution main rupture</b>
                  <p>Requires physical acoustic leak detector before confirmation by field inspector.</p>
                </article>
              </div>

              <div className="clustered-sources-list">
                <div className="source-row">
                  <span className="source-tag">REPORT A</span>
                  <span>Geotagged Photo (20.2961° N, 85.8245° E) · Submitted 12m ago</span>
                </div>
                <div className="source-row">
                  <span className="source-tag">REPORT B</span>
                  <span>Citizen Text Description (&quot;Water burst beside DAV school gate&quot;)</span>
                </div>
                <div className="source-row">
                  <span className="source-tag">REPORT C</span>
                  <span>5s Video Clip · Citizen category corrected from Pothole → Water Leak</span>
                </div>
              </div>
            </section>

            {/* SECTION 02: GIS LOCATION MAP */}
            <section id="gis" className="dossier-card">
              <div className="dossier-card-header">
                <span className="section-pill">02</span>
                <div>
                  <h2>GIS Geospatial Proximity & Hazard Buffer</h2>
                  <p>PostGIS 3.4 spatial calculations indicate active hazard within school safety zone.</p>
                </div>
              </div>

              <div className="dossier-map-wrap">
                <MiniMap selectedIncidentId={incidentId} height="400px" />
              </div>

              <div className="gis-metrics-row">
                <div className="gis-metric">
                  <span>NEAREST LANDMARK</span>
                  <b>DAV Public School (14m)</b>
                </div>
                <div className="gis-metric">
                  <span>HAZARD ZONE</span>
                  <b className="p1-text">Inside 500m Safety Buffer</b>
                </div>
                <div className="gis-metric">
                  <span>POSTGIS CLUSTER RADIUS</span>
                  <b>38m Spatial Dispersion</b>
                </div>
              </div>
            </section>

            {/* SECTION 03: RISK & SEVERITY */}
            <section id="assessment" className="dossier-card">
              <div className="dossier-card-header">
                <span className="section-pill">03</span>
                <div>
                  <h2>Severity & Priority Intelligence</h2>
                  <p>Deterministic models evaluate physical infrastructure impact independently from response urgency.</p>
                </div>
              </div>

              <div className="assessment-metrics-grid">
                <div className="metric-box">
                  <span>PRIMARY CATEGORY</span>
                  <b>Water Leakage</b>
                  <small>Auto-corrected from citizen input</small>
                </div>
                <div className="metric-box">
                  <span>CLUSTER SIMILARITY</span>
                  <b>0.84 (Threshold 0.72)</b>
                  <small>3 convergent reports</small>
                </div>
                <div className="metric-box">
                  <span>SEVERITY SCORE</span>
                  <b className="p1-text">78 / 100 · High</b>
                  <small>Active road flooding hazard</small>
                </div>
                <div className="metric-box">
                  <span>PRIORITY LEVEL</span>
                  <b className="p1-text">P1 · Critical</b>
                  <small>School proximity + rush hour</small>
                </div>
              </div>
            </section>

            {/* SECTION 04: ROUTING & WORK ORDER */}
            <section id="routing" className="dossier-card">
              <div className="dossier-card-header">
                <span className="section-pill">04</span>
                <div>
                  <h2>Policy-Grounded Routing & Work Order Plan</h2>
                  <p>Operational work order compiled from municipal playbooks without hallucinated promises.</p>
                </div>
              </div>

              <div className="jurisdiction-flow-bar">
                <div className="flow-dept">
                  <span>PRIMARY JURISDICTION</span>
                  <b>Water Supply & Drainage Dept</b>
                </div>
                <span className="flow-arrow">→</span>
                <div className="flow-dept">
                  <span>SUPPORT COORDINATION</span>
                  <b>Traffic Control Division</b>
                </div>
              </div>

              <div className="work-order-box">
                <div className="wo-header">
                  <span className="wo-id">WORK ORDER DRAFT (WO-0241-A)</span>
                  <span className="wo-sla">Target Window: 8 – 14 Hours</span>
                </div>
                <h3>Isolate active pipe rupture and secure pedestrian school crossing.</h3>
                <ul className="wo-tasks">
                  <li>Confirm exact leak source near East Gate valve box.</li>
                  <li>Erect protective barricades around 50m flooded perimeter.</li>
                  <li>Coordinate with Traffic Control for school bus routing.</li>
                  <li>Backfill excavation and re-surface asphalt after pipe clamping.</li>
                </ul>
                <div className="wo-footer">
                  <b>Grounded by Municipal Policy PLAY-WATER-01 & ROUTE-WATER-02</b>
                  <span>Requires Supervisor Authorization</span>
                </div>
              </div>
            </section>

            {/* SECTION 05: RESOLUTION VERIFICATION */}
            <section id="resolution" className="dossier-card">
              <div className="dossier-card-header">
                <span className="section-pill">05</span>
                <div>
                  <h2>Before / After Resolution Verification</h2>
                  <p>Visual classification verifies completed field work before ticket closure.</p>
                </div>
              </div>
              <ErrorBoundary>
                <ResolutionSlider />
              </ErrorBoundary>
            </section>

            {/* SECTION 06: AGENT TRACE OBSERVABILITY */}
            <section id="trace" className="dossier-card">
              <div className="dossier-card-header">
                <span className="section-pill">06</span>
                <div>
                  <h2>LangGraph Agent Workflow Observability</h2>
                  <p>Inspect node-by-node execution, latency metrics, and critic check states.</p>
                </div>
              </div>
              <ErrorBoundary>
                <AgentTraceVisualizer incidentId={incidentId} />
              </ErrorBoundary>
            </section>
          </div>

          {/* RIGHT: STICKY SUPERVISOR REVIEW ACTION PANEL */}
          <aside className="incident-sidebar-col">
            <div className="sticky-review-panel" id="review">
              <div className="panel-kicker-bar">
                <span>HUMAN-IN-THE-LOOP CHECKPOINT</span>
              </div>
              <ErrorBoundary>
                <ReviewPanel workflowId={`wf-${incidentId.toLowerCase()}`} />
              </ErrorBoundary>
            </div>
          </aside>
        </div>
      </main>
      <Footer />

      <style jsx>{`
        .incident-shell {
          width: min(calc(100% - 40px), 1280px);
          margin: 32px auto 80px;
        }
        .incident-top-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 24px;
          padding-bottom: 24px;
          border-bottom: 2px solid #172019;
          margin-bottom: 20px;
          flex-wrap: wrap;
        }
        .incident-title-block {
          max-width: 800px;
        }
        .incident-tag-row {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
        }
        .prio-tag {
          font-size: 0.62rem;
          font-weight: 900;
          padding: 2px 6px;
          border-radius: 3px;
        }
        .prio-tag.p1 {
          background: #e84d7a;
          color: #ffffff;
        }
        .incident-id-badge {
          font-size: 0.72rem;
          font-weight: 850;
          color: #687067;
        }
        .ward-tag {
          font-size: 0.65rem;
          font-weight: 850;
          background: #dce8dd;
          color: #0f5f4f;
          padding: 2px 6px;
          border-radius: 3px;
        }
        .incident-main-heading {
          font-size: clamp(2.2rem, 4vw, 3.2rem);
          font-family: Georgia, serif;
          margin: 0 0 8px;
          color: #172019;
          line-height: 1.1;
        }
        .incident-sub-desc {
          font-size: 0.95rem;
          color: #555e54;
          margin: 0;
          line-height: 1.55;
        }
        .incident-state-card {
          padding: 14px 18px;
          border: 1px solid #172019;
          background: #ffffff;
          box-shadow: 3px 3px 0 #172019;
          border-radius: 6px;
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .state-label {
          font-size: 0.58rem;
          font-weight: 900;
          letter-spacing: 0.1em;
          color: #687067;
        }
        .trace-id-box {
          display: flex;
          flex-direction: column;
          font-size: 0.65rem;
          font-family: monospace;
          color: #687067;
          border-top: 1px solid #e2ded4;
          padding-top: 6px;
          margin-top: 4px;
        }
        .incident-subnav-tabs {
          display: flex;
          gap: 0;
          border-bottom: 1px solid #172019;
          margin-bottom: 32px;
          overflow-x: auto;
        }
        .tab-anchor {
          padding: 12px 18px;
          border-right: 1px solid #e2ded4;
          font-size: 0.8rem;
          font-weight: 750;
          color: #555e54;
          text-decoration: none;
          white-space: nowrap;
          transition: all 0.15s ease;
        }
        .tab-anchor:first-child {
          border-left: 1px solid #e2ded4;
        }
        .tab-anchor:hover {
          color: #172019;
          background: #fbf9f4;
        }
        .tab-anchor.active {
          color: #ffffff;
          background: #172019;
        }
        .incident-two-column-layout {
          display: grid;
          grid-template-columns: 1fr 380px;
          gap: 36px;
          align-items: start;
        }
        .incident-dossier-col {
          display: flex;
          flex-direction: column;
          gap: 36px;
          min-width: 0;
        }
        .dossier-card {
          border: 2px solid #172019;
          background: #ffffff;
          box-shadow: 4px 4px 0 #172019;
          padding: 28px;
        }
        .dossier-card-header {
          display: flex;
          align-items: flex-start;
          gap: 16px;
          margin-bottom: 24px;
          padding-bottom: 16px;
          border-bottom: 1px solid #e2ded4;
        }
        .section-pill {
          font-size: 0.8rem;
          font-weight: 900;
          color: #0f5f4f;
          font-family: monospace;
          background: #dce8dd;
          width: 32px;
          height: 32px;
          display: grid;
          place-items: center;
          border: 1px solid #0f5f4f;
          border-radius: 4px;
          flex-shrink: 0;
        }
        .dossier-card-header h2 {
          font-size: 1.45rem;
          font-family: Georgia, serif;
          margin: 0 0 4px;
          color: #172019;
        }
        .dossier-card-header p {
          font-size: 0.85rem;
          color: #555e54;
          margin: 0;
        }
        .evidence-grid-triad {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 14px;
          margin-bottom: 20px;
        }
        .evidence-triad-card {
          border: 1px solid #172019;
          background: #fbf9f4;
          padding: 16px;
          border-radius: 4px;
        }
        .triad-kicker {
          font-size: 0.58rem;
          font-weight: 900;
          letter-spacing: 0.08em;
          display: block;
          margin-bottom: 6px;
        }
        .triad-kicker.obs {
          color: #0f5f4f;
        }
        .triad-kicker.rep {
          color: #e84d7a;
        }
        .triad-kicker.inf {
          color: #e3b950;
        }
        .evidence-triad-card b {
          display: block;
          font-size: 0.88rem;
          color: #172019;
          margin-bottom: 6px;
          line-height: 1.35;
        }
        .evidence-triad-card p {
          font-size: 0.78rem;
          color: #687067;
          margin: 0;
          line-height: 1.45;
        }
        .clustered-sources-list {
          display: flex;
          flex-direction: column;
          gap: 6px;
          border-top: 1px solid #e2ded4;
          padding-top: 14px;
        }
        .source-row {
          display: flex;
          align-items: center;
          gap: 10px;
          font-size: 0.78rem;
          color: #555e54;
        }
        .source-tag {
          font-size: 0.62rem;
          font-weight: 900;
          background: #172019;
          color: #ffffff;
          padding: 2px 6px;
          border-radius: 3px;
        }
        .dossier-map-wrap {
          margin-bottom: 16px;
          border: 1px solid #172019;
          overflow: hidden;
        }
        .gis-metrics-row {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 12px;
          background: #fbf9f4;
          border: 1px solid #172019;
          padding: 14px;
        }
        .gis-metric span {
          display: block;
          font-size: 0.58rem;
          font-weight: 900;
          color: #687067;
        }
        .gis-metric b {
          display: block;
          font-size: 0.88rem;
          color: #172019;
          margin-top: 2px;
        }
        .assessment-metrics-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 14px;
        }
        .metric-box {
          border: 1px solid #172019;
          background: #fbf9f4;
          padding: 14px;
        }
        .metric-box span {
          display: block;
          font-size: 0.58rem;
          font-weight: 900;
          color: #687067;
        }
        .metric-box b {
          display: block;
          font-size: 1.05rem;
          color: #172019;
          margin: 4px 0 2px;
        }
        .metric-box small {
          display: block;
          font-size: 0.68rem;
          color: #687067;
        }
        .p1-text {
          color: #e84d7a !important;
        }
        .jurisdiction-flow-bar {
          display: flex;
          align-items: center;
          gap: 16px;
          background: #fbf9f4;
          border: 1px solid #172019;
          padding: 14px 18px;
          margin-bottom: 20px;
        }
        .flow-dept span {
          display: block;
          font-size: 0.58rem;
          font-weight: 900;
          color: #687067;
        }
        .flow-dept b {
          font-size: 0.95rem;
          color: #172019;
        }
        .flow-arrow {
          font-size: 1.2rem;
          color: #0f5f4f;
          font-weight: 900;
        }
        .work-order-box {
          border: 1px solid #172019;
          background: #ffffff;
          padding: 20px;
        }
        .wo-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 10px;
        }
        .wo-id {
          font-size: 0.65rem;
          font-weight: 900;
          letter-spacing: 0.08em;
          color: #0f5f4f;
        }
        .wo-sla {
          font-size: 0.72rem;
          font-weight: 800;
          color: #e84d7a;
        }
        .work-order-box h3 {
          font-size: 1.15rem;
          font-family: Georgia, serif;
          margin: 0 0 14px;
          color: #172019;
        }
        .wo-tasks {
          margin: 0 0 18px 20px;
          padding: 0;
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .wo-tasks li {
          font-size: 0.85rem;
          color: #495248;
        }
        .wo-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
          border-top: 1px solid #e2ded4;
          padding-top: 12px;
          font-size: 0.72rem;
          color: #687067;
        }
        .wo-footer b {
          color: #0f5f4f;
        }
        .incident-sidebar-col {
          position: sticky;
          top: 90px;
        }
        .sticky-review-panel {
          border: 2px solid #172019;
          background: #ffffff;
          box-shadow: 6px 6px 0 #172019;
        }
        .panel-kicker-bar {
          background: #172019;
          color: #ffffff;
          padding: 8px 14px;
          font-size: 0.62rem;
          font-weight: 900;
          letter-spacing: 0.1em;
        }
        @media (max-width: 1050px) {
          .incident-two-column-layout {
            grid-template-columns: 1fr;
          }
          .incident-sidebar-col {
            position: static;
          }
          .evidence-grid-triad {
            grid-template-columns: 1fr;
          }
          .assessment-metrics-grid {
            grid-template-columns: 1fr 1fr;
          }
        }
      `}</style>
    </>
  );
}
