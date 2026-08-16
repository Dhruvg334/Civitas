import { renderToStaticMarkup } from "react-dom/server";
import { expect, it } from "vitest";

import { ReviewFields, ReviewPanel } from "./review-panel";

it("keeps review controls narrow by default", () => {
  const html = renderToStaticMarkup(<ReviewPanel workflowId="wf-test-review" />);

  expect(html).toContain("Approve");
  expect(html).toContain("Reroute");
  expect(html).not.toContain("Work-order summary");
  expect(html).not.toContain("Primary department");
});

it("limits EDIT and REROUTE to their permitted fields", () => {
  const dummySubmit = () => {};
  const edit = renderToStaticMarkup(<ReviewFields mode="edit" onSubmit={dummySubmit} />);
  const reroute = renderToStaticMarkup(<ReviewFields mode="reroute" onSubmit={dummySubmit} />);
  const reject = renderToStaticMarkup(<ReviewFields mode="reject" onSubmit={dummySubmit} />);
  const evidence = renderToStaticMarkup(<ReviewFields mode="evidence" onSubmit={dummySubmit} />);

  expect(edit).toContain("Work-order summary");
  expect(edit).not.toContain("Primary department");
  expect(reroute).toContain("Grounded policy references");
  expect(reroute).not.toContain("Work-order summary");
  expect(reject).toContain("Reason for rejection");
  expect(evidence).toContain("Evidence needed");
});
