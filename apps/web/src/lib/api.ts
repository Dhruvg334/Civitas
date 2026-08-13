export type CivitasEnvelope<T> =
  | { success: true; data: T; trace_id?: string; timestamp?: string }
  | { success: false; error: { message: string; code?: string; details?: unknown } };

export function unwrapEnvelope<T>(payload: CivitasEnvelope<T>): T {
  if (!payload.success) {
    throw new Error(payload.error.message);
  }
  return payload.data;
}

const API_BASE_URL =
  typeof window !== "undefined"
    ? (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1")
    : "http://localhost:8000/api/v1";

export interface IncidentRecord {
  id: string;
  title: string;
  category: string;
  priority: "Low" | "Medium" | "High" | "Critical";
  severityScore: number;
  reportsCount: number;
  primaryDepartment: string;
  secondaryDepartments: string[];
  status: string;
  location: {
    landmark: string;
    latitude: number;
    longitude: number;
  };
  submittedAt: string;
  workOrderId?: string;
  workOrderSummary?: string;
}

export interface IncidentTraceStep {
  step: string;
  status: "completed" | "in_progress" | "waiting_review" | "pending";
  timestamp: string;
  details: string;
}

// Fallback seed data when backend API is unreachable
export const SEEDED_INCIDENTS: IncidentRecord[] = [
  {
    id: "INC-0241",
    title: "Water leak near school crossing",
    category: "Water leakage",
    priority: "High",
    severityScore: 78,
    reportsCount: 3,
    primaryDepartment: "Water Supply",
    secondaryDepartments: ["Traffic Coordination"],
    status: "WAITING_FOR_REVIEW",
    location: {
      landmark: "Civitas Public School, East Gate",
      latitude: 20.2961,
      longitude: 85.8245,
    },
    submittedAt: "2026-08-07T08:42:00Z",
    workOrderId: "WO-0241-A",
    workOrderSummary: "Inspect and isolate the active leak; secure the school crossing section.",
  },
  {
    id: "INC-0240",
    title: "Blocked pedestrian pathway from fallen branch",
    category: "Fallen tree",
    priority: "Medium",
    severityScore: 45,
    reportsCount: 2,
    primaryDepartment: "Public Works",
    secondaryDepartments: [],
    status: "ASSIGNED",
    location: {
      landmark: "Ward 12 Park Road",
      latitude: 20.2985,
      longitude: 85.821,
    },
    submittedAt: "2026-08-07T07:15:00Z",
    workOrderId: "WO-0240-B",
    workOrderSummary: "Clear obstruction from primary footpath.",
  },
  {
    id: "INC-0238",
    title: "Streetlight outage on main ward route",
    category: "Broken streetlight",
    priority: "High",
    severityScore: 62,
    reportsCount: 1,
    primaryDepartment: "Electrical Infrastructure",
    secondaryDepartments: [],
    status: "WAITING_FOR_CLARIFICATION",
    location: {
      landmark: "Ward 12 Junction",
      latitude: 20.294,
      longitude: 85.829,
    },
    submittedAt: "2026-08-06T21:30:00Z",
  },
];

export async function fetchIncidents(): Promise<IncidentRecord[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/incidents`, {
      headers: { Accept: "application/json" },
      next: { revalidate: 10 },
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const envelope = (await res.json()) as CivitasEnvelope<IncidentRecord[]>;
    return unwrapEnvelope(envelope);
  } catch (err) {
    console.info("Using local fallback seed incidents (backend API offline or unheated):", err);
    return SEEDED_INCIDENTS;
  }
}

export async function fetchIncidentDetail(id: string): Promise<IncidentRecord> {
  try {
    const res = await fetch(`${API_BASE_URL}/incidents/${id}`, {
      headers: { Accept: "application/json" },
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const envelope = (await res.json()) as CivitasEnvelope<IncidentRecord>;
    return unwrapEnvelope(envelope);
  } catch (err) {
    console.info(`Using local fallback for incident ${id}:`, err);
    const found = SEEDED_INCIDENTS.find((item) => item.id === id || id === "demo-water");
    return found || SEEDED_INCIDENTS[0];
  }
}

export async function submitReport(payload: {
  description: string;
  category?: string;
  latitude?: number;
  longitude?: number;
}): Promise<{ report_id: string; status: string }> {
  try {
    const res = await fetch(`${API_BASE_URL}/reports`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        description: payload.description,
        latitude: payload.latitude || 20.2961,
        longitude: payload.longitude || 85.8245,
        citizen_selected_category: payload.category || null,
        submitted_at: new Date().toISOString(),
      }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const envelope = (await res.json()) as CivitasEnvelope<{ report_id: string; status: string }>;
    return unwrapEnvelope(envelope);
  } catch (err) {
    console.info("Simulating report submission (local mock fallback):", err);
    return {
      report_id: `RPT-${Math.floor(1000 + Math.random() * 9000)}`,
      status: "submitted",
    };
  }
}

export async function approveWorkOrder(
  workOrderId: string,
  reviewAction: "approve" | "edit" | "reroute" | "reject",
  notes?: string
): Promise<{ status: string; updated_at: string }> {
  try {
    const res = await fetch(`${API_BASE_URL}/work-orders/${workOrderId}/approve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: reviewAction, notes }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const envelope = (await res.json()) as CivitasEnvelope<{ status: string; updated_at: string }>;
    return unwrapEnvelope(envelope);
  } catch (err) {
    console.info(`Simulating work order review action '${reviewAction}' (local fallback):`, err);
    return {
      status: reviewAction === "approve" ? "APPROVED" : reviewAction === "reject" ? "REJECTED" : "MODIFIED",
      updated_at: new Date().toISOString(),
    };
  }
}

export async function fetchIncidentTrace(id: string): Promise<IncidentTraceStep[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/incidents/${id}/trace`, {
      headers: { Accept: "application/json" },
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const envelope = (await res.json()) as CivitasEnvelope<IncidentTraceStep[]>;
    return unwrapEnvelope(envelope);
  } catch (err) {
    return [
      { step: "Report Intake & Evidence Extraction", status: "completed", timestamp: "08:42:01", details: "3 report items normalized. Contradictions & source claims preserved." },
      { step: "Multimodal ML Analysis", status: "completed", timestamp: "08:42:04", details: "Duplicate similarity score 0.84. Primary category set to water_leakage." },
      { step: "Policy Grounding & Retrieval", status: "completed", timestamp: "08:42:06", details: "PLAY-WATER-01 & ROUTE-WATER-02 retrieved from municipal knowledge base." },
      { step: "Risk Assessment & Routing", status: "completed", timestamp: "08:42:08", details: "Severity: 78 (High). Priority: Critical (School crossing proximity)." },
      { step: "Work Order Synthesis & Critic Check", status: "completed", timestamp: "08:42:10", details: "Critic check passed. Non-binding estimate 8-14 hours." },
      { step: "Human Review Interrupt", status: "waiting_review", timestamp: "08:42:12", details: "Awaiting supervisor sign-off before dispatch." },
    ];
  }
}
