import { renderToStaticMarkup } from "react-dom/server";
import { expect, it } from "vitest";

import Report from "./page";

it("renders validation requirements for a report", () => {
  const html = renderToStaticMarkup(<Report />);

  expect(html).toContain("required=\"\"");
  expect(html).toContain("minLength=\"3\"");
  expect(html).toContain("Latitude");
  expect(html).toContain("Longitude");
});
