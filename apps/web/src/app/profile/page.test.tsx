import { renderToStaticMarkup } from "react-dom/server";
import { expect, it, describe } from "vitest";

import Profile from "./page";

describe("Profile Page Component", () => {
  it("renders a safe signed-out profile state by default", () => {
    const html = renderToStaticMarkup(<Profile />);

    expect(html).toContain("Signed Out Preview");
    expect(html).toContain("Sign in or create account");
  });

  it("does not render demo persona switcher when demo mode is inactive", () => {
    const originalEnv = process.env.NEXT_PUBLIC_CIVITAS_DEMO_MODE;
    delete process.env.NEXT_PUBLIC_CIVITAS_DEMO_MODE;

    const html = renderToStaticMarkup(<Profile />);
    expect(html).not.toContain("ROLE PREVIEW (DEMO)");

    process.env.NEXT_PUBLIC_CIVITAS_DEMO_MODE = originalEnv;
  });
});
