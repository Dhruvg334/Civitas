import { renderToStaticMarkup } from "react-dom/server";
import { expect, it } from "vitest";
import Demo from "./page";

it("renders the seeded water-leak workflow story", () => {
  const html = renderToStaticMarkup(<Demo />);
  expect(html).toContain("GOLDEN SCENARIO / WATER LEAK");
  expect(html).toContain("REPORTS");
  expect(html).toContain("Three residents describe the same place differently");
});
