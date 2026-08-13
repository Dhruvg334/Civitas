import { renderToStaticMarkup } from "react-dom/server";
import { expect, it } from "vitest";

import Report from "./page";

it("renders the first step with meaningful validation", () => {
  const html = renderToStaticMarkup(<Report />);

  expect(html).toContain("required=\"\"");
  expect(html).toContain("minLength=\"3\"");
  expect(html).toContain("Describe the issue");
  expect(html).toContain("I’m not sure");
  expect(html).toContain("STEP 01 / 04");
});
