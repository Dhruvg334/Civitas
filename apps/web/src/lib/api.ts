/**
 * Civitas Canonical Web API Client.
 *
 * Grounded in the FastAPI backend contracts with envelope validation,
 * explicit demo-mode control, LangGraph workflow runtime endpoints,
 * media upload support, and zero fabricated tokens.
 */

import { getAuthHeadersAsync } from "./auth";

export class ApiError extends Error {
  readonly status: number;
  readonly code?: string;
  readonly details?: unknown;

  constructor(message: string, status = 500, code?: string, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export type CivitasEnvelope<T> =
  | { success: true; data: T; trace_id?: string; timestamp?: string }
  | { success: false; error: { message: string; code?: string; details?: unknown } };

export function unwrapEnvelope<T>(payload: CivitasEnvelope<T>): T {
  if (!payload || typeof payload !== "object") {
    throw new ApiError("Malformed response payload received from server.", 502);
  }
  if (!payload.success) {
    const err = payload.error || { message: "Unknown API error" };
    throw new ApiError(err.message, 400, err.code, err.details);
  }
  return payload.data;
}

export function getApiBaseUrl(): string {
  const raw =
    typeof window !== "undefined"
      ? (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1")
      : (process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1");
  const trimmed = raw.replace(/\/+$/, "");
  if (trimmed.endsWith("/api/v1")) return trimmed;
  return `${trimmed}/api/v1`;
}

export function isDemoMode(): boolean {
  return process.env.NEXT_PUBLIC_CIVITAS_DEMO_MODE === "true";
}

export type IncidentPriority =
  | "Low"
  | "Medium"
  | "High"
  | "Critical"
  | "P1"
  | "P2"
  | "P3"
  | "Unassigned";

export interface IncidentRecord {
  id: string;
  title: string;
  category: string;
  priority: IncidentPriority;
  severityScore: number | null;
  reportsCount: number;
  primaryDepartment: string;
  secondaryDepartments: string[];
  status: string;
  location: {
    landmark: string;
    latitude: number | null;
    longitude: number | null;
  };
  submittedAt: string | null;
  workOrderId?: string;
  workOrderSummary?: string;
  workflowId?: string;
  workflowStatus?: WorkflowStatusType;
  workflowTraceId?: string;
}

export interface IncidentTraceStep {
  step: string;
  status: "completed" | "in_progress" | "waiting_review" | "pending";
  timestamp: string;
  details: string;
}

export type WorkflowStatusType =
  | "RUNNING"
  | "WAITING_FOR_CLARIFICATION"
  | "WAITING_FOR_REVIEW"
  | "COMPLETED"
  | "REJECTED"
  | "FAILED";

export interface WorkflowSummary {
  workflow_id: string;
  report_id: string;
  incident_id?: string | null;
  trace_id: string;
  status: WorkflowStatusType;
  interrupt_type?: string | null;
  state?: {
    work_order_id?: string | null;
    warnings?: string[];
  };
}

export interface EditableWorkOrder {
  summary?: string;
  required_actions?: string[];
  suggested_resources?: string[];
  safety_notes?: string[];
}

export interface RoutingOverride {
  primary_department: string;
  secondary_departments?: string[];
  escalation_required?: boolean;
  rationale?: string[];
  policy_references?: string[];
}

export interface WorkflowReviewRequest {
  action: "approve" | "edit" | "reroute" | "reject" | "request_more_evidence";
  notes?: string;
  routing?: RoutingOverride;
  operational_plan?: EditableWorkOrder;
}

export interface UploadedMediaRecord {
  media_id: string;
  report_id: string;
  kind: "image" | "video";
  mime_type: string;
  bytes_size: number;
  storage_path: string;
  uploaded_at: string;
  signed_url?: string;
}

export interface UserProfileResponse {
  user_id: string;
  email: string;
  role: string;
  display_name: string;
}

interface RawIncidentPayload {
  incident_id?: string;
  id?: string;
  title?: string;
  category?: string;
  priority?: IncidentPriority;
  priority_level?: IncidentPriority;
  severity_score?: number;
  severityScore?: number;
  duplicates_seen?: number;
  reportsCount?: number;
  assigned_department?: string;
  primaryDepartment?: string;
  secondary_departments?: string[];
  status?: string;
  landmark?: string;
  latitude?: number | string;
  longitude?: number | string;
  reported_at?: string;
  submittedAt?: string;
  assigned_work_order_id?: string;
  workOrderId?: string;
  work_order_summary?: string;
  workOrderSummary?: string;
  workflow_id?: string;
  workflow_status?: WorkflowStatusType;
  workflow_trace_id?: string;
}

interface RawIncidentDetailPayload extends RawIncidentPayload {
  description?: string;
  latest_assessment?: {
    severity_score?: number;
    priority_level?: IncidentPriority;
  };
  routing_decisions?: Array<{
    primary_department?: string;
    secondary_departments?: string[];
  }>;
  work_orders?: Array<{
    work_order_id?: string;
    summary?: string;
    primary_department?: string;
    secondary_departments?: string[];
  }>;
}

interface RawIncidentListContainer {
  incidents?: RawIncidentPayload[];
  count?: number;
}

// Labeled fixtures for explicit demo mode only
export const DEMO_SEEDED_INCIDENTS: IncidentRecord[] = [
  {
    id: "INC-0241",
    title: "School Crossing Water Main Leakage",
    category: "Water Supply & Drainage",
    priority: "High",
    severityScore: 78,
    reportsCount: 3,
    primaryDepartment: "Water Supply & Drainage",
    secondaryDepartments: ["Traffic Coordination"],
    status: "WAITING_FOR_REVIEW",
    location: {
      landmark: "14m from DAV Public School Gate",
      latitude: 20.2961,
      longitude: 85.8245,
    },
    submittedAt: "2026-08-07T08:42:00Z",
    workOrderId: "WO-0241-A",
    workOrderSummary: "Dispatch ductile collar repair sleeve (8-inch) + excavation crew to Ward 12.",
    workflowId: "wf-demo-water-0241",
  },
  {
    id: "INC-0240",
    title: "Fallen Banyan Tree Branch Blocking Road",
    category: "Parks & Urban Forestry",
    priority: "Medium",
    severityScore: 45,
    reportsCount: 2,
    primaryDepartment: "Parks & Urban Forestry",
    secondaryDepartments: [],
    status: "ASSIGNED",
    location: {
      landmark: "Opposite Community Garden",
      latitude: 20.2985,
      longitude: 85.821,
    },
    submittedAt: "2026-08-07T07:15:00Z",
    workOrderId: "WO-0240-B",
    workOrderSummary: "Clear heavy obstruction from primary roadway and clear footpath.",
    workflowId: "wf-demo-tree-0240",
  },
  {
    id: "INC-0238",
    title: "Streetlight Cluster Power Failure",
    category: "Electrical & Public Lighting",
    priority: "High",
    severityScore: 62,
    reportsCount: 1,
    primaryDepartment: "Electrical Works",
    secondaryDepartments: [],
    status: "WAITING_FOR_CLARIFICATION",
    location: {
      landmark: "Commercial Junction Poles #104-106",
      latitude: 20.294,
      longitude: 85.829,
    },
    submittedAt: "2026-08-06T21:30:00Z",
    workflowId: "wf-demo-light-0238",
  },
  {
    id: "INC-0235",
    title: "Severe Asphalt Pothole on Bus Route",
    category: "Road Infrastructure",
    priority: "High",
    severityScore: 84,
    reportsCount: 4,
    primaryDepartment: "Road Maintenance",
    secondaryDepartments: ["Traffic Control"],
    status: "RESOLVED",
    location: {
      landmark: "Near City Hospital Exit",
      latitude: 20.2885,
      longitude: 85.8268,
    },
    submittedAt: "2026-08-06T14:10:00Z",
    workOrderId: "WO-0235-C",
    workOrderSummary: "Hot-mix asphalt patch completed and road surface leveled.",
    workflowId: "wf-demo-road-0235",
  },
];

// Helper to format human-readable workflow status
export function formatWorkflowStatus(status: WorkflowStatusType | string): {
  label: string;
  tone: "neutral" | "good" | "warn" | "danger";
} {
  const norm = (status || "").toUpperCase();
  switch (norm) {
    case "WAITING_FOR_REVIEW":
    case "WAITING_FOR_HUMAN_REVIEW":
      return { label: "Review Required", tone: "warn" };
    case "WAITING_FOR_CLARIFICATION":
      return { label: "Clarification Needed", tone: "danger" };
    case "RUNNING":
      return { label: "Processing", tone: "neutral" };
    case "COMPLETED":
    case "APPROVED":
    case "RESOLVED":
      return { label: "Completed", tone: "good" };
    case "REJECTED":
      return { label: "Rejected", tone: "danger" };
    case "FAILED":
      return { label: "Failed", tone: "danger" };
    default:
      return { label: status || "Submitted", tone: "neutral" };
  }
}

/**
 * Fetch verified profile identity for current session.
 */
export async function fetchMe(): Promise<UserProfileResponse | null> {
  const headers = await getAuthHeadersAsync();
  if (!headers.Authorization) {
    return null;
  }
  const res = await fetch(`${getApiBaseUrl()}/me`, { headers });
  if (!res.ok) {
    if (res.status === 401) return null;
    throw new ApiError(`Failed to fetch current user profile (HTTP ${res.status})`, res.status);
  }
  const envelope = (await res.json()) as CivitasEnvelope<UserProfileResponse>;
  return unwrapEnvelope(envelope);
}

/**
 * Fetch incident list from backend operations API.
 */
export async function fetchIncidents(): Promise<IncidentRecord[]> {
  try {
    const headers = await getAuthHeadersAsync();
    const res = await fetch(`${getApiBaseUrl()}/incidents`, {
      headers,
      next: { revalidate: 5 },
    });
    if (!res.ok) {
      throw new ApiError(`Failed to fetch incidents (HTTP ${res.status})`, res.status);
    }
    const envelope = (await res.json()) as CivitasEnvelope<RawIncidentListContainer | RawIncidentPayload[]>;
    const unwrapped = unwrapEnvelope(envelope);
    const rawList: RawIncidentPayload[] = Array.isArray(unwrapped)
      ? unwrapped
      : unwrapped.incidents || [];

    if (!rawList.length && isDemoMode()) {
      return DEMO_SEEDED_INCIDENTS;
    }

    return rawList.map((item: RawIncidentPayload) => {
      const lat = item.latitude !== undefined && item.latitude !== null && !isNaN(Number(item.latitude)) ? Number(item.latitude) : null;
      const lng = item.longitude !== undefined && item.longitude !== null && !isNaN(Number(item.longitude)) ? Number(item.longitude) : null;
      const landmark = item.landmark || (lat !== null && lng !== null ? `Coordinates (${lat.toFixed(4)}°, ${lng.toFixed(4)}°)` : "Location unavailable");

      return {
        id: item.incident_id || item.id || "INC-UNKNOWN",
        title: item.title || (item.category ? `${item.category.replace(/_/g, " ")} Incident` : `Incident ${item.incident_id || item.id}`),
        category: item.category ? item.category.replace(/_/g, " ") : "General Incident",
        priority: (item.priority_level || item.priority || "Unassigned") as IncidentPriority,
        severityScore: item.severity_score ?? item.severityScore ?? null,
        reportsCount: item.duplicates_seen || item.reportsCount || 1,
        primaryDepartment: item.assigned_department || item.primaryDepartment || "Unassigned",
        secondaryDepartments: item.secondary_departments || [],
        status: item.status || "submitted",
        location: {
          landmark,
          latitude: lat,
          longitude: lng,
        },
        submittedAt: item.reported_at || item.submittedAt || null,
        workOrderId: item.assigned_work_order_id || item.workOrderId,
        workOrderSummary: item.work_order_summary || item.workOrderSummary,
        workflowId: item.workflow_id,
        workflowStatus: item.workflow_status,
        workflowTraceId: item.workflow_trace_id,
      };
    });
  } catch (err) {
    if (isDemoMode()) {
      return DEMO_SEEDED_INCIDENTS;
    }
    throw err instanceof ApiError ? err : new ApiError(err instanceof Error ? err.message : "Unable to reach Civitas API", 503);
  }
}

/**
 * Fetch detailed incident dossier by ID.
 */
export async function fetchIncidentDetail(id: string): Promise<IncidentRecord> {
  try {
    const headers = await getAuthHeadersAsync();
    const res = await fetch(`${getApiBaseUrl()}/incidents/${encodeURIComponent(id)}`, {
      headers,
    });
    if (!res.ok) {
      throw new ApiError(`Incident ${id} not found or inaccessible (HTTP ${res.status})`, res.status);
    }
    const envelope = (await res.json()) as CivitasEnvelope<RawIncidentDetailPayload>;
    const data = unwrapEnvelope(envelope);

    const lat = data.latitude !== undefined && data.latitude !== null && !isNaN(Number(data.latitude)) ? Number(data.latitude) : null;
    const lng = data.longitude !== undefined && data.longitude !== null && !isNaN(Number(data.longitude)) ? Number(data.longitude) : null;
    const landmark = data.landmark || (lat !== null && lng !== null ? `Coordinates (${lat.toFixed(4)}°, ${lng.toFixed(4)}°)` : "Location unavailable");

    return {
      id: data.incident_id || data.id || id,
      title: data.title || (data.category ? `${data.category.replace(/_/g, " ")} Incident` : `Incident ${id}`),
      category: data.category ? data.category.replace(/_/g, " ") : "Municipal Incident",
      priority: (data.latest_assessment?.priority_level || data.priority || "Unassigned") as IncidentPriority,
      severityScore: data.latest_assessment?.severity_score ?? data.severityScore ?? null,
      reportsCount: data.duplicates_seen || data.reportsCount || 1,
      primaryDepartment:
        data.assigned_department ||
        data.routing_decisions?.[0]?.primary_department ||
        data.work_orders?.[0]?.primary_department ||
        data.primaryDepartment ||
        "Unassigned",
      secondaryDepartments:
        data.routing_decisions?.[0]?.secondary_departments ||
        data.work_orders?.[0]?.secondary_departments ||
        data.secondary_departments ||
        [],
      status: data.status || "submitted",
      location: {
        landmark,
        latitude: lat,
        longitude: lng,
      },
      submittedAt: data.reported_at || data.submittedAt || null,
      workOrderId: data.assigned_work_order_id || (data.work_orders?.[0]?.work_order_id),
      workOrderSummary: data.work_orders?.[0]?.summary,
      workflowId: data.workflow_id,
      workflowStatus: data.workflow_status,
      workflowTraceId: data.workflow_trace_id,
    };
  } catch (err) {
    if (isDemoMode()) {
      const found = DEMO_SEEDED_INCIDENTS.find((item) => item.id === id || id === "demo-water");
      if (found) return found;
      return DEMO_SEEDED_INCIDENTS[0];
    }
    throw err instanceof ApiError ? err : new ApiError(err instanceof Error ? err.message : `Failed to load incident ${id}`, 500);
  }
}

/**
 * Submit a citizen report to the backend.
 */
export async function submitReport(payload: {
  description: string;
  category?: string;
  latitude?: number;
  longitude?: number;
}): Promise<{ report_id: string; status: string; description: string }> {
  if (
    payload.latitude === undefined ||
    payload.latitude === null ||
    payload.longitude === undefined ||
    payload.longitude === null ||
    isNaN(payload.latitude) ||
    isNaN(payload.longitude)
  ) {
    if (!isDemoMode()) {
      throw new ApiError("Valid latitude and longitude coordinates are required to submit a report.", 400);
    }
  }

  try {
    const headers = await getAuthHeadersAsync();
    const res = await fetch(`${getApiBaseUrl()}/reports`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...headers,
      },
      body: JSON.stringify({
        description: payload.description,
        location: {
          latitude: payload.latitude !== undefined && !isNaN(payload.latitude) ? payload.latitude : 20.29614,
          longitude: payload.longitude !== undefined && !isNaN(payload.longitude) ? payload.longitude : 85.82451,
        },
        citizen_selected_category: payload.category || null,
      }),
    });
    if (!res.ok) {
      let msg = `Report submission failed (HTTP ${res.status})`;
      try {
        const body = await res.json();
        if (body?.error?.message) msg = body.error.message;
        else if (body?.detail) msg = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      } catch {}
      throw new ApiError(msg, res.status);
    }
    const envelope = (await res.json()) as CivitasEnvelope<{ report_id: string; status: string; description: string }>;
    return unwrapEnvelope(envelope);
  } catch (err) {
    if (isDemoMode()) {
      return {
        report_id: `DEMO-RPT-${Math.floor(1000 + Math.random() * 9000)}`,
        status: "submitted",
        description: payload.description,
      };
    }
    throw err instanceof ApiError ? err : new ApiError(err instanceof Error ? err.message : "Failed to submit report", 500);
  }
}

/**
 * Extract GPS coordinates from a Google Maps or OpenStreetMap share link.
 */
export async function extractMapCoordinates(
  url: string
): Promise<{ latitude: number; longitude: number; source: string }> {
  if (!url || !url.trim()) {
    throw new ApiError("A valid map URL or coordinate string is required.", 422);
  }

  // Handle plain coords locally for instant response
  const plainMatch = url.trim().match(/^([+-]?\d+(?:\.\d+)?)\s*,\s*([+-]?\d+(?:\.\d+)?)$/);
  if (plainMatch) {
    const lat = parseFloat(plainMatch[1]);
    const lon = parseFloat(plainMatch[2]);
    if (lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180) {
      return { latitude: lat, longitude: lon, source: "plain" };
    }
  }

  try {
    const res = await fetch(`${getApiBaseUrl()}/map-extract`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: url.trim() }),
    });

    if (!res.ok) {
      let msg = "Could not extract coordinates from map link.";
      try {
        const body = await res.json();
        if (body?.detail?.message) msg = body.detail.message;
        else if (body?.error?.message) msg = body.error.message;
      } catch {}
      throw new ApiError(msg, res.status);
    }

    const envelope = (await res.json()) as CivitasEnvelope<{
      latitude: number;
      longitude: number;
      source: string;
      url: string;
    }>;
    return unwrapEnvelope(envelope);
  } catch (err) {
    if (isDemoMode()) {
      return { latitude: 20.29614, longitude: 85.82451, source: "demo" };
    }
    throw err instanceof ApiError ? err : new ApiError(err instanceof Error ? err.message : "Failed to parse map link", 500);
  }
}

/**
 * Upload photographic or video media attached to a report.
 */
export async function uploadReportMedia(
  reportId: string,
  file: File,
  capturedAt?: string
): Promise<UploadedMediaRecord> {
  const allowedMime = new Set([
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
    "video/mp4",
    "video/webm",
    "video/quicktime",
    "video/x-matroska",
  ]);

  if (!allowedMime.has(file.type.toLowerCase())) {
    throw new ApiError(
      `File format '${file.type}' is not supported. Please upload PNG, JPG, WEBP, or MP4.`,
      415
    );
  }

  const maxBytes = 50 * 1024 * 1024; // 50MB
  if (file.size > maxBytes) {
    throw new ApiError("Uploaded file exceeds the maximum permitted 50MB size limit.", 413);
  }

  try {
    const headers = await getAuthHeadersAsync();
    const formData = new FormData();
    formData.append("file", file);
    if (capturedAt) {
      formData.append("captured_at", capturedAt);
    }

    const res = await fetch(`${getApiBaseUrl()}/reports/${encodeURIComponent(reportId)}/media`, {
      method: "POST",
      headers,
      body: formData,
    });

    if (!res.ok) {
      let msg = `Media upload failed (HTTP ${res.status})`;
      try {
        const body = await res.json();
        if (body?.error?.message) msg = body.error.message;
        else if (body?.detail) msg = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      } catch {}
      throw new ApiError(msg, res.status);
    }

    const envelope = (await res.json()) as CivitasEnvelope<UploadedMediaRecord>;
    return unwrapEnvelope(envelope);
  } catch (err) {
    if (isDemoMode()) {
      return {
        media_id: `med-demo-${Math.floor(1000 + Math.random() * 9000)}`,
        report_id: reportId,
        kind: file.type.startsWith("video") ? "video" : "image",
        mime_type: file.type,
        bytes_size: file.size,
        storage_path: `${reportId}/${file.name}`,
        uploaded_at: new Date().toISOString(),
      };
    }
    throw err instanceof ApiError ? err : new ApiError(err instanceof Error ? err.message : "Media upload failed", 500);
  }
}

/**
 * Start LangGraph agent workflow for a submitted report.
 */
export async function startWorkflow(reportId: string): Promise<WorkflowSummary> {
  try {
    const headers = await getAuthHeadersAsync();
    const res = await fetch(`${getApiBaseUrl()}/reports/${encodeURIComponent(reportId)}/workflow`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...headers,
      },
    });
    if (!res.ok) {
      let msg = `Failed to start workflow runtime (HTTP ${res.status})`;
      try {
        const body = await res.json();
        if (body?.error?.message) msg = body.error.message;
        else if (body?.detail) msg = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      } catch {}
      throw new ApiError(msg, res.status);
    }
    const envelope = (await res.json()) as CivitasEnvelope<WorkflowSummary>;
    return unwrapEnvelope(envelope);
  } catch (err) {
    if (isDemoMode()) {
      return {
        workflow_id: `wf-demo-${reportId}`,
        report_id: reportId,
        trace_id: `trc-demo-${reportId}`,
        status: "WAITING_FOR_REVIEW",
        interrupt_type: "human_review",
        state: {
          work_order_id: `WO-DEMO-${reportId}`,
          warnings: [],
        },
      };
    }
    throw err instanceof ApiError ? err : new ApiError(err instanceof Error ? err.message : "Unable to start workflow", 500);
  }
}

/**
 * Retrieve current status & state of a running/interrupted workflow.
 */
export async function getWorkflow(workflowId: string): Promise<WorkflowSummary> {
  try {
    const headers = await getAuthHeadersAsync();
    const res = await fetch(`${getApiBaseUrl()}/workflows/${encodeURIComponent(workflowId)}`, {
      headers,
    });
    if (!res.ok) {
      throw new ApiError(`Workflow ${workflowId} not found (HTTP ${res.status})`, res.status);
    }
    const envelope = (await res.json()) as CivitasEnvelope<WorkflowSummary>;
    return unwrapEnvelope(envelope);
  } catch (err) {
    if (isDemoMode()) {
      return {
        workflow_id: workflowId,
        report_id: "demo-report-01",
        trace_id: "trc-demo-01",
        status: "WAITING_FOR_REVIEW",
        interrupt_type: "human_review",
        state: {
          work_order_id: "WO-0241-A",
          warnings: [],
        },
      };
    }
    throw err instanceof ApiError ? err : new ApiError(err instanceof Error ? err.message : "Unable to fetch workflow status", 500);
  }
}

/**
 * Submit answers to a clarification question, resuming LangGraph workflow execution.
 */
export async function submitWorkflowClarification(
  workflowId: string,
  answers: Record<string, string>
): Promise<WorkflowSummary> {
  const headers = await getAuthHeadersAsync();
  if (!headers.Authorization && !isDemoMode()) {
    throw new ApiError("Authentication required to submit clarification responses.", 401);
  }
  try {
    const res = await fetch(`${getApiBaseUrl()}/workflows/${encodeURIComponent(workflowId)}/clarification`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...headers,
      },
      body: JSON.stringify({ answers }),
    });
    if (!res.ok) {
      let msg = `Clarification submission failed (HTTP ${res.status})`;
      try {
        const body = await res.json();
        if (body?.error?.message) msg = body.error.message;
        else if (body?.detail) msg = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      } catch {}
      throw new ApiError(msg, res.status);
    }
    const envelope = (await res.json()) as CivitasEnvelope<WorkflowSummary>;
    return unwrapEnvelope(envelope);
  } catch (err) {
    if (isDemoMode()) {
      return {
        workflow_id: workflowId,
        report_id: "demo-report",
        trace_id: "trc-demo",
        status: "RUNNING",
        state: {},
      };
    }
    throw err instanceof ApiError ? err : new ApiError(err instanceof Error ? err.message : "Clarification submission failed", 500);
  }
}

/**
 * Submit supervisor decision to resume LangGraph workflow from WAITING_FOR_REVIEW.
 */
export async function submitWorkflowReview(
  workflowId: string,
  payload: WorkflowReviewRequest
): Promise<WorkflowSummary> {
  const headers = await getAuthHeadersAsync();
  if (!headers.Authorization && !isDemoMode()) {
    throw new ApiError("Municipal Reviewer authentication required to execute review decisions.", 401);
  }
  try {
    const res = await fetch(`${getApiBaseUrl()}/workflows/${encodeURIComponent(workflowId)}/review`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...headers,
      },
      body: JSON.stringify({
        action: payload.action,
        notes: payload.notes || null,
        routing: payload.routing || null,
        operational_plan: payload.operational_plan || null,
      }),
    });
    if (!res.ok) {
      let msg = `Supervisor review submission failed (HTTP ${res.status})`;
      try {
        const body = await res.json();
        if (body?.error?.message) msg = body.error.message;
        else if (body?.detail) msg = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      } catch {}
      throw new ApiError(msg, res.status);
    }
    const envelope = (await res.json()) as CivitasEnvelope<WorkflowSummary>;
    return unwrapEnvelope(envelope);
  } catch (err) {
    if (isDemoMode()) {
      return {
        workflow_id: workflowId,
        report_id: "demo-report",
        trace_id: "trc-demo",
        status: payload.action === "reject" ? "REJECTED" : "COMPLETED",
        state: {
          work_order_id: "WO-0241-A",
        },
      };
    }
    throw err instanceof ApiError ? err : new ApiError(err instanceof Error ? err.message : "Review submission failed", 500);
  }
}

/**
 * Legacy Work Order review endpoint fallback for backward compatibility.
 */
export async function approveWorkOrder(
  workOrderId: string,
  reviewAction: "approve" | "edit" | "reroute" | "reject",
  notes?: string
): Promise<{ status: string; updated_at: string }> {
  const headers = await getAuthHeadersAsync();
  if (!headers.Authorization && !isDemoMode()) {
    throw new ApiError("Reviewer authentication required.", 401);
  }
  try {
    const endpoint =
      reviewAction === "reject"
        ? `${getApiBaseUrl()}/work-orders/${encodeURIComponent(workOrderId)}/reject`
        : `${getApiBaseUrl()}/work-orders/${encodeURIComponent(workOrderId)}/approve`;

    const res = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...headers,
      },
      body: JSON.stringify({ notes }),
    });
    if (!res.ok) throw new ApiError(`Work order review action failed (HTTP ${res.status})`, res.status);
    const envelope = (await res.json()) as CivitasEnvelope<{ status: string; updated_at: string }>;
    return unwrapEnvelope(envelope);
  } catch (err) {
    if (isDemoMode()) {
      return {
        status: reviewAction === "approve" ? "APPROVED" : reviewAction === "reject" ? "REJECTED" : "MODIFIED",
        updated_at: new Date().toISOString(),
      };
    }
    throw err instanceof ApiError ? err : new ApiError(err instanceof Error ? err.message : "Work order review action failed", 500);
  }
}

/**
 * Fetch incident trace events.
 */
export async function fetchIncidentTrace(id: string): Promise<IncidentTraceStep[]> {
  try {
    const headers = await getAuthHeadersAsync();
    const res = await fetch(`${getApiBaseUrl()}/incidents/${encodeURIComponent(id)}/trace`, {
      headers,
    });
    if (!res.ok) throw new ApiError(`Trace not found (HTTP ${res.status})`, res.status);
    const envelope = (await res.json()) as CivitasEnvelope<IncidentTraceStep[]>;
    return unwrapEnvelope(envelope);
  } catch (err) {
    if (isDemoMode()) {
      return [
        { step: "Report Intake & Evidence Extraction", status: "completed", timestamp: "08:42:01", details: "3 report items normalized. Contradictions & source claims preserved." },
        { step: "Multimodal ML Analysis", status: "completed", timestamp: "08:42:04", details: "Duplicate similarity score 0.84. Primary category set to water_leakage." },
        { step: "Policy Grounding & Retrieval", status: "completed", timestamp: "08:42:06", details: "PLAY-WATER-01 & ROUTE-WATER-02 retrieved from municipal knowledge base." },
        { step: "Risk Assessment & Routing", status: "completed", timestamp: "08:42:08", details: "Severity: 78 (High). Priority: Critical (School crossing proximity)." },
        { step: "Work Order Synthesis & Critic Check", status: "completed", timestamp: "08:42:10", details: "Critic check passed. Non-binding estimate 8-14 hours." },
        { step: "Human Review Interrupt", status: "waiting_review", timestamp: "08:42:12", details: "Awaiting supervisor sign-off before dispatch." },
      ];
    }
    throw err instanceof ApiError ? err : new ApiError("Unable to retrieve trace events", 500);
  }
}
