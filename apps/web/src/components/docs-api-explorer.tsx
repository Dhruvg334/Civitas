"use client";

import { useState } from "react";

interface Endpoint {
  method: "GET" | "POST" | "PATCH";
  path: string;
  title: string;
  summary: string;
  authRequired: boolean;
  requestBody?: string;
  responseSample: string;
  parameters?: Array<{ name: string; type: string; required: boolean; description: string }>;
}

const ENDPOINTS: Endpoint[] = [
  {
    method: "POST",
    path: "/api/v1/reports",
    title: "Submit Citizen Report",
    summary: "Accepts multimodal citizen report (text, media URLs, GPS coordinates) and initializes evidence validation.",
    authRequired: false,
    requestBody: JSON.stringify(
      {
        description: "Water leaking heavily from main pipe near DAV school gate. Road is flooded.",
        category: "water_leakage",
        latitude: 20.29614,
        longitude: 85.82451,
        ward: "Ward 12",
        media_urls: ["https://civitas.local/media/leak_photo_01.jpg"],
      },
      null,
      2
    ),
    responseSample: JSON.stringify(
      {
        success: true,
        data: {
          report_id: "RPT-103",
          status: "RECEIVED",
          cluster_id: "INC-0241",
          tracking_url: "/incidents/INC-0241",
          created_at: "2026-08-15T11:42:00Z",
        },
      },
      null,
      2
    ),
    parameters: [
      { name: "description", type: "string", required: true, description: "Raw citizen text report" },
      { name: "latitude", type: "float", required: true, description: "WGS84 latitude coordinate" },
      { name: "longitude", type: "float", required: true, description: "WGS84 longitude coordinate" },
      { name: "ward", type: "string", required: false, description: "Municipal ward identifier" },
    ],
  },
  {
    method: "GET",
    path: "/api/v1/incidents/{incident_id}",
    title: "Get Incident Dossier",
    summary: "Retrieves complete evidence dossier, ML classification, retrieved policy references, and work order.",
    authRequired: false,
    responseSample: JSON.stringify(
      {
        success: true,
        data: {
          incident_id: "INC-0241",
          category: "water_leakage",
          priority: "P1",
          status: "WAITING_FOR_REVIEW",
          reports_count: 3,
          routing: {
            primary_department: "Water Supply & Drainage",
            secondary_department: "Traffic Control",
          },
          policy_grounding: {
            retrieved_playbooks: ["PLAY-WATER-01", "ROUTE-WATER-02"],
            grounded: true,
          },
          work_order: {
            id: "WO-0241-A",
            summary: "Inspect and isolate water main leak; secure school crossing.",
            estimated_hours: "8-14",
          },
        },
      },
      null,
      2
    ),
    parameters: [
      { name: "incident_id", type: "string", required: true, description: "Canonical incident identifier (e.g. INC-0241)" },
    ],
  },
  {
    method: "POST",
    path: "/api/v1/workflows/{workflow_id}/review",
    title: "Submit Supervisor Review Action",
    summary: "Executes human authorization checkpoint (approve, edit, reroute, or reject) and resumes LangGraph thread.",
    authRequired: true,
    requestBody: JSON.stringify(
      {
        action: "approve",
        reviewer_id: "REV-SUPERVISOR-04",
        notes: "Verified school proximity. Work order dispatched to field crew.",
        modifications: null,
      },
      null,
      2
    ),
    responseSample: JSON.stringify(
      {
        success: true,
        data: {
          workflow_id: "WF-DEMO-0241",
          thread_id: "thread-water-0241",
          action_applied: "approve",
          work_order_state: "ISSUED",
          resident_notified: true,
        },
      },
      null,
      2
    ),
    parameters: [
      { name: "workflow_id", type: "string", required: true, description: "Active workflow execution ID" },
    ],
  },
  {
    method: "POST",
    path: "/api/v1/ml/analyze",
    title: "Internal ML & Geospatial Analysis Bridge",
    summary: "Executes vision zero-shot classification, DBSCAN spatial clustering, and deterministic risk calculation.",
    authRequired: true,
    requestBody: JSON.stringify(
      {
        report_id: "RPT-103",
        media_cases: ["photo"],
        coordinates: [20.29614, 85.82451],
      },
      null,
      2
    ),
    responseSample: JSON.stringify(
      {
        success: true,
        data: {
          primary_category: "water_leakage",
          confidence: 0.89,
          severity_score: 78,
          priority_level: "P1",
          duplicate_candidates: ["RPT-101", "RPT-102"],
          cluster_id: "INC-0241",
        },
      },
      null,
      2
    ),
  },
  {
    method: "GET",
    path: "/api/v1/public/incidents.geojson",
    title: "Public GeoJSON Transparency Feed",
    summary: "Publishes real-time RFC 7946 GeoJSON FeatureCollection with bounded ±25m Gaussian spatial perturbation and automated PII scrubbing.",
    authRequired: false,
    responseSample: JSON.stringify(
      {
        type: "FeatureCollection",
        features: [
          {
            type: "Feature",
            geometry: { type: "Point", coordinates: [85.82472, 20.29621] },
            properties: {
              incident_id: "INC-0241",
              category: "water_leakage",
              status: "WAITING_FOR_REVIEW",
              reported_at: "2026-08-20T08:30:00Z",
              description_sanitized: "High-pressure potable water main leak [ADDRESS_REDACTED] near school gate.",
              h3_hex_cell: "8860b29849fffff",
              assigned_department: "water_supply",
              privacy_preserved: true,
            },
          },
        ],
      },
      null,
      2
    ),
    parameters: [
      { name: "limit", type: "integer", required: false, description: "Maximum number of GeoJSON features to return (default 200, max 1000)" },
    ],
  },
  {
    method: "GET",
    path: "/api/v1/public/incidents.csv",
    title: "Public Open Data CSV Stream",
    summary: "Exports sanitized civic incident records as a streamable tabular CSV for civic researchers and urban planners.",
    authRequired: false,
    responseSample: "incident_id,category,status,reported_at,sanitized_description,h3_hex_cell,assigned_department\nINC-0241,water_leakage,WAITING_FOR_REVIEW,2026-08-20T08:30:00Z,\"High-pressure potable water main leak [ADDRESS_REDACTED]\",8860b29849fffff,water_supply",
    parameters: [
      { name: "limit", type: "integer", required: false, description: "Maximum number of rows to export (default 500, max 5000)" },
    ],
  },
  {
    method: "GET",
    path: "/api/v1/analytics/contractors",
    title: "Contractor Performance & SLA Analytics",
    summary: "Returns municipal vendor performance metrics: Mean Time to Resolution (MTTR), statutory SLA compliance %, dispute %, and composite 0–100 scorecards.",
    authRequired: false,
    responseSample: JSON.stringify(
      {
        success: true,
        data: {
          total_contractors: 4,
          scorecards: [
            {
              contractor_id: "CONT-WAT-01",
              contractor_name: "Apex Municipal Dewatering & Pipeline Services",
              department: "water_supply",
              total_assigned_jobs: 48,
              completed_jobs: 46,
              sla_compliant_jobs: 43,
              sla_compliance_rate_pct: 93.5,
              mean_time_to_resolution_hours: 6.4,
              dispute_count: 1,
              dispute_rate_pct: 2.1,
              composite_performance_score: 92.4,
              performance_tier: "TIER_1_EXCELLENT",
            },
          ],
        },
      },
      null,
      2
    ),
  },
  {
    method: "GET",
    path: "/api/v1/work-orders/batches",
    title: "Spatial Work Order Crew Batching",
    summary: "Clusters open work orders by crew specialty and spatial H3 hexagonal grid cells to optimize travel routes and minimize mobilization costs.",
    authRequired: false,
    responseSample: JSON.stringify(
      {
        success: true,
        data: {
          total_bundles: 2,
          bundles: [
            {
              bundle_id: "BUNDLE-CREW-001",
              crew_type: "Water Main & Dewatering Specialist Crew",
              target_hex_cell: "8860b29849fffff",
              work_order_ids: ["WO-0241-A", "WO-0235-B"],
              total_duration_hours: 9.0,
              total_cost_inr: 28450.0,
              total_cost_usd: 328.9,
              waypoints: [
                {
                  work_order_id: "WO-0241-A",
                  incident_id: "INC-0241",
                  latitude: 20.29614,
                  longitude: 85.82451,
                  category: "water_leakage",
                  estimated_hours: 4.5,
                },
              ],
            },
          ],
        },
      },
      null,
      2
    ),
  },
  {
    method: "POST",
    path: "/api/v1/work-orders/boq-estimate",
    title: "Schedule of Rates (SOR) BOQ Costing",
    summary: "Calculates material tonnage, machinery operating hours, labor rates, and total estimated repair costs in INR and USD.",
    authRequired: false,
    requestBody: JSON.stringify(
      {
        category: "pothole_road_damage",
        defect_area_cm2: 2500,
        defect_depth_mm: 75,
        is_emergency: true,
      },
      null,
      2
    ),
    responseSample: JSON.stringify(
      {
        success: true,
        data: {
          category: "pothole_road_damage",
          defect_area_m2: 0.25,
          defect_depth_cm: 7.5,
          subtotal_inr: 14850.0,
          contingency_inr: 2227.5,
          total_estimated_cost_inr: 17077.5,
          total_estimated_cost_usd: 197.4,
          estimated_duration_hours: 4.0,
          line_items: [
            {
              item_code: "SOR-RDS-204",
              description: "Dense Bituminous Macadam (DBM) Hot Mix Compaction",
              unit: "tonnes",
              quantity: 0.55,
              unit_rate_inr: 6500.0,
              total_cost_inr: 3575.0,
            },
          ],
        },
      },
      null,
      2
    ),
  },
  {
    method: "GET",
    path: "/api/v1/resolutions/{incident_id}/certificate",
    title: "Cryptographic Municipal Audit Certificate",
    summary: "Fetches official digital audit certificate with verifiable SHA-256 digest sealing the end-to-end incident lifecycle evidence trail.",
    authRequired: false,
    responseSample: JSON.stringify(
      {
        success: true,
        data: {
          certificate_id: "CERT-CIVITAS-0241-E9F4A8C1",
          incident_id: "INC-0241",
          issued_at: "2026-08-20T12:00:00Z",
          governing_municipality: "Civitas Smart Municipal Corporation Digital Evidence Repository",
          sha256_cryptographic_digest: "e9f4a8c17b5e32049d10a84fb79201ca74319fb9a8321049b78e24c5019d82ae",
          verification_url: "https://civitas-web.vercel.app/incidents/INC-0241/certificate",
        },
      },
      null,
      2
    ),
  },
  {
    method: "GET",
    path: "/api/v1/resolutions/{incident_id}/dispute-status",
    title: "72-Hour Citizen Dispute Window Status",
    summary: "Checks if a resolved incident is within the 72-hour citizen dispute and rebuttal review window.",
    authRequired: false,
    responseSample: JSON.stringify(
      {
        success: true,
        data: {
          incident_id: "INC-0241",
          status: "resolved",
          is_disputable: true,
          resolved_at: "2026-08-20T12:00:00Z",
          dispute_deadline: "2026-08-23T12:00:00Z",
          hours_remaining: 64.0,
        },
      },
      null,
      2
    ),
  },
  {
    method: "POST",
    path: "/api/v1/resolutions/{incident_id}/dispute",
    title: "Submit Citizen Dispute & Reopen Incident",
    summary: "Allows citizens to submit rebuttal descriptions and photographic evidence within 72 hours of closure, automatically transitioning status to reopened_disputed with P1 escalation.",
    authRequired: false,
    requestBody: JSON.stringify(
      {
        dispute_reason: "Water is still leaking actively across the road. The patch was only temporary sandbags.",
        rebuttal_photo_url: "https://civitas-storage.blob.core.windows.net/evidence/rebuttal-0241.jpg",
      },
      null,
      2
    ),
    responseSample: JSON.stringify(
      {
        success: true,
        data: {
          incident_id: "INC-0241",
          previous_status: "resolved",
          new_status: "reopened_disputed",
          dispute_ticket_id: "DISP-0241",
          priority_escalation: "P1_CRITICAL_SUPERVISOR_REVIEW",
          reopened_at: "2026-08-20T15:30:00Z",
        },
      },
      null,
      2
    ),
  },
  {
    method: "POST",
    path: "/api/v1/intake/simulate",
    title: "Omnichannel Intake Simulator",
    summary: "Simulates incoming multimodal messages from WhatsApp Webhooks, Telegram Bot updates, or recorded voice note audio payloads.",
    authRequired: false,
    requestBody: JSON.stringify(
      {
        channel: "whatsapp",
        sender_phone: "+919876543210",
        message_text: "High-pressure potable water main leak near DAV School Gate.",
        latitude: 20.29614,
        longitude: 85.82451,
        media_url: "https://civitas.local/media/leak_01.jpg",
      },
      null,
      2
    ),
    responseSample: JSON.stringify(
      {
        success: true,
        data: {
          channel: "whatsapp",
          report_id: "RPT-SIM-0241",
          status: "ACCEPTED",
          exif_gps_extracted: true,
          device_fingerprint_scrubbed: true,
        },
      },
      null,
      2
    ),
  },
  {
    method: "GET",
    path: "/api/v1/open311/v2/services.json",
    title: "Open311 GeoReport v2 Service Discovery",
    summary: "Returns standard Open311 service definitions (potable water, road potholes, streetlight outages, tree hazards) for municipal interoperability.",
    authRequired: false,
    responseSample: JSON.stringify(
      [
        {
          service_code: "water_leakage",
          service_name: "Water Main Leakage & Pipe Burst",
          description: "Subsurface and surface potable water distribution leaks.",
          metadata: true,
          type: "realtime",
          group: "Infrastructure",
        },
      ],
      null,
      2
    ),
  },
];

export function DocsApiExplorer() {
  const [expandedIndex, setExpandedIndex] = useState<number>(0);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [activeTabMap, setActiveTabMap] = useState<{ [key: number]: "response" | "request" | "params" }>({});

  const handleCopyCurl = (ep: Endpoint, index: number) => {
    const curl = ep.method === "GET"
      ? `curl -X GET "https://api.civitas.civic.local${ep.path}" \\
  -H "Accept: application/json"`
      : `curl -X ${ep.method} "https://api.civitas.civic.local${ep.path}" \\
  -H "Content-Type: application/json" \\
  -d '${ep.requestBody || "{}"}'`;

    navigator.clipboard.writeText(curl);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 3000);
  };

  return (
    <div className="api-explorer-root">
      <div className="api-explorer-header">
        <span className="api-kicker">INTERACTIVE SPECIFICATION</span>
        <h3>Civitas REST API Endpoints</h3>
        <p>
          All endpoints return a typed Civitas Envelope structure. Model outputs, retrieved policy references,
          and human decisions are strictly isolated in schema responses.
        </p>
      </div>

      <div className="endpoints-accordion">
        {ENDPOINTS.map((ep, index) => {
          const isExpanded = expandedIndex === index;
          const activeTab = activeTabMap[index] || (ep.requestBody ? "request" : "response");

          return (
            <div key={ep.path} className={`endpoint-card ${isExpanded ? "expanded" : ""}`}>
              <div
                className="endpoint-summary-bar"
                onClick={() => setExpandedIndex(isExpanded ? -1 : index)}
              >
                <div className="method-path-group">
                  <span className={`method-badge ${ep.method.toLowerCase()}`}>{ep.method}</span>
                  <code className="endpoint-path">{ep.path}</code>
                </div>
                <div className="title-auth-group">
                  <span className="endpoint-title">{ep.title}</span>
                  {ep.authRequired && <span className="auth-badge">AUTH REQUIRED</span>}
                  <span className="toggle-chevron">{isExpanded ? "▲" : "▼"}</span>
                </div>
              </div>

              {isExpanded && (
                <div className="endpoint-details-drawer">
                  <p className="endpoint-desc">{ep.summary}</p>

                  <div className="details-tab-bar">
                    {ep.parameters && (
                      <button
                        className={`tab-btn ${activeTab === "params" ? "active" : ""}`}
                        onClick={() => setActiveTabMap({ ...activeTabMap, [index]: "params" })}
                      >
                        Parameters ({ep.parameters.length})
                      </button>
                    )}
                    {ep.requestBody && (
                      <button
                        className={`tab-btn ${activeTab === "request" ? "active" : ""}`}
                        onClick={() => setActiveTabMap({ ...activeTabMap, [index]: "request" })}
                      >
                        Request Body (JSON)
                      </button>
                    )}
                    <button
                      className={`tab-btn ${activeTab === "response" ? "active" : ""}`}
                      onClick={() => setActiveTabMap({ ...activeTabMap, [index]: "response" })}
                    >
                      Response Envelope
                    </button>
                    <button
                      className="copy-curl-btn"
                      onClick={() => handleCopyCurl(ep, index)}
                    >
                      {copiedIndex === index ? "✓ Copied cURL" : "📋 Copy cURL"}
                    </button>
                  </div>

                  <div className="details-content-box">
                    {activeTab === "params" && ep.parameters && (
                      <div className="params-table-wrap">
                        <table className="params-table">
                          <thead>
                            <tr>
                              <th>Field</th>
                              <th>Type</th>
                              <th>Required</th>
                              <th>Description</th>
                            </tr>
                          </thead>
                          <tbody>
                            {ep.parameters.map((p) => (
                              <tr key={p.name}>
                                <td><code>{p.name}</code></td>
                                <td><span className="type-tag">{p.type}</span></td>
                                <td>{p.required ? <b className="req-yes">Yes</b> : <span className="req-no">No</span>}</td>
                                <td>{p.description}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}

                    {activeTab === "request" && ep.requestBody && (
                      <div className="json-box">
                        <pre><code>{ep.requestBody}</code></pre>
                      </div>
                    )}

                    {activeTab === "response" && (
                      <div className="json-box">
                        <pre><code>{ep.responseSample}</code></pre>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <style jsx>{`
        .api-explorer-root {
          margin: 32px 0 50px;
          border: 1px solid #172019;
          background: #ffffff;
          box-shadow: 4px 4px 0 #172019;
          padding: 28px;
        }
        .api-kicker {
          font-size: 0.65rem;
          font-weight: 900;
          letter-spacing: 0.12em;
          color: #0f5f4f;
          display: block;
          margin-bottom: 4px;
        }
        .api-explorer-header h3 {
          font-size: 1.5rem;
          font-family: Georgia, serif;
          margin: 0 0 8px;
          color: #172019;
        }
        .api-explorer-header p {
          color: #555e54;
          font-size: 0.88rem;
          line-height: 1.6;
          max-width: 720px;
          margin: 0 0 24px;
        }
        .endpoints-accordion {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .endpoint-card {
          border: 1px solid #172019;
          background: #fbf9f4;
          transition: all 0.15s ease;
        }
        .endpoint-card.expanded {
          background: #ffffff;
          box-shadow: 3px 3px 0 #172019;
        }
        .endpoint-summary-bar {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 14px 18px;
          cursor: pointer;
          user-select: none;
        }
        .method-path-group {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .method-badge {
          padding: 3px 8px;
          font-size: 0.65rem;
          font-weight: 900;
          letter-spacing: 0.08em;
          color: #ffffff;
          border-radius: 4px;
        }
        .method-badge.get {
          background: #0f5f4f;
        }
        .method-badge.post {
          background: #e84d7a;
        }
        .method-badge.patch {
          background: #e3b950;
          color: #172019;
        }
        .endpoint-path {
          font-family: monospace;
          font-size: 0.85rem;
          font-weight: 750;
          color: #172019;
        }
        .title-auth-group {
          display: flex;
          align-items: center;
          gap: 14px;
        }
        .endpoint-title {
          font-size: 0.82rem;
          font-weight: 700;
          color: #555e54;
        }
        .auth-badge {
          font-size: 0.58rem;
          font-weight: 850;
          letter-spacing: 0.08em;
          padding: 2px 6px;
          background: #172019;
          color: #ffffff;
          border-radius: 3px;
        }
        .toggle-chevron {
          font-size: 0.7rem;
          color: #687067;
        }
        .endpoint-details-drawer {
          padding: 18px;
          border-top: 1px solid #e2ded4;
          background: #ffffff;
        }
        .endpoint-desc {
          font-size: 0.85rem;
          color: #495248;
          line-height: 1.55;
          margin: 0 0 16px;
        }
        .details-tab-bar {
          display: flex;
          align-items: center;
          gap: 8px;
          border-bottom: 1px solid #172019;
          padding-bottom: 8px;
          margin-bottom: 14px;
        }
        .tab-btn {
          padding: 6px 12px;
          border: 1px solid #172019;
          background: #fbf9f4;
          font-size: 0.72rem;
          font-weight: 750;
          cursor: pointer;
          border-radius: 4px;
          transition: all 0.15s ease;
        }
        .tab-btn.active {
          background: #172019;
          color: #ffffff;
        }
        .copy-curl-btn {
          margin-left: auto;
          padding: 6px 12px;
          border: 1px solid #0f5f4f;
          background: #dce8dd;
          color: #0f5f4f;
          font-size: 0.72rem;
          font-weight: 800;
          border-radius: 4px;
          cursor: pointer;
        }
        .params-table-wrap {
          overflow-x: auto;
        }
        .params-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 0.78rem;
        }
        .params-table th {
          text-align: left;
          padding: 8px 10px;
          background: #fbf9f4;
          border-bottom: 1px solid #172019;
          font-size: 0.68rem;
          letter-spacing: 0.08em;
          color: #687067;
        }
        .params-table td {
          padding: 10px;
          border-bottom: 1px solid #e2ded4;
        }
        .params-table code {
          font-weight: 750;
          color: #e84d7a;
        }
        .type-tag {
          font-size: 0.65rem;
          background: #fbf9f4;
          padding: 2px 6px;
          border: 1px solid #e2ded4;
        }
        .req-yes {
          color: #e84d7a;
          font-size: 0.7rem;
        }
        .req-no {
          color: #687067;
          font-size: 0.7rem;
        }
        .json-box pre {
          margin: 0;
          padding: 16px;
          background: #172019;
          color: #fbf9f4;
          border-radius: 6px;
          font-size: 0.78rem;
          font-family: monospace;
          overflow-x: auto;
          line-height: 1.5;
        }
        @media (max-width: 768px) {
          .endpoint-summary-bar {
            flex-direction: column;
            align-items: flex-start;
            gap: 8px;
          }
          .title-auth-group {
            width: 100%;
            justify-content: space-between;
          }
        }
      `}</style>
    </div>
  );
}
