import { describe, expect, it, beforeEach, afterEach } from "vitest";
import {
  unwrapEnvelope,
  formatWorkflowStatus,
  submitWorkflowReview,
  submitWorkflowClarification,
  isDemoMode,
} from "./api";
import { getAuthHeaders, setSession, clearSession } from "./auth";

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

  it("forwards real bearer token when user session is present", () => {
    setSession({
      accessToken: "real.jwt.token",
      user: {
        id: "usr-123",
        email: "officer@bhubaneswar.gov.in",
        name: "Officer",
        role: "reviewer",
      },
    });

    const headers = getAuthHeaders();
    expect(headers.Authorization).toBe("Bearer real.jwt.token");
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
