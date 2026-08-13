import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { Nav, Status } from "./site";

describe("navigation", () => {
  it("renders global links and report action", () => {
    const html = renderToStaticMarkup(<Nav />);
    expect(html).toContain("Workspace");
    expect(html).toContain("Demo");
    expect(html).toContain("Report an issue");
  });
  it("exposes all three About choices", () => {
    const html = renderToStaticMarkup(<Nav />);
    expect(html).toContain("About App"); expect(html).toContain("Why It Is Needed"); expect(html).toContain("Team behind");
  });
  it("renders documentation navigation", () => {
    const html = renderToStaticMarkup(<Nav docs />);
    expect(html).toContain("System"); expect(html).toContain("Governance");
  });
  it("makes workflow status readable", () => { expect(renderToStaticMarkup(<Status>WAITING_FOR_REVIEW</Status>)).toContain("waiting for review"); });
});
