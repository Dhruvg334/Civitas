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
