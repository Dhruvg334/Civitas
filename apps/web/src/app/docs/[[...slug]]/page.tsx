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
    nextPage: { label: "End-to-End Lifecycle →", href: "/docs/lifecycle" },
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
  lifecycle: {
    title: "Incident Lifecycle & Core Process",
    intro: "A step-by-step engineering breakdown of how an incident flows from mobile citizen intake to zero-shot ML triage, LangGraph multi-agent reasoning, human supervisor review, and before/after resolution verification.",
    slug: "lifecycle",
    prevPage: { label: "← Workflow & Operations", href: "/docs/workflow" },
    nextPage: { label: "Governance & Safety →", href: "/docs/safety" },
    blocks: [
      {
        heading: "Stage 01: Multimodal Intake & Zero-Trust Ingestion",
        body: "Citizen reporting begins through the responsive web wizard or public API. To support high-volume mobile submissions over constrained cellular networks, incoming media is optimized and hardened prior to backend storage.",
        alert: {
          type: "note",
          title: "Intake Hardening Rules",
          content: "Client-side canvas downsampling reduces 40MB photos to <1.2MB in under 200ms. The backend performs binary magic-byte validation (PNG, JPEG, WebP, MP4) and isolates storage under non-enumerable UUIDs with 1-hour signed access URLs.",
        },
        bullets: [
          "WGS84 GPS coordinate capture with offline Google Maps/OSM share link regex parsing.",
          "Strict 50MB file size ceiling and MIME-type allowlist enforcement.",
          "Citizen text description, category selection, and timestamp normalization into PostgreSQL.",
        ],
        code: `Citizen Device (Web Wizard / Mobile PWA)
  ├── 1. Canvas Downscaler (≤ 1920x1080 @ 0.85 JPEG)
  ├── 2. Map-Link / GPS Extraction (WGS84 lat/lon)
  └── 3. POST /api/v1/reports + POST /reports/{id}/media
        │
        ▼
FastAPI Ingestion Adapter
  ├── Binary Magic Byte Header Check (\\x89PNG, \\xff\\xd8\\xff, ftyp)
  └── Isolated Storage Vault (med-<uuid>.<ext>)`,
      },
      {
        heading: "Stage 02: Deterministic Geospatial & Zero-Shot Vision Triage",
        body: "Before invoking generative agent nodes, incoming reports are processed through fast, deterministic spatial queries and computer vision defect models to establish observable facts.",
        bullets: [
          "PostGIS Spatial Clustering: ST_DWithin queries group reports within dynamic radiuses (50m for potholes, 150m for water bursts) over a 72-hour rolling window to eliminate duplicate work orders.",
          "Zero-Shot Defect Vision: CLIP embeddings categorize visual defects against municipal taxonomies and extract physical attributes (e.g. standing water depth, pavement cavity, tree trunk diameter).",
          "Landmark Proximity Buffer: Calculates exact distances to schools, hospital emergency bays, and transit corridors to assign deterministic P1/P2/P3 priority ratings.",
        ],
        code: `Raw Report (med-0241.jpg, lat=20.29614, lon=85.82451)
  │
  ├──► [PostGIS ST_DWithin(50m, 72h)] ──► Clustered to INC-0241 (duplicates: 3)
  ├──► [CLIP Zero-Shot Vision]         ──► Defect: Water Leakage (Conf: 0.94)
  └──► [Spatial Buffer Engine]         ──► 14m from DAV School Gate ──► PRIORITY: P1`,
      },
      {
        heading: "Stage 03: LangGraph Checkpointed Multi-Agent Reasoning",
        body: "The incident enters a deterministic LangGraph state machine. Each agent operates with an isolated system prompt, dedicated schema contracts, and separate LLM calls to prevent cross-contamination.",
        alert: {
          type: "important",
          title: "The 6-Agent Reasoning Pipeline",
          content: "1. Structure Evidence (triad separation) → 2. Clarification Check (interactive interrupt) → 3. Grounding Retrieval (playbooks) → 4. Policy Routing (jurisdiction) → 5. Operational Planning (SLA & work order) → 6. Adversarial Critic (safety check loop, max 2 revisions).",
        },
        code: `[load_context] ──► [ml_intelligence] ──► [structure_evidence]
                                                 │
                                                 ▼
[knowledge_grounding] ◄── [clarification_check] ──► (Missing info? ──► [WAITING_FOR_CLARIFICATION])
         │
         ▼
  [routing_agent] ──► (Cites ROUTE-WATER-02)
         │
         ▼
[operational_planner] ◄──┐
         │               │ (Critic Rejection, max 2 revisions)
         ▼               │
      [critic] ──────────┘
         │
         ▼ (Critic Approved)
[prepare_human_review] ──► [WAITING_FOR_REVIEW]`,
      },
      {
        heading: "Stage 04: Human-in-the-Loop Review Gate & Command Center",
        body: "Civitas enforces a strict governance standard: AI proposes operational plans, but authorized municipal supervisors hold final decision authority. Work orders are never automatically dispatched without human approval.",
        bullets: [
          "Checkpointed Halt: LangGraph freezes execution state to PostgreSQL at WAITING_FOR_REVIEW.",
          "Supervisor Incident Dossier: Municipal supervisors review GIS hazard buffers, visual evidence triads, and the draft work order in the Command Center.",
          "5 Canonical Review Actions: Approve (dispatch), Edit Work Order (adjust SLA/equipment), Reroute Department, Reject (dismiss false alarm), or Request Additional Evidence.",
          "Resumption: Submitting the review resumes the existing thread ID idempotently via POST /api/v1/workflows/{id}/review.",
        ],
      },
      {
        heading: "Stage 05: Field Dispatch & Citizen Communication",
        body: "Upon supervisor authorization, the work order is formally dispatched to district field crew leads with exact spatial coordinates, safety protocols, and equipment requirements. Concurrently, the citizen communication agent generates a non-technical status update for residents.",
        bullets: [
          "Work Order Dispatch: Assigned to designated crew lead (e.g. Marcus Vance, Ward 12 Water Supply Dept) with required tools (ductile clamp, backhoe, asphalt patch).",
          "Citizen Status Feed: Reassuring, non-technical notification informing the citizen that crew dispatch is active with an estimated resolution window (e.g. 8–14 hours).",
        ],
      },
      {
        heading: "Stage 06: Closed-Loop Resolution Verification",
        body: "An incident cannot be marked RESOLVED based on time elapsed alone. Field crews must submit post-repair photographic evidence, which is verified against pre-repair defect embeddings before closing the ticket.",
        alert: {
          type: "note",
          title: "Resolution Verification Protocol",
          content: "The ML resolution model evaluates the pre-repair vs post-repair image pair to confirm physical hazard remediation (e.g. 98.4% visual match to resolved standard) and generates a complete audit trail.",
        },
        code: `Field Crew Completes Repair ──► Uploads Post-Repair Photo
                                      │
                                      ▼
[Resolution Inspector Engine] ──► Pre/Post CLIP Embedding Delta
                                      │
                                      ├── Verification Checklist Passed (Grates clear, asphalt sealed)
                                      └── Incident Status ──► RESOLVED · Archive Audit Trail`,
      },
    ],
  },
  safety: {
    title: "Governance, Safety and Evaluation",
    intro: "Civitas is engineered to expose uncertainty and preserve human accountability rather than manufacture artificial confidence.",
    slug: "safety",
    prevPage: { label: "← End-to-End Lifecycle", href: "/docs/lifecycle" },
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
  process: "lifecycle",
  pipeline: "lifecycle",
  stages: "lifecycle",
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
            <span className="pagination-kicker">PREVIOUS TOPIC</span>
            <span className="pagination-title">{page.prevPage.label}</span>
          </Link>
        ) : (
          <div />
        )}
        {page.nextPage ? (
          <Link href={page.nextPage.href} className="pagination-link next">
            <span className="pagination-kicker">NEXT TOPIC</span>
            <span className="pagination-title">{page.nextPage.label}</span>
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
          align-items: flex-end;
        }
        .pagination-link.prev {
          text-align: left;
          align-items: flex-start;
        }
        .pagination-link:hover {
          background: #172019;
          color: #ffffff;
          box-shadow: 2px 2px 0 #0f5f4f;
          transform: translateY(-2px);
        }
        .pagination-kicker {
          display: block;
          font-size: 0.65rem;
          font-weight: 900;
          letter-spacing: 0.1em;
          color: #0f5f4f;
          text-transform: uppercase;
        }
        .pagination-title {
          display: block;
          font-size: 1rem;
          font-weight: 800;
          color: #172019;
          line-height: 1.3;
        }
        .pagination-link:hover .pagination-kicker {
          color: #dce8dd;
        }
        .pagination-link:hover .pagination-title {
          color: #ffffff;
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
