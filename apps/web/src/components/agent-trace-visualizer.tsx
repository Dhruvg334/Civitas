"use client";

import { useState } from "react";

export interface TraceNode {
  id: string;
  name: string;
  layer: "Orchestration" | "ML Vision" | "Knowledge Grounding" | "Risk Engine" | "Critic Check" | "Human Review";
  status: "completed" | "active" | "waiting" | "passed";
  latencyMs: number;
  tokensUsed?: number;
  inputSnippet: string;
  outputSnippet: string;
  criticValidation?: {
    unsupportedClaims: boolean;
    validPolicyRefs: boolean;
    confidenceBasis: string;
  };
}

const DEFAULT_NODES: TraceNode[] = [
  {
    id: "node-1",
    name: "multimodal_intake_extractor",
    layer: "Orchestration",
    status: "completed",
    latencyMs: 184,
    tokensUsed: 420,
    inputSnippet: '{"report_ids": ["RPT-A", "RPT-B", "RPT-C"], "location": [20.2961, 85.8245]}',
    outputSnippet: '{"observable_facts": ["standing water on road", "near school gate"], "source_claims_preserved": true}',
  },
  {
    id: "node-2",
    name: "vision_clip_classifier",
    layer: "ML Vision",
    status: "completed",
    latencyMs: 310,
    inputSnippet: '{"media_case": "short_video", "frames": ["frame-002", "frame-004"]}',
    outputSnippet: '{"primary_category": "water_leakage", "secondary": ["road_flooding"], "confidence": 0.89}',
  },
  {
    id: "node-3",
    name: "duplicate_candidate_retriever",
    layer: "Orchestration",
    status: "completed",
    latencyMs: 95,
    inputSnippet: '{"radius_metres": 500, "time_window_hours": 72}',
    outputSnippet: '{"duplicate_score": 0.84, "merged_reports": 3, "cluster_id": "INC-0241"}',
  },
  {
    id: "node-4",
    name: "policy_grounding_retriever",
    layer: "Knowledge Grounding",
    status: "completed",
    latencyMs: 215,
    tokensUsed: 650,
    inputSnippet: '{"category": "water_leakage", "hazards": ["slip_risk", "traffic_disruption"]}',
    outputSnippet: '{"retrieved": ["PLAY-WATER-01", "ROUTE-WATER-02"], "grounded": true}',
  },
  {
    id: "node-5",
    name: "critic_hallucination_gate",
    layer: "Critic Check",
    status: "passed",
    latencyMs: 140,
    tokensUsed: 310,
    inputSnippet: '{"draft_work_order": "WO-0241-A", "retrieved_policies": ["PLAY-WATER-01"]}',
    outputSnippet: '{"critic_passed": true, "unsupported_claims": false, "policy_refs_valid": true}',
    criticValidation: {
      unsupportedClaims: false,
      validPolicyRefs: true,
      confidenceBasis: "Grounding verified against PLAY-WATER-01.",
    },
  },
  {
    id: "node-6",
    name: "human_approval_interrupt",
    layer: "Human Review",
    status: "waiting",
    latencyMs: 0,
    inputSnippet: '{"incident_id": "INC-0241", "work_order_id": "WO-0241-A"}',
    outputSnippet: '{"state": "WAITING_FOR_REVIEW", "checkpoint_thread": "thread-0241"}',
  },
];

export function AgentTraceVisualizer({
  incidentId = "INC-0241",
  workflowId = "WF-DEMO-0241",
  currentStep,
}: {
  incidentId?: string;
  workflowId?: string;
  currentStep?: string;
}) {
  const [selectedNode, setSelectedNode] = useState<TraceNode>(DEFAULT_NODES[0]);

  return (
    <div className="trace-visualizer">
      <div className="visualizer-header">
        <div>
          <span className="kicker">AGENTIC OBSERVABILITY · {incidentId} ({workflowId})</span>
          <h3>Illustrative Workflow Execution Trace</h3>
        </div>
        <div className="trace-metrics">
          <span>Mode: <b>Illustrative Trace</b></span>
          <span>Step: <b>{currentStep || "active"}</b></span>
        </div>
      </div>

      <div className="trace-graph-flow">
        {DEFAULT_NODES.map((node, index) => (
          <div key={node.id} className="node-wrapper">
            <button
              onClick={() => setSelectedNode(node)}
              className={`node-card ${node.id === selectedNode.id ? "selected" : ""} ${node.status}`}
            >
              <div className="node-top">
                <span className="node-index">0{index + 1}</span>
                <span className="layer-pill">{node.layer}</span>
              </div>
              <b className="node-name">{node.name}</b>
              <div className="node-footer">
                <span className="latency">{node.latencyMs > 0 ? `${node.latencyMs} ms` : "waiting"}</span>
                <span className={`status-dot ${node.status}`} />
              </div>
            </button>
            {index < DEFAULT_NODES.length - 1 && <span className="flow-arrow">→</span>}
          </div>
        ))}
      </div>

      {/* INSPECTOR PANEL */}
      <div className="node-inspector">
        <div className="inspector-top">
          <div>
            <h4>Node: {selectedNode.name}</h4>
            <span className="sub-layer">Layer: {selectedNode.layer}</span>
          </div>
          <span className={`node-status-badge ${selectedNode.status}`}>
            {selectedNode.status.toUpperCase()}
          </span>
        </div>

        {selectedNode.criticValidation && (
          <div className="critic-banner">
            <b>🛡️ Critic Gate Verdict</b>
            <p>{selectedNode.criticValidation.confidenceBasis}</p>
            <div className="critic-checks">
              <span>Unsupported Claims: <b>{selectedNode.criticValidation.unsupportedClaims ? "YES (Rejected)" : "NO (Clean)"}</b></span>
              <span>Policy Refs Valid: <b>{selectedNode.criticValidation.validPolicyRefs ? "YES (Grounded)" : "NO (Invalid)"}</b></span>
            </div>
          </div>
        )}

        <div className="code-comparison">
          <div className="code-box">
            <span className="box-title">Input Payload Snippet</span>
            <pre><code>{selectedNode.inputSnippet}</code></pre>
          </div>
          <div className="code-box">
            <span className="box-title">Output Result Snippet</span>
            <pre><code>{selectedNode.outputSnippet}</code></pre>
          </div>
        </div>
      </div>

      <style jsx>{`
        .trace-visualizer {
          background: rgba(15, 23, 42, 0.9);
          border: 1px solid rgba(99, 102, 241, 0.25);
          border-radius: 14px;
          padding: 1.25rem;
          margin: 1.5rem 0;
          color: #f8fafc;
        }
        .visualizer-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1.25rem;
        }
        .kicker {
          font-size: 0.7rem;
          font-weight: 700;
          letter-spacing: 0.08em;
          color: #818cf8;
          display: block;
        }
        .visualizer-header h3 {
          margin: 0;
          font-size: 1.125rem;
          font-family: "Outfit", sans-serif;
        }
        .trace-metrics {
          display: flex;
          gap: 1rem;
          font-size: 0.8125rem;
          color: #94a3b8;
          background: rgba(255, 255, 255, 0.04);
          padding: 0.35rem 0.875rem;
          border-radius: 20px;
        }
        .trace-metrics b {
          color: #38bdf8;
        }
        .trace-graph-flow {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          overflow-x: auto;
          padding-bottom: 0.75rem;
          margin-bottom: 1rem;
        }
        .node-wrapper {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          flex-shrink: 0;
        }
        .node-card {
          background: rgba(30, 41, 59, 0.6);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 10px;
          padding: 0.75rem;
          width: 170px;
          text-align: left;
          cursor: pointer;
          transition: all 0.2s ease;
        }
        .node-card:hover {
          background: rgba(30, 41, 59, 0.9);
          border-color: rgba(99, 102, 241, 0.4);
        }
        .node-card.selected {
          border-color: #6366f1;
          box-shadow: 0 0 12px rgba(99, 102, 241, 0.3);
          background: rgba(49, 46, 129, 0.4);
        }
        .node-top {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 0.35rem;
        }
        .node-index {
          font-size: 0.7rem;
          font-weight: 700;
          color: #64748b;
        }
        .layer-pill {
          font-size: 0.625rem;
          padding: 2px 6px;
          border-radius: 4px;
          background: rgba(255, 255, 255, 0.08);
          color: #cbd5e1;
        }
        .node-name {
          font-size: 0.8125rem;
          display: block;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          color: #e2e8f0;
          margin-bottom: 0.5rem;
        }
        .node-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
          font-size: 0.75rem;
          color: #94a3b8;
        }
        .status-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }
        .status-dot.completed, .status-dot.passed {
          background: #10b981;
        }
        .status-dot.waiting {
          background: #f59e0b;
        }
        .flow-arrow {
          color: #475569;
          font-weight: bold;
        }
        .node-inspector {
          background: rgba(15, 23, 42, 0.6);
          border: 1px solid rgba(255, 255, 255, 0.06);
          border-radius: 10px;
          padding: 1rem;
        }
        .inspector-top {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 0.875rem;
        }
        .inspector-top h4 {
          margin: 0;
          font-size: 0.9375rem;
          color: #f1f5f9;
        }
        .sub-layer {
          font-size: 0.75rem;
          color: #818cf8;
        }
        .node-status-badge {
          font-size: 0.7rem;
          font-weight: 700;
          padding: 3px 8px;
          border-radius: 12px;
        }
        .node-status-badge.completed, .node-status-badge.passed {
          background: rgba(16, 185, 129, 0.2);
          color: #34d399;
        }
        .node-status-badge.waiting {
          background: rgba(245, 158, 11, 0.2);
          color: #fbbf24;
        }
        .critic-banner {
          background: rgba(16, 185, 129, 0.1);
          border: 1px solid rgba(16, 185, 129, 0.3);
          border-radius: 8px;
          padding: 0.75rem;
          margin-bottom: 0.875rem;
          font-size: 0.8125rem;
        }
        .critic-banner b {
          color: #34d399;
          display: block;
          margin-bottom: 0.25rem;
        }
        .critic-banner p {
          margin: 0 0 0.5rem;
          color: #cbd5e1;
        }
        .critic-checks {
          display: flex;
          gap: 1.5rem;
          font-size: 0.75rem;
          color: #94a3b8;
        }
        .critic-checks b {
          display: inline;
          color: #f1f5f9;
        }
        .code-comparison {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 1rem;
        }
        .code-box {
          background: #090d16;
          border: 1px solid rgba(255, 255, 255, 0.05);
          border-radius: 8px;
          padding: 0.75rem;
        }
        .box-title {
          font-size: 0.7rem;
          font-weight: 700;
          text-transform: uppercase;
          color: #64748b;
          display: block;
          margin-bottom: 0.35rem;
        }
        .code-box pre {
          margin: 0;
          font-family: monospace;
          font-size: 0.75rem;
          color: #38bdf8;
          white-space: pre-wrap;
          word-break: break-all;
        }
        @media (max-width: 768px) {
          .code-comparison {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
}
