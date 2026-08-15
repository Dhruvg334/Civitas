import { renderToStaticMarkup } from "react-dom/server";
import { expect, it } from "vitest";

import Report from "./page";

it("renders the first step with meaningful validation and quality meter", () => {
  const html = renderToStaticMarkup(<Report />);

  expect(html).toContain("required=\"\"");
  expect(html).toContain("minLength=\"8\"");
  expect(html).toContain("Describe what is happening");
  expect(html).toContain("REPORT EVIDENCE STRENGTH");
  expect(html).toContain("STEP 01 / 04");
});
