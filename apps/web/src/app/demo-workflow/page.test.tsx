import { renderToStaticMarkup } from "react-dom/server";
import { expect, it } from "vitest";

import Demo from "./page";

it("renders the seeded water-leak workflow evidence", () => {
  const html = renderToStaticMarkup(<Demo />);
  expect(html).toContain("GOLDEN RUNTIME SLICE / BHUBANESWAR DEMO");
  expect(html).toContain("INC-0241");
  expect(html).toContain("Omnichannel reports enter with zero-trust EXIF");
});
