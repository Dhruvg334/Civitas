import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { Nav, Status } from "./site";

describe("navigation", () => {
  it("renders global links, report action, and sign in", () => {
    const html = renderToStaticMarkup(<Nav />);
    expect(html).toContain("Workspace");
    expect(html).toContain("Report an issue");
    expect(html).toContain("Sign In");
  });
  it("exposes all three Explore choices", () => {
    const html = renderToStaticMarkup(<Nav />);
    expect(html).toContain("Explore Civitas");
    expect(html).toContain("Why It Is Needed");
    expect(html).toContain("Engineering Team");
  });
  it("renders documentation navigation", () => {
    const html = renderToStaticMarkup(<Nav docs />);
    expect(html).toContain("System");
    expect(html).toContain("Governance");
  });
  it("makes workflow status readable", () => {
    expect(renderToStaticMarkup(<Status>WAITING_FOR_REVIEW</Status>)).toContain("waiting for review");
  });
});
