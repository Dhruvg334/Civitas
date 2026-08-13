import { DocsPage } from "@/components/site";

const sections: Record<string, { title: string; intro: string; blocks: Array<{ heading: string; body: string; code?: string; points?: string[] }> }> = {
  "": { title: "System overview", intro: "A practical guide to how Civitas turns resident reports into traceable municipal decisions.", blocks: [
    { heading: "What Civitas does", body: "Civitas connects report intake, multimodal analysis, duplicate reasoning, severity and priority, policy grounding, routing, operational planning, human review and resident communication without collapsing those responsibilities into one opaque model call." },
    { heading: "Core boundary", body: "The product supports municipal decision-making; it does not silently commit high-impact action. The workflow pauses at a human review checkpoint before operational approval." },
    { heading: "Read next", body: "Architecture explains system boundaries. Workflow explains the LangGraph state machine. Evaluation explains the three-system comparison used to test whether decomposition adds value.", points: ["Architecture and runtime composition", "Agent responsibilities and grounding", "ML and geospatial capabilities", "Evaluation, safety and deployment"] },
  ]},
  architecture: { title: "Architecture", intro: "Civitas is split into explicit product, API, workflow, knowledge, ML and persistence boundaries.", blocks: [
    { heading: "Request path", body: "The Next.js client consumes typed FastAPI envelopes. FastAPI owns authentication, report and incident operations, workflow execution, persistence and internal ML bridging." },
    { heading: "Reasoning path", body: "LangGraph orchestrates evidence structuring, clarification, ML intelligence, knowledge retrieval, routing, planning, critic checks and human review. The LLM provider remains behind a typed interface.", code: "Next.js → FastAPI → LangGraph\n                ↘ ML + Geospatial\n                ↘ Knowledge + Policies\n                ↘ PostgreSQL / Supabase\n                ↘ Groq LLM provider" },
    { heading: "State and persistence", body: "Operational workflow metadata is stored separately from LangGraph checkpoint state. A stable thread identifier allows an interrupted workflow to resume rather than restart." },
  ]},
  workflow: { title: "Workflow", intro: "The workflow is a sequence of typed decisions with explicit interruption and revision points.", blocks: [
    { heading: "Execution order", body: "A report context is loaded deterministically before any model reasoning. Evidence is structured, decision-relevant clarification is considered, ML outputs are attached, policy knowledge is retrieved, then routing and planning recommendations are reviewed by a critic." , code: "report → evidence → clarification → ML → knowledge\n       → routing → plan → critic → human review → update"},
    { heading: "Interrupts", body: "Clarification and human review use real LangGraph interrupts. The same persisted thread resumes after an answer or review decision." },
    { heading: "Idempotency", body: "Repeated start requests reuse an existing active or completed workflow. Persistence paths are designed to avoid duplicate routing or work-order records during replay." },
  ]},
  agents: { title: "Agents", intro: "Agents exist only where responsibilities, tools, schemas and failure behavior are meaningfully different.", blocks: [
    { heading: "Evidence structuring", body: "Separates observed visual facts, resident-reported claims, retrieved context and inference. Unknowns remain unknown." },
    { heading: "Routing and planning", body: "Routing interprets grounded policy references to recommend departments and escalation. Planning turns the approved context into a municipality-ready work-order recommendation." },
    { heading: "Critic and communication", body: "The critic checks unsupported claims, evidence confusion, routing contradictions and unsafe promises. Citizen communication runs only after an allowed operational state." },
  ]},
  ml: { title: "ML & geospatial", intro: "Civitas keeps statistical and vision capabilities separate from LLM reasoning.", blocks: [
    { heading: "Vision", body: "The vision layer classifies supported civic incident categories and produces typed visual evidence. It is not used to invent details that are absent from media." },
    { heading: "Duplicates and clustering", body: "Spatial, temporal, categorical and visual signals help decide whether multiple reports refer to the same operational incident, including hard-negative cases at similar locations." },
    { heading: "Risk and resolution", body: "Severity and priority are distinct outputs. Resolution verification compares follow-up evidence and can represent complete, partial, conflicting or unverifiable outcomes." },
  ]},
  knowledge: { title: "Knowledge grounding", intro: "Municipal recommendations are tied to retrieved policy and playbook evidence rather than invented operational rules.", blocks: [
    { heading: "Deterministic first", body: "The current corpus is small enough that exact category, department and policy-purpose filters are preferred before keyword ranking or optional semantic ranking." },
    { heading: "Grounding states", body: "Knowledge results distinguish supported, partially supported and insufficient-knowledge outcomes. Missing jurisdiction evidence produces an explicit limitation rather than an inferred rule." },
    { heading: "Reference validation", body: "Downstream agent outputs are checked against known knowledge identifiers so fabricated policy IDs can be rejected before a decision is accepted." },
  ]},
  api: { title: "API", intro: "FastAPI exposes citizen, municipal and internal runtime surfaces through a common success/error envelope.", blocks: [
    { heading: "Workflow routes", body: "The workflow API starts a report workflow, returns current state, accepts clarification answers and resumes human review decisions.", code: "POST /api/v1/reports/{report_id}/workflow\nGET  /api/v1/workflows/{workflow_id}\nPOST /api/v1/workflows/{workflow_id}/clarification\nPOST /api/v1/workflows/{workflow_id}/review" },
    { heading: "Internal ML bridge", body: "The FastAPI runtime exposes a protected internal ML analysis route around the existing unified Python pipeline rather than deploying a redundant ML microservice.", code: "POST /api/v1/ml/analyze" },
    { heading: "Authorization", body: "Citizen and municipal actions use existing role boundaries. Internal runtime surfaces require the configured internal authentication mechanism in production." },
  ]},
  evaluation: { title: "Evaluation", intro: "Civitas is compared against simpler prompting approaches instead of assuming that more agents automatically means better performance.", blocks: [
    { heading: "Three systems", body: "Baseline A is one competent prompt. Baseline B is one structured mega-prompt. System C executes the real Civitas graph. All three use the same 25-case corpus." },
    { heading: "Offline versus live", body: "Offline deterministic runs verify architecture, contracts, metric computation and reproducibility. They are not presented as live model-quality evidence. A Groq path exists for manual live comparison." },
    { heading: "Measured behavior", body: "Metrics cover structured validity, category and routing correctness, escalation, knowledge references, unsupported claims, work-order completeness, clarification, abstention, workflow failures, latency and usage where available." },
  ]},
  safety: { title: "Safety & accountability", intro: "The system is designed around evidence boundaries, review gates and traceable operational decisions.", blocks: [
    { heading: "Human review", body: "Approve, edit, reroute, reject and request-more-evidence actions are narrow typed operations. Arbitrary graph-state injection is blocked." },
    { heading: "Abstention", body: "Missing policy evidence, uncertain evidence or invalid references do not trigger invented certainty. The workflow can surface a limitation or require review." },
    { heading: "Traceability", body: "Node traces retain workflow status, tools/models, knowledge references and validation outcomes without storing secrets or hidden chain-of-thought." },
  ]},
  deployment: { title: "Deployment", intro: "The production topology keeps the product simple: one web client, one FastAPI runtime, managed Postgres/Supabase services and an external LLM provider.", blocks: [
    { heading: "Target topology", body: "The intended topology is Next.js on Vercel, FastAPI on Render, Supabase/PostgreSQL for application data and checkpoints, and environment-configured Groq models." },
    { heading: "Production configuration", body: "Python is standardized on 3.12. Production startup validates authentication and internal runtime configuration rather than silently falling back to insecure development behavior." },
    { heading: "Operational checks", body: "Liveness and readiness are separate. Readiness checks database availability before a deployment is considered ready to serve runtime traffic." },
  ]},
};

export default async function Docs({ params }: { params: Promise<{ slug?: string[] }> }) {
  const { slug = [] } = await params;
  const page = sections[slug[0] ?? ""] ?? sections[""];
  return <DocsPage title={page.title} intro={page.intro}>{page.blocks.map((block, index) => <section className="doc-section" key={block.heading} id={`section-${index + 1}`}><div className="doc-section-number">{String(index + 1).padStart(2, "0")}</div><div><h2>{block.heading}</h2><p>{block.body}</p>{block.points && <ul>{block.points.map((point) => <li key={point}>{point}</li>)}</ul>}{block.code && <pre><code>{block.code}</code></pre>}</div></section>)}</DocsPage>;
}
