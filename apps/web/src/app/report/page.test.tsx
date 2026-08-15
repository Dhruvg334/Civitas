import { renderToStaticMarkup } from "react-dom/server";
import { expect, it, describe } from "vitest";

import Report from "./page";

describe("Report Page Component", () => {
  it("renders the first step with meaningful validation and quality meter", () => {
    const html = renderToStaticMarkup(<Report />);

    expect(html).toContain("required=\"\"");
    expect(html).toContain("minLength=\"8\"");
    expect(html).toContain("Describe what is happening");
    expect(html).toContain("REPORT EVIDENCE STRENGTH");
    expect(html).toContain("STEP 01 / 04");
  });

  it("renders all 8 incident categories from shared taxonomy", () => {
    const html = renderToStaticMarkup(<Report />);

    expect(html).toContain("Water Leak / Pipe Burst");
    expect(html).toContain("Pothole / Road Damage");
    expect(html).toContain("Broken Streetlight &amp; Power");
    expect(html).toContain("Fallen Tree &amp; Branches");
    expect(html).toContain("Garbage &amp; Waste Dumping");
  });
});
