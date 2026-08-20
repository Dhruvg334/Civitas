import { describe, expect, it, beforeEach, afterEach } from "vitest";
import {
  unwrapEnvelope,
  formatWorkflowStatus,
  submitWorkflowReview,
  submitWorkflowClarification,
  uploadReportMedia,
  getApiBaseUrl,
  isDemoMode,
} from "./api";
import {
  getAuthHeaders,
  getAuthHeadersAsync,
  setSession,
  clearSession,
  hasMinimumRole,
  getRoleTitle,
  signInWithPassword,
} from "./auth";
import {
  INCIDENT_CATEGORIES,
  getCategoryById,
  getCategoryBySlug,
  normalizeCategorySlug,
} from "./taxonomy";

describe("Civitas Envelope Validation", () => {
  it("unwraps Civitas success envelopes", () => {
    expect(unwrapEnvelope({ success: true, data: "ok" })).toBe("ok");
  });

  it("throws ApiError for failed envelopes with useful message", () => {
    expect(() =>
      unwrapEnvelope({ success: false, error: { message: "report not found", code: "NOT_FOUND" } })
    ).toThrow("report not found");
  });

  it("rejects non-object or null envelopes", () => {
    // @ts-expect-error testing runtime malformed payload
    expect(() => unwrapEnvelope(null)).toThrow("Malformed response payload");
  });
});

describe("API Base URL Configuration", () => {
  it("normalizes API base URL to include /api/v1 prefix", () => {
    const base = getApiBaseUrl();
    expect(base).toContain("/api/v1");
  });
});

describe("Authentication & Header Security", () => {
  beforeEach(() => {
    clearSession();
  });

  afterEach(() => {
    clearSession();
  });

  it("returns no Authorization header when unauthenticated (no fake token)", () => {
    const headers = getAuthHeaders();
    expect(headers.Authorization).toBeUndefined();
    expect(headers.Accept).toBe("application/json");
  });

  it("forwards real bearer token when user session is present", async () => {
    setSession({
      accessToken: "real.jwt.token",
      user: {
        id: "usr-123",
        email: "officer@bhubaneswar.gov.in",
        name: "Officer",
        role: "reviewer",
      },
    });

    const headers = await getAuthHeadersAsync();
    expect(headers.Authorization).toBe("Bearer real.jwt.token");
  });

  it("evaluates role ranking correctly", () => {
    expect(hasMinimumRole("reviewer", "citizen")).toBe(true);
    expect(hasMinimumRole("supervisor", "triage")).toBe(true);
    expect(hasMinimumRole("citizen", "reviewer")).toBe(false);
  });

  it("formats role titles cleanly", () => {
    expect(getRoleTitle("admin")).toContain("Administrator");
    expect(getRoleTitle("reviewer")).toContain("Reviewer");
    expect(getRoleTitle("citizen")).toContain("Citizen");
  });

  it("rejects protected review mutations when unauthenticated in production mode", async () => {
    const originalEnv = process.env.NEXT_PUBLIC_CIVITAS_DEMO_MODE;
    delete process.env.NEXT_PUBLIC_CIVITAS_DEMO_MODE;

    await expect(
      submitWorkflowReview("wf-test-123", { action: "approve" })
    ).rejects.toThrow("Municipal Reviewer authentication required");

    process.env.NEXT_PUBLIC_CIVITAS_DEMO_MODE = originalEnv;
  });

  it("rejects protected clarification mutations when unauthenticated in production mode", async () => {
    const originalEnv = process.env.NEXT_PUBLIC_CIVITAS_DEMO_MODE;
    delete process.env.NEXT_PUBLIC_CIVITAS_DEMO_MODE;

    await expect(
      submitWorkflowClarification("wf-test-123", { q1: "No electrical wires" })
    ).rejects.toThrow("Authentication required");

    process.env.NEXT_PUBLIC_CIVITAS_DEMO_MODE = originalEnv;
  });

  it("fails clearly when signInWithPassword is called without Supabase in production", async () => {
    const originalEnv = process.env.NEXT_PUBLIC_CIVITAS_DEMO_MODE;
    delete process.env.NEXT_PUBLIC_CIVITAS_DEMO_MODE;

    await expect(
      signInWithPassword("test@civic.local", "secret123")
    ).rejects.toThrow("Supabase identity provider is not configured");

    process.env.NEXT_PUBLIC_CIVITAS_DEMO_MODE = originalEnv;
  });
});

describe("Media Upload Validation", () => {
  it("rejects unsupported MIME types before network call", async () => {
    const file = new File(["dummy"], "malicious.exe", { type: "application/x-msdownload" });
    await expect(uploadReportMedia("rpt-123", file)).rejects.toThrow("File format 'application/x-msdownload' is not supported");
  });

  it("rejects files larger than 50MB", async () => {
    const largeFile = new File([new ArrayBuffer(10)], "giant.mp4", { type: "video/mp4" });
    Object.defineProperty(largeFile, "size", { value: 55 * 1024 * 1024 });

    await expect(uploadReportMedia("rpt-123", largeFile)).rejects.toThrow("exceeds the maximum permitted 50MB size limit");
  });
});

describe("Incident Taxonomy Contract", () => {
  it("defines the 5 core MVP categories plus extensions", () => {
    const core = INCIDENT_CATEGORIES.filter((c) => c.isMvpCore);
    expect(core.length).toBe(5);
    expect(core.map((c) => c.slug)).toEqual([
      "water_leakage",
      "pothole_road_damage",
      "broken_streetlight",
      "fallen_tree",
      "garbage_overflow",
    ]);
  });

  it("resolves categories by id and slug", () => {
    expect(getCategoryById("Water leak")?.slug).toBe("water_leakage");
    expect(getCategoryBySlug("pothole_road_damage")?.id).toBe("Pothole or road damage");
    expect(normalizeCategorySlug("Water leak")).toBe("water_leakage");
  });
});

describe("Explicit Demo Mode vs Production Errors", () => {
  it("recognizes demo mode from NEXT_PUBLIC_CIVITAS_DEMO_MODE", () => {
    process.env.NEXT_PUBLIC_CIVITAS_DEMO_MODE = "true";
    expect(isDemoMode()).toBe(true);

    process.env.NEXT_PUBLIC_CIVITAS_DEMO_MODE = "false";
    expect(isDemoMode()).toBe(false);

    delete process.env.NEXT_PUBLIC_CIVITAS_DEMO_MODE;
    expect(isDemoMode()).toBe(false);
  });

  it("formats workflow statuses with appropriate UX labels and tones", () => {
    expect(formatWorkflowStatus("WAITING_FOR_REVIEW")).toEqual({
      label: "Review Required",
      tone: "warn",
    });
    expect(formatWorkflowStatus("WAITING_FOR_CLARIFICATION")).toEqual({
      label: "Clarification Needed",
      tone: "danger",
    });
    expect(formatWorkflowStatus("COMPLETED")).toEqual({
      label: "Completed",
      tone: "good",
    });
    expect(formatWorkflowStatus("RUNNING")).toEqual({
      label: "Processing",
      tone: "neutral",
    });
  });
});

describe("Client-Side Image Optimization", () => {
  it("preserves small or non-image files without corruption", async () => {
    const { compressImageFile } = await import("./image-compress");
    const smallFile = new File(["fake-image-bytes"], "photo.jpg", { type: "image/jpeg" });
    const result = await compressImageFile(smallFile);
    expect(result.name).toBe("photo.jpg");
    expect(result.size).toBe(smallFile.size);

    const videoFile = new File(["fake-video-bytes"], "clip.mp4", { type: "video/mp4" });
    const videoResult = await compressImageFile(videoFile);
    expect(videoResult.name).toBe("clip.mp4");
  });
});
