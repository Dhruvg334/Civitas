"use client";

import { use } from "react";
import Link from "next/link";
import { DocsPage } from "@/components/site";
import { DocsApiExplorer } from "@/components/docs-api-explorer";

interface Block {
  heading: string;
  body: string;
  alert?: { type: "note" | "important" | "warning"; title: string; content: string };
  bullets?: string[];
  code?: string;
}

interface Doc {
  title: string;
  intro: string;
  slug: string;
  blocks: Block[];
  nextPage?: { label: string; href: string };
  prevPage?: { label: string; href: string };
}

const docs: Record<string, Doc> = {
  "": {
    title: "Civitas System Guide",
    intro: "A practical engineering reference for the product path from citizen report to a reviewed municipal recommendation.",
    slug: "",
    nextPage: { label: "System Architecture →", href: "/docs/architecture" },
    blocks: [
      {
        heading: "Operating Principle: Evidence Over Direct Instruction",
        body: "Civitas treats incoming citizen reports as evidence that requires interpretation, rather than raw instructions that automatically trigger municipal actions. It preserves the vital boundary between what a resident reported, what media appears to show, context retrieved from GIS systems or city policies, and conclusions reached by deterministic tools or agents.",
        alert: {
          type: "important",
          title: "Core Governance Boundary",
          content: "Observable evidence, retrieved knowledge, model outputs, inferences, and human decisions are kept strictly distinct in every contract, database record, and UI surface.",
        },
        bullets: [
          "Preserve contradictory claims across multiple citizen reports instead of silently overwriting them.",
          "Expose model uncertainty explicitly rather than fabricating high confidence.",
          "Enforce human approval checkpoints for high-impact routing, work-order creation, and ticket closure.",
        ],
      },
      {
        heading: "Decision Lifecycle & Golden Slice",
        body: "A citizen report undergoes a multi-stage deterministic pipeline. Disparate reports are clustered into shared incidents via PostGIS spatial indexing. ML models extract visual features, policy playbooks are retrieved via hybrid grounding, and a critic node verifies the draft work order before pausing for human supervisor authorization.",
        code: `Citizen Report (Text + Media + GPS)
       │
       ▼
[01 Intake Context Normalization]
       │
       ▼
[02 Multimodal ML & Spatial Clustering] ──► (DBSCAN + CLIP Zero-Shot)
       │
       ▼
[03 Policy Grounding & Retrieval]      ──► (PostGIS + Playbooks)
       │
       ▼
[04 Work Order Synthesis & Routing]
       │
       ▼
[05 Critic Node Validation]             ──► (Check Constraints)
       │
       ▼
[06 Human Supervisor Gate]              ──► (Approve / Edit / Reroute / Reject)`,
      },
      {
        heading: "Typed Shared Contracts",
        body: "Public API envelopes, ML inference payloads, LangGraph checkpoint state, knowledge evidence, and human review actions are strictly schema-validated with Pydantic and TypeScript. Typed contracts make failures immediately visible at component boundaries instead of allowing corrupted data to silently influence downstream municipal decisions.",
      },
      {
        heading: "Traceability & Observability",
        body: "Every node execution records a unique trace identifier, model name, token usage metrics, latency, retry counts, validation state, and referenced policy IDs. Secrets, authorization headers, and unnecessary raw private resident data are never persisted into operational trace logs.",
      },
    ],
  },
  architecture: {
    title: "System Architecture",
    intro: "Explicit architectural boundaries keep the platform testable, operationally comprehensible, and safe to evolve.",
    slug: "architecture",
    prevPage: { label: "← System Guide", href: "/docs" },
    nextPage: { label: "Operations & Workflow →", href: "/docs/workflow" },
    blocks: [
      {
        heading: "Runtime Topology & Stack",
        body: "The Civitas architecture separates user interfaces, operational runtime, workflow orchestration, and geospatial storage into independent, reviewable modules.",
        code: `Next.js 16 (App Router + Leaflet GIS)
    │  (Typed HTTP Envelopes)
    ▼
FastAPI Operational Backend (apps/api)
    ├── Internal ML Engine (CLIP Zero-Shot, DBSCAN)
    ├── Geospatial Service (PostGIS 3.4 + H3 Indexing)
    ├── Knowledge Service (Policy & Playbook Retrieval)
    └── LangGraph Workflow Orchestrator (Checkpoint Saver)
        │
        ▼
PostgreSQL / Supabase (Application Data + LangGraph State)`,
      },
      {
        heading: "Why the ML Bridge is Internal",
        body: "The unified ReportAnalysis pipeline remains directly installed with the FastAPI runtime as a clean internal adapter. The internal analyze endpoint is a contract boundary rather than a separately deployed microservice, avoiding cold-start latency and duplicated model logic while keeping inference fully testable.",
        alert: {
          type: "note",
          title: "Inference Isolation",
          content: "ML inference runs deterministically with fallback heuristics if GPU acceleration or model checkpoints are unavailable.",
        },
      },
      {
        heading: "Persistence & State Storage Split",
        body: "Workflow-run metadata records execution IDs, report references, incident associations, trace IDs, and thread IDs in PostgreSQL. Canonical report, assessment, routing, work-order, and human review structures remain owned by the backend persistence layer.",
      },
    ],
  },
  workflow: {
    title: "Workflow and Operations",
    intro: "The LangGraph orchestration graph turns incoming reports into reviewable work orders through bounded nodes and explicit checkpoints.",
    slug: "workflow",
    prevPage: { label: "← System Architecture", href: "/docs/architecture" },
    nextPage: { label: "Governance & Safety →", href: "/docs/safety" },
    blocks: [
      {
        heading: "Context Normalization & Evidence Extraction",
        body: "The context loader deterministically normalizes citizen descriptions, categories, GPS coordinates, media metadata, existing incident associations, and clarification responses. The evidence agent produces structured output identifying observable facts, reported claims, hazards, landmarks, and contradictions.",
        bullets: [
          "Differentiates what is directly visible in media from citizen assertions.",
          "Identifies spatial landmarks (e.g. '14m from DAV Public School Gate').",
          "Flags safety-critical hazards and missing information.",
        ],
      },
      {
        heading: "Deterministic Intelligence & Geospatial Grounding",
        body: "Duplicate detection, spatial clustering, severity calculation, and priority assignment are derived using deterministic algorithms and PostGIS queries. The workflow does not rely on an LLM to guess coordinates or compute distance buffers.",
      },
      {
        heading: "Checkpoint Interrupt & Human Resume",
        body: "When clarification is needed from a citizen or when a high-impact work order is prepared, the LangGraph graph saves state to PostgreSQL and transitions to WAITING_FOR_CLARIFICATION or WAITING_FOR_REVIEW. Resuming reuses the existing stable thread ID without rebuilding state from scratch.",
        alert: {
          type: "important",
          title: "Idempotent Execution",
          content: "Starting a workflow for an existing report ID reuses active or completed runs to prevent duplicate work orders.",
        },
      },
    ],
  },
  safety: {
    title: "Governance, Safety and Evaluation",
    intro: "Civitas is engineered to expose uncertainty and preserve human accountability rather than manufacture artificial confidence.",
    slug: "safety",
    prevPage: { label: "← Operations & Workflow", href: "/docs/workflow" },
    nextPage: { label: "API Reference →", href: "/docs/api" },
    blocks: [
      {
        heading: "Evidence State Categorization",
        body: "The platform tracks four distinct categories of information across all workflows and user interfaces:",
        bullets: [
          "Observed: Directly confirmed by media analysis or sensor data.",
          "Reported: Asserted by citizens in their raw text submission.",
          "Retrieved: Extracted from verified municipal policy playbooks and PostGIS databases.",
          "Inferred: Recommended by agentic models and subject to human review.",
        ],
      },
      {
        heading: "Policy Grounding & Abstention",
        body: "Every policy-dependent claim in a work order or routing decision must cite a valid retrieved municipal playbook (e.g., PLAY-WATER-01). If no grounding playbook exists, the workflow records INSUFFICIENT_KNOWLEDGE and requests manual human supervisor review.",
        alert: {
          type: "warning",
          title: "Zero Hallucination Tolerance",
          content: "Agents are strictly prohibited from inventing municipal jurisdictions, response SLAs, or repair commitments.",
        },
      },
      {
        heading: "Supervisor Review Controls",
        body: "Review actions are deliberately constrained to five canonical operations: Approve, Edit Work Order, Reroute Department, Reject, and Request Additional Evidence. Rejections cannot create an active work order.",
      },
    ],
  },
  api: {
    title: "API & Integration Reference",
    intro: "Typed operational boundaries for citizen reporting, workflow execution, ML inference, and supervisor review actions.",
    slug: "api",
    prevPage: { label: "← Governance & Safety", href: "/docs/safety" },
    blocks: [
      {
        heading: "Civitas Envelope Specification",
        body: "Every API endpoint wraps its payload in a standardized Civitas Envelope. Successful responses include a success boolean, data payload, and metadata. Error responses return structured error codes and human-actionable messages without leaking private secrets.",
      },
    ],
  },
};

const legacySlugs: Record<string, string> = {
  agents: "workflow",
  ml: "architecture",
  knowledge: "safety",
  evaluation: "safety",
  deployment: "api",
};

export default function Docs({
  params,
}: {
  params: Promise<{ slug?: string[] }>;
}) {
  const { slug = [] } = use(params);
  const rawKey = slug[0] ?? "";
  const key = legacySlugs[rawKey] ?? rawKey;
  const page = docs[key] ?? docs[""];

  const tocItems = page.blocks.map((b, i) => ({
    id: `section-${i + 1}`,
    label: b.heading,
  }));

  return (
    <DocsPage
      title={page.title}
      intro={page.intro}
      activeSlug={page.slug}
      tocItems={tocItems}
    >
      {/* SECTION BLOCKS */}
      <div className="docs-sections-list">
        {page.blocks.map((block, index) => (
          <section
            className="doc-section-card"
            key={block.heading}
            id={`section-${index + 1}`}
          >
            <div className="section-number-pill">
              {String(index + 1).padStart(2, "0")}
            </div>

            <div className="section-content-wrap">
              <h2 className="section-heading">{block.heading}</h2>
              <p className="section-body">{block.body}</p>

              {block.alert && (
                <div className={`doc-alert-box alert-${block.alert.type}`}>
                  <span className="alert-badge">{block.alert.type.toUpperCase()}</span>
                  <div className="alert-content">
                    <b>{block.alert.title}</b>
                    <p>{block.alert.content}</p>
                  </div>
                </div>
              )}

              {block.bullets && (
                <ul className="section-bullet-list">
                  {block.bullets.map((bullet) => (
                    <li key={bullet}>{bullet}</li>
                  ))}
                </ul>
              )}

              {block.code && (
                <div className="section-code-wrap">
                  <div className="code-header">
                    <span className="code-lang">SCHEMA / FLOW</span>
                  </div>
                  <pre>
                    <code>{block.code}</code>
                  </pre>
                </div>
              )}
            </div>
          </section>
        ))}
      </div>

      {/* SPECIAL INTERACTIVE API EXPLORER FOR /docs/api */}
      {page.slug === "api" && <DocsApiExplorer />}

      {/* PAGINATION FOOTER */}
      <nav className="docs-pagination-nav" aria-label="Docs pagination">
        {page.prevPage ? (
          <Link href={page.prevPage.href} className="pagination-link prev">
            <small>PREVIOUS TOPIC</small>
            <span>{page.prevPage.label}</span>
          </Link>
        ) : (
          <div />
        )}
        {page.nextPage ? (
          <Link href={page.nextPage.href} className="pagination-link next">
            <small>NEXT TOPIC</small>
            <span>{page.nextPage.label}</span>
          </Link>
        ) : (
          <div />
        )}
      </nav>

      <style jsx>{`
        .docs-sections-list {
          display: flex;
          flex-direction: column;
          gap: 40px;
        }
        .doc-section-card {
          display: grid;
          grid-template-columns: 48px 1fr;
          gap: 24px;
          padding-bottom: 36px;
          border-bottom: 1px solid #e2ded4;
        }
        .section-number-pill {
          font-size: 0.85rem;
          font-weight: 900;
          color: #0f5f4f;
          font-family: monospace;
          background: #dce8dd;
          height: 36px;
          display: grid;
          place-items: center;
          border: 1px solid #0f5f4f;
          border-radius: 4px;
        }
        .section-content-wrap {
          min-width: 0;
        }
        .section-heading {
          font-size: 1.55rem;
          font-family: Georgia, serif;
          margin: 0 0 12px;
          color: #172019;
          line-height: 1.25;
        }
        .section-body {
          font-size: 0.95rem;
          line-height: 1.68;
          color: #495248;
          margin: 0 0 16px;
        }
        .doc-alert-box {
          display: flex;
          gap: 14px;
          padding: 14px 18px;
          border: 1px solid #172019;
          margin: 18px 0;
          background: #fbf9f4;
          border-radius: 6px;
          box-shadow: 3px 3px 0 #172019;
        }
        .alert-important {
          border-left: 6px solid #e84d7a;
        }
        .alert-warning {
          border-left: 6px solid #e3b950;
        }
        .alert-note {
          border-left: 6px solid #0f5f4f;
        }
        .alert-badge {
          font-size: 0.6rem;
          font-weight: 900;
          letter-spacing: 0.08em;
          padding: 3px 6px;
          background: #172019;
          color: #ffffff;
          border-radius: 3px;
          height: max-content;
        }
        .alert-content b {
          display: block;
          font-size: 0.88rem;
          color: #172019;
          margin-bottom: 4px;
        }
        .alert-content p {
          font-size: 0.84rem;
          color: #555e54;
          margin: 0;
          line-height: 1.5;
        }
        .section-bullet-list {
          margin: 14px 0 18px 20px;
          padding: 0;
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .section-bullet-list li {
          font-size: 0.9rem;
          color: #495248;
          line-height: 1.5;
        }
        .section-code-wrap {
          margin: 20px 0;
          border: 1px solid #172019;
          background: #172019;
          border-radius: 6px;
          overflow: hidden;
        }
        .code-header {
          padding: 6px 14px;
          background: #232d25;
          border-bottom: 1px solid #333f36;
          font-size: 0.62rem;
          font-weight: 850;
          letter-spacing: 0.1em;
          color: #9da99e;
        }
        .section-code-wrap pre {
          margin: 0;
          padding: 16px;
          color: #fbf9f4;
          font-size: 0.8rem;
          font-family: monospace;
          line-height: 1.55;
          overflow-x: auto;
        }
        .docs-pagination-nav {
          display: flex;
          justify-content: space-between;
          margin-top: 72px;
          padding-top: 40px;
          border-top: 2px solid #172019;
          gap: 24px;
        }
        .pagination-link {
          display: flex;
          flex-direction: column;
          gap: 6px;
          padding: 16px 24px;
          min-width: 220px;
          border: 2px solid #172019;
          background: #ffffff;
          box-shadow: 4px 4px 0 #172019;
          text-decoration: none;
          border-radius: 6px;
          transition: all 0.15s ease;
        }
        .pagination-link.next {
          margin-left: auto;
          text-align: right;
        }
        .pagination-link:hover {
          background: #172019;
          color: #ffffff;
          box-shadow: 2px 2px 0 #0f5f4f;
          transform: translateY(-2px);
        }
        .pagination-link:hover small {
          color: #dce8dd;
        }
        .pagination-link:hover span {
          color: #ffffff;
        }
        .pagination-link small {
          font-size: 0.65rem;
          font-weight: 900;
          letter-spacing: 0.1em;
          color: #0f5f4f;
        }
        .pagination-link span {
          font-size: 1rem;
          font-weight: 800;
          color: #172019;
        }
        @media (max-width: 600px) {
          .doc-section-card {
            grid-template-columns: 1fr;
            gap: 12px;
          }
          .docs-pagination-nav {
            flex-direction: column;
          }
        }
      `}</style>
    </DocsPage>
  );
}
