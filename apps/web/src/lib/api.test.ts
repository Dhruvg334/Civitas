import { expect, it } from "vitest";
import { unwrapEnvelope } from "./api";

it("unwraps Civitas success envelopes", () => expect(unwrapEnvelope({ success: true, data: "ok" })).toBe("ok"));
it("exposes a useful Civitas error message", () => expect(() => unwrapEnvelope({ success: false, error: { message: "report not found" } })).toThrow("report not found"));
