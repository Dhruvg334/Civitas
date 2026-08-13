import { renderToStaticMarkup } from "react-dom/server";
import { expect, it } from "vitest";

import { ReviewFields, ReviewPanel } from "./review-panel";

it("keeps review controls narrow by default", () => {
  const html = renderToStaticMarkup(<ReviewPanel />);

  expect(html).toContain("Approve");
  expect(html).toContain("Reroute");
  expect(html).not.toContain("Work-order summary");
  expect(html).not.toContain("Primary department");
});

it("limits EDIT and REROUTE to their permitted fields", () => {
  const edit = renderToStaticMarkup(<ReviewFields mode="edit" />);
  const reroute = renderToStaticMarkup(<ReviewFields mode="reroute" />);

  expect(edit).toContain("Work-order summary");
  expect(edit).not.toContain("Primary department");
  expect(reroute).toContain("Grounded policy references");
  expect(reroute).not.toContain("Work-order summary");
});
