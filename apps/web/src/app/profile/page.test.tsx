import { renderToStaticMarkup } from "react-dom/server";
import { expect, it } from "vitest";

import Profile from "./page";

it("renders a safe signed-out profile state", () => {
  const html = renderToStaticMarkup(<Profile />);

  expect(html).toContain("Signed-out preview");
  expect(html).toContain("sign in required");
});
